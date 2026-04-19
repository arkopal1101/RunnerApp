"""
Tests for coach notes — pace parsing, metrics computation, route integration.

LLM calls are disabled by default (no OPENAI_API_KEY in test env), so the
service falls back to rules-based text. Tests exercise the rules path +
confirm the DB cache works. Where we need to test the LLM path, we
monkeypatch `backend.coach._llm_generate`.
"""
import json
from datetime import date, timedelta

import pytest

from backend import coach
from backend.models import CoachNote, DailyCheckin, User


# ----------------------------- pace utilities -----------------------------

class TestPaceUtilities:
    @pytest.mark.parametrize("s, expected", [
        ("8:30", 510),
        ("10:00", 600),
        ("6:30/km", 390),
        ("<7:30", 450),
        ("~7:06", 426),
        ("10:30-11:00", 630),  # takes first
        ("invalid", None),
        (None, None),
        ("", None),
    ])
    def test_pace_to_seconds(self, s, expected):
        assert coach.pace_to_seconds(s) == expected

    def test_seconds_to_pace(self):
        assert coach.seconds_to_pace(510) == "8:30/km"
        assert coach.seconds_to_pace(426) == "7:06/km"
        assert coach.seconds_to_pace(600) == "10:00/km"

    @pytest.mark.parametrize("target, expected", [
        ("10:30-11:00", (630, 660)),
        ("<7:30", (None, 450)),
        ("~7:06", (426, 426)),
        ("tempo ~6:30", (390, 390)),
        ("", (None, None)),
        (None, (None, None)),
    ])
    def test_target_pace_range(self, target, expected):
        assert coach.target_pace_range_seconds(target) == expected


# ----------------------------- pre-run metrics -----------------------------

class TestPreRunMetrics:
    def _seed_user(self, db):
        user = User(username="arko", password_hash="$2b$12$xxxxxxxxxxxxxxxxxxxxxx")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def _seed_checkin(self, db, user, days_ago, pace, hr=142, distance=5.0):
        d = (date.today() - timedelta(days=days_ago)).isoformat()
        c = DailyCheckin(
            user_id=user.id, checkin_date=d, avg_pace_per_km=pace,
            avg_hr_bpm=hr, total_distance_km=distance,
        )
        db.add(c)
        db.commit()
        return c

    def test_no_history_returns_empty_stats(self, db):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        m = coach.compute_pre_run_metrics(db, user, date.today(), 1, 1)
        assert m["recent_run_count"] == 0
        assert m["recent_avg_pace_sec"] is None
        assert m["trend"] == "insufficient_data"

    def test_improving_trend_detected(self, db):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        # 4 runs: slow → fast
        for day, pace in [(20, "10:00"), (15, "9:30"), (10, "9:00"), (5, "8:30")]:
            self._seed_checkin(db, user, day, pace)
        m = coach.compute_pre_run_metrics(db, user, date.today(), 1, 1)
        assert m["recent_run_count"] == 4
        assert m["trend"] == "improving"

    def test_target_parsed_into_metrics(self, db):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        # Week 1 Tuesday = easy Z2 run, target pace 10:30-11:00
        m = coach.compute_pre_run_metrics(db, user, date.today(), 1, 1)
        assert m["target_pace"] == "10:30-11:00"
        assert m["target_pace_upper_sec"] == 660
        assert m["type_label"] == "Easy Zone 2 Run"


# ----------------------------- post-run metrics -----------------------------

class TestPostRunMetrics:
    def test_on_target_verdict(self, db):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        # Today (Sunday in test) = Week 1 long-run, target pace 10:30-11:00 (upper 660s)
        today = date.today()
        c = DailyCheckin(
            user_id=user.id, checkin_date=today.isoformat(),
            week_number=1, avg_pace_per_km="10:30", avg_hr_bpm=148.0,
            total_distance_km=6.0,
        )
        db.add(c); db.commit(); db.refresh(c)
        m = coach.compute_post_run_metrics(db, user, c)
        # 10:30 = 630s. Target upper = 660s. Offset = -30 → ahead_of_target
        assert m["pace_offset_sec"] == -30
        assert m["pace_verdict"] == "ahead_of_target"

    def test_behind_target_verdict(self, db):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        # Seed on a Tuesday where target is 10:30-11:00 (upper=660)
        # Run at 12:00 = 720s → offset = +60 → behind
        today = date.today()
        # Use Tuesday to match the plan's target pace for weekday 1
        dow_today = today.weekday()
        tuesday = today - timedelta(days=dow_today - 1) if dow_today >= 1 else today + timedelta(days=1)
        c = DailyCheckin(
            user_id=user.id, checkin_date=tuesday.isoformat(),
            week_number=1, avg_pace_per_km="12:00", avg_hr_bpm=155.0,
            total_distance_km=3.0,
        )
        db.add(c); db.commit(); db.refresh(c)
        m = coach.compute_post_run_metrics(db, user, c)
        assert m["pace_verdict"] == "behind"
        assert m["pace_offset_sec"] >= 60

    def test_splits_negative_split_detected(self, db):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        today = date.today()
        splits = [
            {"km": 1, "pace_per_km": "10:00", "hr_bpm": 140},
            {"km": 2, "pace_per_km": "9:50", "hr_bpm": 143},
            {"km": 3, "pace_per_km": "9:30", "hr_bpm": 144},
            {"km": 4, "pace_per_km": "9:20", "hr_bpm": 146},
        ]
        c = DailyCheckin(
            user_id=user.id, checkin_date=today.isoformat(), week_number=1,
            avg_pace_per_km="9:40", total_distance_km=4.0,
            splits_json=json.dumps(splits),
        )
        db.add(c); db.commit(); db.refresh(c)
        m = coach.compute_post_run_metrics(db, user, c)
        assert m["split_summary"] is not None
        assert m["split_summary"]["type"] == "negative"


# ----------------------------- rules fallback text -----------------------------

class TestRulesFallback:
    def test_rest_day_returns_rest_message(self):
        m = {"day_type": "rest", "plan_note": "Recover well."}
        text = coach._rules_pre_run_text(m)
        assert "rest" in text.lower()

    def test_post_run_behind_target_mentions_offset(self):
        m = {
            "type_label": "Easy Zone 2 Run", "actual_distance_km": 4.0,
            "actual_pace": "12:00", "actual_avg_hr": 155, "pace_offset_sec": 90,
            "pace_verdict": "behind", "hr_verdict": "over_cap",
        }
        text = coach._rules_post_run_text(m)
        assert "+90" in text or "90" in text
        assert "HR" in text or "hr" in text


# ----------------------------- caching & DB integration -----------------------------

class TestNoteCaching:
    def test_pre_run_note_cached_per_day(self, db):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        n1 = coach.get_or_create_pre_run_note(db, user, date.today(), 1, 1)
        n2 = coach.get_or_create_pre_run_note(db, user, date.today(), 1, 1)
        assert n1.id == n2.id
        # Only one row in table
        assert db.query(CoachNote).filter(CoachNote.note_type == "pre").count() == 1

    def test_post_run_note_cached_per_checkin(self, db):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        c = DailyCheckin(
            user_id=user.id, checkin_date=date.today().isoformat(),
            week_number=1, avg_pace_per_km="10:00", avg_hr_bpm=142,
            total_distance_km=5.0,
        )
        db.add(c); db.commit(); db.refresh(c)
        n1 = coach.get_or_create_post_run_note(db, user, c)
        n2 = coach.get_or_create_post_run_note(db, user, c)
        assert n1.id == n2.id

    def test_falls_back_to_rules_when_llm_unavailable(self, db, monkeypatch):
        # Ensure we test the no-LLM path even if .env set a real key
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        note = coach.get_or_create_pre_run_note(db, user, date.today(), 1, 1)
        assert note.model_used == "rules"
        assert len(note.text) > 10

    def test_uses_llm_when_available(self, db, monkeypatch):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        monkeypatch.setattr(coach, "_llm_generate", lambda sys, user_p, max_tokens=180: ("LLM said hi.", "gpt-5-nano"))
        note = coach.get_or_create_pre_run_note(db, user, date.today(), 1, 1)
        assert note.text == "LLM said hi."
        assert note.model_used == "gpt-5-nano"


# ----------------------------- route integration -----------------------------

class TestCoachRoutes:
    def test_pre_run_endpoint_requires_auth(self, client):
        r = client.get("/api/coach/pre-run")
        assert r.status_code == 401

    def test_pre_run_endpoint_returns_note(self, client, auth_headers, monkeypatch):
        # Pin to rules path so test is deterministic regardless of env
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        r = client.get("/api/coach/pre-run", headers=auth_headers)
        assert r.status_code == 200
        j = r.json()
        assert j["type"] == "pre"
        assert len(j["text"]) > 0
        assert j["model"] in ("rules", "gpt-5-nano", "gpt-5-mini")

    def test_pre_run_endpoint_is_cached(self, client, auth_headers):
        r1 = client.get("/api/coach/pre-run", headers=auth_headers).json()
        r2 = client.get("/api/coach/pre-run", headers=auth_headers).json()
        assert r1["id"] == r2["id"]

    def test_post_run_endpoint_404_for_missing_checkin(self, client, auth_headers):
        r = client.get("/api/coach/post-run/99999", headers=auth_headers)
        assert r.status_code == 404

    def test_post_run_endpoint_for_existing_checkin(self, client, auth_headers, db):
        # Seed a checkin via API so user_id resolution stays consistent
        user = db.query(User).filter(User.username == "arko").first()
        c = DailyCheckin(
            user_id=user.id, checkin_date=date.today().isoformat(),
            week_number=1, avg_pace_per_km="10:00", avg_hr_bpm=140,
            total_distance_km=5.0,
        )
        db.add(c); db.commit(); db.refresh(c)
        r = client.get(f"/api/coach/post-run/{c.id}", headers=auth_headers)
        assert r.status_code == 200
        j = r.json()
        assert j["type"] == "post"
        assert j["checkin_id"] == c.id

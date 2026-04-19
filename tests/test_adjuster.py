"""
Tests for dynamic plan adjuster.

Verify:
- guardrails clamp distance and pace to the allowed range
- adjustments are stored and replace prior adjustments on re-run
- adjustments only land on run/long-run/tempo days, never rest/strength
- /api/plan/week merges adjustments into the response with a flag + rationale
- with no LLM key, run_adjuster is a no-op
- when weekly log saved → adjuster triggered (if LLM available via mock)
"""
import json

import pytest

from backend import plan_data
from backend.services import adjuster
from backend.models import DailyCheckin, PlanAdjustment, User, WeeklyLog


# ----------------------------- guardrails -----------------------------

class TestGuardrails:
    @pytest.mark.parametrize("original, proposed, expected", [
        (10.0, 10.0, 10.0),         # no change
        (10.0, 11.0, 11.0),         # +10% ok
        (10.0, 15.0, 12.0),         # +50% clamped to +20%
        (10.0, 5.0, 8.0),           # -50% clamped to -20%
        (10.0, None, None),
        (None, 5.0, None),
    ])
    def test_clamp_distance(self, original, proposed, expected):
        result = adjuster._clamp_distance(original, proposed)
        if expected is None:
            assert result is None
        else:
            assert result == pytest.approx(expected, abs=0.01)

    def test_clamp_pace_within_bounds_keeps_value(self):
        # Original target pace upper bound 10:30 = 630s.
        # Proposed 10:00 = 600s, delta -30s (~5%), within ±10% → allowed.
        result = adjuster._clamp_pace("10:30-11:00", "10:00")
        assert result is not None
        # Result string should round-trip to ~600 seconds
        assert adjuster.pace_to_seconds(result) == 600

    def test_clamp_pace_beyond_bounds_clamps(self):
        # Baseline 630s. Proposed 500s = -21% → clamp to -10% = 567s = 9:27
        result = adjuster._clamp_pace("10:30-11:00", "8:00")
        assert result is not None
        sec = adjuster.pace_to_seconds(result)
        assert sec >= int(630 * 0.9) - 1  # allow 1s rounding


# ----------------------------- persistence -----------------------------

class TestApplyAndStore:
    def _user(self, db):
        u = User(username="u1", password_hash="x")
        db.add(u); db.commit(); db.refresh(u)
        return u

    def test_skips_non_run_days(self, db):
        user = self._user(db)
        # Week 1 Monday (dow=0) is strength — adjustments to it must be ignored
        llm_out = [{"week": 3, "day_of_week": 0, "adjusted_distance_km": 5.0, "rationale": "x"}]
        rows = adjuster._apply_and_store(db, user.id, llm_out, [3])
        assert rows == []
        assert db.query(PlanAdjustment).count() == 0

    def test_skips_days_with_no_real_change(self, db):
        user = self._user(db)
        # Week 3 Tuesday run: distance 5.0, pace "10:00-10:30".
        # Propose same values → no actual change → skipped.
        original = plan_data.get_day(3, 1)
        llm_out = [{
            "week": 3, "day_of_week": 1,
            "adjusted_distance_km": original["targets"]["distance_km"],
            "adjusted_pace": original["targets"]["target_pace"],
            "rationale": "no-op",
        }]
        rows = adjuster._apply_and_store(db, user.id, llm_out, [3])
        assert rows == []

    def test_applies_valid_run_day_adjustment(self, db):
        user = self._user(db)
        # Week 3 Tuesday (dow=1): original 5km, pace 10:00-10:30.
        # Propose 6km (within +20%) and "9:30" (within -10%).
        llm_out = [{
            "week": 3, "day_of_week": 1,
            "adjusted_distance_km": 6.0,
            "adjusted_pace": "9:30",
            "rationale": "Runner is ahead of pace trend.",
        }]
        rows = adjuster._apply_and_store(db, user.id, llm_out, [3])
        assert len(rows) == 1
        # Reloaded via get_adjusted_day
        adj = adjuster.get_adjusted_day(db, user.id, 3, 1)
        assert adj is not None
        assert adj["day"]["targets"]["distance_km"] == pytest.approx(6.0, abs=0.01)
        assert adj["rationale"] == "Runner is ahead of pace trend."

    def test_rerun_replaces_prior_adjustments(self, db):
        user = self._user(db)
        # First batch
        adjuster._apply_and_store(db, user.id, [{
            "week": 3, "day_of_week": 1, "adjusted_distance_km": 6.0, "rationale": "first"
        }], [3])
        # Second batch targeting same week — should replace
        adjuster._apply_and_store(db, user.id, [{
            "week": 3, "day_of_week": 1, "adjusted_distance_km": 5.5, "rationale": "second"
        }], [3])
        rows = db.query(PlanAdjustment).filter(PlanAdjustment.week_number == 3).all()
        assert len(rows) == 1
        assert rows[0].rationale == "second"


class TestNoLLMIsNoOp:
    def test_run_adjuster_without_api_key(self, db, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)
        result = adjuster.run_adjuster(db, user)
        assert result == []
        assert db.query(PlanAdjustment).count() == 0


class TestRunAdjusterWithMock:
    def test_mocked_llm_produces_stored_adjustments(self, db, monkeypatch):
        user = User(username="u1", password_hash="x")
        db.add(user); db.commit(); db.refresh(user)

        # Mock LLM to return a couple of valid adjustments for near-future weeks.
        # The adjuster picks target weeks as current+1..current+4.
        from backend.routes.progress import get_current_week
        curr = get_current_week()
        future_week = curr + 1
        if future_week > 31:
            pytest.skip("Plan complete — no future weeks to adjust")

        # Find a run day in future_week
        days = plan_data.get_days_for_week(future_week)
        dow = next((i for i, d in enumerate(days) if d["type"] in {"run", "long-run", "tempo", "intervals"}), None)
        assert dow is not None

        fake_response = {
            "adjustments": [{
                "week": future_week,
                "day_of_week": dow,
                "adjusted_distance_km": (days[dow]["targets"]["distance_km"] or 5.0) * 1.1,
                "rationale": "Mocked adjustment",
            }]
        }
        monkeypatch.setattr(adjuster, "_llm_generate_adjustments", lambda p: fake_response)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        rows = adjuster.run_adjuster(db, user)
        assert len(rows) >= 1
        assert any(r.week_number == future_week and r.day_of_week == dow for r in rows)


# ----------------------------- endpoint merge -----------------------------

class TestPlanEndpointMergesAdjustments:
    def test_adjusted_day_is_flagged_in_week_response(self, client, auth_headers, db):
        user = db.query(User).filter(User.username == "arko").first()
        # Pick week 3 Tuesday = run
        adjuster._apply_and_store(db, user.id, [{
            "week": 3, "day_of_week": 1,
            "adjusted_distance_km": 6.0, "adjusted_pace": "9:30",
            "rationale": "Runner trending ahead."
        }], [3])
        r = client.get("/api/plan/week/3", headers=auth_headers)
        assert r.status_code == 200
        days = r.json()["days"]
        tuesday = days[1]
        assert tuesday.get("adjusted") is True
        assert "Runner trending ahead" in tuesday.get("adjustment_rationale", "")
        # Non-adjusted days should have adjusted=False
        monday = days[0]
        assert monday.get("adjusted") is False

    def test_plan_today_returns_adjusted_when_applicable(self, client, auth_headers, db):
        user = db.query(User).filter(User.username == "arko").first()
        from datetime import date
        from backend.routes.today import get_current_week
        week = get_current_week()
        dow = date.today().weekday()
        day = plan_data.get_day(week, dow)
        if not day or day["type"] not in {"run", "long-run", "tempo", "intervals"}:
            pytest.skip("Today is not a run day — adjuster cannot adjust")
        adjuster._apply_and_store(db, user.id, [{
            "week": week, "day_of_week": dow,
            "adjusted_distance_km": (day["targets"]["distance_km"] or 5.0) * 1.1,
            "rationale": "Today adjustment"
        }], [week])
        r = client.get("/api/plan/today", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["day"]["adjusted"] is True

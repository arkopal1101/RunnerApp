"""
Tests for Phase F:
- DayLog CRUD + idempotent upsert + auto-completion on run save
- Workout upload endpoint stores image + creates DayLog (kind=strength)
- Baseline calibration (write-once, force override, validation)
"""
import io
from datetime import date

import pytest

from backend.models import DailyCheckin, DayLog, User


# ----------------------------- DayLog endpoint -----------------------------

class TestDayLogAuth:
    def test_post_requires_auth(self, client):
        r = client.post("/api/day-log", json={"kind": "rest", "week_number": 1, "day_of_week": 2})
        assert r.status_code == 401

    def test_week_get_requires_auth(self, client):
        r = client.get("/api/day-log/week/1")
        assert r.status_code == 401


class TestDayLogCreate:
    def test_create_rest_day_log(self, client, auth_headers):
        r = client.post("/api/day-log",
                        json={"kind": "rest", "week_number": 1, "day_of_week": 2},
                        headers=auth_headers)
        assert r.status_code == 200
        j = r.json()
        assert j["kind"] == "rest"
        assert j["week_number"] == 1
        assert j["day_of_week"] == 2

    def test_idempotent_upsert(self, client, auth_headers, db):
        # Two POSTs for the same week/dow should not create two rows
        for _ in range(2):
            client.post("/api/day-log",
                        json={"kind": "rest", "week_number": 1, "day_of_week": 2},
                        headers=auth_headers)
        count = db.query(DayLog).filter(
            DayLog.week_number == 1, DayLog.day_of_week == 2,
        ).count()
        assert count == 1

    def test_invalid_kind_rejected(self, client, auth_headers):
        r = client.post("/api/day-log",
                        json={"kind": "banana", "week_number": 1, "day_of_week": 0},
                        headers=auth_headers)
        assert r.status_code == 422

    def test_invalid_week_rejected(self, client, auth_headers):
        r = client.post("/api/day-log",
                        json={"kind": "rest", "week_number": 0, "day_of_week": 0},
                        headers=auth_headers)
        assert r.status_code == 422


class TestDayLogQueries:
    def test_week_endpoint_returns_keyed_map(self, client, auth_headers):
        # Log Mon and Sat as rest
        for dow in (0, 5):
            client.post("/api/day-log",
                        json={"kind": "rest", "week_number": 3, "day_of_week": dow},
                        headers=auth_headers)
        r = client.get("/api/day-log/week/3", headers=auth_headers)
        assert r.status_code == 200
        j = r.json()
        assert j["week"] == 3
        assert set(j["by_day_of_week"].keys()) == {"0", "5"}

    def test_all_endpoint(self, client, auth_headers):
        client.post("/api/day-log",
                    json={"kind": "rest", "week_number": 2, "day_of_week": 0},
                    headers=auth_headers)
        client.post("/api/day-log",
                    json={"kind": "rest", "week_number": 5, "day_of_week": 0},
                    headers=auth_headers)
        r = client.get("/api/day-log/all", headers=auth_headers)
        assert r.status_code == 200
        by_week = r.json()["by_week"]
        assert "2" in by_week and "5" in by_week


# ----------------------------- auto-completion on run save -----------------------------

class TestAutoCompleteOnRunSave:
    def test_checkin_daily_auto_creates_day_log(self, client, auth_headers, db):
        # POST a manual checkin via /api/checkin/daily — it should create a
        # DayLog row for that date automatically.
        import json as _json
        override = _json.dumps({
            "total_distance_km": 5.0,
            "avg_pace_per_km": "10:00",
            "avg_hr_bpm": 142,
            "splits": [],
        })
        checkin_date = "2026-04-15"  # Wed of Week 1 (dow=2)
        r = client.post("/api/checkin/daily",
                        data={"checkin_date": checkin_date, "override_json": override},
                        headers=auth_headers)
        assert r.status_code == 200
        checkin_id = r.json()["id"]

        # DayLog row should exist, kind=run, week=1, dow=2, linked to this checkin
        log = db.query(DayLog).filter(DayLog.checkin_id == checkin_id).first()
        assert log is not None
        assert log.kind == "run"
        assert log.week_number == 1
        assert log.day_of_week == 2


# ----------------------------- workout upload -----------------------------

class TestWorkoutUpload:
    def _fake_image(self):
        # Minimal 1x1 PNG
        import base64
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")
        return ("workout.png", io.BytesIO(png), "image/png")

    def test_workout_upload_creates_day_log(self, client, auth_headers, db):
        files = {"image": self._fake_image()}
        data = {"week_number": "1", "day_of_week": "0", "notes": "felt great"}
        r = client.post("/api/day-log/workout", files=files, data=data, headers=auth_headers)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["kind"] == "strength"
        assert j["week_number"] == 1
        assert j["day_of_week"] == 0
        assert j["notes"] == "felt great"
        # Verify exactly one DayLog row in DB for this week+day
        rows = db.query(DayLog).filter(DayLog.week_number == 1, DayLog.day_of_week == 0).all()
        assert len(rows) == 1
        assert rows[0].image_path is not None

    def test_workout_upload_idempotent(self, client, auth_headers, db):
        files = {"image": self._fake_image()}
        data = {"week_number": "1", "day_of_week": "0"}
        for _ in range(2):
            r = client.post("/api/day-log/workout", files=files, data=data, headers=auth_headers)
            assert r.status_code == 200
        rows = db.query(DayLog).filter(DayLog.week_number == 1, DayLog.day_of_week == 0).all()
        assert len(rows) == 1

    def test_workout_upload_requires_week_and_dow(self, client, auth_headers):
        files = {"image": self._fake_image()}
        r = client.post("/api/day-log/workout", files=files, data={}, headers=auth_headers)
        assert r.status_code == 422

    def test_workout_upload_requires_auth(self, client):
        files = {"image": self._fake_image()}
        data = {"week_number": "1", "day_of_week": "0"}
        r = client.post("/api/day-log/workout", files=files, data=data)
        assert r.status_code == 401


# ----------------------------- baseline calibration -----------------------------

class TestBaseline:
    def _seed_week1_runs(self, db, user_id, pace_list):
        """Seed Week 1 check-ins with the provided list of pace strings."""
        for i, pace in enumerate(pace_list):
            db.add(DailyCheckin(
                user_id=user_id,
                checkin_date=f"2026-04-{14 + i}",
                week_number=1,
                total_distance_km=4.0,
                avg_pace_per_km=pace,
                avg_hr_bpm=142,
            ))
        db.commit()

    def test_get_baseline_initial(self, client, auth_headers):
        r = client.get("/api/baseline", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["is_calibrated"] is False

    def test_calibrate_requires_minimum_runs(self, client, auth_headers, db):
        user = db.query(User).filter(User.username == "arko").first()
        self._seed_week1_runs(db, user.id, ["10:30"])  # only 1 run
        r = client.post("/api/baseline/calibrate", headers=auth_headers)
        assert r.status_code == 400

    def test_calibrate_happy_path(self, client, auth_headers, db):
        user = db.query(User).filter(User.username == "arko").first()
        # Three runs: 10:00 (600), 10:30 (630), 11:00 (660) → avg 630 = 10:30
        self._seed_week1_runs(db, user.id, ["10:00", "10:30", "11:00"])
        r = client.post("/api/baseline/calibrate", headers=auth_headers)
        assert r.status_code == 200
        j = r.json()
        assert j["is_calibrated"] is True
        assert j["baseline_pace_seconds"] == 630
        assert j["baseline_pace_str"] == "10:30/km"
        assert j["runs_used"] == 3

    def test_calibrate_write_once(self, client, auth_headers, db):
        user = db.query(User).filter(User.username == "arko").first()
        self._seed_week1_runs(db, user.id, ["10:00", "10:30"])
        r = client.post("/api/baseline/calibrate", headers=auth_headers)
        assert r.status_code == 200
        # Second call without force returns 409
        r2 = client.post("/api/baseline/calibrate", headers=auth_headers)
        assert r2.status_code == 409

    def test_calibrate_force_overrides(self, client, auth_headers, db):
        user = db.query(User).filter(User.username == "arko").first()
        self._seed_week1_runs(db, user.id, ["10:00", "10:30"])
        r = client.post("/api/baseline/calibrate", headers=auth_headers)
        first = r.json()["baseline_pace_seconds"]
        # Add a slow run, force recalibrate
        db.add(DailyCheckin(
            user_id=user.id, checkin_date="2026-04-18", week_number=1,
            total_distance_km=4.0, avg_pace_per_km="12:00", avg_hr_bpm=144,
        ))
        db.commit()
        r2 = client.post("/api/baseline/calibrate?force=true", headers=auth_headers)
        assert r2.status_code == 200
        second = r2.json()["baseline_pace_seconds"]
        assert second > first  # slower avg after adding the slow run

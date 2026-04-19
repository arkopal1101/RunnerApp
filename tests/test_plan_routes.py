"""
Integration tests for /api/plan/* endpoints.

Covers:
- auth enforcement (401 without bearer token)
- GET /api/plan/week/{n} for valid weeks and bad inputs
- GET /api/plan/all returns all 32 weeks
- GET /api/plan/today returns a day matching today's weekday
"""
from datetime import date

from backend.plan_data import DELOAD_WEEKS, RACE_WEEK


# ----------------------------- auth -----------------------------

class TestPlanRouteAuth:
    def test_week_requires_auth(self, client):
        r = client.get("/api/plan/week/1")
        assert r.status_code == 401

    def test_today_requires_auth(self, client):
        r = client.get("/api/plan/today")
        assert r.status_code == 401

    def test_all_requires_auth(self, client):
        r = client.get("/api/plan/all")
        assert r.status_code == 401


# ----------------------------- /api/plan/week/{n} -----------------------------

class TestPlanWeek:
    def test_week_1_returns_phase1(self, client, auth_headers):
        r = client.get("/api/plan/week/1", headers=auth_headers)
        assert r.status_code == 200
        j = r.json()
        assert j["week"] == 1
        assert j["phase"] == 1
        assert j["phase_name"] == "Aerobic Base"
        assert len(j["days"]) == 7
        assert j["is_deload"] is False
        assert j["is_race_week"] is False

    def test_week_8_is_phase1_gate(self, client, auth_headers):
        r = client.get("/api/plan/week/8", headers=auth_headers)
        j = r.json()
        assert r.status_code == 200
        assert j["phase"] == 1
        sunday = j["days"][6]
        assert sunday["targets"]["distance_km"] == 14.0

    def test_week_9_is_phase2(self, client, auth_headers):
        r = client.get("/api/plan/week/9", headers=auth_headers)
        j = r.json()
        assert r.status_code == 200
        assert j["phase"] == 2
        assert j["phase_name"] == "Build & Recomp"
        # Week 9 Friday is the first tempo run
        friday = j["days"][4]
        assert friday["type"] == "tempo"

    def test_deload_week_flagged(self, client, auth_headers):
        r = client.get("/api/plan/week/5", headers=auth_headers)
        assert r.json()["is_deload"] is True

    def test_race_week_flagged(self, client, auth_headers):
        r = client.get(f"/api/plan/week/{RACE_WEEK}", headers=auth_headers)
        j = r.json()
        assert j["is_race_week"] is True
        sunday = j["days"][6]
        assert "race" in sunday["type_label"].lower()

    def test_week_out_of_range_returns_404(self, client, auth_headers):
        r = client.get("/api/plan/week/0", headers=auth_headers)
        assert r.status_code == 404
        r = client.get("/api/plan/week/33", headers=auth_headers)
        assert r.status_code == 404

    def test_week_non_numeric_returns_422(self, client, auth_headers):
        r = client.get("/api/plan/week/abc", headers=auth_headers)
        assert r.status_code == 422


# ----------------------------- /api/plan/all -----------------------------

class TestPlanAll:
    def test_returns_32_weeks(self, client, auth_headers):
        r = client.get("/api/plan/all", headers=auth_headers)
        assert r.status_code == 200
        weeks = r.json()["weeks"]
        assert len(weeks) == 32
        assert [w["week"] for w in weeks] == list(range(1, 33))

    def test_deload_weeks_in_all(self, client, auth_headers):
        weeks = client.get("/api/plan/all", headers=auth_headers).json()["weeks"]
        deloads = {w["week"] for w in weeks if w["is_deload"]}
        assert deloads == DELOAD_WEEKS

    def test_every_week_has_full_shape(self, client, auth_headers):
        weeks = client.get("/api/plan/all", headers=auth_headers).json()["weeks"]
        for w in weeks:
            assert len(w["days"]) == 7
            for d in w["days"]:
                assert "name" in d
                assert "type" in d
                assert "type_label" in d
                assert "details" in d
                assert "targets" in d


# ----------------------------- /api/plan/today -----------------------------

class TestPlanToday:
    def test_today_returns_matching_weekday(self, client, auth_headers):
        r = client.get("/api/plan/today", headers=auth_headers)
        assert r.status_code == 200
        j = r.json()
        expected_dow = date.today().weekday()
        assert j["day_of_week"] == expected_dow
        assert j["day"]["name"] == [
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ][expected_dow]

    def test_today_includes_targets(self, client, auth_headers):
        j = client.get("/api/plan/today", headers=auth_headers).json()
        t = j["day"]["targets"]
        # Every targets dict must at minimum have these four keys
        assert set(t.keys()) == {"distance_km", "target_pace", "target_hr", "duration_min"}

    def test_today_has_week_and_phase(self, client, auth_headers):
        j = client.get("/api/plan/today", headers=auth_headers).json()
        assert 1 <= j["week"] <= 32
        assert 1 <= j["phase"] <= 4

"""
Integration tests for the extended /api/today endpoint.

Feature B: /api/today now returns `activity` (full day spec from plan_data)
and `week_focus` in addition to the existing fields.
"""
from datetime import date


class TestTodayActivity:
    def test_today_includes_activity_and_week_focus(self, client, auth_headers):
        r = client.get("/api/today", headers=auth_headers)
        assert r.status_code == 200
        j = r.json()
        assert "activity" in j
        assert "week_focus" in j

    def test_activity_has_full_shape(self, client, auth_headers):
        j = client.get("/api/today", headers=auth_headers).json()
        a = j["activity"]
        assert a is not None
        for key in ("name", "type", "type_label", "details", "targets"):
            assert key in a, f"activity missing {key}"

    def test_activity_day_matches_todays_weekday(self, client, auth_headers):
        j = client.get("/api/today", headers=auth_headers).json()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        assert j["activity"]["name"] == day_names[date.today().weekday()]

    def test_day_type_matches_activity_type(self, client, auth_headers):
        j = client.get("/api/today", headers=auth_headers).json()
        assert j["day_type"] == j["activity"]["type"]

    def test_week_focus_nonempty(self, client, auth_headers):
        j = client.get("/api/today", headers=auth_headers).json()
        assert isinstance(j["week_focus"], str)
        assert len(j["week_focus"]) > 0

    def test_activity_targets_structure(self, client, auth_headers):
        j = client.get("/api/today", headers=auth_headers).json()
        t = j["activity"]["targets"]
        assert set(t.keys()) == {"distance_km", "target_pace", "target_hr", "duration_min"}

    def test_activity_details_nonempty(self, client, auth_headers):
        j = client.get("/api/today", headers=auth_headers).json()
        details = j["activity"]["details"]
        assert isinstance(details, list)
        assert len(details) >= 1
        # Each detail is a [label, value] pair
        for item in details:
            assert isinstance(item, list)
            assert len(item) == 2


class TestTodayBackwardsCompat:
    """The pre-existing /api/today contract must still work."""

    def test_original_fields_still_present(self, client, auth_headers):
        j = client.get("/api/today", headers=auth_headers).json()
        for key in (
            "today_date", "current_week", "current_phase", "phase_name",
            "day_of_week", "day_type", "next_action", "plan_complete",
            "phase_progress_pct", "weeks_until_phase_gate",
            "latest_checkin", "latest_weekly_log",
            "phase_gate", "status", "coaching_note",
        ):
            assert key in j, f"original /api/today field missing: {key}"

    def test_phase_gate_has_requirements(self, client, auth_headers):
        j = client.get("/api/today", headers=auth_headers).json()
        assert "requirements" in j["phase_gate"] or "status" in j["phase_gate"]


class TestTodayAuth:
    def test_requires_auth(self, client):
        r = client.get("/api/today")
        assert r.status_code == 401

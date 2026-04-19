"""
Unit + integration tests for weekly summary (rings + WoW).

Week 1 spans 2026-04-14 (Tue) through 2026-04-20 (Mon) technically no — the
plan defines Week 1 as starting on the Monday of 2026-04-14. The
`week_date_range` helper computes a full Mon-Sun window relative to START_DATE.
"""
from datetime import date, timedelta

import pytest

from backend import weekly_summary as ws
from backend.models import DailyCheckin, User


# ----------------------------- planned week totals -----------------------------

class TestPlannedWeek:
    def test_week1_planned_totals(self):
        """
        Week 1 per plan_data:
          Mon strength, Tue run 3km, Wed rest, Thu strength, Fri run 4km,
          Sat rest, Sun long-run 6km → 3 run sessions, 13 km total.
        """
        planned = ws.compute_planned_week(1)
        assert planned["session_count"] == 3
        assert planned["total_km"] == pytest.approx(13.0, abs=0.1)

    def test_deload_week_has_fewer_sessions(self):
        """Week 5 is deload; should have runs on Tue/Fri/Sun → 3 sessions."""
        planned = ws.compute_planned_week(5)
        assert planned["session_count"] == 3

    def test_race_week_has_race_day(self):
        """Week 32 race week: Mon/Wed easy, Sat shakeout, Sun RACE = 4 runs."""
        planned = ws.compute_planned_week(32)
        assert planned["session_count"] == 4


# ----------------------------- rings -----------------------------

class TestRings:
    def test_zero_runs_returns_zero_pct(self):
        rings = ws.compute_rings([], 1)
        assert rings["volume"]["pct"] == 0
        assert rings["sessions"]["pct"] == 0
        assert rings["z2_adherence"]["pct"] == 0

    def test_full_volume_returns_100(self):
        # Week 1 plan is ~13km. Simulate 3 runs = 13 km
        checkins = [
            DailyCheckin(total_distance_km=3.0, avg_pace_per_km="10:30", avg_hr_bpm=140),
            DailyCheckin(total_distance_km=4.0, avg_pace_per_km="10:30", avg_hr_bpm=140),
            DailyCheckin(total_distance_km=6.0, avg_pace_per_km="10:30", avg_hr_bpm=145),
        ]
        rings = ws.compute_rings(checkins, 1)
        assert rings["volume"]["pct"] == 100
        assert rings["sessions"]["pct"] == 100

    def test_z2_adherence_compliant(self):
        """If all runs have HR at or under the cap, adherence = 100%."""
        # Week 1 easy-run caps are 140, 145 → avg 142
        checkins = [
            DailyCheckin(total_distance_km=3.0, avg_pace_per_km="10:30", avg_hr_bpm=138),
            DailyCheckin(total_distance_km=4.0, avg_pace_per_km="10:30", avg_hr_bpm=140),
            DailyCheckin(total_distance_km=6.0, avg_pace_per_km="10:30", avg_hr_bpm=142),
        ]
        rings = ws.compute_rings(checkins, 1)
        assert rings["z2_adherence"]["actual_pct"] == 100
        assert rings["z2_adherence"]["pct"] == 100  # actual (100%) / target (80%) -> clamped 100

    def test_z2_adherence_partial(self):
        checkins = [
            DailyCheckin(total_distance_km=3.0, avg_pace_per_km="10:30", avg_hr_bpm=138),
            DailyCheckin(total_distance_km=4.0, avg_pace_per_km="10:30", avg_hr_bpm=160),
            DailyCheckin(total_distance_km=6.0, avg_pace_per_km="10:30", avg_hr_bpm=170),
        ]
        rings = ws.compute_rings(checkins, 1)
        assert rings["z2_adherence"]["actual_pct"] == 33  # 1/3


# ----------------------------- WoW -----------------------------

class TestWeekOverWeek:
    def _mk_checkin(self, iso_date, distance=5.0, pace="10:00", hr=145):
        return DailyCheckin(
            checkin_date=iso_date, total_distance_km=distance,
            avg_pace_per_km=pace, avg_hr_bpm=hr,
        )

    def test_week_1_has_no_prev_week(self):
        wow = ws.compute_wow([], 1)
        assert wow["prev_week"] is None
        assert wow["volume_km"]["prev"] is None
        assert wow["avg_pace"]["delta_sec"] is None

    def test_volume_and_pace_delta(self):
        # Week 1: 3 runs totalling 10 km, pace 10:00
        # Week 2: 3 runs totalling 15 km, pace 9:30
        w1_start, _ = ws.week_date_range(1)
        w2_start, _ = ws.week_date_range(2)
        checkins = [
            self._mk_checkin((w1_start + timedelta(days=1)).isoformat(), 3.0, "10:00"),
            self._mk_checkin((w1_start + timedelta(days=3)).isoformat(), 3.0, "10:00"),
            self._mk_checkin((w1_start + timedelta(days=5)).isoformat(), 4.0, "10:00"),
            self._mk_checkin((w2_start + timedelta(days=1)).isoformat(), 5.0, "9:30"),
            self._mk_checkin((w2_start + timedelta(days=3)).isoformat(), 5.0, "9:30"),
            self._mk_checkin((w2_start + timedelta(days=5)).isoformat(), 5.0, "9:30"),
        ]
        wow = ws.compute_wow(checkins, 2)
        assert wow["prev_week"] == 1
        assert wow["volume_km"]["current"] == 15.0
        assert wow["volume_km"]["prev"] == 10.0
        assert wow["volume_km"]["delta"] == 5.0
        assert wow["avg_pace"]["delta_sec"] == -30  # 30s faster

    def test_session_count_delta(self):
        w1_start, _ = ws.week_date_range(1)
        w2_start, _ = ws.week_date_range(2)
        checkins = [
            self._mk_checkin((w1_start + timedelta(days=1)).isoformat()),
            self._mk_checkin((w2_start + timedelta(days=1)).isoformat()),
            self._mk_checkin((w2_start + timedelta(days=2)).isoformat()),
            self._mk_checkin((w2_start + timedelta(days=4)).isoformat()),
        ]
        wow = ws.compute_wow(checkins, 2)
        assert wow["sessions"]["prev"] == 1
        assert wow["sessions"]["current"] == 3
        assert wow["sessions"]["delta"] == 2


# ----------------------------- endpoint integration -----------------------------

class TestWeeklySummaryEndpoint:
    def test_requires_auth(self, client):
        r = client.get("/api/progress/weekly-summary")
        assert r.status_code == 401

    def test_default_is_current_week(self, client, auth_headers):
        r = client.get("/api/progress/weekly-summary", headers=auth_headers)
        assert r.status_code == 200
        j = r.json()
        assert 1 <= j["week"] <= 32
        assert "rings" in j
        assert "week_over_week" in j

    def test_explicit_week(self, client, auth_headers):
        r = client.get("/api/progress/weekly-summary?week=5", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["week"] == 5

    def test_out_of_range_week(self, client, auth_headers):
        r = client.get("/api/progress/weekly-summary?week=0", headers=auth_headers)
        assert r.status_code == 404
        r = client.get("/api/progress/weekly-summary?week=33", headers=auth_headers)
        assert r.status_code == 404

    def test_rings_shape(self, client, auth_headers):
        j = client.get("/api/progress/weekly-summary?week=1", headers=auth_headers).json()
        rings = j["rings"]
        for key in ("volume", "sessions", "z2_adherence"):
            assert key in rings
            assert "pct" in rings[key]
            assert "display" in rings[key]

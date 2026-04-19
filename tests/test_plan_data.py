"""
Unit tests for backend/plan_data.py — the single source of truth for the
32-week training plan.

Covers:
- every week (1-32) builds without error and returns 7 days
- every day has the required shape (name, type, type_label, details, targets)
- phase assignment (1: 1-8, 2: 9-16, 3: 17-24, 4: 25-32)
- deload weeks flagged correctly
- race week (32) has Sunday race
- Phase 1 content matches the original verbatim (spot checks against known weeks)
- target fields are consistent with day type
"""
import pytest

from backend.plan_data import (
    get_week, get_day, get_all_weeks, get_phase, get_week_focus,
    PHASE_NAMES, DELOAD_WEEKS, RACE_WEEK, DAY_NAMES,
)


# ----------------------------- shape & completeness -----------------------------

class TestPlanShape:
    """Every week must build, have 7 days, and every day must have the expected shape."""

    @pytest.mark.parametrize("week_num", list(range(1, 33)))
    def test_every_week_has_7_days(self, week_num):
        w = get_week(week_num)
        assert w["week"] == week_num
        assert len(w["days"]) == 7, f"Week {week_num} has {len(w['days'])} days, expected 7"

    @pytest.mark.parametrize("week_num", list(range(1, 33)))
    def test_every_day_has_required_fields(self, week_num):
        required = {"name", "type", "type_label", "details", "targets"}
        w = get_week(week_num)
        for i, day in enumerate(w["days"]):
            missing = required - set(day.keys())
            assert not missing, f"Week {week_num} day {i} missing: {missing}"
            assert day["name"] in DAY_NAMES, f"Week {week_num} day {i} bad name: {day['name']!r}"
            assert day["type"] in {"run", "long-run", "tempo", "intervals", "strength", "rest"}, \
                f"Week {week_num} day {i} bad type: {day['type']!r}"
            assert isinstance(day["type_label"], str) and day["type_label"]
            assert isinstance(day["details"], list) and len(day["details"]) > 0
            # targets should be a dict with the four standard keys
            t = day["targets"]
            assert set(t.keys()) == {"distance_km", "target_pace", "target_hr", "duration_min"}

    @pytest.mark.parametrize("week_num", list(range(1, 33)))
    def test_days_are_ordered_mon_to_sun(self, week_num):
        w = get_week(week_num)
        names = [d["name"] for d in w["days"]]
        assert names == DAY_NAMES, f"Week {week_num} wrong day order: {names}"


# ----------------------------- phase assignment -----------------------------

class TestPhases:
    @pytest.mark.parametrize("week, expected_phase", [
        (1, 1), (4, 1), (8, 1),
        (9, 2), (12, 2), (16, 2),
        (17, 3), (20, 3), (24, 3),
        (25, 4), (28, 4), (32, 4),
    ])
    def test_get_phase(self, week, expected_phase):
        assert get_phase(week) == expected_phase

    @pytest.mark.parametrize("week_num", list(range(1, 33)))
    def test_week_metadata_matches_phase(self, week_num):
        w = get_week(week_num)
        assert w["phase"] == get_phase(week_num)
        assert w["phase_name"] == PHASE_NAMES[w["phase"]]


# ----------------------------- deload & race flags -----------------------------

class TestSpecialWeeks:
    def test_deload_weeks_flagged(self):
        for w_num in range(1, 33):
            w = get_week(w_num)
            expected = w_num in DELOAD_WEEKS
            assert w["is_deload"] is expected, f"Week {w_num} deload flag wrong"

    def test_race_week_flagged(self):
        assert get_week(32)["is_race_week"] is True
        for w_num in range(1, 32):
            assert get_week(w_num)["is_race_week"] is False

    def test_race_week_sunday_is_race_day(self):
        w = get_week(RACE_WEEK)
        sunday = w["days"][6]
        assert sunday["type"] == "long-run"
        assert "race" in sunday["type_label"].lower()
        # 21.1 km is the HM distance
        assert sunday["targets"]["distance_km"] == pytest.approx(21.1, abs=0.01)


# ----------------------------- content spot checks -----------------------------

class TestPhase1Content:
    """Phase 1 days are ported verbatim from PlanViewer.jsx — sanity-check a few."""

    def test_week1_sunday_is_6km_long_run(self):
        day = get_day(1, 6)
        assert day["name"] == "Sunday"
        assert day["type"] == "long-run"
        assert day["targets"]["distance_km"] == 6.0
        # The original note mentions cardiac drift at 3.7km
        assert "cardiac drift" in day["note"].lower() or "3.7" in day["note"]

    def test_week1_wednesday_is_rest(self):
        day = get_day(1, 2)
        assert day["type"] == "rest"
        assert day["targets"]["distance_km"] is None

    def test_week5_is_deload_monday_is_rest(self):
        day = get_day(5, 0)
        assert day["type"] == "rest"
        assert "deload" in day["type_label"].lower()

    def test_week8_sunday_is_phase_gate_14km(self):
        day = get_day(8, 6)
        assert day["type"] == "long-run"
        assert day["targets"]["distance_km"] == 14.0
        # Gate pace threshold is 7:30
        assert "7:30" in day["targets"]["target_pace"]


class TestPhase2PlusContent:
    def test_week9_friday_is_first_tempo(self):
        day = get_day(9, 4)
        assert day["type"] == "tempo"
        assert "tempo" in day["type_label"].lower()

    def test_week12_is_deload(self):
        assert get_week(12)["is_deload"] is True

    def test_week16_is_phase2_gate(self):
        """Week 16 should have the pace test + 18km long run."""
        tue = get_day(16, 1)
        sun = get_day(16, 6)
        assert "test" in tue["type_label"].lower() or "pace" in tue["type_label"].lower()
        assert sun["targets"]["distance_km"] == 18.0

    def test_week19_is_first_20km(self):
        sun = get_day(19, 6)
        assert sun["targets"]["distance_km"] == 20.0

    def test_week32_full_taper_schedule(self):
        """Week 32 race week: Mon easy, Tue rest, Wed easy, Thu rest, Fri rest, Sat shakeout, Sun RACE."""
        days = get_week(32)["days"]
        assert days[0]["type"] == "run"
        assert days[1]["type"] == "rest"
        assert days[2]["type"] == "run"
        assert days[3]["type"] == "rest"
        assert days[4]["type"] == "rest"
        assert days[5]["type"] == "run"   # shakeout
        assert days[6]["type"] == "long-run"  # RACE
        assert days[6]["targets"]["distance_km"] == pytest.approx(21.1)


# ----------------------------- target field sanity -----------------------------

class TestTargetsSanity:
    """Run/long-run/tempo/intervals days should have a distance or duration target;
    rest days should not have a distance_km."""

    @pytest.mark.parametrize("week_num", list(range(1, 33)))
    def test_run_days_have_distance(self, week_num):
        days = get_week(week_num)["days"]
        for d in days:
            if d["type"] in ("run", "long-run", "tempo", "intervals"):
                assert d["targets"]["distance_km"] is not None, \
                    f"Week {week_num} {d['name']} ({d['type']}) missing distance_km"
                assert d["targets"]["distance_km"] > 0

    @pytest.mark.parametrize("week_num", list(range(1, 33)))
    def test_rest_days_have_no_distance(self, week_num):
        days = get_week(week_num)["days"]
        for d in days:
            if d["type"] == "rest":
                assert d["targets"]["distance_km"] is None, \
                    f"Week {week_num} {d['name']} (rest) has unexpected distance"


# ----------------------------- API access functions -----------------------------

class TestAccessors:
    def test_get_all_weeks_returns_32(self):
        all_weeks = get_all_weeks()
        assert len(all_weeks) == 32
        assert [w["week"] for w in all_weeks] == list(range(1, 33))

    def test_get_week_clamps_out_of_range(self):
        assert get_week(0)["week"] == 1
        assert get_week(-5)["week"] == 1
        assert get_week(99)["week"] == 32

    def test_get_day_returns_none_for_invalid_dow(self):
        assert get_day(1, -1) is None
        assert get_day(1, 7) is None

    def test_get_day_returns_correct_day(self):
        assert get_day(1, 0)["name"] == "Monday"
        assert get_day(1, 6)["name"] == "Sunday"

    def test_get_week_focus_nonempty_for_all_weeks(self):
        for w in range(1, 33):
            focus = get_week_focus(w)
            assert focus, f"Week {w} has empty focus"

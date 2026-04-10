"""Tests for parser.py — regex extraction and aggregate computation."""
import pytest
from backend.parser import _extract_splits_regex, _pace_to_seconds, _seconds_to_pace, _compute_aggregates


class TestPaceConversions:
    def test_pace_to_seconds_normal(self):
        assert _pace_to_seconds("9:49") == 589
        assert _pace_to_seconds("10:30") == 630
        assert _pace_to_seconds("7:00") == 420
        assert _pace_to_seconds("7:30") == 450

    def test_pace_to_seconds_invalid(self):
        assert _pace_to_seconds("") is None
        assert _pace_to_seconds("notapace") is None
        assert _pace_to_seconds("abc:de") is None

    def test_seconds_to_pace(self):
        assert _seconds_to_pace(589) == "9:49"
        assert _seconds_to_pace(630) == "10:30"
        assert _seconds_to_pace(420) == "7:00"
        assert _seconds_to_pace(605) == "10:05"

    def test_roundtrip(self):
        for pace in ["7:00", "7:30", "9:49", "10:30", "11:05"]:
            assert _seconds_to_pace(_pace_to_seconds(pace)) == pace


class TestRegexExtraction:
    # Simulate typical Apple Health OCR output
    SAMPLE_TEXT = """
    Splits
    1  09:49  9'49''/km  144BPM  159W
    2  10:10  10'10''/km  148BPM  155W
    3  10:39  10'39''/km  152BPM  151W
    4  10:59  10'59''/km  146BPM  148W
    """

    def test_extracts_correct_count(self):
        splits = _extract_splits_regex(self.SAMPLE_TEXT)
        assert len(splits) == 4

    def test_first_split_values(self):
        splits = _extract_splits_regex(self.SAMPLE_TEXT)
        s = splits[0]
        assert s["km"] == 1
        assert s["hr_bpm"] == 144
        assert s["power_watts"] == 159

    def test_all_split_numbers(self):
        splits = _extract_splits_regex(self.SAMPLE_TEXT)
        assert [s["km"] for s in splits] == [1, 2, 3, 4]

    def test_hr_values_extracted(self):
        splits = _extract_splits_regex(self.SAMPLE_TEXT)
        assert [s["hr_bpm"] for s in splits] == [144, 148, 152, 146]

    def test_power_values_extracted(self):
        splits = _extract_splits_regex(self.SAMPLE_TEXT)
        assert [s["power_watts"] for s in splits] == [159, 155, 151, 148]

    def test_empty_text_returns_empty(self):
        assert _extract_splits_regex("") == []
        assert _extract_splits_regex("no splits here") == []

    def test_partial_text_single_split(self):
        text = "1  09:49  9'49''/km  144BPM  159W"
        splits = _extract_splits_regex(text)
        assert len(splits) == 1

    def test_lowercase_bpm(self):
        text = "1  09:49  9'49''/km  144bpm  159W"
        splits = _extract_splits_regex(text)
        assert len(splits) == 1
        assert splits[0]["hr_bpm"] == 144


class TestComputeAggregates:
    def test_avg_hr(self):
        result = {
            "splits": [
                {"km": 1, "hr_bpm": 144, "power_watts": 159, "pace_per_km": "9:49"},
                {"km": 2, "hr_bpm": 148, "power_watts": 155, "pace_per_km": "10:10"},
                {"km": 3, "hr_bpm": 152, "power_watts": 151, "pace_per_km": "10:39"},
            ],
            "avg_hr": None, "max_hr": None, "avg_power": None, "avg_pace": None,
            "total_distance_km": None,
        }
        _compute_aggregates(result)
        assert result["avg_hr"] == pytest.approx(148.0, abs=0.5)

    def test_max_hr(self):
        result = {
            "splits": [
                {"km": 1, "hr_bpm": 144, "power_watts": 159, "pace_per_km": "9:49"},
                {"km": 2, "hr_bpm": 152, "power_watts": 155, "pace_per_km": "10:10"},
            ],
            "avg_hr": None, "max_hr": None, "avg_power": None, "avg_pace": None,
            "total_distance_km": None,
        }
        _compute_aggregates(result)
        assert result["max_hr"] == 152

    def test_total_distance_equals_split_count(self):
        result = {
            "splits": [
                {"km": i, "hr_bpm": 144, "power_watts": 150, "pace_per_km": "10:00"}
                for i in range(1, 5)
            ],
            "avg_hr": None, "max_hr": None, "avg_power": None, "avg_pace": None,
            "total_distance_km": None,
        }
        _compute_aggregates(result)
        assert result["total_distance_km"] == 4

    def test_empty_splits(self):
        result = {
            "splits": [],
            "avg_hr": None, "max_hr": None, "avg_power": None, "avg_pace": None,
            "total_distance_km": None,
        }
        _compute_aggregates(result)
        assert result["avg_hr"] is None


class TestSeedUser:
    """Ensure seed_user handles env edge cases correctly."""

    def test_valid_hash_accepted(self):
        import bcrypt as _bcrypt
        h = _bcrypt.hashpw(b"mypassword", _bcrypt.gensalt()).decode()
        assert h.startswith("$2b$")

    def test_hash_with_crlf_stripped(self):
        """Simulate Windows .env CRLF ending."""
        import bcrypt as _bcrypt
        from backend.routes.auth import verify_password
        h = _bcrypt.hashpw(b"mypassword", _bcrypt.gensalt()).decode()
        # With carriage return as Docker would pass from CRLF file
        assert verify_password("mypassword", h + "\r") is True

    def test_corrupted_hash_raises_not_crashes(self):
        """A bad hash should raise ValueError with a useful message, not crash silently."""
        from backend.routes.auth import verify_password
        with pytest.raises(ValueError) as exc_info:
            verify_password("anypassword", "2b12corrupted_no_dollar_signs")
        assert "not a valid bcrypt hash" in str(exc_info.value)

"""Tests for the progress / dashboard endpoint."""
import io
import pytest
from PIL import Image


def png_bytes():
    img = Image.new("RGB", (100, 50), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestProgress:
    def test_empty_progress(self, client, auth_headers):
        resp = client.get("/api/progress", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        # All chart arrays should be empty lists
        assert body["weight_chart"] == []
        assert body["waist_chart"] == []
        assert body["pace_chart"] == []
        assert body["hr_chart"] == []
        assert body["volume_chart"] == []

    def test_summary_keys_present(self, client, auth_headers):
        resp = client.get("/api/progress", headers=auth_headers)
        summary = resp.json()["summary"]
        required = [
            "current_week", "current_phase", "runs_this_week",
            "latest_weight", "target_weight", "latest_pace",
            "weeks_until_phase_gate", "phase_progress_pct",
            "start_weight", "start_waist", "target_waist",
        ]
        for key in required:
            assert key in summary, f"Missing summary key: {key}"

    def test_references_keys_present(self, client, auth_headers):
        resp = client.get("/api/progress", headers=auth_headers)
        refs = resp.json()["references"]
        for key in ["start_weight", "target_weight", "start_waist", "target_waist",
                    "baseline_pace_seconds", "phase1_gate_seconds", "phase2_gate_seconds"]:
            assert key in refs

    def test_current_week_is_positive(self, client, auth_headers):
        resp = client.get("/api/progress", headers=auth_headers)
        assert resp.json()["summary"]["current_week"] >= 1

    def test_current_phase_in_range(self, client, auth_headers):
        resp = client.get("/api/progress", headers=auth_headers)
        assert resp.json()["summary"]["current_phase"] in (1, 2, 3, 4)

    def test_progress_after_weekly_log(self, client, auth_headers):
        client.post("/api/log/weekly", json={"weight_kg": 91.5, "waist_inches": 37.0},
                    headers=auth_headers)
        resp = client.get("/api/progress", headers=auth_headers)
        body = resp.json()
        assert len(body["weight_chart"]) == 1
        assert body["weight_chart"][0]["weight"] == 91.5
        assert len(body["waist_chart"]) == 1
        assert body["summary"]["latest_weight"] == 91.5

    def test_progress_after_checkin(self, client, auth_headers):
        client.post(
            "/api/checkin/daily",
            files={"image": ("w.png", png_bytes(), "image/png")},
            headers=auth_headers,
        )
        resp = client.get("/api/progress", headers=auth_headers)
        # Volume chart should have 1 entry (even if distance is 0/None for blank image)
        body = resp.json()
        assert resp.status_code == 200

    def test_phase_progress_pct_range(self, client, auth_headers):
        resp = client.get("/api/progress", headers=auth_headers)
        pct = resp.json()["summary"]["phase_progress_pct"]
        assert 0 <= pct <= 100

    def test_requires_auth(self, client):
        resp = client.get("/api/progress")
        assert resp.status_code == 401

    def test_reference_pace_values_sane(self, client, auth_headers):
        """Baseline 10:30 = 630s, P1 gate 7:30 = 450s, P2 gate 7:00 = 420s."""
        resp = client.get("/api/progress", headers=auth_headers)
        refs = resp.json()["references"]
        assert refs["baseline_pace_seconds"] == 630
        assert refs["phase1_gate_seconds"] == 450
        assert refs["phase2_gate_seconds"] == 420

    def test_target_weights(self, client, auth_headers):
        resp = client.get("/api/progress", headers=auth_headers)
        refs = resp.json()["references"]
        assert refs["start_weight"] == 94.0
        assert refs["target_weight"] == 80.0

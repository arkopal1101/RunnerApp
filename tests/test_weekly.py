"""Tests for the weekly log endpoint."""
import pytest


class TestWeeklyLog:
    def test_create_log(self, client, auth_headers):
        resp = client.post("/api/log/weekly", json={
            "weight_kg": 91.5,
            "waist_inches": 37.0,
        }, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["weight_kg"] == 91.5
        assert body["waist_inches"] == 37.0
        assert "bmi" in body
        assert "week_number" in body
        assert "weight_change_from_start" in body
        assert "weight_change_from_last_week" in body

    def test_bmi_calculation(self, client, auth_headers):
        """BMI = weight / (1.805^2) = 91.5 / 3.258 ≈ 28.1"""
        resp = client.post("/api/log/weekly", json={
            "weight_kg": 91.5,
            "waist_inches": 37.0,
        }, headers=auth_headers)
        bmi = resp.json()["bmi"]
        assert 27.0 < bmi < 30.0, f"BMI {bmi} out of expected range"

    def test_weight_change_from_start(self, client, auth_headers):
        """Start weight is 94kg; logging 91.5 should show -2.5"""
        resp = client.post("/api/log/weekly", json={
            "weight_kg": 91.5,
            "waist_inches": 37.0,
        }, headers=auth_headers)
        assert resp.json()["weight_change_from_start"] == pytest.approx(-2.5, abs=0.1)

    def test_weight_change_from_last_week(self, client, auth_headers):
        """Second log delta should reflect change from first log."""
        client.post("/api/log/weekly", json={"weight_kg": 92.0, "waist_inches": 37.5}, headers=auth_headers)
        resp2 = client.post("/api/log/weekly", json={"weight_kg": 91.0, "waist_inches": 37.0}, headers=auth_headers)
        assert resp2.json()["weight_change_from_last_week"] == pytest.approx(-1.0, abs=0.1)

    def test_optional_fields(self, client, auth_headers):
        resp = client.post("/api/log/weekly", json={
            "weight_kg": 90.0,
            "waist_inches": 36.5,
            "chest_inches": 40.0,
            "hips_inches": 38.0,
            "body_fat_pct": 22.5,
            "notes": "Feeling good",
            "week_number": 3,
        }, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["chest_inches"] == 40.0
        assert body["hips_inches"] == 38.0
        assert body["body_fat_pct"] == 22.5
        assert body["week_number"] == 3

    def test_missing_required_weight(self, client, auth_headers):
        resp = client.post("/api/log/weekly", json={
            "waist_inches": 37.0,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_missing_required_waist(self, client, auth_headers):
        resp = client.post("/api/log/weekly", json={
            "weight_kg": 91.5,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_list_logs(self, client, auth_headers):
        client.post("/api/log/weekly", json={"weight_kg": 92.0, "waist_inches": 37.5}, headers=auth_headers)
        client.post("/api/log/weekly", json={"weight_kg": 91.5, "waist_inches": 37.0}, headers=auth_headers)
        resp = client.get("/api/log/weekly", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_logs_empty(self, client, auth_headers):
        resp = client.get("/api/log/weekly", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_week_number_autodetect(self, client, auth_headers):
        """Week number is auto-computed and should be a positive int."""
        resp = client.post("/api/log/weekly", json={
            "weight_kg": 91.5,
            "waist_inches": 37.0,
        }, headers=auth_headers)
        assert resp.json()["week_number"] >= 1

    def test_requires_auth(self, client):
        resp = client.post("/api/log/weekly", json={"weight_kg": 91.5, "waist_inches": 37.0})
        assert resp.status_code == 401

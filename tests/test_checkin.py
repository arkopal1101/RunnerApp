"""Tests for the daily check-in endpoint."""
import io
import json
import pytest
from PIL import Image


def make_fake_image(text_hint: str = "") -> bytes:
    """Create a tiny white PNG in memory."""
    img = Image.new("RGB", (100, 50), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestDailyCheckin:
    def test_upload_image_success(self, client, auth_headers):
        img_bytes = make_fake_image()
        resp = client.post(
            "/api/checkin/daily",
            files={"image": ("workout.png", img_bytes, "image/png")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "id" in body
        assert "checkin_date" in body
        assert "week_number" in body
        assert "confidence" in body

    def test_upload_returns_week_number(self, client, auth_headers):
        img_bytes = make_fake_image()
        resp = client.post(
            "/api/checkin/daily",
            files={"image": ("workout.png", img_bytes, "image/png")},
            headers=auth_headers,
        )
        assert resp.json()["week_number"] >= 1

    def test_upload_with_notes(self, client, auth_headers):
        img_bytes = make_fake_image()
        resp = client.post(
            "/api/checkin/daily",
            files={"image": ("workout.png", img_bytes, "image/png")},
            data={"notes": "Felt strong today"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_upload_jpeg(self, client, auth_headers):
        img = Image.new("RGB", (100, 50), color=(200, 200, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        resp = client.post(
            "/api/checkin/daily",
            files={"image": ("workout.jpg", buf.getvalue(), "image/jpeg")},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_upload_missing_image_returns_422(self, client, auth_headers):
        resp = client.post("/api/checkin/daily", headers=auth_headers)
        assert resp.status_code == 422

    def test_list_checkins_empty(self, client, auth_headers):
        resp = client.get("/api/checkin/daily", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_checkins_after_upload(self, client, auth_headers):
        img_bytes = make_fake_image()
        client.post(
            "/api/checkin/daily",
            files={"image": ("w.png", img_bytes, "image/png")},
            headers=auth_headers,
        )
        resp = client.get("/api/checkin/daily", headers=auth_headers)
        assert len(resp.json()) == 1

    def test_multiple_uploads_accumulate(self, client, auth_headers):
        img_bytes = make_fake_image()
        for _ in range(3):
            client.post(
                "/api/checkin/daily",
                files={"image": ("w.png", img_bytes, "image/png")},
                headers=auth_headers,
            )
        resp = client.get("/api/checkin/daily", headers=auth_headers)
        assert len(resp.json()) == 3

    def test_checkin_requires_auth(self, client):
        img_bytes = make_fake_image()
        resp = client.post(
            "/api/checkin/daily",
            files={"image": ("workout.png", img_bytes, "image/png")},
        )
        assert resp.status_code == 401

    def test_list_requires_auth(self, client):
        resp = client.get("/api/checkin/daily")
        assert resp.status_code == 401

    def test_confidence_field_present(self, client, auth_headers):
        img_bytes = make_fake_image()
        resp = client.post(
            "/api/checkin/daily",
            files={"image": ("w.png", img_bytes, "image/png")},
            headers=auth_headers,
        )
        assert resp.json()["confidence"] in ("ocr", "llm", "failed")

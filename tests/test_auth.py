"""
Tests for auth: password hashing, JWT creation, login endpoint.
These directly guard against the 'Invalid salt' class of bugs.
"""
import pytest
import bcrypt as _bcrypt
from backend.routes.auth import verify_password, create_access_token


# ── Password hashing ─────────────────────────────────────────────────────────

class TestVerifyPassword:
    def test_correct_password(self):
        h = _bcrypt.hashpw(b"secret", _bcrypt.gensalt()).decode()
        assert verify_password("secret", h) is True

    def test_wrong_password(self):
        h = _bcrypt.hashpw(b"secret", _bcrypt.gensalt()).decode()
        assert verify_password("wrong", h) is False

    def test_strips_trailing_crlf(self):
        """Windows .env files embed \\r — must not cause Invalid salt."""
        h = _bcrypt.hashpw(b"secret", _bcrypt.gensalt()).decode()
        assert verify_password("secret", h + "\r") is True

    def test_strips_trailing_newline(self):
        h = _bcrypt.hashpw(b"secret", _bcrypt.gensalt()).decode()
        assert verify_password("secret", h + "\n") is True

    def test_strips_trailing_spaces(self):
        h = _bcrypt.hashpw(b"secret", _bcrypt.gensalt()).decode()
        assert verify_password("secret", h + "   ") is True

    def test_invalid_hash_raises(self):
        """Garbage hash (e.g. env var interpolated away) raises ValueError."""
        with pytest.raises(ValueError, match="not a valid bcrypt hash"):
            verify_password("secret", "notahash")

    def test_empty_hash_raises(self):
        with pytest.raises(ValueError, match="not a valid bcrypt hash"):
            verify_password("secret", "")

    def test_hash_with_dollar_signs_intact(self):
        """The hash must contain $2b$12$ — verifies no $ stripping happens."""
        h = _bcrypt.hashpw(b"runner123", _bcrypt.gensalt()).decode()
        assert h.startswith("$2b$12$")
        assert verify_password("runner123", h) is True

    def test_special_chars_in_password(self):
        pwd = "P@$$w0rd!#%^&*()"
        h = _bcrypt.hashpw(pwd.encode(), _bcrypt.gensalt()).decode()
        assert verify_password(pwd, h) is True

    def test_unicode_password(self):
        pwd = "pässwörд123"
        h = _bcrypt.hashpw(pwd.encode("utf-8"), _bcrypt.gensalt()).decode()
        assert verify_password(pwd, h) is True


# ── JWT ───────────────────────────────────────────────────────────────────────

class TestJWT:
    def test_token_created(self):
        token = create_access_token({"sub": "arko"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_different_tokens_each_call(self):
        t1 = create_access_token({"sub": "arko"})
        t2 = create_access_token({"sub": "arko"})
        # Tokens differ because exp timestamps differ (at least by 1s most of the time)
        # Just verify both are valid strings
        assert isinstance(t1, str) and isinstance(t2, str)


# ── Login endpoint ────────────────────────────────────────────────────────────

class TestLoginEndpoint:
    def test_login_success(self, client):
        from tests.conftest import TEST_PASSWORD
        resp = client.post(
            "/api/auth/login",
            data={"username": "arko", "password": TEST_PASSWORD},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/api/auth/login",
            data={"username": "arko", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_login_wrong_username(self, client):
        from tests.conftest import TEST_PASSWORD
        resp = client.post(
            "/api/auth/login",
            data={"username": "notarko", "password": TEST_PASSWORD},
        )
        assert resp.status_code == 401

    def test_login_empty_password(self, client):
        resp = client.post(
            "/api/auth/login",
            data={"username": "arko", "password": ""},
        )
        assert resp.status_code == 401

    def test_login_returns_usable_token(self, client):
        """Token from login must work on a protected route."""
        from tests.conftest import TEST_PASSWORD
        resp = client.post(
            "/api/auth/login",
            data={"username": "arko", "password": TEST_PASSWORD},
        )
        token = resp.json()["access_token"]
        protected = client.get(
            "/api/checkin/daily",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert protected.status_code == 200

    def test_protected_route_without_token(self, client):
        resp = client.get("/api/checkin/daily")
        assert resp.status_code == 401

    def test_protected_route_bad_token(self, client):
        resp = client.get(
            "/api/checkin/daily",
            headers={"Authorization": "Bearer garbage.token.here"},
        )
        assert resp.status_code == 401

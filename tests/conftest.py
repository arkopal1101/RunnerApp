"""
Shared fixtures for all tests.
Uses an in-memory SQLite DB (StaticPool) so every connection shares
the same database — without this, each new connection gets a blank DB
and tables aren't found.
"""
import os
import pytest
import bcrypt as _bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# ── Set env vars BEFORE any backend import so module-level code picks them up ─
os.environ["JWT_SECRET"] = "test-secret-key-32-chars-minimum!!"
os.environ["DATA_DIR"] = "/tmp/runner_test_data"

TEST_PASSWORD = "TestPass123!"
os.environ["APP_PASSWORD"] = TEST_PASSWORD

# ── Now import backend ────────────────────────────────────────────────────────
from backend.database import Base, get_db
from backend.models import User
from backend import main  # noqa: triggers app creation


# ── Shared in-memory engine (StaticPool = one connection, tables persist) ─────
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(autouse=True)
def _reset_db():
    """Drop and recreate all tables before every test for full isolation."""
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db(_reset_db):
    """A fresh SQLAlchemy session per test."""
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """
    TestClient wired to the in-memory DB.
    Seeds the arko user with a known password for every test.
    """
    # Seed user with known hash derived from TEST_PASSWORD
    test_hash = _bcrypt.hashpw(TEST_PASSWORD.encode(), _bcrypt.gensalt()).decode()
    db.add(User(username="arko", password_hash=test_hash))
    db.commit()

    def _override_db():
        yield db

    main.app.dependency_overrides[get_db] = _override_db
    with TestClient(main.app, raise_server_exceptions=False) as c:
        yield c
    main.app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Bearer token for the seeded arko user."""
    resp = client.post(
        "/api/auth/login",
        data={"username": "arko", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200, (
        f"Login fixture failed ({resp.status_code}): {resp.text}"
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}

"""
Diagnostic: why does login fail?

Run it from the worktree root (where `backend/` lives):

    python diagnose_login.py

It will:
  1. Show which env vars the backend actually sees
  2. Show the current bcrypt hash stored in your runner.db
  3. Try to login with 'runner123' via the actual FastAPI app
  4. Try to login with whatever APP_PASSWORD is set to (if any)
  5. Tell you exactly why it failed
"""
import os
import sys
import sqlite3
from pathlib import Path

# Force-load the same env view the backend sees
DATA_DIR = os.getenv("DATA_DIR", "./data")
DB_PATH = Path(DATA_DIR) / "runner.db"

print("=" * 70)
print("ENV VARS (as the backend sees them):")
print("=" * 70)
for name in ("APP_PASSWORD", "PASSWORD_HASH", "JWT_SECRET", "DATA_DIR"):
    v = os.environ.get(name)
    if v is None:
        print(f"  {name:14} = <not set>")
    else:
        # Show length + visible chars (but redact middle)
        shown = f"{v[:3]}...{v[-3:]}" if len(v) > 6 else "***"
        print(f"  {name:14} = {shown!r} (len={len(v)}, raw repr first 20 chars: {v[:20]!r})")

print()
print("=" * 70)
print("DATABASE STATE:")
print("=" * 70)
print(f"  Expected DB path: {DB_PATH.resolve()}")
print(f"  Exists: {DB_PATH.exists()}")

if DB_PATH.exists():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash, created_at FROM users")
        rows = cur.fetchall()
        print(f"  users table rows: {len(rows)}")
        for row in rows:
            uid, uname, phash, created = row
            print(f"    id={uid} username={uname!r}")
            print(f"    stored_hash[:10]={phash[:10]!r} (full length={len(phash)})")
            print(f"    hash starts with $2 (valid bcrypt)? {phash.strip().startswith('$2')}")
    except sqlite3.OperationalError as e:
        print(f"  (table read error: {e})")
    finally:
        conn.close()
else:
    print("  (DB file does not exist yet — it will be created on first `uvicorn` startup)")

print()
print("=" * 70)
print("LOGIN TEST via FastAPI:")
print("=" * 70)
# Import here so the env view above is accurate
from fastapi.testclient import TestClient
from backend import main  # this triggers seed_user()
from backend.models import User
from backend.database import SessionLocal

# Confirm what the DB now contains after seed_user ran
db = SessionLocal()
user = db.query(User).filter(User.username == "arko").first()
db.close()
print(f"  After startup, user 'arko' in DB: {user is not None}")
if user:
    print(f"    stored_hash[:15]: {user.password_hash[:15]!r}")

client = TestClient(main.app)

for trial_password in ["runner123", os.environ.get("APP_PASSWORD", "")]:
    if not trial_password:
        continue
    r = client.post("/api/auth/login", data={"username": "arko", "password": trial_password})
    print(f"\n  POST /api/auth/login username=arko password={trial_password!r}")
    print(f"    status: {r.status_code}")
    print(f"    body:   {r.text[:200]}")

print()
print("=" * 70)
print("DIAGNOSIS:")
print("=" * 70)
if not DB_PATH.exists():
    print("  No DB yet — run uvicorn once, then rerun this script.")
elif os.environ.get("APP_PASSWORD") is None and os.environ.get("PASSWORD_HASH") is None:
    print("  No APP_PASSWORD / PASSWORD_HASH env var is set.")
    print("  The seed fell back to default 'runner123'.")
    print("  -> If `runner123` login above returned 200, everything is fine.")
    print("    If the browser still rejects it, the browser is hitting a different")
    print("    backend (different port / cwd) or sending the wrong payload.")
else:
    print("  APP_PASSWORD is set. Login should work with that exact value.")
    print("  If it does not, check for trailing whitespace / CRLF in your .env file.")

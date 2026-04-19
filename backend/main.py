import os
from pathlib import Path

# Load .env from the project root BEFORE any other import that reads env vars.
# Notepad on Windows saves files as UTF-16 LE by default — detect BOM and pick
# the right encoding so we don't crash on user-authored .env files.
# Falls through silently if python-dotenv isn't installed (e.g. in CI).
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        with open(_env_path, "rb") as _f:
            _head = _f.read(4)
        if _head.startswith(b"\xff\xfe") or _head.startswith(b"\xfe\xff"):
            _encoding = "utf-16"
        elif _head.startswith(b"\xef\xbb\xbf"):
            _encoding = "utf-8-sig"
        else:
            _encoding = "utf-8"
        load_dotenv(_env_path, encoding=_encoding)
        print(f"[runner] Loaded env from {_env_path} (encoding={_encoding})")
except ImportError:
    pass
except Exception as _e:
    print(f"[runner] Failed to load .env: {_e}")

import bcrypt as _bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import engine, SessionLocal, ensure_columns
from .models import Base, User
from .routes import auth, checkin, weekly, progress, today, plan, coach, day_log, baseline

# Create tables + apply any missing column migrations.
Base.metadata.create_all(bind=engine)
ensure_columns()

app = FastAPI(title="Runner API", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(checkin.router, prefix="/api/checkin", tags=["checkin"])
app.include_router(weekly.router, prefix="/api/log", tags=["weekly"])
app.include_router(progress.router, prefix="/api", tags=["progress"])
app.include_router(today.router, prefix="/api", tags=["today"])
app.include_router(plan.router, prefix="/api/plan", tags=["plan"])
app.include_router(coach.router, prefix="/api/coach", tags=["coach"])
app.include_router(day_log.router, prefix="/api/day-log", tags=["day-log"])
app.include_router(baseline.router, prefix="/api/baseline", tags=["baseline"])


def _make_hash(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def seed_user():
    """
    Create or update the 'arko' user on every startup.

    Priority:
      1. APP_PASSWORD  — plain-text password (simplest, recommended)
      2. PASSWORD_HASH — pre-computed bcrypt hash (must start with $2)
      3. Fallback      — hashes the literal string 'runner123'
    """
    app_password = os.getenv("APP_PASSWORD", "").strip()
    password_hash = os.getenv("PASSWORD_HASH", "").strip()

    if app_password:
        final_hash = _make_hash(app_password)
        print(f"[runner] Using APP_PASSWORD from env.")
    elif password_hash.startswith("$2"):
        final_hash = password_hash
        print(f"[runner] Using PASSWORD_HASH from env.")
    else:
        final_hash = _make_hash("runner123")
        print(
            "[runner] WARNING: Neither APP_PASSWORD nor a valid PASSWORD_HASH is set. "
            "Falling back to default password 'runner123'. "
            "Set APP_PASSWORD=<yourpassword> in your .env file."
        )

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "arko").first()
        if user:
            user.password_hash = final_hash
            db.commit()
            print("[runner] User 'arko' password synced from env.")
        else:
            db.add(User(username="arko", password_hash=final_hash))
            db.commit()
            print("[runner] User 'arko' created.")
    finally:
        db.close()


seed_user()

# Serve React static files (built frontend)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/", include_in_schema=False)
    async def serve_root():
        return FileResponse(str(static_dir / "index.html"))

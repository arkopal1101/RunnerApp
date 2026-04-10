import os
from pathlib import Path

import bcrypt as _bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import engine, SessionLocal
from .models import Base, User
from .routes import auth, checkin, weekly, progress

# Create tables
Base.metadata.create_all(bind=engine)

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

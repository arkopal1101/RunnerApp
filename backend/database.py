import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR}/runner.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Lightweight SQLite migrations ──────────────────────────────────────────
# SQLAlchemy's create_all doesn't ALTER existing tables to add new columns.
# We ship a small migration list that gets applied on every startup; each
# entry is idempotent (only runs if the column is missing).
_MIGRATIONS = [
    ("users", "baseline_pace_seconds", "INTEGER"),
    ("users", "baseline_calibrated_at", "DATETIME"),
]


def ensure_columns():
    """Add any declared columns that don't yet exist. Safe to call repeatedly."""
    with engine.begin() as conn:
        insp = inspect(conn)
        existing_tables = set(insp.get_table_names())
        for table, column, coltype in _MIGRATIONS:
            if table not in existing_tables:
                continue
            cols = {c["name"] for c in insp.get_columns(table)}
            if column not in cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"))
                print(f"[migrate] {table}.{column} added")

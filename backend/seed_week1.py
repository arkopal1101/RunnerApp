"""
Seed script: ingest Week 1 run screenshots from a directory and calibrate
the user's baseline.

Usage (from the worktree root):
    python -m backend.seed_week1 --dir "Week 1 Run Data"
    python -m backend.seed_week1 --dir "Week 1 Run Data" --user arko

Week 1 per the plan runs Tue (3km), Fri (4km), Sun (6km) — 3 runs total.
Files are mapped to the Week 1 run days in sorted order:
    Run 1 → Tue (dow=1)
    Run 2 → Fri (dow=4)
    Run 3 → Sun (dow=6)

The script:
  1. Parses each image via parse_workout_screenshot (OpenAI vision)
  2. Saves a DailyCheckin row tagged to Week 1 + the matching weekday
  3. Creates a DayLog row (kind=run) so the day cards show completed
  4. Calls baseline calibration to lock in the user's Z2 starting pace
"""
import argparse
import os
import shutil
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

# Allow running as a script (python -m backend.seed_week1 works either way)
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env like main.py does so OPENAI_API_KEY is available.
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "rb") as f:
            head = f.read(4)
        if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
            enc = "utf-16"
        elif head.startswith(b"\xef\xbb\xbf"):
            enc = "utf-8-sig"
        else:
            enc = "utf-8"
        load_dotenv(env_path, encoding=enc)
except ImportError:
    pass

import json

from backend.database import Base, SessionLocal, engine, ensure_columns
from backend.models import DailyCheckin, User
from backend.parser import parse_workout_screenshot
from backend.routes.baseline import calibrate_baseline
from backend.routes.day_log import upsert_day_log
from backend.routes.checkin import get_week_number

# Sunday of Week 1 = 2026-04-19 (per START_DATE 2026-04-13 Mon).
# Map files → weekdays (Mon=0..Sun=6).
WEEK1_DAY_MAP = {0: 1, 1: 4, 2: 6}  # index of sorted file → day_of_week


def _week1_date(day_of_week: int) -> str:
    start = date(2026, 4, 13)  # Week 1 Monday
    return (start + timedelta(days=day_of_week)).isoformat()


def _find_images(source_dir: Path) -> list[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    files = [p for p in source_dir.iterdir() if p.suffix.lower() in exts]
    return sorted(files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="Directory containing Week 1 run screenshots")
    parser.add_argument("--user", default="arko", help="Username to seed for")
    parser.add_argument("--force", action="store_true", help="Re-parse and overwrite existing Week 1 runs")
    args = parser.parse_args()

    source = Path(args.dir)
    if not source.exists():
        print(f"[seed] Directory not found: {source}", file=sys.stderr)
        sys.exit(1)

    images = _find_images(source)
    if not images:
        print(f"[seed] No images found in {source}", file=sys.stderr)
        sys.exit(1)
    print(f"[seed] Found {len(images)} image(s) in {source.name}")

    # Make sure tables exist and the schema has the new columns.
    Base.metadata.create_all(bind=engine)
    ensure_columns()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == args.user).first()
        if not user:
            print(f"[seed] User {args.user!r} not found — start uvicorn once to seed the user", file=sys.stderr)
            sys.exit(1)

        # Existing Week 1 runs
        existing = (
            db.query(DailyCheckin)
            .filter(DailyCheckin.user_id == user.id, DailyCheckin.week_number == 1)
            .all()
        )
        if existing and not args.force:
            print(f"[seed] Week 1 already has {len(existing)} run(s). Pass --force to re-ingest.")
            print(f"[seed] Running calibration only...")
        else:
            if existing and args.force:
                print(f"[seed] --force: deleting {len(existing)} existing Week 1 run(s)")
                for c in existing:
                    db.delete(c)
                db.commit()

            uploads_dir = Path(os.getenv("DATA_DIR", "./data")) / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)

            openai_key = os.getenv("OPENAI_API_KEY") or None
            for idx, img_path in enumerate(images):
                if idx not in WEEK1_DAY_MAP:
                    print(f"[seed] Skipping extra file: {img_path.name}")
                    continue
                dow = WEEK1_DAY_MAP[idx]
                run_date = _week1_date(dow)

                # Copy into uploads dir so the app can later reference it
                dest_name = f"week1_run{idx+1}_{uuid.uuid4()}{img_path.suffix}"
                dest_path = uploads_dir / dest_name
                shutil.copy2(img_path, dest_path)

                print(f"[seed] Parsing {img_path.name} (Week 1 dow={dow}, date={run_date})...")
                parsed = parse_workout_screenshot(str(dest_path), openai_api_key=openai_key)
                conf = parsed.get("confidence", "failed")
                splits = parsed.get("splits", [])
                print(f"       confidence={conf}, {len(splits)} splits, "
                      f"avg_pace={parsed.get('avg_pace')}, total_km={parsed.get('total_distance_km')}")

                checkin = DailyCheckin(
                    user_id=user.id,
                    checkin_date=run_date,
                    image_path=dest_name,
                    raw_text_extracted=parsed.get("raw_text", ""),
                    total_distance_km=parsed.get("total_distance_km"),
                    avg_pace_per_km=parsed.get("avg_pace"),
                    avg_hr_bpm=parsed.get("avg_hr"),
                    max_hr_bpm=parsed.get("max_hr"),
                    avg_power_watts=parsed.get("avg_power"),
                    splits_json=json.dumps(splits),
                    week_number=1,
                    notes=f"Seeded from {img_path.name}",
                )
                db.add(checkin)
                db.commit()
                db.refresh(checkin)

                upsert_day_log(
                    db, user.id, 1, dow,
                    kind="run", log_date=run_date, checkin_id=checkin.id,
                )
                print(f"       saved checkin id={checkin.id}, marked dow={dow} completed")

        # Calibrate (or re-calibrate with --force)
        print(f"[seed] Running baseline calibration...")
        try:
            result = calibrate_baseline(force=args.force, current_user=user, db=db)
            print(f"[seed] Baseline calibrated: {result['baseline_pace_str']} "
                  f"({result['baseline_pace_seconds']}s/km, {result['runs_used']} runs)")
        except Exception as e:
            # FastAPI HTTPException → render its detail
            detail = getattr(e, "detail", str(e))
            print(f"[seed] Calibration skipped: {detail}")

    finally:
        db.close()

    print("[seed] Done.")


if __name__ == "__main__":
    main()

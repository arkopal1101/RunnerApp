import json
import os
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import DailyCheckin, User
from ..parser import parse_workout_screenshot
from .auth import get_current_user
from .day_log import upsert_day_log

router = APIRouter()

DATA_DIR = os.getenv("DATA_DIR", "./data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")


def get_week_number(checkin_date: date) -> int:
    start = date(2026, 4, 14)
    delta = (checkin_date - start).days
    if delta < 0:
        return 0
    return (delta // 7) + 1


def checkin_to_dict(checkin: DailyCheckin, include_splits: bool = True) -> dict:
    return {
        "id": checkin.id,
        "checkin_date": checkin.checkin_date,
        "week_number": checkin.week_number,
        "total_distance_km": checkin.total_distance_km,
        "avg_pace_per_km": checkin.avg_pace_per_km,
        "avg_hr_bpm": checkin.avg_hr_bpm,
        "max_hr_bpm": checkin.max_hr_bpm,
        "avg_power_watts": checkin.avg_power_watts,
        "splits": json.loads(checkin.splits_json) if include_splits and checkin.splits_json else [],
        "notes": checkin.notes,
    }


# ── Parse-only (no DB write) ──────────────────────────────────────────────────

@router.post("/parse")
async def parse_checkin(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload screenshot and return parsed data WITHOUT saving to DB."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ext = os.path.splitext(image.filename or "")[1] or ".png"
    filename = f"tmp_{uuid.uuid4()}{ext}"
    image_path = os.path.join(UPLOADS_DIR, filename)

    content = await image.read()
    with open(image_path, "wb") as f:
        f.write(content)

    openai_key = os.getenv("OPENAI_API_KEY")
    parsed = parse_workout_screenshot(image_path, openai_api_key=openai_key or None)

    return {
        "tmp_image_path": filename,
        "total_distance_km": parsed.get("total_distance_km"),
        "avg_pace_per_km": parsed.get("avg_pace"),
        "avg_hr_bpm": parsed.get("avg_hr"),
        "max_hr_bpm": parsed.get("max_hr"),
        "avg_power_watts": parsed.get("avg_power"),
        "splits": parsed.get("splits", []),
        "confidence": parsed.get("confidence", "failed"),
        "raw_text": parsed.get("raw_text", ""),
    }


# ── Confirm & save (or manual entry) ─────────────────────────────────────────

class CheckinConfirm(BaseModel):
    checkin_date: Optional[str] = None
    week_number: Optional[int] = None
    total_distance_km: Optional[float] = None
    avg_pace_per_km: Optional[str] = None
    avg_hr_bpm: Optional[int] = None
    max_hr_bpm: Optional[int] = None
    avg_power_watts: Optional[int] = None
    splits: Optional[list] = None
    notes: Optional[str] = None
    tmp_image_path: Optional[str] = None  # from /parse step


@router.post("/daily")
async def daily_checkin(
    # Support both multipart (legacy + parse confirm) and JSON (manual)
    image: Optional[UploadFile] = File(None),
    notes: Optional[str] = Form(None),
    checkin_date: Optional[str] = Form(None),
    override_json: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save a daily check-in. Three modes:
    1. image + optional override_json → parse image then save (legacy)
    2. override_json only (no image) → save manual entry data directly
    3. override_json with tmp_image_path → save confirmed parsed data from /parse step
    """
    parsed = {}
    image_filename = None

    if image:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        ext = os.path.splitext(image.filename or "")[1] or ".png"
        image_filename = f"{uuid.uuid4()}{ext}"
        image_path = os.path.join(UPLOADS_DIR, image_filename)
        content = await image.read()
        with open(image_path, "wb") as f:
            f.write(content)

        openai_key = os.getenv("OPENAI_API_KEY")
        parsed = parse_workout_screenshot(image_path, openai_api_key=openai_key or None)

    if override_json:
        try:
            overrides = json.loads(override_json)
            # Handle tmp_image_path rename
            if "tmp_image_path" in overrides and not image_filename:
                image_filename = overrides.pop("tmp_image_path")
            parsed.update(overrides)
        except Exception:
            pass

    today_str = checkin_date or parsed.get("checkin_date") or date.today().isoformat()
    try:
        d = date.fromisoformat(today_str)
    except ValueError:
        d = date.today()
        today_str = d.isoformat()

    week_num = parsed.get("week_number") or get_week_number(d)

    checkin = DailyCheckin(
        user_id=current_user.id,
        checkin_date=today_str,
        image_path=image_filename,
        raw_text_extracted=parsed.get("raw_text", ""),
        total_distance_km=parsed.get("total_distance_km"),
        avg_pace_per_km=parsed.get("avg_pace_per_km") or parsed.get("avg_pace"),
        avg_hr_bpm=parsed.get("avg_hr_bpm") or parsed.get("avg_hr"),
        max_hr_bpm=parsed.get("max_hr_bpm") or parsed.get("max_hr"),
        avg_power_watts=parsed.get("avg_power_watts") or parsed.get("avg_power"),
        splits_json=json.dumps(parsed.get("splits", [])),
        week_number=week_num,
        notes=notes or parsed.get("notes"),
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    # Auto-mark this day as completed so the Plan viewer shows a ✓ badge.
    try:
        upsert_day_log(
            db, current_user.id, week_num, d.weekday(),
            kind="run", log_date=today_str, checkin_id=checkin.id,
        )
    except Exception:
        pass

    return {
        **checkin_to_dict(checkin),
        "confidence": parsed.get("confidence", "manual"),
    }


# ── Update existing check-in ──────────────────────────────────────────────────

@router.put("/daily/{checkin_id}")
def update_checkin(
    checkin_id: int,
    payload: CheckinConfirm,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    checkin = db.query(DailyCheckin).filter(
        DailyCheckin.id == checkin_id,
        DailyCheckin.user_id == current_user.id,
    ).first()
    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in not found")

    if payload.checkin_date is not None:
        checkin.checkin_date = payload.checkin_date
        try:
            d = date.fromisoformat(payload.checkin_date)
            checkin.week_number = get_week_number(d)
        except ValueError:
            pass
    if payload.week_number is not None:
        checkin.week_number = payload.week_number
    if payload.total_distance_km is not None:
        checkin.total_distance_km = payload.total_distance_km
    if payload.avg_pace_per_km is not None:
        checkin.avg_pace_per_km = payload.avg_pace_per_km
    if payload.avg_hr_bpm is not None:
        checkin.avg_hr_bpm = payload.avg_hr_bpm
    if payload.max_hr_bpm is not None:
        checkin.max_hr_bpm = payload.max_hr_bpm
    if payload.avg_power_watts is not None:
        checkin.avg_power_watts = payload.avg_power_watts
    if payload.splits is not None:
        checkin.splits_json = json.dumps(payload.splits)
    if payload.notes is not None:
        checkin.notes = payload.notes

    db.commit()
    db.refresh(checkin)
    return checkin_to_dict(checkin)


# ── List check-ins ────────────────────────────────────────────────────────────

@router.get("/daily")
def list_checkins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == current_user.id)
        .order_by(DailyCheckin.checkin_date.desc())
        .all()
    )
    return [checkin_to_dict(r) for r in rows]

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

router = APIRouter()

DATA_DIR = os.getenv("DATA_DIR", "./data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")


def get_week_number(checkin_date: date) -> int:
    start = date(2026, 4, 14)
    delta = (checkin_date - start).days
    if delta < 0:
        return 0
    return (delta // 7) + 1


@router.post("/daily")
async def daily_checkin(
    image: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    checkin_date: Optional[str] = Form(None),
    # Allow manual override of parsed fields
    override_json: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ext = os.path.splitext(image.filename)[1] or ".png"
    filename = f"{uuid.uuid4()}{ext}"
    image_path = os.path.join(UPLOADS_DIR, filename)

    content = await image.read()
    with open(image_path, "wb") as f:
        f.write(content)

    openai_key = os.getenv("OPENAI_API_KEY")
    parsed = parse_workout_screenshot(image_path, openai_api_key=openai_key or None)

    # Apply manual overrides if provided
    if override_json:
        try:
            overrides = json.loads(override_json)
            parsed.update(overrides)
        except Exception:
            pass

    today = checkin_date or date.today().isoformat()
    try:
        d = date.fromisoformat(today)
    except ValueError:
        d = date.today()

    week_num = get_week_number(d)

    checkin = DailyCheckin(
        user_id=current_user.id,
        checkin_date=today,
        image_path=filename,
        raw_text_extracted=parsed.get("raw_text", ""),
        total_distance_km=parsed.get("total_distance_km"),
        avg_pace_per_km=parsed.get("avg_pace"),
        avg_hr_bpm=parsed.get("avg_hr"),
        max_hr_bpm=parsed.get("max_hr"),
        avg_power_watts=parsed.get("avg_power"),
        splits_json=json.dumps(parsed.get("splits", [])),
        week_number=week_num,
        notes=notes,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    return {
        "id": checkin.id,
        "checkin_date": checkin.checkin_date,
        "week_number": checkin.week_number,
        "total_distance_km": checkin.total_distance_km,
        "avg_pace_per_km": checkin.avg_pace_per_km,
        "avg_hr_bpm": checkin.avg_hr_bpm,
        "max_hr_bpm": checkin.max_hr_bpm,
        "avg_power_watts": checkin.avg_power_watts,
        "splits": parsed.get("splits", []),
        "confidence": parsed.get("confidence", "failed"),
    }


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
    result = []
    for r in rows:
        result.append({
            "id": r.id,
            "checkin_date": r.checkin_date,
            "week_number": r.week_number,
            "total_distance_km": r.total_distance_km,
            "avg_pace_per_km": r.avg_pace_per_km,
            "avg_hr_bpm": r.avg_hr_bpm,
            "max_hr_bpm": r.max_hr_bpm,
            "avg_power_watts": r.avg_power_watts,
            "splits": json.loads(r.splits_json) if r.splits_json else [],
            "notes": r.notes,
        })
    return result

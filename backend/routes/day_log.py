"""
Day-level completion tracking: one DayLog row per (user, week, day_of_week).

Three kinds:
  run       — created automatically when /api/checkin/daily saves a run
  strength  — created when /api/workout/upload accepts a workout image
  rest      — created when the user clicks "Rested Today" on a rest day

This is the single source of truth for "is this day completed?" used by
the Plan viewer (to show a ✓ badge) and the Today page (to know whether
to surface the action CTA).
"""
import json
import os
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import DailyCheckin, DayLog, User
from .auth import get_current_user

router = APIRouter()

DATA_DIR = os.getenv("DATA_DIR", "./data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")

VALID_KINDS = {"run", "strength", "rest"}


def _serialize(log: DayLog) -> dict:
    return {
        "id": log.id,
        "log_date": log.log_date,
        "week_number": log.week_number,
        "day_of_week": log.day_of_week,
        "kind": log.kind,
        "checkin_id": log.checkin_id,
        "image_path": log.image_path,
        "notes": log.notes,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def upsert_day_log(
    db: Session,
    user_id: int,
    week: int,
    day_of_week: int,
    kind: str,
    log_date: str,
    *,
    checkin_id: Optional[int] = None,
    image_path: Optional[str] = None,
    notes: Optional[str] = None,
) -> DayLog:
    """
    Idempotent upsert keyed on (user, week, day_of_week). Used both by the
    endpoint below and by auto-completion hooks in checkin / workout routes.
    """
    existing = (
        db.query(DayLog)
        .filter(DayLog.user_id == user_id)
        .filter(DayLog.week_number == week)
        .filter(DayLog.day_of_week == day_of_week)
        .first()
    )
    if existing:
        existing.kind = kind
        existing.log_date = log_date
        if checkin_id is not None:
            existing.checkin_id = checkin_id
        if image_path is not None:
            existing.image_path = image_path
        if notes is not None:
            existing.notes = notes
        db.commit()
        db.refresh(existing)
        return existing

    row = DayLog(
        user_id=user_id,
        log_date=log_date,
        week_number=week,
        day_of_week=day_of_week,
        kind=kind,
        checkin_id=checkin_id,
        image_path=image_path,
        notes=notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


class DayLogCreate(BaseModel):
    kind: str
    week_number: int
    day_of_week: int
    log_date: Optional[str] = None
    notes: Optional[str] = None


@router.post("")
def create_day_log(
    payload: DayLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log completion for a day. Used primarily for 'Rested Today'."""
    if payload.kind not in VALID_KINDS:
        raise HTTPException(status_code=422, detail=f"kind must be one of {sorted(VALID_KINDS)}")
    if not 1 <= payload.week_number <= 32:
        raise HTTPException(status_code=422, detail="week_number must be 1-32")
    if not 0 <= payload.day_of_week <= 6:
        raise HTTPException(status_code=422, detail="day_of_week must be 0-6")

    log_date = payload.log_date or date.today().isoformat()
    row = upsert_day_log(
        db, current_user.id, payload.week_number, payload.day_of_week,
        payload.kind, log_date, notes=payload.notes,
    )
    return _serialize(row)


@router.get("/week/{week_number}")
def get_week_logs(
    week_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return DayLog rows for every completed day in this week (keyed by dow)."""
    if not 1 <= week_number <= 32:
        raise HTTPException(status_code=404, detail="Week out of range (1-32)")
    rows = (
        db.query(DayLog)
        .filter(DayLog.user_id == current_user.id, DayLog.week_number == week_number)
        .all()
    )
    return {
        "week": week_number,
        "by_day_of_week": {str(r.day_of_week): _serialize(r) for r in rows},
    }


@router.get("/all")
def get_all_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return a compact completion map for every week. Used by PlanViewer to
    decorate all 32 weeks in one shot.
    """
    rows = (
        db.query(DayLog)
        .filter(DayLog.user_id == current_user.id)
        .all()
    )
    result: dict[str, dict[str, dict]] = {}
    for r in rows:
        result.setdefault(str(r.week_number), {})[str(r.day_of_week)] = _serialize(r)
    return {"by_week": result}


# ──────────────────────────────────────────────────────────────────────────
# Workout upload — strength/workout screenshots
# ──────────────────────────────────────────────────────────────────────────
@router.post("/workout")
async def upload_workout(
    image: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    week_number: Optional[int] = Form(None),
    day_of_week: Optional[int] = Form(None),
    log_date: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a workout screenshot (strength session). Saves the image and
    creates/updates the DayLog for this week/day with kind=strength.

    No OCR/LLM parsing for workouts in v1 — we just store the file so you can
    review it later. The card is marked as completed.
    """
    if week_number is None or day_of_week is None:
        raise HTTPException(status_code=422, detail="week_number and day_of_week required")
    if not 1 <= week_number <= 32:
        raise HTTPException(status_code=422, detail="week_number must be 1-32")
    if not 0 <= day_of_week <= 6:
        raise HTTPException(status_code=422, detail="day_of_week must be 0-6")

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ext = os.path.splitext(image.filename or "")[1] or ".png"
    filename = f"workout_{uuid.uuid4()}{ext}"
    disk_path = os.path.join(UPLOADS_DIR, filename)
    content = await image.read()
    with open(disk_path, "wb") as f:
        f.write(content)

    row = upsert_day_log(
        db, current_user.id, week_number, day_of_week,
        kind="strength",
        log_date=log_date or date.today().isoformat(),
        image_path=filename,
        notes=notes,
    )
    return _serialize(row)

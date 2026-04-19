import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..coach import get_or_create_pre_run_note, get_or_create_post_run_note
from ..database import get_db
from ..models import DailyCheckin, User
from .auth import get_current_user
from .today import get_current_week

router = APIRouter()


def _serialize(note) -> dict:
    return {
        "id": note.id,
        "type": note.note_type,
        "date": note.note_date,
        "week": note.week_number,
        "checkin_id": note.checkin_id,
        "text": note.text,
        "model": note.model_used,
        "metrics": json.loads(note.metrics_json) if note.metrics_json else None,
    }


@router.get("/pre-run")
def pre_run_note(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return today's pre-run coach note (cached per day)."""
    today = date.today()
    week = get_current_week()
    day_of_week = today.weekday()
    note = get_or_create_pre_run_note(db, current_user, today, week, day_of_week)
    return _serialize(note)


@router.get("/post-run/{checkin_id}")
def post_run_note(
    checkin_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return post-run summary for a specific check-in (cached per checkin)."""
    checkin = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.id == checkin_id, DailyCheckin.user_id == current_user.id)
        .first()
    )
    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in not found")
    note = get_or_create_post_run_note(db, current_user, checkin)
    return _serialize(note)

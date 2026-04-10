from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import WeeklyLog, User
from .auth import get_current_user

router = APIRouter()

START_DATE = date(2026, 4, 14)
START_WEIGHT_KG = 94.0
HEIGHT_CM = 180.5  # 5'11"


def get_week_number(log_date: date) -> int:
    delta = (log_date - START_DATE).days
    if delta < 0:
        return 0
    return (delta // 7) + 1


class WeeklyLogCreate(BaseModel):
    log_date: Optional[str] = None
    week_number: Optional[int] = None
    weight_kg: float
    waist_inches: float
    chest_inches: Optional[float] = None
    hips_inches: Optional[float] = None
    body_fat_pct: Optional[float] = None
    notes: Optional[str] = None


@router.post("/weekly")
def create_weekly_log(
    payload: WeeklyLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = payload.log_date or date.today().isoformat()
    try:
        d = date.fromisoformat(today)
    except ValueError:
        d = date.today()

    week_num = payload.week_number if payload.week_number is not None else get_week_number(d)

    log = WeeklyLog(
        user_id=current_user.id,
        log_date=today,
        week_number=week_num,
        weight_kg=payload.weight_kg,
        waist_inches=payload.waist_inches,
        chest_inches=payload.chest_inches,
        hips_inches=payload.hips_inches,
        body_fat_pct=payload.body_fat_pct,
        notes=payload.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Compute derived fields
    bmi = payload.weight_kg / ((HEIGHT_CM / 100) ** 2)
    weight_change_from_start = payload.weight_kg - START_WEIGHT_KG

    # Previous week weight
    prev = (
        db.query(WeeklyLog)
        .filter(
            WeeklyLog.user_id == current_user.id,
            WeeklyLog.id != log.id,
        )
        .order_by(WeeklyLog.log_date.desc())
        .first()
    )
    weekly_change = payload.weight_kg - prev.weight_kg if prev else 0.0

    return {
        "id": log.id,
        "log_date": log.log_date,
        "week_number": log.week_number,
        "weight_kg": log.weight_kg,
        "waist_inches": log.waist_inches,
        "chest_inches": log.chest_inches,
        "hips_inches": log.hips_inches,
        "body_fat_pct": log.body_fat_pct,
        "bmi": round(bmi, 1),
        "weight_change_from_start": round(weight_change_from_start, 1),
        "weight_change_from_last_week": round(weekly_change, 1),
        "notes": log.notes,
    }


@router.get("/weekly")
def list_weekly_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(WeeklyLog)
        .filter(WeeklyLog.user_id == current_user.id)
        .order_by(WeeklyLog.log_date.asc())
        .all()
    )
    result = []
    prev_weight = START_WEIGHT_KG
    for r in rows:
        bmi = r.weight_kg / ((HEIGHT_CM / 100) ** 2)
        result.append({
            "id": r.id,
            "log_date": r.log_date,
            "week_number": r.week_number,
            "weight_kg": r.weight_kg,
            "waist_inches": r.waist_inches,
            "chest_inches": r.chest_inches,
            "hips_inches": r.hips_inches,
            "body_fat_pct": r.body_fat_pct,
            "bmi": round(bmi, 1),
            "weight_change_from_start": round(r.weight_kg - START_WEIGHT_KG, 1),
            "weight_change_from_last_week": round(r.weight_kg - prev_weight, 1),
            "notes": r.notes,
        })
        prev_weight = r.weight_kg
    return result

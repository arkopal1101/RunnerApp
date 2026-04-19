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
START_WEIGHT_KG = 95.0
START_WAIST_INCHES = 40.0
HEIGHT_CM = 180.5  # 5'11"


def get_week_number(log_date: date) -> int:
    delta = (log_date - START_DATE).days
    if delta < 0:
        return 0
    return (delta // 7) + 1


def compute_derived(weight_kg: float, prev_weight: float) -> dict:
    bmi = weight_kg / ((HEIGHT_CM / 100) ** 2)
    weight_change_from_start = weight_kg - START_WEIGHT_KG
    weight_change_from_last = weight_kg - prev_weight
    return {
        "bmi": round(bmi, 1),
        "weight_change_from_start": round(weight_change_from_start, 1),
        "weight_change_from_last_week": round(weight_change_from_last, 1),
    }


def log_to_dict(log: WeeklyLog, prev_weight: float = START_WEIGHT_KG) -> dict:
    derived = compute_derived(log.weight_kg, prev_weight)
    return {
        "id": log.id,
        "log_date": log.log_date,
        "week_number": log.week_number,
        "weight_kg": log.weight_kg,
        "waist_inches": log.waist_inches,
        "chest_inches": log.chest_inches,
        "hips_inches": log.hips_inches,
        "body_fat_pct": log.body_fat_pct,
        "notes": log.notes,
        **derived,
    }


class WeeklyLogCreate(BaseModel):
    log_date: Optional[str] = None
    week_number: Optional[int] = None
    weight_kg: float
    waist_inches: float
    chest_inches: Optional[float] = None
    hips_inches: Optional[float] = None
    body_fat_pct: Optional[float] = None
    notes: Optional[str] = None


class WeeklyLogUpdate(BaseModel):
    weight_kg: Optional[float] = None
    waist_inches: Optional[float] = None
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
        today = d.isoformat()

    week_num = payload.week_number if payload.week_number is not None else get_week_number(d)

    # Check for existing log this week
    existing = (
        db.query(WeeklyLog)
        .filter(
            WeeklyLog.user_id == current_user.id,
            WeeklyLog.week_number == week_num,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"message": f"A log already exists for Week {week_num}.", "existing_id": existing.id}
        )

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

    prev = (
        db.query(WeeklyLog)
        .filter(WeeklyLog.user_id == current_user.id, WeeklyLog.id != log.id)
        .order_by(WeeklyLog.log_date.desc())
        .first()
    )
    prev_weight = prev.weight_kg if prev else START_WEIGHT_KG
    return log_to_dict(log, prev_weight)


@router.put("/weekly/{log_id}")
def update_weekly_log(
    log_id: int,
    payload: WeeklyLogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = db.query(WeeklyLog).filter(
        WeeklyLog.id == log_id,
        WeeklyLog.user_id == current_user.id,
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    if payload.weight_kg is not None:
        log.weight_kg = payload.weight_kg
    if payload.waist_inches is not None:
        log.waist_inches = payload.waist_inches
    if payload.chest_inches is not None:
        log.chest_inches = payload.chest_inches
    if payload.hips_inches is not None:
        log.hips_inches = payload.hips_inches
    if payload.body_fat_pct is not None:
        log.body_fat_pct = payload.body_fat_pct
    if payload.notes is not None:
        log.notes = payload.notes

    db.commit()
    db.refresh(log)

    prev = (
        db.query(WeeklyLog)
        .filter(WeeklyLog.user_id == current_user.id, WeeklyLog.id != log.id)
        .order_by(WeeklyLog.log_date.desc())
        .first()
    )
    prev_weight = prev.weight_kg if prev else START_WEIGHT_KG
    return log_to_dict(log, prev_weight)


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
        result.append(log_to_dict(r, prev_weight))
        prev_weight = r.weight_kg
    return result

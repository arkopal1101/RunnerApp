from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..plan_data import get_week, get_all_weeks, get_day, get_phase
from ..services.adjuster import get_adjusted_day
from .auth import get_current_user
from .today import START_DATE, get_current_week

router = APIRouter()


def _apply_adjustments_to_week(week_data: dict, user_id: int, db: Session) -> dict:
    """
    Merge any PlanAdjustment rows for this user/week into the week's days.
    Adjusted days get `adjusted: true` + `adjustment_rationale` markers so the
    UI can flag them.
    """
    for dow, day in enumerate(week_data["days"]):
        adj = get_adjusted_day(db, user_id, week_data["week"], dow)
        if adj:
            merged = dict(adj["day"])
            merged["adjusted"] = True
            merged["adjustment_rationale"] = adj["rationale"]
            merged["adjusted_at"] = adj["adjusted_at"]
            week_data["days"][dow] = merged
        else:
            day["adjusted"] = False
    return week_data


@router.get("/week/{week_number}")
def plan_week(
    week_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not 1 <= week_number <= 32:
        raise HTTPException(status_code=404, detail="Week out of range (1-32)")
    w = get_week(week_number)
    return _apply_adjustments_to_week(w, current_user.id, db)


@router.get("/today")
def plan_today(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return today's planned activity with full detail (adjustments merged)."""
    week = get_current_week()
    day_of_week = date.today().weekday()  # Mon=0..Sun=6
    day = get_day(week, day_of_week)
    if not day:
        raise HTTPException(status_code=404, detail="No activity for today")
    adj = get_adjusted_day(db, current_user.id, week, day_of_week)
    if adj:
        day = dict(adj["day"])
        day["adjusted"] = True
        day["adjustment_rationale"] = adj["rationale"]
        day["adjusted_at"] = adj["adjusted_at"]
    else:
        day["adjusted"] = False
    return {
        "week": week,
        "phase": get_phase(week),
        "day_of_week": day_of_week,
        "day": day,
    }


@router.get("/all")
def plan_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    weeks = get_all_weeks()
    return {"weeks": [_apply_adjustments_to_week(w, current_user.id, db) for w in weeks]}

"""
Baseline calibration — compute a personal Z2 baseline pace from Week 1 runs
and store it on the User. Write-once: after calibration, the stored value
is locked unless the caller passes `force=true`.

The baseline is used by coach notes and the adjuster for "gap to target"
math so guidance reflects your actual starting point, not the hardcoded
10:30/km baseline.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..coach import pace_to_seconds, seconds_to_pace
from ..database import get_db
from ..models import DailyCheckin, User
from .auth import get_current_user

router = APIRouter()

CALIBRATION_WEEK = 1
MIN_RUNS_REQUIRED = 2


def _current_baseline(user: User) -> dict:
    return {
        "baseline_pace_seconds": user.baseline_pace_seconds,
        "baseline_pace_str": seconds_to_pace(user.baseline_pace_seconds) if user.baseline_pace_seconds else None,
        "calibrated_at": user.baseline_calibrated_at.isoformat() if user.baseline_calibrated_at else None,
        "is_calibrated": user.baseline_pace_seconds is not None,
    }


@router.get("")
def get_baseline(current_user: User = Depends(get_current_user)):
    return _current_baseline(current_user)


@router.post("/calibrate")
def calibrate_baseline(
    force: bool = Query(False, description="Re-run calibration even if already set"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compute an average Z2 pace from this user's Week 1 run check-ins and
    store it as their personal baseline. Write-once by default — pass
    `?force=true` to override.
    """
    if current_user.baseline_pace_seconds is not None and not force:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Baseline already calibrated. Pass ?force=true to override.",
                **_current_baseline(current_user),
            },
        )

    runs = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == current_user.id)
        .filter(DailyCheckin.week_number == CALIBRATION_WEEK)
        .filter(DailyCheckin.avg_pace_per_km.isnot(None))
        .all()
    )
    if len(runs) < MIN_RUNS_REQUIRED:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {MIN_RUNS_REQUIRED} Week 1 runs to calibrate (have {len(runs)})",
        )

    pace_secs = [pace_to_seconds(r.avg_pace_per_km) for r in runs]
    pace_secs = [p for p in pace_secs if p]
    if not pace_secs:
        raise HTTPException(status_code=400, detail="No parseable pace values found in Week 1 runs")

    avg = sum(pace_secs) // len(pace_secs)
    current_user.baseline_pace_seconds = avg
    current_user.baseline_calibrated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)

    return {
        **_current_baseline(current_user),
        "runs_used": len(pace_secs),
        "individual_paces_sec": pace_secs,
    }

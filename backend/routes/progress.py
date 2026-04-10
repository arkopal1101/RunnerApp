import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DailyCheckin, WeeklyLog, User
from .auth import get_current_user

router = APIRouter()

START_DATE = date(2026, 4, 14)
START_WEIGHT_KG = 94.0
TARGET_WEIGHT_KG = 80.0
START_WAIST_INCHES = 38.0
TARGET_WAIST_INCHES = 32.0
BASELINE_PACE = "10:30"   # mm:ss per km
PHASE1_GATE_PACE = "7:30"
PHASE2_GATE_PACE = "7:00"
HEIGHT_CM = 180.5


def pace_to_seconds(pace_str: str) -> int:
    try:
        parts = pace_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0


def get_current_week() -> int:
    delta = (date.today() - START_DATE).days
    if delta < 0:
        return 1
    return (delta // 7) + 1


def get_phase(week: int) -> int:
    if week <= 8:
        return 1
    elif week <= 16:
        return 2
    elif week <= 24:
        return 3
    return 4


@router.get("/progress")
def get_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fetch all weekly logs
    weekly_logs = (
        db.query(WeeklyLog)
        .filter(WeeklyLog.user_id == current_user.id)
        .order_by(WeeklyLog.log_date.asc())
        .all()
    )

    # Fetch all daily checkins
    checkins = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == current_user.id)
        .order_by(DailyCheckin.checkin_date.asc())
        .all()
    )

    # Weight chart data
    weight_data = [{"date": w.log_date, "week": w.week_number, "weight": w.weight_kg} for w in weekly_logs]

    # Waist chart data
    waist_data = [{"date": w.log_date, "week": w.week_number, "waist": w.waist_inches} for w in weekly_logs]

    # Pace over time from checkins
    pace_data = []
    for c in checkins:
        if c.avg_pace_per_km:
            pace_data.append({
                "date": c.checkin_date,
                "week": c.week_number,
                "pace_seconds": pace_to_seconds(c.avg_pace_per_km),
                "pace_str": c.avg_pace_per_km,
            })

    # HR over time
    hr_data = [
        {"date": c.checkin_date, "week": c.week_number, "avg_hr": c.avg_hr_bpm}
        for c in checkins if c.avg_hr_bpm
    ]

    # Weekly run volume (km per week)
    volume_by_week: dict = {}
    for c in checkins:
        if c.week_number and c.total_distance_km:
            volume_by_week[c.week_number] = volume_by_week.get(c.week_number, 0) + c.total_distance_km

    volume_data = [{"week": k, "km": round(v, 2)} for k, v in sorted(volume_by_week.items())]

    # Current week stats
    current_week = get_current_week()
    current_phase = get_phase(current_week)

    # Runs this week
    week_start = START_DATE + timedelta(weeks=current_week - 1)
    week_end = week_start + timedelta(days=6)
    runs_this_week = sum(
        1 for c in checkins
        if c.checkin_date and week_start.isoformat() <= c.checkin_date <= week_end.isoformat()
    )

    # Latest pace
    latest_pace_str = None
    latest_pace_sec = None
    if pace_data:
        latest_pace_str = pace_data[-1]["pace_str"]
        latest_pace_sec = pace_data[-1]["pace_seconds"]

    # Latest weight
    latest_weight = weekly_logs[-1].weight_kg if weekly_logs else None

    # Phase gate progress
    phase_gates = {1: 8, 2: 16, 3: 24, 4: 32}
    phase_gate_week = phase_gates.get(current_phase, 32)
    phase_start_week = {1: 1, 2: 9, 3: 17, 4: 25}.get(current_phase, 1)
    phase_total_weeks = phase_gate_week - phase_start_week + 1
    weeks_into_phase = current_week - phase_start_week + 1
    phase_progress_pct = min(100, round((weeks_into_phase / phase_total_weeks) * 100))

    return {
        "weight_chart": weight_data,
        "waist_chart": waist_data,
        "pace_chart": pace_data,
        "hr_chart": hr_data,
        "volume_chart": volume_data,
        "summary": {
            "current_week": current_week,
            "current_phase": current_phase,
            "runs_this_week": runs_this_week,
            "latest_weight": latest_weight,
            "target_weight": TARGET_WEIGHT_KG,
            "latest_pace": latest_pace_str,
            "latest_pace_seconds": latest_pace_sec,
            "baseline_pace": BASELINE_PACE,
            "phase1_gate_pace": PHASE1_GATE_PACE,
            "phase2_gate_pace": PHASE2_GATE_PACE,
            "weeks_until_phase_gate": max(0, phase_gate_week - current_week),
            "phase_progress_pct": phase_progress_pct,
            "start_weight": START_WEIGHT_KG,
            "start_waist": START_WAIST_INCHES,
            "target_waist": TARGET_WAIST_INCHES,
        },
        "references": {
            "start_weight": START_WEIGHT_KG,
            "target_weight": TARGET_WEIGHT_KG,
            "start_waist": START_WAIST_INCHES,
            "target_waist": TARGET_WAIST_INCHES,
            "baseline_pace_seconds": pace_to_seconds(BASELINE_PACE),
            "phase1_gate_seconds": pace_to_seconds(PHASE1_GATE_PACE),
            "phase2_gate_seconds": pace_to_seconds(PHASE2_GATE_PACE),
        }
    }

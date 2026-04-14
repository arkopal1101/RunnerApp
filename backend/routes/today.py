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
BASELINE_PACE = "10:30"
PHASE1_GATE_PACE = "7:30"
PHASE2_GATE_PACE = "7:00"

PHASE_NAMES = {1: "Aerobic Base", 2: "Build & Recomp", 3: "Race Specific", 4: "Peak & Race Ready"}


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
    return min((delta // 7) + 1, 32)


def get_phase(week: int) -> int:
    if week <= 8:
        return 1
    elif week <= 16:
        return 2
    elif week <= 24:
        return 3
    return 4


# Standard weekly day types: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
STANDARD_DAY_TYPES = {0: "strength", 1: "run", 2: "rest", 3: "strength", 4: "run", 5: "rest", 6: "long-run"}
DELOAD_DAY_TYPES = {0: "rest", 1: "run", 2: "strength", 3: "rest", 4: "run", 5: "rest", 6: "long-run"}
DELOAD_WEEKS = {5, 12, 21, 29, 30, 31}
RACE_WEEK = 32


def get_day_type(week: int, day_of_week: int) -> str:
    if week == RACE_WEEK:
        race_map = {0: "run", 1: "rest", 2: "run", 3: "rest", 4: "rest", 5: "run", 6: "long-run"}
        return race_map.get(day_of_week, "rest")
    if week in DELOAD_WEEKS:
        return DELOAD_DAY_TYPES.get(day_of_week, "rest")
    return STANDARD_DAY_TYPES.get(day_of_week, "rest")


def compute_phase_gate(phase: int, checkins: list, weekly_logs: list) -> dict:
    if not checkins:
        return {
            "phase": phase,
            "status": "insufficient_data",
            "message": "Log your first few runs to unlock phase gate tracking.",
            "requirements": [],
        }

    max_long_run = max((c.total_distance_km or 0.0) for c in checkins)
    pace_entries = [
        pace_to_seconds(c.avg_pace_per_km)
        for c in checkins
        if c.avg_pace_per_km and pace_to_seconds(c.avg_pace_per_km) > 0
    ]
    latest_pace_sec = pace_entries[-1] if pace_entries else None

    # Adherence: runs in last 4 weeks vs planned ~8
    lookback = date.today() - timedelta(weeks=4)
    recent_runs = sum(
        1 for c in checkins
        if c.checkin_date and c.checkin_date >= lookback.isoformat()
    )
    adherence_pct = min(100, round(recent_runs / 8 * 100))

    def pace_display(sec):
        if sec is None:
            return "no data"
        return f"{sec // 60}:{sec % 60:02d}/km"

    if phase == 1:
        req_lr, req_pace, req_adh = 14.0, pace_to_seconds(PHASE1_GATE_PACE), 75
        reqs = [
            {"label": "Long run >= 14 km", "current": f"{max_long_run:.1f} km", "met": max_long_run >= req_lr},
            {"label": "Zone 2 pace <= 7:30/km", "current": pace_display(latest_pace_sec), "met": latest_pace_sec is not None and latest_pace_sec <= req_pace},
            {"label": "Consistency >= 75%", "current": f"{adherence_pct}%", "met": adherence_pct >= req_adh},
        ]
    elif phase == 2:
        req_lr, req_pace, req_adh = 18.0, pace_to_seconds(PHASE2_GATE_PACE), 75
        reqs = [
            {"label": "Long run >= 18 km", "current": f"{max_long_run:.1f} km", "met": max_long_run >= req_lr},
            {"label": "Zone 2 pace <= 7:00/km", "current": pace_display(latest_pace_sec), "met": latest_pace_sec is not None and latest_pace_sec <= req_pace},
            {"label": "Consistency >= 75%", "current": f"{adherence_pct}%", "met": adherence_pct >= 75},
        ]
    elif phase == 3:
        latest_weight = weekly_logs[-1].weight_kg if weekly_logs else None
        reqs = [
            {"label": "Long run / race sim >= 19 km", "current": f"{max_long_run:.1f} km", "met": max_long_run >= 19.0},
            {"label": "Consistency >= 75%", "current": f"{adherence_pct}%", "met": adherence_pct >= 75},
            {"label": "Weight approaching target (<83 kg)", "current": f"{latest_weight:.1f} kg" if latest_weight else "no data", "met": latest_weight is not None and latest_weight <= 83.0},
        ]
    else:
        return {
            "phase": 4,
            "status": "taper",
            "message": "Focus on freshness, consistency, and injury avoidance. Race day is close.",
            "requirements": [],
        }

    met = sum(1 for r in reqs if r["met"])
    if latest_pace_sec is None and phase <= 2:
        status = "insufficient_data"
    elif met == len(reqs):
        status = "ready"
    elif met >= len(reqs) - 1:
        status = "almost_ready"
    else:
        status = "repeat_phase"

    return {"phase": phase, "status": status, "requirements": reqs}


def get_coaching_note(week: int, phase: int, checkins: list, weekly_logs: list) -> str:
    if not checkins and not weekly_logs:
        return "Welcome to Week 1. Start by logging your first run and weekly check-in."
    if not checkins:
        return "Log your first run to start tracking pace and heart rate trends."

    # Volume jump check
    week_start = START_DATE + timedelta(weeks=week - 1)
    prev_week_start = week_start - timedelta(weeks=1)
    curr_vol = sum(c.total_distance_km or 0 for c in checkins if c.checkin_date and c.checkin_date >= week_start.isoformat())
    prev_vol = sum(
        c.total_distance_km or 0 for c in checkins
        if c.checkin_date and prev_week_start.isoformat() <= c.checkin_date < week_start.isoformat()
    )
    if prev_vol > 0 and curr_vol > prev_vol * 1.3:
        return "Your weekly volume jumped quickly. Keep your next run easy to avoid overloading."

    latest = checkins[-1]
    if latest.avg_pace_per_km:
        pace_sec = pace_to_seconds(latest.avg_pace_per_km)
        gate_sec = pace_to_seconds(PHASE1_GATE_PACE) if phase == 1 else pace_to_seconds(PHASE2_GATE_PACE)
        if phase <= 2 and pace_sec <= gate_sec:
            return f"Your Zone 2 pace is at {latest.avg_pace_per_km}/km - hitting phase gate territory. Stay consistent."
        if phase == 1:
            return f"Zone 2 pace at {latest.avg_pace_per_km}/km. You're building your aerobic base - consistency is everything right now."

    if weekly_logs:
        weight_change = weekly_logs[-1].weight_kg - START_WEIGHT_KG
        if weight_change <= -1.0:
            return f"You're down {abs(weight_change):.1f} kg from your start weight. Keep showing up."

    return f"Week {week}, Phase {phase} - {PHASE_NAMES[phase]}. Phase progress depends on both time and readiness."


@router.get("/today")
def get_today(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    current_week = get_current_week()
    current_phase = get_phase(current_week)
    day_of_week = today.weekday()  # 0=Mon, 6=Sun
    plan_complete = (today - START_DATE).days > 32 * 7

    checkins = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == current_user.id)
        .order_by(DailyCheckin.checkin_date.asc())
        .all()
    )
    weekly_logs = (
        db.query(WeeklyLog)
        .filter(WeeklyLog.user_id == current_user.id)
        .order_by(WeeklyLog.log_date.asc())
        .all()
    )

    latest_checkin = None
    if checkins:
        c = checkins[-1]
        latest_checkin = {
            "id": c.id,
            "checkin_date": c.checkin_date,
            "week_number": c.week_number,
            "total_distance_km": c.total_distance_km,
            "avg_pace_per_km": c.avg_pace_per_km,
            "avg_hr_bpm": c.avg_hr_bpm,
            "notes": c.notes,
        }

    latest_weekly = None
    if weekly_logs:
        w = weekly_logs[-1]
        latest_weekly = {
            "id": w.id,
            "log_date": w.log_date,
            "week_number": w.week_number,
            "weight_kg": w.weight_kg,
            "waist_inches": w.waist_inches,
        }

    day_type = get_day_type(current_week, day_of_week)

    # Next action
    if day_of_week == 6:  # Sunday: suggest weekly check-in alongside run
        next_action = "weekly_checkin"
    elif day_type in ("run", "long-run", "tempo"):
        next_action = "log_run"
    elif day_type == "strength":
        next_action = "log_strength"
    else:
        next_action = "log_recovery"

    # Phase progress
    phase_gate_week = {1: 8, 2: 16, 3: 24, 4: 32}[current_phase]
    phase_start_week = {1: 1, 2: 9, 3: 17, 4: 25}[current_phase]
    phase_total = phase_gate_week - phase_start_week + 1
    phase_progress_pct = min(100, round((current_week - phase_start_week + 1) / phase_total * 100))

    # Overall status: needs_attention if no run in past 7 days or no weekly log ever
    recent_cutoff = (today - timedelta(days=7)).isoformat()
    recent_runs = [c for c in checkins if c.checkin_date and c.checkin_date >= recent_cutoff]
    overall_status = "on_track" if (recent_runs or not checkins) and weekly_logs else "needs_attention"
    if not checkins:
        overall_status = "needs_attention"

    return {
        "today_date": today.isoformat(),
        "current_week": current_week,
        "current_phase": current_phase,
        "phase_name": PHASE_NAMES[current_phase],
        "day_of_week": day_of_week,
        "day_type": day_type,
        "next_action": next_action,
        "plan_complete": plan_complete,
        "phase_progress_pct": phase_progress_pct,
        "weeks_until_phase_gate": max(0, phase_gate_week - current_week),
        "latest_checkin": latest_checkin,
        "latest_weekly_log": latest_weekly,
        "phase_gate": compute_phase_gate(current_phase, checkins, weekly_logs),
        "status": overall_status,
        "coaching_note": get_coaching_note(current_week, current_phase, checkins, weekly_logs),
    }

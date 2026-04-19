import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DailyCheckin, WeeklyLog, User
from ..weekly_summary import compute_weekly_summary
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


def compute_insights(checkins: list, weekly_logs: list, current_week: int) -> dict:
    """Generate coaching insights from logged data."""

    # --- Aerobic Fitness ---
    pace_entries = [
        {"date": c.checkin_date, "sec": pace_to_seconds(c.avg_pace_per_km), "hr": c.avg_hr_bpm}
        for c in checkins if c.avg_pace_per_km and pace_to_seconds(c.avg_pace_per_km) > 0
    ]
    if len(pace_entries) >= 2:
        latest_pace = pace_entries[-1]["sec"]
        baseline_sec = pace_to_seconds(BASELINE_PACE)
        improvement = baseline_sec - latest_pace  # positive = faster
        improvement_pct = round(improvement / baseline_sec * 100, 1) if baseline_sec > 0 else 0
        latest_hr = pace_entries[-1]["hr"]
        hr_controlled = latest_hr is not None and latest_hr <= 145

        aerobic = {
            "status": "improving" if improvement > 0 else "regressing",
            "latest_pace": f"{latest_pace // 60}:{latest_pace % 60:02d}/km",
            "baseline_pace": BASELINE_PACE,
            "improvement_pct": improvement_pct,
            "latest_hr": latest_hr,
            "hr_controlled": hr_controlled,
            "message": (
                f"Your Zone 2 pace improved {improvement_pct:.1f}% from baseline ({BASELINE_PACE}/km to {latest_pace // 60}:{latest_pace % 60:02d}/km)."
                + (" Heart rate is staying controlled." if hr_controlled else " Watch your heart rate - it's running high.")
            ) if improvement > 0 else (
                f"Pace at {latest_pace // 60}:{latest_pace % 60:02d}/km. Aerobic base takes time - keep the easy effort consistent."
            ),
        }
    elif len(pace_entries) == 1:
        sec = pace_entries[0]["sec"]
        aerobic = {
            "status": "baseline",
            "latest_pace": f"{sec // 60}:{sec % 60:02d}/km",
            "message": "One run logged. Log more runs to see your pace trend.",
        }
    else:
        aerobic = {
            "status": "no_data",
            "message": "No pace data yet. Upload a run to start tracking aerobic fitness.",
        }

    # --- Body Recomposition ---
    if len(weekly_logs) >= 2:
        latest_w = weekly_logs[-1]
        prev_w = weekly_logs[-2]
        weight_change_start = round(latest_w.weight_kg - START_WEIGHT_KG, 1)
        weight_change_week = round(latest_w.weight_kg - prev_w.weight_kg, 1)
        waist_change_start = round(latest_w.waist_inches - START_WAIST_INCHES, 1)

        # Pace interpretation: healthy = -0.1 to -0.5 kg/week
        if weight_change_week < -0.8:
            rate_msg = "Weight dropping fast. Make sure you're eating enough to fuel training."
        elif weight_change_week < -0.1:
            rate_msg = "Healthy rate of change. Keep it consistent."
        elif weight_change_week < 0.2:
            rate_msg = "Weight holding steady. Normal during high-training weeks."
        else:
            rate_msg = "Weight ticked up this week. Check sleep, stress, and nutrition."

        body_recomp = {
            "status": "tracking",
            "weight_change_start": weight_change_start,
            "weight_change_week": weight_change_week,
            "waist_change_start": waist_change_start,
            "latest_weight": latest_w.weight_kg,
            "target_weight": TARGET_WEIGHT_KG,
            "message": f"{'+' if weight_change_start >= 0 else ''}{weight_change_start} kg from start. {rate_msg}",
        }
    elif len(weekly_logs) == 1:
        w = weekly_logs[0]
        body_recomp = {
            "status": "baseline",
            "latest_weight": w.weight_kg,
            "weight_change_start": round(w.weight_kg - START_WEIGHT_KG, 1),
            "message": "One check-in logged. Log again next week to see your trend.",
        }
    else:
        body_recomp = {
            "status": "no_data",
            "message": "No weekly check-ins yet. Log weight and waist to track body recomposition.",
        }

    # --- Training Load ---
    week_start = START_DATE + timedelta(weeks=current_week - 1)
    prev_week_start = week_start - timedelta(weeks=1)
    curr_vol = sum(
        c.total_distance_km or 0 for c in checkins
        if c.checkin_date and c.checkin_date >= week_start.isoformat()
    )
    prev_vol = sum(
        c.total_distance_km or 0 for c in checkins
        if c.checkin_date and prev_week_start.isoformat() <= c.checkin_date < week_start.isoformat()
    )

    if curr_vol > 0 and prev_vol > 0:
        vol_change_pct = round((curr_vol - prev_vol) / prev_vol * 100, 1)
        if vol_change_pct > 30:
            load_status = "high_jump"
            load_msg = f"Volume jumped {vol_change_pct:.0f}% from last week. Keep your next run easy - sudden jumps increase injury risk."
        elif vol_change_pct > 10:
            load_status = "normal_increase"
            load_msg = f"Volume up {vol_change_pct:.0f}% from last week. Solid progression."
        elif vol_change_pct < -20:
            load_status = "low"
            load_msg = f"Volume down {abs(vol_change_pct):.0f}% from last week. Deload week or missed sessions?"
        else:
            load_status = "steady"
            load_msg = f"Volume steady at {curr_vol:.1f} km this week. Consistent effort."

        training_load = {
            "status": load_status,
            "current_week_km": round(curr_vol, 1),
            "prev_week_km": round(prev_vol, 1),
            "change_pct": vol_change_pct,
            "message": load_msg,
        }
    elif curr_vol > 0:
        training_load = {
            "status": "first_week",
            "current_week_km": round(curr_vol, 1),
            "message": f"{curr_vol:.1f} km logged this week. Keep going.",
        }
    else:
        training_load = {
            "status": "no_data",
            "message": "No runs logged this week yet.",
        }

    # --- Consistency ---
    runs_this_week = sum(
        1 for c in checkins
        if c.checkin_date and c.checkin_date >= week_start.isoformat()
    )
    planned_per_week = 2
    lookback_4w = (date.today() - timedelta(weeks=4)).isoformat()
    runs_4w = sum(1 for c in checkins if c.checkin_date and c.checkin_date >= lookback_4w)
    adherence_pct = min(100, round(runs_4w / (planned_per_week * 4) * 100)) if checkins else 0

    if adherence_pct >= 80:
        consistency_msg = f"Excellent consistency - {adherence_pct}% adherence over the past 4 weeks. You're building a habit."
    elif adherence_pct >= 60:
        consistency_msg = f"{adherence_pct}% adherence over 4 weeks. You're building consistency - log one more run this week to stay on track."
    elif checkins:
        consistency_msg = f"{adherence_pct}% adherence over 4 weeks. Consistency is the single biggest predictor of race readiness. Aim for 2-3 runs per week."
    else:
        consistency_msg = "No runs logged yet. Start with 2 runs this week."

    consistency = {
        "runs_this_week": runs_this_week,
        "planned_this_week": planned_per_week,
        "adherence_pct": adherence_pct,
        "message": consistency_msg,
    }

    # --- Next Best Action ---
    if not checkins and not weekly_logs:
        next_action = {"action": "log_run", "message": "Log your first run to get started."}
    elif not checkins:
        next_action = {"action": "log_run", "message": "You have a weekly check-in - now log a run to unlock pace and load insights."}
    elif not weekly_logs:
        next_action = {"action": "weekly_checkin", "message": "Complete your first weekly check-in to start tracking body recomposition."}
    elif runs_this_week == 0:
        next_action = {"action": "log_run", "message": "Log a run this week to maintain consistency."}
    elif training_load.get("status") == "high_jump":
        next_action = {"action": "easy_run", "message": "Volume jumped - keep your next run short and easy."}
    elif adherence_pct < 60:
        next_action = {"action": "log_run", "message": "Log one more run this week to improve consistency."}
    else:
        next_action = {"action": "continue", "message": "You're on track. Keep logging and stay consistent."}

    return {
        "aerobic_fitness": aerobic,
        "body_recomposition": body_recomp,
        "training_load": training_load,
        "consistency": consistency,
        "next_best_action": next_action,
    }


def compute_phase_gate(phase: int, checkins: list, weekly_logs: list) -> dict:
    if not checkins:
        return {
            "phase": phase,
            "status": "insufficient_data",
            "message": "Log your first few runs to see phase gate readiness.",
            "requirements": [],
        }

    max_long_run = max((c.total_distance_km or 0.0) for c in checkins)
    pace_entries = [
        pace_to_seconds(c.avg_pace_per_km)
        for c in checkins if c.avg_pace_per_km and pace_to_seconds(c.avg_pace_per_km) > 0
    ]
    latest_pace_sec = pace_entries[-1] if pace_entries else None
    lookback = (date.today() - timedelta(weeks=4)).isoformat()
    recent_runs = sum(1 for c in checkins if c.checkin_date and c.checkin_date >= lookback)
    adherence_pct = min(100, round(recent_runs / 8 * 100))

    def fmt_pace(sec):
        if sec is None:
            return "no data"
        return f"{sec // 60}:{sec % 60:02d}/km"

    if phase == 1:
        reqs = [
            {"label": "Long run >= 14 km", "current": f"{max_long_run:.1f} km", "met": max_long_run >= 14.0},
            {"label": "Zone 2 pace <= 7:30/km", "current": fmt_pace(latest_pace_sec), "met": latest_pace_sec is not None and latest_pace_sec <= pace_to_seconds(PHASE1_GATE_PACE)},
            {"label": "Consistency >= 75%", "current": f"{adherence_pct}%", "met": adherence_pct >= 75},
        ]
    elif phase == 2:
        reqs = [
            {"label": "Long run >= 18 km", "current": f"{max_long_run:.1f} km", "met": max_long_run >= 18.0},
            {"label": "Zone 2 pace <= 7:00/km", "current": fmt_pace(latest_pace_sec), "met": latest_pace_sec is not None and latest_pace_sec <= pace_to_seconds(PHASE2_GATE_PACE)},
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
        return {"phase": 4, "status": "taper", "message": "Focus on freshness and race readiness.", "requirements": []}

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


@router.get("/progress")
def get_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    weekly_logs = (
        db.query(WeeklyLog)
        .filter(WeeklyLog.user_id == current_user.id)
        .order_by(WeeklyLog.log_date.asc())
        .all()
    )

    checkins = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == current_user.id)
        .order_by(DailyCheckin.checkin_date.asc())
        .all()
    )

    # Chart data
    weight_data = [{"date": w.log_date, "week": w.week_number, "weight": w.weight_kg} for w in weekly_logs]
    waist_data = [{"date": w.log_date, "week": w.week_number, "waist": w.waist_inches} for w in weekly_logs]

    pace_data = []
    for c in checkins:
        if c.avg_pace_per_km:
            pace_data.append({
                "date": c.checkin_date,
                "week": c.week_number,
                "pace_seconds": pace_to_seconds(c.avg_pace_per_km),
                "pace_str": c.avg_pace_per_km,
            })

    hr_data = [
        {"date": c.checkin_date, "week": c.week_number, "avg_hr": c.avg_hr_bpm}
        for c in checkins if c.avg_hr_bpm
    ]

    volume_by_week: dict = {}
    for c in checkins:
        if c.week_number and c.total_distance_km:
            volume_by_week[c.week_number] = volume_by_week.get(c.week_number, 0) + c.total_distance_km

    volume_data = [{"week": k, "km": round(v, 2)} for k, v in sorted(volume_by_week.items())]

    current_week = get_current_week()
    current_phase = get_phase(current_week)

    week_start = START_DATE + timedelta(weeks=current_week - 1)
    week_end = week_start + timedelta(days=6)
    runs_this_week = sum(
        1 for c in checkins
        if c.checkin_date and week_start.isoformat() <= c.checkin_date <= week_end.isoformat()
    )

    latest_pace_str = pace_data[-1]["pace_str"] if pace_data else None
    latest_pace_sec = pace_data[-1]["pace_seconds"] if pace_data else None
    latest_weight = weekly_logs[-1].weight_kg if weekly_logs else None

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
        },
        "insights": compute_insights(checkins, weekly_logs, current_week),
        "phase_gate": compute_phase_gate(current_phase, checkins, weekly_logs),
    }


@router.get("/progress/weekly-summary")
def weekly_summary(
    week: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rings (volume/sessions/Z2 adherence) + week-over-week comparison."""
    target_week = week if week is not None else get_current_week()
    if not 1 <= target_week <= 32:
        raise HTTPException(status_code=404, detail="Week out of range (1-32)")

    checkins = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == current_user.id)
        .order_by(DailyCheckin.checkin_date.asc())
        .all()
    )
    return compute_weekly_summary(checkins, target_week)

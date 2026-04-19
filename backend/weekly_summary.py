"""
Weekly summary — computes three progress rings and a week-over-week
comparison for a given training week.

Rings:
  volume        — actual km ran vs planned km (sum of all run days in plan)
  sessions      — runs logged in the week vs planned runs
  z2_adherence  — % of easy/Z2 runs where avg_hr stayed within the planned HR cap

WoW comparison: total volume, avg pace, avg HR, session count.

All computation is pure (reads from a DailyCheckin list + plan_data), no I/O.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from .coach import pace_to_seconds, seconds_to_pace
from .plan_data import get_days_for_week

# Plan start date (same as today.py / progress.py).
START_DATE = date(2026, 4, 14)

# Day types that count as a running session.
RUN_TYPES = {"run", "long-run", "tempo", "intervals"}
EASY_Z2_TYPES = {"run", "long-run"}  # tempo/intervals are not Z2 by definition


def week_date_range(week: int) -> tuple[date, date]:
    """Return (Monday, Sunday) of the given training week."""
    start = START_DATE + timedelta(weeks=week - 1)
    end = start + timedelta(days=6)
    return start, end


def _checkins_in_week(checkins: list, week_start: date, week_end: date) -> list:
    start_iso = week_start.isoformat()
    end_iso = week_end.isoformat()
    return [c for c in checkins if c.checkin_date and start_iso <= c.checkin_date <= end_iso]


def _parse_hr_cap(target_hr: Optional[str]) -> Optional[int]:
    """Extract a numeric HR ceiling from a plan target string."""
    if not target_hr:
        return None
    s = target_hr.strip().lstrip("<").strip()
    # "130-145" → 145, "140-145" → 145, "<145" → 145
    try:
        parts = s.split("-")
        return int(parts[-1])
    except (ValueError, IndexError):
        return None


def compute_planned_week(week: int) -> dict:
    """Sum up planned targets for a week: total km, session count, easy-run HR caps."""
    days = get_days_for_week(week)
    total_km = 0.0
    session_count = 0
    easy_run_caps = []  # list of HR caps for Z2-style runs
    for d in days:
        t = d.get("targets", {})
        if d["type"] in RUN_TYPES:
            session_count += 1
            if t.get("distance_km"):
                total_km += t["distance_km"]
            if d["type"] in EASY_Z2_TYPES:
                cap = _parse_hr_cap(t.get("target_hr"))
                easy_run_caps.append(cap)
    return {
        "total_km": round(total_km, 1),
        "session_count": session_count,
        "easy_run_caps": easy_run_caps,  # by day index among easy runs
    }


def compute_rings(checkins_in_week: list, week: int) -> dict:
    """Three rings, each with label/actual/target/pct (clamped 0-100)."""
    planned = compute_planned_week(week)

    # Volume ring
    actual_km = round(sum(c.total_distance_km or 0 for c in checkins_in_week), 1)
    target_km = planned["total_km"]
    volume_pct = min(100, round(actual_km / target_km * 100)) if target_km > 0 else 0

    # Sessions ring — count runs logged
    actual_sessions = len(checkins_in_week)
    target_sessions = planned["session_count"]
    sessions_pct = min(100, round(actual_sessions / target_sessions * 100)) if target_sessions > 0 else 0

    # Z2 adherence ring — of this week's runs, how many stayed under the applicable HR cap?
    # We use an average cap across easy runs, since checkins aren't tagged to a specific day.
    easy_caps = [c for c in planned["easy_run_caps"] if c]
    avg_cap = int(sum(easy_caps) / len(easy_caps)) if easy_caps else 150  # fallback cap
    compliant = sum(1 for c in checkins_in_week if c.avg_hr_bpm and c.avg_hr_bpm <= avg_cap + 2)
    total_runs_with_hr = sum(1 for c in checkins_in_week if c.avg_hr_bpm)
    z2_actual_pct = round(compliant / total_runs_with_hr * 100) if total_runs_with_hr > 0 else 0
    z2_target_pct = 80  # a reasonable adherence bar
    z2_ring_pct = min(100, round(z2_actual_pct / z2_target_pct * 100)) if z2_target_pct > 0 else 0

    return {
        "volume": {
            "label": "Volume",
            "actual_km": actual_km,
            "target_km": target_km,
            "pct": volume_pct,
            "display": f"{actual_km} / {target_km} km",
        },
        "sessions": {
            "label": "Sessions",
            "actual": actual_sessions,
            "target": target_sessions,
            "pct": sessions_pct,
            "display": f"{actual_sessions} / {target_sessions}",
        },
        "z2_adherence": {
            "label": "Z2 Adherence",
            "actual_pct": z2_actual_pct,
            "target_pct": z2_target_pct,
            "pct": z2_ring_pct,
            "hr_cap": avg_cap,
            "compliant_runs": compliant,
            "total_runs_with_hr": total_runs_with_hr,
            "display": f"{z2_actual_pct}% / {z2_target_pct}%",
        },
    }


def _avg_pace(checkins: list) -> Optional[int]:
    secs = [pace_to_seconds(c.avg_pace_per_km) for c in checkins]
    secs = [s for s in secs if s]
    return sum(secs) // len(secs) if secs else None


def _avg_hr(checkins: list) -> Optional[float]:
    hrs = [c.avg_hr_bpm for c in checkins if c.avg_hr_bpm]
    return round(sum(hrs) / len(hrs), 1) if hrs else None


def compute_wow(all_checkins: list, week: int) -> dict:
    """Compare this week's metrics to the prior week."""
    curr_start, curr_end = week_date_range(week)
    curr = _checkins_in_week(all_checkins, curr_start, curr_end)

    if week <= 1:
        return {
            "prev_week": None,
            "volume_km": {"current": round(sum(c.total_distance_km or 0 for c in curr), 1), "prev": None, "delta": None},
            "avg_pace": {"current": seconds_to_pace(_avg_pace(curr)) if _avg_pace(curr) else None, "prev": None, "delta_sec": None},
            "avg_hr": {"current": _avg_hr(curr), "prev": None, "delta_bpm": None},
            "sessions": {"current": len(curr), "prev": None, "delta": None},
        }

    prev_start, prev_end = week_date_range(week - 1)
    prev = _checkins_in_week(all_checkins, prev_start, prev_end)

    curr_km = round(sum(c.total_distance_km or 0 for c in curr), 1)
    prev_km = round(sum(c.total_distance_km or 0 for c in prev), 1)
    curr_pace = _avg_pace(curr)
    prev_pace = _avg_pace(prev)
    curr_hr = _avg_hr(curr)
    prev_hr = _avg_hr(prev)

    return {
        "prev_week": week - 1,
        "volume_km": {
            "current": curr_km,
            "prev": prev_km,
            "delta": round(curr_km - prev_km, 1),
        },
        "avg_pace": {
            "current": seconds_to_pace(curr_pace) if curr_pace else None,
            "prev": seconds_to_pace(prev_pace) if prev_pace else None,
            "delta_sec": (curr_pace - prev_pace) if (curr_pace and prev_pace) else None,
        },
        "avg_hr": {
            "current": curr_hr,
            "prev": prev_hr,
            "delta_bpm": round(curr_hr - prev_hr, 1) if (curr_hr is not None and prev_hr is not None) else None,
        },
        "sessions": {
            "current": len(curr),
            "prev": len(prev),
            "delta": len(curr) - len(prev),
        },
    }


def compute_weekly_summary(all_checkins: list, week: int) -> dict:
    """Top-level function combining rings + WoW for the given week."""
    curr_start, curr_end = week_date_range(week)
    curr = _checkins_in_week(all_checkins, curr_start, curr_end)
    return {
        "week": week,
        "week_start": curr_start.isoformat(),
        "week_end": curr_end.isoformat(),
        "rings": compute_rings(curr, week),
        "week_over_week": compute_wow(all_checkins, week),
    }

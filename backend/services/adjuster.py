"""
Dynamic plan adjuster.

Trigger: after a user saves a weekly log, we re-evaluate their progress and
propose per-day adjustments to the next `HORIZON` weeks' run/long-run/tempo
targets. The race date (week 32) is immutable — we only scale intensity
within that fixed timeframe.

Guardrails (enforced post-LLM):
  - distance deltas clamped to ±20% of the original target
  - pace deltas clamped to ±10% of the original target upper bound
  - HR targets never loosened (we keep the original HR cap)
  - adjustments are *replacements* per user+week+day; stale rows are deleted
    before new ones are inserted.

Graceful degradation: if OPENAI_API_KEY is unset, this function is a no-op
(returns an empty adjustment list).
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..coach import pace_to_seconds, seconds_to_pace, target_pace_range_seconds
from ..models import DailyCheckin, PlanAdjustment, User, WeeklyLog
from ..plan_data import DELOAD_WEEKS, RACE_WEEK, get_days_for_week, get_phase

HORIZON_WEEKS = 4  # adjust next N weeks only

MAX_DISTANCE_DELTA = 0.20  # ±20%
MAX_PACE_DELTA = 0.10       # ±10% (of target upper bound in seconds)
RUN_TYPES = {"run", "long-run", "tempo", "intervals"}

_SYSTEM_PROMPT = (
    "You are a running coach adjusting a training plan mid-cycle. "
    "Given the runner's actual performance vs plan, propose small, evidence-based "
    "adjustments to pace and distance targets for the next few weeks of run days. "
    "Keep the race date fixed. If the runner is ahead of target, you may tighten "
    "paces slightly; if behind, you may reduce pace/distance to realistic numbers. "
    "Respect these hard limits: distance changes within ±20% of the original target, "
    "pace changes within ±10% of the original upper bound. Never loosen HR caps. "
    "For deload weeks, prefer keeping the original plan unchanged unless there is a "
    "strong reason to adjust. "
    "Return strict JSON only (no markdown): {\"adjustments\": [{\"week\": N, "
    "\"day_of_week\": 0-6, \"adjusted_distance_km\": float|null, "
    "\"adjusted_pace\": \"mm:ss\" or \"<mm:ss\" or \"~mm:ss\" or null, "
    "\"rationale\": \"short reason\"}]}. Only include days you want to change; "
    "omit days that should stay on the original plan."
)


# --------------------------------------------------------------------------
# Performance snapshot
# --------------------------------------------------------------------------
def _recent_performance(db: Session, user_id: int, today: date, lookback_weeks: int = 4) -> dict:
    cutoff = (today - timedelta(weeks=lookback_weeks)).isoformat()
    checkins = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == user_id)
        .filter(DailyCheckin.checkin_date >= cutoff)
        .order_by(DailyCheckin.checkin_date.asc())
        .all()
    )
    weekly = (
        db.query(WeeklyLog)
        .filter(WeeklyLog.user_id == user_id)
        .order_by(WeeklyLog.log_date.asc())
        .all()
    )
    paces = [pace_to_seconds(c.avg_pace_per_km) for c in checkins]
    paces = [p for p in paces if p]
    total_km = sum(c.total_distance_km or 0 for c in checkins)
    hrs = [c.avg_hr_bpm for c in checkins if c.avg_hr_bpm]
    return {
        "run_count": len(checkins),
        "total_km": round(total_km, 1),
        "avg_pace": seconds_to_pace(sum(paces) // len(paces)) if paces else None,
        "best_pace": seconds_to_pace(min(paces)) if paces else None,
        "avg_hr": round(sum(hrs) / len(hrs), 1) if hrs else None,
        "latest_weight": weekly[-1].weight_kg if weekly else None,
    }


def _target_weeks(current_week: int) -> list[int]:
    """Return weeks to consider adjusting. Skip race week (untouchable)."""
    end = min(RACE_WEEK - 1, current_week + HORIZON_WEEKS)
    return [w for w in range(current_week + 1, end + 1)]


# --------------------------------------------------------------------------
# Guardrails (clamp LLM output to safe bounds)
# --------------------------------------------------------------------------
def _clamp_distance(original_km: Optional[float], proposed_km: Optional[float]) -> Optional[float]:
    if proposed_km is None or original_km is None:
        return None
    lo = original_km * (1 - MAX_DISTANCE_DELTA)
    hi = original_km * (1 + MAX_DISTANCE_DELTA)
    return round(max(lo, min(hi, proposed_km)), 2)


def _clamp_pace(original_pace_str: Optional[str], proposed_pace_str: Optional[str]) -> Optional[str]:
    if not proposed_pace_str or not original_pace_str:
        return None
    orig_lo, orig_hi = target_pace_range_seconds(original_pace_str)
    baseline = orig_hi or orig_lo
    if not baseline:
        return None
    # Parse proposed — may have <, ~ prefix
    prefix = ""
    raw = proposed_pace_str.strip()
    if raw.startswith("<") or raw.startswith("~"):
        prefix = raw[0]
        raw = raw[1:].strip()
    prop_lo, prop_hi = target_pace_range_seconds(raw)
    prop = prop_hi or prop_lo
    if not prop:
        return None
    # Clamp to within MAX_PACE_DELTA of baseline
    lo_bound = int(baseline * (1 - MAX_PACE_DELTA))
    hi_bound = int(baseline * (1 + MAX_PACE_DELTA))
    clamped = max(lo_bound, min(hi_bound, prop))
    if "-" in raw:
        # Range input — preserve range width, shifted to clamped
        try:
            lo_raw, hi_raw = raw.split("-", 1)
            lo_sec = pace_to_seconds(lo_raw)
            hi_sec = pace_to_seconds(hi_raw)
            if lo_sec and hi_sec and hi_sec - lo_sec > 0:
                width = hi_sec - lo_sec
                new_hi = clamped
                new_lo = max(0, new_hi - width)
                return f"{seconds_to_pace(new_lo).rstrip('/km')}-{seconds_to_pace(new_hi).rstrip('/km')}"
        except (ValueError, IndexError):
            pass
    return f"{prefix}{seconds_to_pace(clamped).rstrip('/km')}" if prefix else seconds_to_pace(clamped).rstrip("/km")


# --------------------------------------------------------------------------
# LLM call
# --------------------------------------------------------------------------
def _llm_generate_adjustments(prompt: str) -> Optional[dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    model = os.getenv("OPENAI_TEXT_MODEL", "gpt-5-nano")
    try:
        import requests
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "max_completion_tokens": 800,
            },
            timeout=45,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        return json.loads(text)
    except Exception:
        return None


def _build_user_prompt(perf: dict, current_week: int, target_weeks: list[int]) -> str:
    lines = [
        f"Current week: {current_week}, Phase {get_phase(current_week)}. Race in week {RACE_WEEK}.",
        "Recent 4 weeks performance:",
        f"  runs: {perf['run_count']}, total {perf['total_km']} km, avg pace {perf['avg_pace']}, best {perf['best_pace']}, avg HR {perf['avg_hr']}",
        f"  latest weight: {perf['latest_weight']} kg",
        "",
        "Original plan for the next weeks (per day — only run/long-run/tempo/intervals shown):",
    ]
    for w in target_weeks:
        is_deload = w in DELOAD_WEEKS
        lines.append(f"  Week {w}{' [DELOAD]' if is_deload else ''}:")
        for dow, day in enumerate(get_days_for_week(w)):
            if day["type"] not in RUN_TYPES:
                continue
            t = day.get("targets", {})
            lines.append(
                f"    day_of_week={dow} ({day['name']}): type={day['type']} "
                f"dist={t.get('distance_km')} km pace={t.get('target_pace')} HR={t.get('target_hr')}"
            )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------
def _delete_stale_adjustments(db: Session, user_id: int, weeks: list[int]):
    if not weeks:
        return
    db.query(PlanAdjustment).filter(
        PlanAdjustment.user_id == user_id,
        PlanAdjustment.week_number.in_(weeks),
    ).delete(synchronize_session=False)


def _apply_and_store(
    db: Session,
    user_id: int,
    adjustments: list[dict],
    target_weeks: list[int],
) -> list[PlanAdjustment]:
    """
    Filter LLM output through guardrails, build PlanAdjustment rows, and
    replace any existing rows for the target weeks.
    """
    batch_id = str(uuid.uuid4())
    rows = []
    for a in adjustments:
        try:
            week = int(a["week"])
            dow = int(a["day_of_week"])
        except (KeyError, TypeError, ValueError):
            continue
        if week not in target_weeks:
            continue
        if not (0 <= dow <= 6):
            continue

        days = get_days_for_week(week)
        if dow >= len(days):
            continue
        original = days[dow]
        if original["type"] not in RUN_TYPES:
            continue  # never touch rest/strength days

        orig_targets = original.get("targets", {})
        clamped_distance = _clamp_distance(
            orig_targets.get("distance_km"), a.get("adjusted_distance_km")
        )
        clamped_pace = _clamp_pace(
            orig_targets.get("target_pace"), a.get("adjusted_pace")
        )

        # Skip if nothing actually changed after clamping
        if clamped_distance is None and clamped_pace is None:
            continue
        if (clamped_distance == orig_targets.get("distance_km") and
                clamped_pace == orig_targets.get("target_pace")):
            continue

        adjusted_day = json.loads(json.dumps(original))  # deep copy
        if clamped_distance is not None:
            adjusted_day["targets"]["distance_km"] = clamped_distance
            # Also update the visible "Distance" row in details, if present
            for item in adjusted_day.get("details", []):
                if isinstance(item, list) and len(item) == 2 and item[0].lower().startswith("distance"):
                    item[1] = f"{clamped_distance:g} km"
        if clamped_pace is not None:
            adjusted_day["targets"]["target_pace"] = clamped_pace
            for item in adjusted_day.get("details", []):
                if isinstance(item, list) and len(item) == 2 and "pace" in item[0].lower():
                    item[1] = clamped_pace

        rows.append(PlanAdjustment(
            user_id=user_id,
            week_number=week,
            day_of_week=dow,
            original_json=json.dumps(original),
            adjusted_json=json.dumps(adjusted_day),
            rationale=str(a.get("rationale", "")).strip() or "Adjusted based on recent progress.",
            batch_id=batch_id,
        ))

    if rows:
        _delete_stale_adjustments(db, user_id, target_weeks)
        for r in rows:
            db.add(r)
        db.commit()
    return rows


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------
def run_adjuster(db: Session, user: User) -> list[PlanAdjustment]:
    """
    Main entry: compute a new batch of adjustments for `user`. Called after
    each weekly log save. Returns the list of saved PlanAdjustment rows
    (empty list if no API key or LLM declined to adjust).
    """
    today = date.today()
    # Use the current week via progress module
    from ..routes.progress import get_current_week
    current_week = get_current_week()
    target_weeks = _target_weeks(current_week)
    if not target_weeks:
        return []

    perf = _recent_performance(db, user.id, today)
    prompt = _build_user_prompt(perf, current_week, target_weeks)
    llm_out = _llm_generate_adjustments(prompt)
    if not llm_out:
        return []

    adjustments = llm_out.get("adjustments") or []
    if not isinstance(adjustments, list):
        return []

    return _apply_and_store(db, user.id, adjustments, target_weeks)


def get_adjusted_day(db: Session, user_id: int, week: int, day_of_week: int) -> Optional[dict]:
    """
    Look up a per-day adjustment. Returns {day: ..., rationale: ...} when an
    adjustment exists for this user/week/day, else None.
    """
    row = (
        db.query(PlanAdjustment)
        .filter(
            PlanAdjustment.user_id == user_id,
            PlanAdjustment.week_number == week,
            PlanAdjustment.day_of_week == day_of_week,
        )
        .order_by(PlanAdjustment.created_at.desc())
        .first()
    )
    if not row:
        return None
    try:
        adjusted = json.loads(row.adjusted_json)
    except (ValueError, TypeError):
        return None
    return {
        "day": adjusted,
        "rationale": row.rationale,
        "adjusted_at": row.created_at.isoformat() if row.created_at else None,
    }

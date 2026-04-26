"""
Coach service — generates pre-run target notes and post-run workout summaries.

Hybrid design: rules compute the numeric metrics (pace deltas, drift, HR
response, offset vs target). Then an LLM turns those numbers into a short,
human-readable coaching note. If no OPENAI_API_KEY is set, we fall back to
a rules-only note so the feature degrades gracefully.

Notes are cached in the `coach_notes` table so repeated page views don't
re-invoke the model.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from .models import CoachNote, DailyCheckin, User
from .plan_data import get_day as plan_get_day, get_week_focus, get_phase
from .services.weather import weather_label, fetch_forecast_weather


# Heat-adjusted target pace constants. Above the neutral threshold, every
# additional °C of "feels like" temperature slows the sustainable pace by
# roughly this many seconds per km. Conservative linear rule of thumb —
# real heat penalty is non-linear (worse above ~25°C) but linear is good
# enough for coach guidance and easy to override later.
HEAT_NEUTRAL_TEMP_C = 15.0
HEAT_PENALTY_SEC_PER_C = 2.0


def heat_adjusted_target_pace_sec(target_sec: Optional[int], apparent_temp_c: Optional[float]) -> Optional[int]:
    """Return the target pace in seconds, slowed for heat. Returns the input
    unchanged if either argument is missing or the temperature is below the
    neutral threshold."""
    if target_sec is None or apparent_temp_c is None:
        return target_sec
    if apparent_temp_c <= HEAT_NEUTRAL_TEMP_C:
        return target_sec
    penalty = round((apparent_temp_c - HEAT_NEUTRAL_TEMP_C) * HEAT_PENALTY_SEC_PER_C)
    return target_sec + penalty


# --------------------------------------------------------------------------
# Pace utilities
# --------------------------------------------------------------------------
def pace_to_seconds(pace: Optional[str]) -> Optional[int]:
    """Convert 'mm:ss' to total seconds. Returns None on failure."""
    if not pace:
        return None
    # Strip prefixes like '<', '~', and trailing '/km'
    s = pace.strip().lstrip("<~").split("/")[0].strip()
    # Handle ranges like '10:30-11:00' by taking the first value
    s = s.split("-")[0].strip()
    try:
        parts = s.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        pass
    return None


def seconds_to_pace(sec: int) -> str:
    return f"{sec // 60}:{sec % 60:02d}/km"


def target_pace_range_seconds(target_str: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """
    Parse a target pace descriptor into a (lower_sec, upper_sec) bound.
    Examples:
        '10:30-11:00' -> (630, 660)
        '<7:30'       -> (None, 450)
        '~7:06'       -> (426, 426)
        'tempo ~6:30' -> (390, 390)
    """
    if not target_str:
        return (None, None)
    s = target_str.strip().lower().replace("tempo", "").replace("race", "").replace("intervals", "").strip()
    if s.startswith("<"):
        upper = pace_to_seconds(s[1:])
        return (None, upper)
    if s.startswith("~"):
        v = pace_to_seconds(s[1:])
        return (v, v)
    if "-" in s:
        lo, hi = s.split("-", 1)
        return (pace_to_seconds(lo), pace_to_seconds(hi))
    v = pace_to_seconds(s)
    return (v, v)


# --------------------------------------------------------------------------
# Metrics computation (pure functions, no I/O besides DB read)
# --------------------------------------------------------------------------
def _recent_run_checkins(db: Session, user_id: int, today: date, lookback_days: int = 28) -> list[DailyCheckin]:
    cutoff = (today - timedelta(days=lookback_days)).isoformat()
    return (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == user_id)
        .filter(DailyCheckin.checkin_date >= cutoff)
        .filter(DailyCheckin.avg_pace_per_km.isnot(None))
        .order_by(DailyCheckin.checkin_date.asc())
        .all()
    )


def _latest_known_location(db: Session, user_id: int) -> Optional[tuple[float, float, str]]:
    """Most recent check-in with a resolved lat/lon. Used as the user's
    'home' location for pre-run forecast lookups."""
    row = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == user_id)
        .filter(DailyCheckin.location_lat.isnot(None))
        .filter(DailyCheckin.location_lon.isnot(None))
        .order_by(DailyCheckin.checkin_date.desc())
        .first()
    )
    if not row:
        return None
    return (row.location_lat, row.location_lon, row.location_name or "")


def _typical_run_hour(db: Session, user_id: int, default: int = 7) -> int:
    """Most common start hour from recent runs, or `default` if unknown.
    Used to pick the right hour from today's forecast."""
    rows = (
        db.query(DailyCheckin.workout_started_at)
        .filter(DailyCheckin.user_id == user_id)
        .filter(DailyCheckin.workout_started_at.isnot(None))
        .order_by(DailyCheckin.checkin_date.desc())
        .limit(10)
        .all()
    )
    hours = []
    for (ts,) in rows:
        try:
            hours.append(datetime.fromisoformat(ts).hour)
        except (ValueError, TypeError):
            continue
    if not hours:
        return default
    # Mode of recent hours
    return max(set(hours), key=hours.count)


def compute_pre_run_metrics(db: Session, user: User, today: date, week: int, day_of_week: int) -> dict:
    """
    Build the structured metrics dict for a pre-run coach note.
    Describes: today's plan, recent pace trend, gap to target.
    """
    plan_day = plan_get_day(week, day_of_week) or {}
    recent = _recent_run_checkins(db, user.id, today)
    # Personal baseline (seconds/km) if calibrated, else None
    baseline_sec = getattr(user, "baseline_pace_seconds", None)

    # Compute recent pace stats
    paces = [pace_to_seconds(c.avg_pace_per_km) for c in recent]
    paces = [p for p in paces if p]
    recent_avg = sum(paces) // len(paces) if paces else None
    recent_best = min(paces) if paces else None

    # Trend: compare first half vs second half of the window
    trend = "insufficient_data"
    if len(paces) >= 4:
        mid = len(paces) // 2
        first_half = sum(paces[:mid]) // mid
        second_half = sum(paces[mid:]) // (len(paces) - mid)
        if second_half < first_half - 15:
            trend = "improving"
        elif second_half > first_half + 15:
            trend = "regressing"
        else:
            trend = "stable"

    # HR stats
    hrs = [c.avg_hr_bpm for c in recent if c.avg_hr_bpm]
    recent_avg_hr = sum(hrs) / len(hrs) if hrs else None

    # Parse today's target pace
    target_lo, target_hi = target_pace_range_seconds(plan_day.get("targets", {}).get("target_pace"))

    # Gap: how far is recent avg from target?
    gap_sec = None
    if recent_avg and target_hi:
        gap_sec = recent_avg - target_hi  # positive means slower than target

    # ── Forecast lookup for heat-adjusted target pace ────────────────────
    # If we know the runner's recent location, fetch today's forecast for
    # their typical run hour and compute a heat-adjusted target. All best
    # effort — the coach degrades gracefully when any piece is missing.
    forecast_temp = None
    forecast_apparent = None
    forecast_humidity = None
    forecast_label = None
    heat_adj_upper_sec = None
    heat_penalty_sec = None
    loc = _latest_known_location(db, user.id)
    if loc:
        lat, lon, loc_name = loc
        run_hour = _typical_run_hour(db, user.id)
        target_dt = datetime.combine(today, datetime.min.time()).replace(hour=run_hour)
        forecast = fetch_forecast_weather(lat, lon, target_dt)
        if forecast:
            forecast_temp = forecast.get("temperature_c")
            forecast_apparent = forecast.get("apparent_temperature_c")
            forecast_humidity = forecast.get("humidity_pct")
            forecast_label = weather_label(forecast.get("weather_code"))
            adj = heat_adjusted_target_pace_sec(target_hi, forecast_apparent)
            if adj is not None and target_hi is not None:
                heat_adj_upper_sec = adj
                heat_penalty_sec = adj - target_hi if adj > target_hi else 0

    return {
        "week": week,
        "phase": get_phase(week),
        "day_name": plan_day.get("name"),
        "day_type": plan_day.get("type"),
        "type_label": plan_day.get("type_label"),
        "target_distance_km": plan_day.get("targets", {}).get("distance_km"),
        "target_pace": plan_day.get("targets", {}).get("target_pace"),
        "target_hr": plan_day.get("targets", {}).get("target_hr"),
        "target_pace_upper_sec": target_hi,
        "recent_avg_pace_sec": recent_avg,
        "recent_avg_pace_str": seconds_to_pace(recent_avg) if recent_avg else None,
        "recent_best_pace_sec": recent_best,
        "recent_best_pace_str": seconds_to_pace(recent_best) if recent_best else None,
        "recent_avg_hr": round(recent_avg_hr, 1) if recent_avg_hr else None,
        "recent_run_count": len(recent),
        "trend": trend,
        "gap_sec": gap_sec,
        "plan_note": plan_day.get("note"),
        "week_focus": get_week_focus(week),
        "user_baseline_sec": baseline_sec,
        "user_baseline_str": seconds_to_pace(baseline_sec) if baseline_sec else None,
        # Forecast + heat-adjusted target
        "forecast_temperature_c": forecast_temp,
        "forecast_apparent_temperature_c": forecast_apparent,
        "forecast_humidity_pct": forecast_humidity,
        "forecast_weather_label": forecast_label,
        "heat_adjusted_target_upper_sec": heat_adj_upper_sec,
        "heat_adjusted_target_upper_str": seconds_to_pace(heat_adj_upper_sec) if heat_adj_upper_sec else None,
        "heat_penalty_sec": heat_penalty_sec,
        "location_name": loc[2] if loc else None,
    }


def compute_post_run_metrics(db: Session, user: User, checkin: DailyCheckin) -> dict:
    """
    Compare an actual check-in to its planned target and recent history.
    """
    checkin_date = date.fromisoformat(checkin.checkin_date) if checkin.checkin_date else date.today()
    week = checkin.week_number or 1
    day_of_week = checkin_date.weekday()
    plan_day = plan_get_day(week, day_of_week) or {}
    targets = plan_day.get("targets", {})

    actual_pace_sec = pace_to_seconds(checkin.avg_pace_per_km)
    target_lo, target_hi = target_pace_range_seconds(targets.get("target_pace"))

    # Pace offset vs target upper bound
    pace_offset_sec = None
    pace_verdict = "unknown"
    if actual_pace_sec and target_hi:
        pace_offset_sec = actual_pace_sec - target_hi
        if pace_offset_sec <= -10:
            pace_verdict = "ahead_of_target"
        elif pace_offset_sec <= 10:
            pace_verdict = "on_target"
        elif pace_offset_sec <= 30:
            pace_verdict = "slightly_behind"
        else:
            pace_verdict = "behind"

    # Distance offset
    distance_offset = None
    if checkin.total_distance_km and targets.get("distance_km"):
        distance_offset = round(checkin.total_distance_km - targets["distance_km"], 2)

    # Split analysis — positive vs negative splits, drift
    splits = []
    if checkin.splits_json:
        try:
            splits = json.loads(checkin.splits_json)
        except (ValueError, TypeError):
            splits = []

    split_summary = None
    if len(splits) >= 3:
        paces = [pace_to_seconds(s.get("pace_per_km")) for s in splits]
        paces = [p for p in paces if p]
        hrs = [s.get("hr_bpm") for s in splits if s.get("hr_bpm")]
        if paces:
            first_half_avg = sum(paces[:len(paces)//2]) // (len(paces) // 2) if len(paces) >= 2 else paces[0]
            second_half_avg = sum(paces[len(paces)//2:]) // (len(paces) - len(paces)//2) if len(paces) >= 2 else paces[0]
            # Negative split = faster in second half (lower seconds)
            split_type = "negative" if second_half_avg < first_half_avg - 10 else "positive" if second_half_avg > first_half_avg + 10 else "even"
            hr_drift = (hrs[-1] - hrs[0]) if len(hrs) >= 2 else None
            split_summary = {
                "type": split_type,
                "first_half_pace_sec": first_half_avg,
                "second_half_pace_sec": second_half_avg,
                "hr_drift_bpm": hr_drift,
                "split_count": len(splits),
            }

    # Target HR parsing — crude, just capture if actual was above the ceiling
    hr_verdict = None
    target_hr_str = targets.get("target_hr") or ""
    if checkin.avg_hr_bpm and target_hr_str:
        m = target_hr_str.strip().lstrip("<")
        try:
            # Handle "130-145" / "<145" / "140-145"
            cap = int(m.split("-")[-1])
            hr_verdict = "over_cap" if checkin.avg_hr_bpm > cap + 2 else "within_cap"
        except (ValueError, IndexError):
            hr_verdict = None

    # ── Heat-adjusted target + offset, using actual run conditions ──────
    apparent = checkin.apparent_temperature_c
    heat_adj_upper = heat_adjusted_target_pace_sec(target_hi, apparent)
    heat_penalty = (heat_adj_upper - target_hi) if (heat_adj_upper and target_hi and heat_adj_upper > target_hi) else 0
    pace_offset_vs_heat_adj = None
    pace_verdict_vs_heat_adj = None
    if actual_pace_sec is not None and heat_adj_upper is not None:
        pace_offset_vs_heat_adj = actual_pace_sec - heat_adj_upper
        if pace_offset_vs_heat_adj <= -10:
            pace_verdict_vs_heat_adj = "ahead_of_target"
        elif pace_offset_vs_heat_adj <= 10:
            pace_verdict_vs_heat_adj = "on_target"
        elif pace_offset_vs_heat_adj <= 30:
            pace_verdict_vs_heat_adj = "slightly_behind"
        else:
            pace_verdict_vs_heat_adj = "behind"

    return {
        "week": week,
        "day_name": plan_day.get("name"),
        "type_label": plan_day.get("type_label"),
        "target_distance_km": targets.get("distance_km"),
        "target_pace": targets.get("target_pace"),
        "target_hr": targets.get("target_hr"),
        "actual_distance_km": checkin.total_distance_km,
        "actual_pace": checkin.avg_pace_per_km,
        "actual_pace_sec": actual_pace_sec,
        "actual_avg_hr": checkin.avg_hr_bpm,
        "actual_max_hr": checkin.max_hr_bpm,
        "pace_offset_sec": pace_offset_sec,
        "pace_verdict": pace_verdict,
        "distance_offset": distance_offset,
        "hr_verdict": hr_verdict,
        "split_summary": split_summary,
        # ── Conditions context from Workout Summary screenshot ──────────
        "location_name": checkin.location_name,
        "elevation_gain_m": checkin.elevation_gain_m,
        "avg_cadence_spm": checkin.avg_cadence_spm,
        "active_calories": checkin.active_calories,
        "perceived_effort": checkin.perceived_effort,
        "workout_started_at": checkin.workout_started_at,
        "workout_time_seconds": checkin.workout_time_seconds,
        "total_elapsed_seconds": checkin.total_elapsed_seconds,
        "pause_seconds": (
            (checkin.total_elapsed_seconds - checkin.workout_time_seconds)
            if checkin.total_elapsed_seconds and checkin.workout_time_seconds
            else None
        ),
        # ── Weather (auto-fetched from Open-Meteo at check-in) ──────────
        "temperature_c": checkin.temperature_c,
        "apparent_temperature_c": apparent,
        "humidity_pct": checkin.humidity_pct,
        "wind_speed_kmh": checkin.wind_speed_kmh,
        "precipitation_mm": checkin.precipitation_mm,
        "weather_label": weather_label(checkin.weather_code),
        # ── Heat-adjusted target + verdict ──────────────────────────────
        "heat_adjusted_target_upper_sec": heat_adj_upper,
        "heat_adjusted_target_upper_str": seconds_to_pace(heat_adj_upper) if heat_adj_upper else None,
        "heat_penalty_sec": heat_penalty,
        "pace_offset_vs_heat_adj_sec": pace_offset_vs_heat_adj,
        "pace_verdict_vs_heat_adj": pace_verdict_vs_heat_adj,
    }


# --------------------------------------------------------------------------
# Rules-based fallback text (used when no API key available)
# --------------------------------------------------------------------------
def _rules_pre_run_text(m: dict) -> str:
    day_type = m.get("day_type")
    if day_type == "rest":
        return f"Rest day. {m.get('plan_note') or 'Recovery is where adaptation happens.'}"

    parts = []
    label = m.get("type_label", "today's run")
    dist = m.get("target_distance_km")
    pace = m.get("target_pace") or "conversational"
    hr = m.get("target_hr") or ""
    parts.append(f"{label}: {dist:g} km" if dist else label)
    parts.append(f"target pace {pace}" + (f" at HR {hr}" if hr else ""))

    # Heat-adjusted target (if forecast available) takes precedence over original target.
    if m.get("heat_adjusted_target_upper_str") and m.get("heat_penalty_sec"):
        apparent = m.get("forecast_apparent_temperature_c")
        parts.append(
            f"feels like {apparent:.0f}°C — aim for {m['heat_adjusted_target_upper_str']}/km instead "
            f"(+{m['heat_penalty_sec']}s/km heat penalty)"
        )

    if m.get("recent_avg_pace_str"):
        parts.append(f"recent avg: {m['recent_avg_pace_str']}")
        gap = m.get("gap_sec")
        if gap is not None:
            if gap > 60:
                parts.append("goal gap is wide — today's priority is HR control, not pace")
            elif gap > 20:
                parts.append("you're within ~30s/km of target — focus on steady HR, pace will come")
            else:
                parts.append("you're at or near target — lock it in")

    trend = m.get("trend")
    if trend == "improving":
        parts.append("trend: improving")
    elif trend == "regressing":
        parts.append("trend: slight regression — ease off, recover")

    return ". ".join(parts) + "."


def _rules_post_run_text(m: dict) -> str:
    label = m.get("type_label") or "run"
    # When heat-adjusted target is available, the verdict against it is the
    # honest one (raw target wasn't achievable in those conditions).
    use_heat_verdict = m.get("heat_adjusted_target_upper_sec") is not None and m.get("heat_penalty_sec", 0) > 0
    verdict = m.get("pace_verdict_vs_heat_adj") if use_heat_verdict else m.get("pace_verdict")
    offset = m.get("pace_offset_vs_heat_adj_sec") if use_heat_verdict else m.get("pace_offset_sec")

    parts = [f"{label}: {m.get('actual_distance_km', '?')} km at {m.get('actual_pace') or '?'}"]

    if use_heat_verdict and m.get("apparent_temperature_c"):
        parts.append(
            f"felt like {m['apparent_temperature_c']:.0f}°C — heat-adjusted target was "
            f"{m.get('heat_adjusted_target_upper_str')}/km"
        )

    if verdict == "ahead_of_target":
        parts.append("paced ahead of target — strong session")
    elif verdict == "on_target":
        parts.append("on target pace")
    elif verdict == "slightly_behind" and offset is not None:
        parts.append(f"ran {offset:+d}s/km vs target — close")
    elif verdict == "behind" and offset is not None:
        parts.append(f"ran {offset:+d}s/km vs target — adjust next session")

    if m.get("hr_verdict") == "over_cap":
        parts.append(f"HR {m.get('actual_avg_hr'):.0f} was above the cap — ease off next run")

    if m.get("elevation_gain_m") and m["elevation_gain_m"] > 50:
        parts.append(f"climbed {m['elevation_gain_m']:.0f}m — pace would've been ~{int(m['elevation_gain_m'] // 10)}s/km faster on flat")

    if m.get("split_summary"):
        ss = m["split_summary"]
        if ss["type"] == "negative":
            parts.append("negative splits — well-paced")
        elif ss["type"] == "positive":
            parts.append("positive splits — started too hot")
        if ss.get("hr_drift_bpm") and ss["hr_drift_bpm"] > 15:
            parts.append(f"HR drifted +{ss['hr_drift_bpm']} bpm — aerobic efficiency still building")

    return ". ".join(parts) + "."


# --------------------------------------------------------------------------
# LLM integration
# --------------------------------------------------------------------------
def _openai_client_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _llm_generate(system_prompt: str, user_prompt: str, max_tokens: int = 180) -> Optional[tuple[str, str]]:
    """
    Call OpenAI and return (text, model_name). Returns None on any failure so
    caller can fall back to rules.
    """
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
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_completion_tokens": max_tokens,
            },
            timeout=20,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        return (text, model)
    except Exception:
        return None


_PRE_RUN_SYSTEM = (
    "You are a concise running coach. Given structured metrics for today's planned "
    "workout and conditions, write 2-3 short sentences of specific guidance. No "
    "markdown, no lists, no preamble. Reference concrete numbers. Tone: direct, "
    "encouraging, not generic. If a heat-adjusted target is provided, state it "
    "explicitly so the runner aims for the adjusted pace, not the original — call "
    "out the temperature briefly ('22°C feels like 25°C' style)."
)

_POST_RUN_SYSTEM = (
    "You are a concise running coach. Given the actual vs target metrics for a workout "
    "just completed, write 2-3 short sentences summarizing performance and giving one "
    "actionable takeaway. No markdown, no lists, no preamble. Reference concrete numbers.\n"
    "Important context rules:\n"
    "- If a heat-adjusted target is present, judge performance against the heat-adjusted "
    "target, not the original. A run that looks 'behind' on raw target may be 'on target' "
    "after heat adjustment.\n"
    "- Mention temperature/humidity briefly only if it materially affected the run "
    "(>20°C apparent or >70% humidity).\n"
    "- Mention elevation gain only if >50m.\n"
    "- If perceived_effort and HR/pace disagree (e.g. felt easy but HR was high), call it out."
)


def _format_pre_prompt(m: dict) -> str:
    lines = [
        f"Week {m['week']} (Phase {m['phase']}). Week focus: {m.get('week_focus')}.",
        f"Today: {m.get('day_name')} — {m.get('type_label')}.",
        f"Target: {m.get('target_distance_km')} km at pace {m.get('target_pace')}, HR {m.get('target_hr')}.",
        f"Plan note: {m.get('plan_note') or '(none)'}",
        f"Recent {m.get('recent_run_count', 0)} runs (last 4 wks): avg pace {m.get('recent_avg_pace_str')}, "
        f"best {m.get('recent_best_pace_str')}, avg HR {m.get('recent_avg_hr')}.",
        f"Trend: {m.get('trend')}. Gap to target upper bound: "
        f"{m.get('gap_sec')}s/km (positive = slower than target).",
    ]
    if m.get("forecast_apparent_temperature_c") is not None:
        lines.append(
            f"Today's forecast at typical run hour ({m.get('location_name') or 'recent location'}): "
            f"{m.get('forecast_temperature_c')}°C, feels like {m.get('forecast_apparent_temperature_c')}°C, "
            f"{m.get('forecast_humidity_pct')}% humidity, {m.get('forecast_weather_label') or 'unknown'}."
        )
    if m.get("heat_adjusted_target_upper_str") and m.get("heat_penalty_sec"):
        lines.append(
            f"Heat-adjusted target upper bound: {m['heat_adjusted_target_upper_str']}/km "
            f"(+{m['heat_penalty_sec']}s/km vs original)."
        )
    return "\n".join(lines)


def _format_post_prompt(m: dict) -> str:
    ss = m.get("split_summary") or {}
    lines = [
        f"Week {m['week']} — {m.get('type_label')} ({m.get('day_name')}).",
        f"Target: {m.get('target_distance_km')} km, pace {m.get('target_pace')}, HR {m.get('target_hr')}.",
        f"Actual: {m.get('actual_distance_km')} km, pace {m.get('actual_pace')}, "
        f"HR avg {m.get('actual_avg_hr')}, max {m.get('actual_max_hr')}.",
        f"Pace offset: {m.get('pace_offset_sec')}s/km ({m.get('pace_verdict')}). "
        f"Distance offset: {m.get('distance_offset')} km. HR verdict: {m.get('hr_verdict')}.",
        f"Splits: {ss.get('type', 'n/a')} splits, "
        f"HR drift {ss.get('hr_drift_bpm')} bpm across {ss.get('split_count', 0)} km.",
    ]
    if m.get("apparent_temperature_c") is not None:
        weather_bits = (
            f"{m.get('temperature_c')}°C, feels like {m.get('apparent_temperature_c')}°C, "
            f"{m.get('humidity_pct')}% humidity"
        )
        if m.get("weather_label"):
            weather_bits += f", {m['weather_label']}"
        if m.get("precipitation_mm"):
            weather_bits += f", {m['precipitation_mm']}mm precipitation"
        lines.append(f"Conditions: {weather_bits}.")
    if m.get("heat_adjusted_target_upper_str") and m.get("heat_penalty_sec"):
        lines.append(
            f"Heat-adjusted target upper bound: {m['heat_adjusted_target_upper_str']}/km "
            f"(+{m['heat_penalty_sec']}s/km). Offset vs heat-adjusted: "
            f"{m.get('pace_offset_vs_heat_adj_sec')}s/km ({m.get('pace_verdict_vs_heat_adj')})."
        )
    if m.get("elevation_gain_m"):
        lines.append(f"Elevation gain: {m['elevation_gain_m']}m.")
    if m.get("avg_cadence_spm"):
        lines.append(f"Avg cadence: {m['avg_cadence_spm']} spm.")
    if m.get("perceived_effort"):
        lines.append(f"Self-reported effort: {m['perceived_effort']}/10.")
    if m.get("pause_seconds") and m["pause_seconds"] > 60:
        lines.append(f"Paused for {m['pause_seconds']}s during the run.")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Public orchestrators (with caching)
# --------------------------------------------------------------------------
def get_or_create_pre_run_note(db: Session, user: User, today: date, week: int, day_of_week: int) -> CoachNote:
    """Return cached pre-run note for today, or generate+save a new one."""
    existing = (
        db.query(CoachNote)
        .filter(CoachNote.user_id == user.id, CoachNote.note_type == "pre", CoachNote.note_date == today.isoformat())
        .first()
    )
    if existing:
        return existing

    metrics = compute_pre_run_metrics(db, user, today, week, day_of_week)
    llm_result = _llm_generate(_PRE_RUN_SYSTEM, _format_pre_prompt(metrics))
    # Fall back to rules when LLM is unavailable OR returned empty text
    if llm_result and llm_result[0].strip():
        text, model_used = llm_result
    else:
        text, model_used = _rules_pre_run_text(metrics), "rules"

    note = CoachNote(
        user_id=user.id,
        note_type="pre",
        note_date=today.isoformat(),
        week_number=week,
        text=text,
        metrics_json=json.dumps(metrics),
        model_used=model_used,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_or_create_post_run_note(db: Session, user: User, checkin: DailyCheckin) -> CoachNote:
    existing = (
        db.query(CoachNote)
        .filter(CoachNote.user_id == user.id, CoachNote.note_type == "post", CoachNote.checkin_id == checkin.id)
        .first()
    )
    if existing:
        return existing

    metrics = compute_post_run_metrics(db, user, checkin)
    llm_result = _llm_generate(_POST_RUN_SYSTEM, _format_post_prompt(metrics))
    if llm_result and llm_result[0].strip():
        text, model_used = llm_result
    else:
        text, model_used = _rules_post_run_text(metrics), "rules"

    note = CoachNote(
        user_id=user.id,
        note_type="post",
        note_date=checkin.checkin_date,
        week_number=checkin.week_number or 1,
        checkin_id=checkin.id,
        text=text,
        metrics_json=json.dumps(metrics),
        model_used=model_used,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

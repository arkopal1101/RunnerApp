import json
import os
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import DailyCheckin, User
from ..parser import parse_workout_screenshot, parse_workout_summary_screenshot
from ..services.weather import geocode, fetch_historical_weather, weather_label
from .auth import get_current_user
from .day_log import upsert_day_log

router = APIRouter()

DATA_DIR = os.getenv("DATA_DIR", "./data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")


def get_week_number(checkin_date: date) -> int:
    start = date(2026, 4, 13)
    delta = (checkin_date - start).days
    if delta < 0:
        return 0
    return (delta // 7) + 1


# Fields the summary parser may return that map directly onto DailyCheckin
# columns. Listed here so we have one source of truth for both the merge and
# the response payload.
_SUMMARY_FIELDS = (
    "workout_started_at",
    "workout_ended_at",
    "workout_time_seconds",
    "total_elapsed_seconds",
    "location_name",
    "elevation_gain_m",
    "avg_cadence_spm",
    "active_calories",
    "total_calories",
    "perceived_effort",
)

_WEATHER_FIELDS = (
    "temperature_c",
    "apparent_temperature_c",
    "humidity_pct",
    "wind_speed_kmh",
    "precipitation_mm",
    "weather_code",
)


def _enrich_with_weather(summary: dict) -> dict:
    """
    Given a parsed summary dict, attempt to add lat/lon + weather fields.
    Mutates and returns the dict. Silent on failure — the coach degrades
    gracefully when weather is missing.
    """
    loc = summary.get("location_name")
    started = summary.get("workout_started_at")
    if not loc or not started:
        return summary
    geo = geocode(loc)
    if not geo:
        return summary
    lat, lon, resolved = geo
    summary["location_lat"] = lat
    summary["location_lon"] = lon
    # Overwrite raw screenshot text with the resolved Open-Meteo label so
    # the user can see which match was picked (e.g. "Gurugram, Haryana, India").
    summary["location_name"] = resolved
    weather = fetch_historical_weather(lat, lon, started)
    if weather:
        summary.update(weather)
    return summary


def checkin_to_dict(checkin: DailyCheckin, include_splits: bool = True) -> dict:
    out = {
        "id": checkin.id,
        "checkin_date": checkin.checkin_date,
        "week_number": checkin.week_number,
        "total_distance_km": checkin.total_distance_km,
        "avg_pace_per_km": checkin.avg_pace_per_km,
        "avg_hr_bpm": checkin.avg_hr_bpm,
        "max_hr_bpm": checkin.max_hr_bpm,
        "avg_power_watts": checkin.avg_power_watts,
        "splits": json.loads(checkin.splits_json) if include_splits and checkin.splits_json else [],
        "notes": checkin.notes,
        # Summary + weather fields (any may be None for legacy rows)
        "workout_started_at": checkin.workout_started_at,
        "workout_ended_at": checkin.workout_ended_at,
        "workout_time_seconds": checkin.workout_time_seconds,
        "total_elapsed_seconds": checkin.total_elapsed_seconds,
        "location_name": checkin.location_name,
        "elevation_gain_m": checkin.elevation_gain_m,
        "avg_cadence_spm": checkin.avg_cadence_spm,
        "active_calories": checkin.active_calories,
        "total_calories": checkin.total_calories,
        "perceived_effort": checkin.perceived_effort,
        "temperature_c": checkin.temperature_c,
        "apparent_temperature_c": checkin.apparent_temperature_c,
        "humidity_pct": checkin.humidity_pct,
        "wind_speed_kmh": checkin.wind_speed_kmh,
        "precipitation_mm": checkin.precipitation_mm,
        "weather_code": checkin.weather_code,
        "weather_label": weather_label(checkin.weather_code),
    }
    return out


# ── Parse-only (no DB write) ──────────────────────────────────────────────────

@router.post("/parse")
async def parse_checkin(
    image: UploadFile = File(...),                             # Splits screenshot, required
    summary_image: Optional[UploadFile] = File(None),          # Workout Summary, optional
    current_user: User = Depends(get_current_user),
):
    """
    Upload screenshot(s) and return parsed data WITHOUT saving to DB.

    `image`         — Splits view (required, source of per-km splits)
    `summary_image` — Workout Summary view (optional, fills in totals/weather)
    """
    os.makedirs(UPLOADS_DIR, exist_ok=True)

    # Save splits image
    ext = os.path.splitext(image.filename or "")[1] or ".png"
    splits_filename = f"tmp_{uuid.uuid4()}{ext}"
    splits_path = os.path.join(UPLOADS_DIR, splits_filename)
    with open(splits_path, "wb") as f:
        f.write(await image.read())

    openai_key = os.getenv("OPENAI_API_KEY")
    parsed = parse_workout_screenshot(splits_path, openai_api_key=openai_key or None)

    # Optionally parse summary image
    summary: dict = {}
    summary_filename: Optional[str] = None
    if summary_image is not None:
        sext = os.path.splitext(summary_image.filename or "")[1] or ".png"
        summary_filename = f"tmp_{uuid.uuid4()}{sext}"
        summary_path = os.path.join(UPLOADS_DIR, summary_filename)
        with open(summary_path, "wb") as f:
            f.write(await summary_image.read())
        summary = parse_workout_summary_screenshot(summary_path, openai_api_key=openai_key or None)
        summary = _enrich_with_weather(summary)

    response = {
        "tmp_image_path": splits_filename,
        "tmp_summary_image_path": summary_filename,
        "total_distance_km": parsed.get("total_distance_km"),
        "avg_pace_per_km": parsed.get("avg_pace"),
        "avg_hr_bpm": parsed.get("avg_hr"),
        "max_hr_bpm": parsed.get("max_hr"),
        "avg_power_watts": parsed.get("avg_power"),
        "splits": parsed.get("splits", []),
        "confidence": parsed.get("confidence", "failed"),
        "raw_text": parsed.get("raw_text", ""),
    }
    # Pull all summary + weather fields onto the response so the UI can preview.
    for field in _SUMMARY_FIELDS + ("location_lat", "location_lon") + _WEATHER_FIELDS:
        if field in summary:
            response[field] = summary[field]
    if summary.get("weather_code") is not None:
        response["weather_label"] = weather_label(summary["weather_code"])
    # Summary may also override the splits-derived totals if both are present;
    # prefer summary-level numbers for the totals (more authoritative).
    if "distance_km" in summary:
        response["total_distance_km"] = summary["distance_km"]
    if "avg_pace" in summary and not response.get("avg_pace_per_km"):
        response["avg_pace_per_km"] = summary["avg_pace"]
    if "avg_hr_bpm" in summary and not response.get("avg_hr_bpm"):
        response["avg_hr_bpm"] = summary["avg_hr_bpm"]
    if "avg_power_watts" in summary and not response.get("avg_power_watts"):
        response["avg_power_watts"] = summary["avg_power_watts"]
    return response


# ── Confirm & save (or manual entry) ─────────────────────────────────────────

class CheckinConfirm(BaseModel):
    checkin_date: Optional[str] = None
    week_number: Optional[int] = None
    total_distance_km: Optional[float] = None
    avg_pace_per_km: Optional[str] = None
    avg_hr_bpm: Optional[int] = None
    max_hr_bpm: Optional[int] = None
    avg_power_watts: Optional[int] = None
    splits: Optional[list] = None
    notes: Optional[str] = None
    tmp_image_path: Optional[str] = None  # from /parse step


@router.post("/daily")
async def daily_checkin(
    image: Optional[UploadFile] = File(None),
    summary_image: Optional[UploadFile] = File(None),
    notes: Optional[str] = Form(None),
    checkin_date: Optional[str] = Form(None),
    override_json: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save a daily check-in. Three modes:
    1. image (+ optional summary_image, + optional override_json) → parse and save
    2. override_json only → manual entry
    3. override_json with tmp_image_path / tmp_summary_image_path → confirmed
       parsed data from /parse step
    """
    parsed = {}
    summary: dict = {}
    image_filename = None
    summary_filename = None

    if image:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        ext = os.path.splitext(image.filename or "")[1] or ".png"
        image_filename = f"{uuid.uuid4()}{ext}"
        image_path = os.path.join(UPLOADS_DIR, image_filename)
        with open(image_path, "wb") as f:
            f.write(await image.read())

        openai_key = os.getenv("OPENAI_API_KEY")
        parsed = parse_workout_screenshot(image_path, openai_api_key=openai_key or None)

    if summary_image:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        sext = os.path.splitext(summary_image.filename or "")[1] or ".png"
        summary_filename = f"{uuid.uuid4()}{sext}"
        summary_path = os.path.join(UPLOADS_DIR, summary_filename)
        with open(summary_path, "wb") as f:
            f.write(await summary_image.read())
        openai_key = os.getenv("OPENAI_API_KEY")
        summary = parse_workout_summary_screenshot(summary_path, openai_api_key=openai_key or None)
        summary = _enrich_with_weather(summary)

    if override_json:
        try:
            overrides = json.loads(override_json)
            # Handle tmp file rename for splits image
            if "tmp_image_path" in overrides and not image_filename:
                image_filename = overrides.pop("tmp_image_path")
            # Handle tmp file rename for summary image
            if "tmp_summary_image_path" in overrides and not summary_filename:
                summary_filename = overrides.pop("tmp_summary_image_path")
            parsed.update(overrides)
        except Exception:
            pass

    today_str = checkin_date or parsed.get("checkin_date") or date.today().isoformat()
    try:
        d = date.fromisoformat(today_str)
    except ValueError:
        d = date.today()
        today_str = d.isoformat()

    week_num = parsed.get("week_number") or get_week_number(d)

    def _pick(field: str, *fallbacks):
        """Return the first non-None value: summary -> parsed -> fallbacks."""
        if summary.get(field) is not None:
            return summary[field]
        for fb in (field,) + fallbacks:
            if parsed.get(fb) is not None:
                return parsed[fb]
        return None

    checkin = DailyCheckin(
        user_id=current_user.id,
        checkin_date=today_str,
        image_path=image_filename,
        summary_image_path=summary_filename,
        raw_text_extracted=parsed.get("raw_text", ""),
        total_distance_km=_pick("distance_km", "total_distance_km"),
        avg_pace_per_km=_pick("avg_pace", "avg_pace_per_km"),
        avg_hr_bpm=_pick("avg_hr_bpm", "avg_hr"),
        max_hr_bpm=parsed.get("max_hr_bpm") or parsed.get("max_hr"),
        avg_power_watts=_pick("avg_power_watts", "avg_power"),
        splits_json=json.dumps(parsed.get("splits", [])),
        week_number=week_num,
        notes=notes or parsed.get("notes"),
        # Summary fields
        workout_started_at=summary.get("workout_started_at") or parsed.get("workout_started_at"),
        workout_ended_at=summary.get("workout_ended_at") or parsed.get("workout_ended_at"),
        workout_time_seconds=summary.get("workout_time_seconds") or parsed.get("workout_time_seconds"),
        total_elapsed_seconds=summary.get("total_elapsed_seconds") or parsed.get("total_elapsed_seconds"),
        location_name=summary.get("location_name") or parsed.get("location_name"),
        location_lat=summary.get("location_lat") or parsed.get("location_lat"),
        location_lon=summary.get("location_lon") or parsed.get("location_lon"),
        elevation_gain_m=summary.get("elevation_gain_m") or parsed.get("elevation_gain_m"),
        avg_cadence_spm=summary.get("avg_cadence_spm") or parsed.get("avg_cadence_spm"),
        active_calories=summary.get("active_calories") or parsed.get("active_calories"),
        total_calories=summary.get("total_calories") or parsed.get("total_calories"),
        perceived_effort=summary.get("perceived_effort") or parsed.get("perceived_effort"),
        # Weather fields
        temperature_c=summary.get("temperature_c") or parsed.get("temperature_c"),
        apparent_temperature_c=summary.get("apparent_temperature_c") or parsed.get("apparent_temperature_c"),
        humidity_pct=summary.get("humidity_pct") or parsed.get("humidity_pct"),
        wind_speed_kmh=summary.get("wind_speed_kmh") or parsed.get("wind_speed_kmh"),
        precipitation_mm=summary.get("precipitation_mm") or parsed.get("precipitation_mm"),
        weather_code=summary.get("weather_code") or parsed.get("weather_code"),
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    # Auto-mark this day as completed so the Plan viewer shows a ✓ badge.
    try:
        upsert_day_log(
            db, current_user.id, week_num, d.weekday(),
            kind="run", log_date=today_str, checkin_id=checkin.id,
        )
    except Exception:
        pass

    return {
        **checkin_to_dict(checkin),
        "confidence": parsed.get("confidence", "manual"),
    }


# ── Update existing check-in ──────────────────────────────────────────────────

@router.put("/daily/{checkin_id}")
def update_checkin(
    checkin_id: int,
    payload: CheckinConfirm,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    checkin = db.query(DailyCheckin).filter(
        DailyCheckin.id == checkin_id,
        DailyCheckin.user_id == current_user.id,
    ).first()
    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in not found")

    if payload.checkin_date is not None:
        checkin.checkin_date = payload.checkin_date
        try:
            d = date.fromisoformat(payload.checkin_date)
            checkin.week_number = get_week_number(d)
        except ValueError:
            pass
    if payload.week_number is not None:
        checkin.week_number = payload.week_number
    if payload.total_distance_km is not None:
        checkin.total_distance_km = payload.total_distance_km
    if payload.avg_pace_per_km is not None:
        checkin.avg_pace_per_km = payload.avg_pace_per_km
    if payload.avg_hr_bpm is not None:
        checkin.avg_hr_bpm = payload.avg_hr_bpm
    if payload.max_hr_bpm is not None:
        checkin.max_hr_bpm = payload.max_hr_bpm
    if payload.avg_power_watts is not None:
        checkin.avg_power_watts = payload.avg_power_watts
    if payload.splits is not None:
        checkin.splits_json = json.dumps(payload.splits)
    if payload.notes is not None:
        checkin.notes = payload.notes

    db.commit()
    db.refresh(checkin)
    return checkin_to_dict(checkin)


# ── List check-ins ────────────────────────────────────────────────────────────

@router.get("/daily")
def list_checkins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == current_user.id)
        .order_by(DailyCheckin.checkin_date.desc())
        .all()
    )
    return [checkin_to_dict(r) for r in rows]

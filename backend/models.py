from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    # Personal Z2 baseline pace in seconds per km, computed from Week 1 runs.
    # Set once via /api/baseline/calibrate and used by coach + adjuster for
    # gap-to-target math. Null means "use the hardcoded 10:30 baseline".
    baseline_pace_seconds = Column(Integer, nullable=True)
    baseline_calibrated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    checkin_date = Column(String, nullable=False)
    image_path = Column(String)
    summary_image_path = Column(String)  # optional Workout Summary screenshot
    raw_text_extracted = Column(Text)
    total_distance_km = Column(Float)
    total_time_seconds = Column(Integer)
    avg_pace_per_km = Column(String)
    avg_hr_bpm = Column(Float)
    max_hr_bpm = Column(Float)
    avg_power_watts = Column(Float)
    splits_json = Column(Text)
    week_number = Column(Integer)
    notes = Column(Text)
    # ── Workout Summary screenshot fields (all nullable) ────────────────
    workout_started_at = Column(String)         # ISO datetime, e.g. "2026-04-26T06:42:00"
    workout_ended_at = Column(String)
    workout_time_seconds = Column(Integer)      # moving time
    total_elapsed_seconds = Column(Integer)     # includes pauses
    location_name = Column(String)              # raw text from screenshot, e.g. "Gurugram"
    location_lat = Column(Float)                # resolved via Open-Meteo geocoding
    location_lon = Column(Float)
    elevation_gain_m = Column(Float)
    avg_cadence_spm = Column(Integer)
    active_calories = Column(Integer)
    total_calories = Column(Integer)
    perceived_effort = Column(Integer)          # Apple's Effort field, 1-10
    # ── Weather fields (auto-fetched from Open-Meteo at check-in) ───────
    temperature_c = Column(Float)
    apparent_temperature_c = Column(Float)
    humidity_pct = Column(Integer)
    wind_speed_kmh = Column(Float)
    precipitation_mm = Column(Float)
    weather_code = Column(Integer)              # WMO code; decoded for display
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WeeklyLog(Base):
    __tablename__ = "weekly_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date = Column(String, nullable=False)
    week_number = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    waist_inches = Column(Float, nullable=False)
    chest_inches = Column(Float)
    hips_inches = Column(Float)
    body_fat_pct = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CoachNote(Base):
    """
    LLM-generated coaching notes, cached so we don't regenerate on every
    page view. Two types:
      pre  — target pace + guidance for a given day (one per user/day)
      post — summary of a specific check-in (one per checkin_id)
    """
    __tablename__ = "coach_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note_type = Column(String, nullable=False)  # "pre" | "post"
    note_date = Column(String, nullable=False)  # ISO date the note applies to
    week_number = Column(Integer, nullable=False)
    checkin_id = Column(Integer, ForeignKey("daily_checkins.id"), nullable=True)
    text = Column(Text, nullable=False)
    metrics_json = Column(Text)  # structured metrics used to build the prompt
    model_used = Column(String)  # which LLM (or "rules" for fallback)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DayLog(Base):
    """
    Tracks per-day completion for any day type (run / strength / rest).
    One row per (user, week, day_of_week) — unique constraint enforced at
    query time. Run days link to a DailyCheckin; strength/workout days
    store an image path; rest days just record that the user rested.
    """
    __tablename__ = "day_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date = Column(String, nullable=False)
    week_number = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Mon..6=Sun
    kind = Column(String, nullable=False)  # "run" | "strength" | "rest"
    checkin_id = Column(Integer, ForeignKey("daily_checkins.id"), nullable=True)
    image_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PlanAdjustment(Base):
    """
    Dynamic per-day plan overrides generated by the adjuster service after
    each weekly log save. Only weeks > current_week are adjusted; the end
    date stays fixed at week 32.
    """
    __tablename__ = "plan_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Mon..6=Sun
    original_json = Column(Text, nullable=False)  # snapshot of the original day spec
    adjusted_json = Column(Text, nullable=False)  # the modified day spec
    rationale = Column(Text, nullable=False)
    batch_id = Column(String, nullable=False)  # groups adjustments from one adjuster run
    created_at = Column(DateTime(timezone=True), server_default=func.now())

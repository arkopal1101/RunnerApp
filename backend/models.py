from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    checkin_date = Column(String, nullable=False)
    image_path = Column(String)
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

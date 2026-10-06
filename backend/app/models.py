from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("hearts BETWEEN 0 AND 5"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80))
    timezone: Mapped[str] = mapped_column(default="Asia/Kolkata")
    hearts: Mapped[int] = mapped_column(default=5)
    gems: Mapped[int] = mapped_column(default=450)
    daily_goal_xp: Mapped[int] = mapped_column(default=40)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    language_code: Mapped[str]
    source_language_code: Mapped[str]


class Unit(Base):
    __tablename__ = "units"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    title: Mapped[str]
    description: Mapped[str]
    position: Mapped[int]


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), index=True)
    title: Mapped[str]
    position: Mapped[int]
    icon_key: Mapped[str] = mapped_column(default="star")


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    title: Mapped[str]
    position: Mapped[int]
    xp_reward: Mapped[int] = mapped_column(default=20)


class Exercise(Base):
    __tablename__ = "exercises"
    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), index=True)
    type: Mapped[str]
    prompt: Mapped[str]
    public_payload: Mapped[dict] = mapped_column(JSON)
    answer_payload: Mapped[dict] = mapped_column(JSON)
    position: Mapped[int]


class SkillProgress(Base):
    __tablename__ = "skill_progress"
    __table_args__ = (UniqueConstraint("user_id", "skill_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LessonAttempt(Base):
    __tablename__ = "lesson_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), index=True)
    status: Mapped[str] = mapped_column(default="active")
    next_exercise_index: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    awarded_xp: Mapped[int] = mapped_column(default=0)


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"
    __table_args__ = (UniqueConstraint("attempt_id", "exercise_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("lesson_attempts.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    submitted_payload: Mapped[dict] = mapped_column(JSON)
    is_correct: Mapped[bool]
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DailyActivity(Base):
    __tablename__ = "daily_activity"
    __table_args__ = (UniqueConstraint("user_id", "activity_date"), CheckConstraint("xp >= 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    activity_date: Mapped[date] = mapped_column(Date)
    xp: Mapped[int] = mapped_column(default=0)
    lessons_completed: Mapped[int] = mapped_column(default=0)


class GuestProfile(Base):
    __tablename__ = "guest_profiles"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

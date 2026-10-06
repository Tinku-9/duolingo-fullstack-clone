import os
import hashlib
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .grading import correction, grade, validate_answer
from .models import AttemptAnswer, DailyActivity, Exercise, Lesson, LessonAttempt, SkillProgress, User, GuestProfile, utc_now
from .seed import seed
from .services import attempt_view, course_path, exercises_for, get_attempt, local_today, stats


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="Duolingo Assignment API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","), allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization"])


class AnswerRequest(BaseModel):
    exercise_id: int
    answer: dict = Field(default_factory=dict)


def write_lock(db):
    # SQLite serializes writers before reading mutable state; prevents concurrent
    # requests from awarding twice or losing a heart update.
    db.execute(text("BEGIN IMMEDIATE"))


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Guest token required")
    token = authorization[7:]
    if len(token) != 43:
        raise HTTPException(401, "Invalid guest token")
    profile = db.get(GuestProfile, hashlib.sha256(token.encode()).hexdigest())
    if not profile:
        raise HTTPException(401, "Invalid guest token")
    return db.get(User, profile.user_id).id


@app.post("/api/guests")
def create_guest(db: Session = Depends(get_db)):
    write_lock(db)
    token = secrets.token_urlsafe(32)
    user = User(display_name="Guest")
    db.add(user)
    db.flush()
    db.add(GuestProfile(token_hash=hashlib.sha256(token.encode()).hexdigest(), user_id=user.id))
    db.commit()
    return {"token": token}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    return stats(db, db.get(User, user_id))


@app.get("/api/courses/{course_id}/path")
def path(course_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    return course_path(db, db.get(User, user_id), course_id)


@app.post("/api/lessons/{lesson_id}/attempts")
def start(lesson_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    write_lock(db)
    user = db.get(User, user_id)
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    state = next((x["state"] for unit in course_path(db, user)["units"] for skill in unit["skills"] for x in skill["lessons"] if x["id"] == lesson_id), "locked")
    if state == "locked":
        raise HTTPException(409, "Finish the previous lesson first")
    if user.hearts == 0:
        raise HTTPException(409, "You are out of hearts. Refill to keep learning.")
    active = db.scalar(select(LessonAttempt).where(LessonAttempt.user_id == user.id, LessonAttempt.status == "active"))
    if active and active.lesson_id != lesson_id:
        raise HTTPException(409, "You already have an active lesson. Resume or exit it first.")
    attempt = active or LessonAttempt(id=str(uuid4()), user_id=user.id, lesson_id=lesson_id)
    db.add(attempt)
    db.commit()
    return attempt_view(db, attempt, user)


@app.get("/api/me/active-attempt")
def active_attempt(db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    user = db.get(User, user_id)
    attempt = db.scalar(select(LessonAttempt).where(LessonAttempt.user_id == user.id, LessonAttempt.status == "active"))
    return attempt_view(db, attempt, user) if attempt else None


@app.get("/api/attempts/{attempt_id}")
def attempt(attempt_id: str, db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    user = db.get(User, user_id)
    return attempt_view(db, get_attempt(db, attempt_id, user), user)


@app.post("/api/attempts/{attempt_id}/answers")
def answer(attempt_id: str, body: AnswerRequest, db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    write_lock(db)
    user = db.get(User, user_id)
    attempt = get_attempt(db, attempt_id, user)
    previous = db.scalar(select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt.id, AttemptAnswer.exercise_id == body.exercise_id))
    exercise = db.get(Exercise, body.exercise_id)
    if previous:
        return {"correct": previous.is_correct, "correction": correction(exercise.type, exercise.public_payload, exercise.answer_payload), "attempt": attempt_view(db, attempt, user)}
    exercises = exercises_for(db, attempt)
    if attempt.status != "active" or attempt.next_exercise_index >= len(exercises):
        raise HTTPException(409, "This attempt is not accepting answers")
    if exercises[attempt.next_exercise_index].id != body.exercise_id:
        raise HTTPException(409, "Submit the current exercise first")
    payload = body.answer
    try:
        validate_answer(exercise.type, exercise.public_payload, payload)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    correct = grade(exercise.type, exercise.public_payload, exercise.answer_payload, payload)
    db.add(AttemptAnswer(attempt_id=attempt.id, exercise_id=exercise.id, submitted_payload=payload, is_correct=correct))
    attempt.next_exercise_index += 1
    if not correct:
        user.hearts = max(0, user.hearts - 1)
        if user.hearts == 0:
            attempt.status = "failed"
    db.commit()
    return {"correct": correct, "correction": correction(exercise.type, exercise.public_payload, exercise.answer_payload), "attempt": attempt_view(db, attempt, user)}


@app.post("/api/attempts/{attempt_id}/complete")
def complete(attempt_id: str, db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    write_lock(db)
    user = db.get(User, user_id)
    attempt = get_attempt(db, attempt_id, user)
    if attempt.status == "completed":
        return {"attempt": attempt_view(db, attempt, user), "learner": stats(db, user)}
    if attempt.status != "active" or attempt.next_exercise_index != len(exercises_for(db, attempt)) or not user.hearts:
        raise HTTPException(409, "Finish the lesson with hearts remaining before claiming XP")
    lesson = db.get(Lesson, attempt.lesson_id)
    attempt.status = "completed"
    attempt.completed_at = utc_now()
    attempt.awarded_xp = lesson.xp_reward
    today = local_today(user)
    activity = db.scalar(select(DailyActivity).where(DailyActivity.user_id == user.id, DailyActivity.activity_date == today))
    if not activity:
        activity = DailyActivity(user_id=user.id, activity_date=today, xp=0, lessons_completed=0)
        db.add(activity)
    activity.xp += lesson.xp_reward
    activity.lessons_completed += 1
    db.flush()
    lessons = set(db.scalars(select(Lesson.id).where(Lesson.skill_id == lesson.skill_id)))
    done = set(db.scalars(select(LessonAttempt.lesson_id).where(LessonAttempt.user_id == user.id, LessonAttempt.status == "completed")))
    progress = db.scalar(select(SkillProgress).where(SkillProgress.user_id == user.id, SkillProgress.skill_id == lesson.skill_id))
    if lessons <= done and not progress:
        db.add(SkillProgress(user_id=user.id, skill_id=lesson.skill_id))
    db.commit()
    return {"attempt": attempt_view(db, attempt, user), "learner": stats(db, user)}


@app.post("/api/attempts/{attempt_id}/abandon")
def abandon(attempt_id: str, db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    write_lock(db)
    user = db.get(User, user_id)
    attempt = get_attempt(db, attempt_id, user)
    if attempt.status == "active":
        attempt.status = "abandoned"
    db.commit()
    return attempt_view(db, attempt, user)


@app.post("/api/me/hearts/refill")
def refill(db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    write_lock(db)
    user = db.get(User, user_id)
    user.hearts = 5
    db.commit()
    return stats(db, user)


@app.get("/api/leaderboard")
def leaderboard(db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    today = local_today(db.get(User, user_id))
    start = today - timedelta(days=today.weekday())
    activity = list(db.scalars(select(DailyActivity).where(DailyActivity.activity_date >= start, DailyActivity.activity_date <= today)))
    rows = [{"id": user.id, "name": user.display_name, "xp": sum(x.xp for x in activity if x.user_id == user.id), "is_you": user.id == user_id} for user in db.scalars(select(User).where((User.id == user_id) | (~User.id.in_(select(GuestProfile.user_id)))))]
    rows.sort(key=lambda x: (-x["xp"], x["id"]))
    return {"league": "Bronze", "week_start": str(start), "entries": [{**row, "rank": i + 1} for i, row in enumerate(rows)]}


@app.get("/api/me/profile")
def profile(db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    user = db.get(User, user_id)
    summary = stats(db, user)
    completed = len(list(db.scalars(select(SkillProgress).where(SkillProgress.user_id == user.id))))
    return {**summary, "completed_skills": completed, "achievements": [{"title": "Wildfire", "description": "Build a 3-day streak", "earned": summary["streak"] >= 3}, {"title": "Sage", "description": "Earn 100 XP", "earned": summary["total_xp"] >= 100}, {"title": "Trailblazer", "description": "Complete 3 skills", "earned": completed >= 3}]}

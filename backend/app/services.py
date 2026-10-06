from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select

from .grading import current_streak
from .models import AttemptAnswer, DailyActivity, Exercise, Lesson, LessonAttempt, Skill, Unit, User


def local_today(user):
    return datetime.now(ZoneInfo(user.timezone)).date()


def stats(db, user):
    days = list(db.scalars(select(DailyActivity).where(DailyActivity.user_id == user.id)))
    today = local_today(user)
    week_start = today - timedelta(days=today.weekday())
    return {
        "id": user.id, "display_name": user.display_name, "hearts": user.hearts,
        "gems": user.gems, "daily_goal_xp": user.daily_goal_xp,
        "daily_xp": sum(x.xp for x in days if x.activity_date == today),
        "total_xp": sum(x.xp for x in days),
        "weekly_xp": sum(x.xp for x in days if week_start <= x.activity_date <= today),
        "streak": current_streak({x.activity_date for x in days if x.lessons_completed > 0}, today),
        "course_id": 1, "timezone": user.timezone,
    }


def course_path(db, user, course_id=1):
    units = list(db.scalars(select(Unit).where(Unit.course_id == course_id).order_by(Unit.position)))
    if not units:
        raise HTTPException(404, "Course not found")
    complete = set(db.scalars(select(LessonAttempt.lesson_id).where(LessonAttempt.user_id == user.id, LessonAttempt.status == "completed")))
    result = []
    previous_complete = True
    for unit in units:
        skills = []
        for skill in db.scalars(select(Skill).where(Skill.unit_id == unit.id).order_by(Skill.position)):
            lessons = []
            for lesson in db.scalars(select(Lesson).where(Lesson.skill_id == skill.id).order_by(Lesson.position)):
                done = lesson.id in complete
                lessons.append({"id": lesson.id, "title": lesson.title, "xp_reward": lesson.xp_reward, "state": "completed" if done else "available" if previous_complete else "locked"})
                previous_complete = previous_complete and done
            count = sum(x["state"] == "completed" for x in lessons)
            skills.append({"id": skill.id, "title": skill.title, "icon_key": skill.icon_key, "completed_lessons": count, "total_lessons": len(lessons), "state": "completed" if count == len(lessons) else "available" if any(x["state"] == "available" for x in lessons) else "locked", "lessons": lessons})
        result.append({"id": unit.id, "title": unit.title, "description": unit.description, "position": unit.position, "skills": skills})
    return {"course_id": course_id, "units": result}


def get_attempt(db, attempt_id, user):
    attempt = db.get(LessonAttempt, attempt_id)
    if not attempt or attempt.user_id != user.id:
        raise HTTPException(404, "Lesson attempt not found")
    return attempt


def exercises_for(db, attempt):
    return list(db.scalars(select(Exercise).where(Exercise.lesson_id == attempt.lesson_id).order_by(Exercise.position)))


def attempt_view(db, attempt, user):
    exercises = exercises_for(db, attempt)
    exercise = exercises[attempt.next_exercise_index] if attempt.status == "active" and attempt.next_exercise_index < len(exercises) else None
    answers = list(db.scalars(select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt.id)))
    return {
        "id": attempt.id, "lesson_id": attempt.lesson_id, "status": attempt.status,
        "answered": attempt.next_exercise_index, "total": len(exercises), "hearts": user.hearts,
        "awarded_xp": attempt.awarded_xp,
        "accuracy": round(100 * sum(x.is_correct for x in answers) / len(answers)) if answers else 0,
        "exercise": {"id": exercise.id, "type": exercise.type, "prompt": exercise.prompt, "payload": exercise.public_payload} if exercise else None,
    }

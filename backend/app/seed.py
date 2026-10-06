from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select

from .models import Course, DailyActivity, Exercise, Lesson, LessonAttempt, Skill, SkillProgress, Unit, User


# Curated small course: each vocabulary set creates five distinct exercise types.
VOCAB = [
    ("Greetings", "hola", "hello", "adiós", "goodbye", "Hola, buenos días", "Hello, good morning"),
    ("First words", "sí", "yes", "no", "no", "Sí, por favor", "Yes, please"),
    ("At the café", "agua", "water", "pan", "bread", "Quiero agua", "I want water"),
    ("A little snack", "leche", "milk", "café", "coffee", "Quiero café", "I want coffee"),
    ("Meet the family", "madre", "mother", "padre", "father", "Mi madre", "My mother"),
    ("People around you", "amigo", "friend", "hermana", "sister", "Mi hermana", "My sister"),
]


def make_exercises(lesson_id: int, vocabulary: tuple, reverse: bool):
    _, word, meaning, word2, meaning2, sentence, translation = vocabulary
    if reverse:
        word, word2, meaning, meaning2 = word2, word, meaning2, meaning
    tokens = translation.split()
    return [
        Exercise(lesson_id=lesson_id, position=0, type="multiple_choice", prompt=f'What does “{word}” mean?', public_payload={"options": [{"id": "a", "text": meaning2}, {"id": "b", "text": meaning}, {"id": "c", "text": "thank you"}]}, answer_payload={"option_id": "b"}),
        Exercise(lesson_id=lesson_id, position=1, type="word_bank", prompt="Translate this sentence", public_payload={"sentence": sentence, "tokens": [{"id": f"t{i}", "text": text} for i, text in reversed(list(enumerate(tokens)))] + [{"id": "extra", "text": "cat"}]}, answer_payload={"token_ids": [f"t{i}" for i in range(len(tokens))]}),
        Exercise(lesson_id=lesson_id, position=2, type="match_pairs", prompt="Match the pairs", public_payload={"left": [{"id": "l1", "text": word}, {"id": "l2", "text": word2}, {"id": "l3", "text": "gracias"}], "right": [{"id": "r3", "text": "thank you"}, {"id": "r1", "text": meaning}, {"id": "r2", "text": meaning2}]}, answer_payload={"pairs": {"l1": "r1", "l2": "r2", "l3": "r3"}}),
        Exercise(lesson_id=lesson_id, position=3, type="fill_blank", prompt="Fill in the missing word", public_payload={"sentence": f"___ = {meaning}", "hint": "Write the Spanish word"}, answer_payload={"accepted": [word]}),
        Exercise(lesson_id=lesson_id, position=4, type="type_answer", prompt="Write this in English", public_payload={"sentence": sentence}, answer_payload={"accepted": [translation]}),
    ]


def seed(db):
    if db.get(Course, 1):
        return
    db.add(Course(id=1, title="Spanish", language_code="es", source_language_code="en"))
    db.add(User(id=1, display_name="Alex"))
    db.flush()
    for idx, (title, desc) in enumerate([("First steps", "Say hello and introduce yourself"), ("A taste of Spanish", "Order drinks and your favorite snacks"), ("Your people", "Talk about friends and family")], start=1):
        db.add(Unit(id=idx, course_id=1, title=title, description=desc, position=idx))
    db.flush()
    for idx, vocabulary in enumerate(VOCAB, start=1):
        db.add(Skill(id=idx, unit_id=(idx - 1) // 2 + 1, title=vocabulary[0], position=idx, icon_key="star" if idx % 2 else "book"))
    db.flush()
    for idx, vocabulary in enumerate(VOCAB, start=1):
        for position in (1, 2):
            lesson_id = (idx - 1) * 2 + position
            db.add(Lesson(id=lesson_id, skill_id=idx, title=f"{vocabulary[0]} · {position}", position=position))
            db.flush()
            db.add_all(make_exercises(lesson_id, vocabulary, position == 2))
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    for days_ago in (1, 2, 3):
        db.add(DailyActivity(user_id=1, activity_date=today - timedelta(days=days_ago), xp=40, lessons_completed=2))
    db.add(SkillProgress(user_id=1, skill_id=1))
    for lesson_id in (1, 2):
        db.add(LessonAttempt(id=str(uuid4()), user_id=1, lesson_id=lesson_id, status="completed", next_exercise_index=5, completed_at=datetime.now(timezone.utc), awarded_xp=20))
    for user_id, name, xp in [(2, "Sofia", 280), (3, "Oliver", 220), (4, "Maya", 180), (5, "Leo", 80), (6, "Priya", 60)]:
        db.add(User(id=user_id, display_name=name))
        db.flush()
        db.add(DailyActivity(user_id=user_id, activity_date=today, xp=xp, lessons_completed=xp // 20))
    db.commit()

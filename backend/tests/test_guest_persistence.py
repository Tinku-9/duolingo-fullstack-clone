import hashlib
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models import GuestProfile, User, DailyActivity, LessonAttempt
from app.seed import seed


class GuestPersistenceTests(unittest.TestCase):
    def test_additive_schema_preserves_legacy_data_and_survives_reopen(self):
        with tempfile.TemporaryDirectory() as folder:
            url = "sqlite:///" + (Path(folder) / "legacy.db").as_posix()
            engine = create_engine(url)
            # Recreate the previous deployed schema, with no guest table.
            Base.metadata.create_all(engine, tables=[t for t in Base.metadata.sorted_tables if t.name != "guest_profiles"])
            with Session(engine) as db:
                seed(db)
                db.get(User, 1).hearts = 2
                db.commit()
                old_activity = [(x.id, x.user_id, x.xp) for x in db.scalars(select(DailyActivity))]
                old_attempts = [(x.id, x.status) for x in db.scalars(select(LessonAttempt))]
            Base.metadata.create_all(engine)
            digest = hashlib.sha256(b"test-persistence-token").hexdigest()
            with Session(engine) as db:
                seed(db)
                user = User(display_name="Guest", hearts=3)
                db.add(user)
                db.flush()
                guest_id = user.id
                db.add(GuestProfile(token_hash=digest, user_id=guest_id))
                db.commit()
            engine.dispose()
            engine = create_engine(url)
            try:
                with Session(engine) as db:
                    self.assertEqual(db.get(GuestProfile, digest).user_id, guest_id)
                    self.assertEqual(db.get(User, guest_id).hearts, 3)
                    self.assertEqual(db.get(User, 1).hearts, 2)
                    self.assertEqual([(x.id, x.user_id, x.xp) for x in db.scalars(select(DailyActivity))], old_activity)
                    self.assertEqual([(x.id, x.status) for x in db.scalars(select(LessonAttempt))], old_attempts)
            finally:
                engine.dispose()

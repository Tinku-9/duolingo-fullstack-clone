import unittest
import importlib.util

DATABASE_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None
if DATABASE_AVAILABLE:
    from sqlalchemy import create_engine, event, select
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session
    from app.database import Base
    from app.models import Exercise, Lesson, User
    from app.seed import seed


@unittest.skipUnless(DATABASE_AVAILABLE, "Install SQLAlchemy to run database tests")
class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        @event.listens_for(self.engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        seed(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_seed_does_not_reset_existing_progress(self):
        self.db.get(User, 1).hearts = 2
        self.db.commit()
        seed(self.db)
        self.assertEqual(self.db.get(User, 1).hearts, 2)
        self.assertEqual(len(list(self.db.scalars(select(Lesson)))), 12)
        self.assertEqual(len(list(self.db.scalars(select(Exercise)))), 60)

    def test_hearts_constraint_rejects_impossible_balance(self):
        self.db.get(User, 1).hearts = -1
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()
        self.assertEqual(self.db.get(User, 1).hearts, 5)

    def test_content_foreign_keys_reject_orphan_lesson(self):
        self.db.add(Lesson(skill_id=99999, title="Orphan", position=1))
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()


if __name__ == "__main__":
    unittest.main()

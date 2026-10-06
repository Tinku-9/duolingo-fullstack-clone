import unittest
import hashlib
import importlib.util
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_AVAILABLE = all(importlib.util.find_spec(name) is not None for name in ("fastapi", "sqlalchemy", "httpx"))
if API_AVAILABLE:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, event, select
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base, get_db
    from app.main import app
    from app.models import DailyActivity, Exercise, User, GuestProfile
    from app.seed import seed
    from app.services import local_today, stats


@unittest.skipUnless(API_AVAILABLE, "Install backend requirements to run API integration tests")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(self.engine, "connect")
        def enforce_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)
        with self.sessions() as db:
            seed(db)
            db.add(GuestProfile(token_hash=hashlib.sha256(("t" * 43).encode()).hexdigest(), user_id=1))
            db.commit()
        def override_db():
            with self.sessions() as db:
                yield db
        app.dependency_overrides[get_db] = override_db
        # Schema and seeds are explicitly created in the isolated test database.
        self.client = TestClient(app, headers={"Authorization": "Bearer " + "t" * 43})

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def start(self, lesson_id=3):
        result = self.client.post(f"/api/lessons/{lesson_id}/attempts")
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def solve(self, attempt):
        while attempt["exercise"]:
            exercise_id = attempt["exercise"]["id"]
            with self.sessions() as db:
                answer = db.get(Exercise, exercise_id).answer_payload.copy()
            if "accepted" in answer:
                answer = {"text": answer["accepted"][0]}
            response = self.client.post(f"/api/attempts/{attempt['id']}/answers", json={"exercise_id": exercise_id, "answer": answer})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(response.json()["correct"])
            attempt = response.json()["attempt"]
        return attempt

    def test_seed_is_idempotent_and_answers_are_private(self):
        with self.sessions() as db:
            user = db.get(User, 1)
            user.hearts = 2
            db.commit()
            seed(db)
            self.assertEqual(db.get(User, 1).hearts, 2)
            self.assertEqual(len(list(db.scalars(select(Exercise)))), 60)
        self.assertNotIn("answer_payload", str(self.start()))

    def test_lock_and_active_attempt_reuse(self):
        self.assertEqual(self.client.post("/api/lessons/5/attempts").status_code, 409)
        first = self.start()
        self.assertEqual(self.start()["id"], first["id"])
        self.assertEqual(self.client.post("/api/lessons/1/attempts").status_code, 409)

    def test_wrong_answer_is_charged_once_and_refresh_recovers(self):
        attempt = self.start()
        payload = {"exercise_id": attempt["exercise"]["id"], "answer": {"option_id": "a"}}
        first = self.client.post(f"/api/attempts/{attempt['id']}/answers", json=payload).json()
        second = self.client.post(f"/api/attempts/{attempt['id']}/answers", json=payload).json()
        self.assertEqual(first["attempt"]["hearts"], 4)
        self.assertEqual(second["attempt"]["hearts"], 4)
        restored = self.client.get(f"/api/attempts/{attempt['id']}").json()
        self.assertEqual(restored["answered"], 1)

    def test_out_of_order_and_invalid_answers_do_not_cost_hearts(self):
        attempt = self.start()
        endpoint = f"/api/attempts/{attempt['id']}/answers"
        self.assertEqual(self.client.post(endpoint, json={"exercise_id": attempt["exercise"]["id"] + 1, "answer": {}}).status_code, 409)
        self.assertEqual(self.client.post(endpoint, json={"exercise_id": attempt["exercise"]["id"], "answer": {"option_id": []}}).status_code, 422)
        self.assertEqual(self.client.get("/api/me").json()["hearts"], 5)

    def test_failure_refill_and_no_unearned_xp(self):
        with self.sessions() as db:
            db.get(User, 1).hearts = 1
            db.commit()
        attempt = self.start()
        result = self.client.post(f"/api/attempts/{attempt['id']}/answers", json={"exercise_id": attempt["exercise"]["id"], "answer": {"option_id": "a"}}).json()
        self.assertEqual(result["attempt"]["status"], "failed")
        self.assertEqual(self.client.post(f"/api/attempts/{attempt['id']}/complete").status_code, 409)
        self.assertEqual(self.client.post("/api/me/hearts/refill").json()["hearts"], 5)
        self.assertEqual(self.client.get(f"/api/attempts/{attempt['id']}").json()["status"], "failed")
        self.assertNotEqual(self.start()["id"], attempt["id"])

    def test_completion_awards_once_and_unlocks_next_skill(self):
        first = self.solve(self.start())
        endpoint = f"/api/attempts/{first['id']}/complete"
        one = self.client.post(endpoint).json()
        two = self.client.post(endpoint).json()
        self.assertEqual(one["learner"]["total_xp"], 140)
        self.assertEqual(two["learner"]["total_xp"], 140)
        self.assertEqual(one["learner"]["streak"], 4)
        second = self.solve(self.start(4))
        self.assertEqual(self.client.post(f"/api/attempts/{second['id']}/complete").status_code, 200)
        me = self.client.get("/api/me").json()
        self.assertEqual(me["daily_xp"], 40)
        self.assertEqual(me["streak"], 4)
        self.assertEqual(self.start(5)["status"], "active")
        self.assertEqual(self.client.get("/api/me/profile").json()["completed_skills"], 2)

    def test_abandon_preserves_stats_and_frees_active_slot(self):
        attempt = self.start()
        response = self.client.post(f"/api/attempts/{attempt['id']}/abandon")
        self.assertEqual(response.json()["status"], "abandoned")
        self.assertEqual(self.client.get("/api/me").json()["total_xp"], 120)
        self.assertNotEqual(self.start()["id"], attempt["id"])

    def test_guest_isolation_and_token_validation(self):
        a = TestClient(app)
        b = TestClient(app)
        try:
            self.assertEqual(a.get("/api/me").status_code, 401)
            self.assertEqual(a.get("/api/me", headers={"Authorization": "Bearer " + "x" * 43}).status_code, 401)
            token_a = a.post("/api/guests").json()["token"]
            token_b = b.post("/api/guests").json()["token"]
            self.assertNotEqual(token_a, token_b)
            a.headers["Authorization"] = "Bearer " + token_a
            b.headers["Authorization"] = "Bearer " + token_b
            before_b = b.get("/api/me").json()
            self.assertEqual(before_b["total_xp"], 0)
            self.assertNotEqual(a.get("/api/me").json()["id"], before_b["id"])
            attempt = a.post("/api/lessons/1/attempts").json()
            root = f"/api/attempts/{attempt['id']}"
            payload = {"exercise_id": attempt["exercise"]["id"], "answer": {"option_id": "a"}}
            self.assertEqual(a.post(root + "/answers", json=payload).json()["attempt"]["hearts"], 4)
            for suffix in ("", "/answers", "/complete", "/abandon"):
                response = b.get(root) if not suffix else b.post(root + suffix, json=payload if suffix == "/answers" else None)
                self.assertEqual(response.status_code, 404)
            self.assertIsNone(b.get("/api/me/active-attempt").json())
            self.assertEqual(b.get("/api/me").json(), before_b)
            self.assertEqual(a.get("/api/me/profile").json()["completed_skills"], 0)
            # A replacement client using the persisted token resumes the same profile.
            restored = TestClient(app, headers={"Authorization": "Bearer " + token_a})
            try:
                self.assertEqual(restored.get(root).json()["answered"], 1)
                self.assertEqual(restored.get("/api/me").json()["hearts"], 4)
            finally:
                restored.close()
            original = self.client
            self.client = a
            finished = self.solve(a.get(root).json())
            self.assertEqual(a.post(root + "/complete").json()["learner"]["total_xp"], 20)
            self.client = original
            self.assertEqual(b.get("/api/me").json(), before_b)
            path_b = b.get("/api/courses/1/path").json()
            self.assertEqual(path_b["units"][0]["skills"][0]["lessons"][1]["state"], "locked")
            board = a.get("/api/leaderboard").json()["entries"]
            self.assertEqual(sum(row["is_you"] for row in board), 1)
            self.assertNotIn(before_b["id"], [row["id"] for row in board])
            self.assertEqual(self.client.get("/api/me").json()["total_xp"], 120)
        finally:
            a.close()
            b.close()

    def test_clock_uses_learner_timezone(self):
        with self.sessions() as db:
            user = db.get(User, 1)
            self.assertEqual(local_today(user), datetime.now(ZoneInfo("Asia/Kolkata")).date())


if __name__ == "__main__":
    unittest.main()

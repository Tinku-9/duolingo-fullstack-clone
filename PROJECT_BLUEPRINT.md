# Duolingo assignment blueprint

## Scope and priorities

Build an original implementation using Next.js (TypeScript), FastAPI (Python), and SQLite. Deliver frontend/ and backend/, a documented public repository, and a working hosted demo. Complete the assignment's required hearts-based experience even if the current production Duolingo experience varies by platform or experiment.

Priority order: complete persisted lesson loop; all five exercise types; path progression and gamification; visual fidelity; deployment and documentation. No copied clone repository. Default learner, one Spanish course, seeded leaderboard, mocked refill and settings are sufficient.

## Screens and visual direction

- /learn: desktop left navigation, central winding lesson path, right status cards. Unit banners, circular raised nodes, progress rings, completed gold nodes, active green nodes, locked grey nodes, and small original mascot flourishes. Stats include course flag, streak, XP, gems, and hearts. Mobile uses a compact stats bar and bottom navigation.
- /lesson/[attemptId]: focused layout with exit control, progress bar, heart count, large exercise prompt, answer controls, and bottom check/feedback/continue bar. Green/red feedback, visible correct answer after a mistake, keyboard support, and clear disabled states.
- /leaderboard: seeded competitors plus the learner, ranked by weekly XP with explicit tie handling.
- /profile: learner identity, streak, total XP, completed skills, and simple earned achievement cards.
- /settings: clearly labeled placeholder settings and explanation of the default learner.
- Completion modal: XP, accuracy, daily goal, and next-step action. Out-of-hearts modal: mocked refill and return-to-path actions. Exit confirmation avoids accidental abandonment.

Use a light background, bright green primary actions, blue accents, orange streaks, red hearts, rounded borders, chunky button shadows, and generous spacing. Build reusable buttons, stat badges, cards, modal, progress bar, and feedback bar. Include focus indicators, sufficient contrast, and reduced-motion support.

Official references to inspect visually before implementing the screens:
- https://blog.duolingo.com/new-duolingo-home-screen-design/
- https://blog.duolingo.com/duolingo-101-how-to-learn-a-language-on-duolingo/
- https://blog.duolingo.com/how-duolingo-streak-builds-habit/

## Architecture

Frontend: Next.js App Router, TypeScript, CSS/Tailwind, reusable exercise components, and a small typed API client. Keep learner state synchronized with backend responses; local UI state holds selections and animations only.

Backend: FastAPI, SQLAlchemy, Pydantic, and SQLite. Separate routers, validation schemas, database models, and services for lessons/progression. Use transactions for grading and completion. Inject a clock into date-sensitive services so tests can simulate days without a public clock-changing endpoint.

Directories:

    frontend/src/app/
    frontend/src/components/{ui,learn,lesson}/
    frontend/src/lib/
    backend/app/{routers,schemas,services}/
    backend/app/models.py
    backend/app/database.py
    backend/app/seed.py
    backend/tests/

## Database relationships

Course -> Unit -> Skill -> Lesson -> Exercise, ordered within their parents.
User -> SkillProgress, LessonAttempt, DailyActivity.
LessonAttempt -> AttemptAnswer.

- users: id, display_name, timezone, hearts (0..5), gems, daily_goal_xp, created_at. Default timezone Asia/Kolkata.
- courses: id, title, language_code, source_language_code.
- units: id, course_id FK, title, description, position.
- skills: id, unit_id FK, title, position, icon_key.
- lessons: id, skill_id FK, title, position, xp_reward.
- exercises: id, lesson_id FK, type, prompt, public_payload JSON, answer_payload JSON, position. Public payload contains choices/tokens/pair items; answer payload stays server-side.
- skill_progress: id, user_id FK, skill_id FK, completed_at; unique(user_id, skill_id). Derive completed lesson counts from successful attempts and unique lesson IDs.
- lesson_attempts: id, user_id FK, lesson_id FK, status (active/completed/failed/abandoned), next_exercise_index, started_at, completed_at, awarded_xp. Attempt ID should be opaque.
- attempt_answers: id, attempt_id FK, exercise_id FK, submitted_payload JSON, is_correct, answered_at; unique(attempt_id, exercise_id). A submitted exercise cannot deduct hearts twice.
- daily_activity: id, user_id FK, activity_date, xp, lessons_completed; unique(user_id, activity_date). Derive total XP, weekly ranking, and streak from these rows to avoid inconsistent duplicate totals.

Foreign keys enabled, indexes on foreign keys and ordering columns, nonnegative XP and heart bounds. Seed data is idempotent and must not reset learner progress on startup. Seed 3 units, 2 skills per unit, 2 lessons per skill, and 5 exercises per lesson. Include all exercise types across the initial accessible lessons and a learner with one completed skill.

## API contract

All routes prefixed /api. Assume the default learner through one backend dependency; do not pretend this provides real authentication.

- GET /health: deployment health.
- GET /api/me: stats, hearts, daily goal, streak, and course.
- GET /api/courses/{courseId}/path: units, skills, lesson summaries, completion/progress and availability states.
- POST /api/lessons/{lessonId}/attempts: validate unlocks/hearts, start or return an active attempt, return current exercise without grading answers.
- GET /api/attempts/{attemptId}: persisted state and current exercise for refresh recovery.
- POST /api/attempts/{attemptId}/answers: exercise ID and typed answer payload; validate order, grade, persist once, return correctness, correction, hearts, progress, and updated status.
- POST /api/attempts/{attemptId}/complete: require every exercise answered and active/completed status; award once, update daily activity and skill progress atomically, return completion summary. Retried calls return the same award rather than granting more XP.
- POST /api/attempts/{attemptId}/abandon: stop an active attempt without rewards.
- POST /api/me/hearts/refill: explicitly mocked refill to five. Failed attempts remain failed; learner restarts the lesson.
- GET /api/leaderboard: seeded and current learner rankings for the current calendar week.
- GET /api/me/profile: stats and derived achievements.

Use clear 404 missing-resource, 409 progression/state conflict, and 422 invalid-input responses. Configure CORS from environment, never ship secret values in frontend code, and never expose answer_payload before grading.

## Lesson and gamification rules

1. Skills unlock linearly across units; a skill completes when both its lessons have at least one completed attempt. Lessons within a skill unlock sequentially. Previously completed lessons can be replayed.
2. Start requires at least one heart. Maximum five hearts shared across attempts. Permit one active attempt per learner to keep progression predictable.
3. Check submits once. Feedback appears before Continue advances the view. Wrong answers cost one heart, reveal the correction, and count as an answered exercise. No retry queue in the initial scope.
4. At zero hearts, mark the attempt failed immediately; no XP or lesson completion. Preserve previously earned progress.
5. Finish after all exercises are answered with hearts remaining. Award 20 XP per successful attempt, including intentional replay. Repeated requests for that same attempt award nothing extra.
6. Accuracy is correct submitted exercises divided by total submitted exercises. Pair matching submits the whole mapping once; wrong matching costs one heart per exercise, not per mismatched pair.
7. Word-bank answers submit token IDs to support repeated words. Matching submits item-ID mappings. Multiple choice submits option ID. Text answers normalize case, whitespace, and optional trailing punctuation; preserve accents and validate against curated accepted answers.
8. Daily activity uses the learner's timezone and is recorded on completion. First completion on a date counts as one active day. More completions that day do not increment the streak. A missed day breaks the current streak; yesterday's streak remains visible until today's completion or until the next missed-day boundary.
9. Daily goal: 40 XP. Weekly leaderboard uses Monday-to-Sunday in the learner's timezone; ties break deterministically by user ID. Gems are a fixed mocked balance.
10. Refill is explicitly mocked and available from the hearts control or failure modal. Automatic regeneration is outside initial scope because the assignment allows either refill or regeneration.

## Milestones and acceptance

M1: runnable services, health endpoint, seeded schema, and path response.
M2: one real persisted lesson from start through grading/completion and refresh recovery.
M3: all five exercise types, failure/refill, sequential unlocks, replay, and duplicate-request protection.
M4: daily activity/streak/goal, leaderboard, profile, and visual completion.
M5: production deployment with persistent SQLite storage, README and schema/API overview, final demo verification.

Test grading/heart idempotency, completion idempotency, locked lesson rejection, out-of-order answers, zero-heart failure, skill unlocking, timezone/day-boundary streak behavior, and idempotent seeding. Manually check keyboard interactions, desktop/mobile layouts, matching/token selection, refreshing an active lesson, error recovery, and the hosted frontend/backend flow.

## Deployment and schedule

Provision backend hosting that supports Python and a persistent writable SQLite volume; verify restart persistence. Frontend hosting must support the chosen Next.js configuration. Set NEXT_PUBLIC_API_URL and backend CORS origin. Hosting/account availability and the actual deadline are still unconfirmed. Avoid a serverless filesystem as the production database location.

Provisional 24 elapsed hours: blueprint 1h; setup/seed/deployment skeleton 2h; vertical lesson flow 3h; exercise coverage 2h; sleep 7h; gamification/profile 3h; visual polish 2h; verification/deployment 2h; documentation 1h; contingency 1h. Move the sleep block once the user supplies their preferred sleep window. Freeze bonuses until required flows pass.

The user will receive an explanation and a short review/demo at each milestone. Do not begin application code until the blueprint phase is finished and the user proceeds to implementation.

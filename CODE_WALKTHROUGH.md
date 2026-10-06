# First implementation walkthrough

## Start with the boundaries

The browser handles presentation: selected words, selected pairs, button states, and feedback animations. FastAPI decides whether an answer is correct and whether the learner earns XP. SQLite retains the course and learner state. Refreshing the browser therefore cannot reset hearts or completed lessons.

## Read these files in this order

1. `backend/app/models.py`: the SQL tables. Content follows Course → Unit → Skill → Lesson → Exercise. Learner history follows User → LessonAttempt → AttemptAnswer, plus DailyActivity and SkillProgress.
2. `backend/app/seed.py`: the actual Spanish course. Public exercise payloads contain display options; private payloads contain grading answers. Seeding checks for an existing course and does not overwrite progress.
3. `backend/app/grading.py`: plain Python functions for answer validation, grading, corrections, and streaks. These functions can be tested without running a web server.
4. `backend/app/services.py`: derives the path states and learner summaries from stored records.
5. `backend/app/main.py`: connects HTTP requests to the database and the lesson rules.
6. `frontend/src/lib/api.ts`: shared TypeScript data shapes and the API client.
7. `frontend/src/components/lesson-player.tsx`: coordinates the lesson screen. `exercise-input.tsx` renders the different answer controls.
8. `frontend/src/components/dashboard.tsx`: renders the path, stats, profile, and leaderboard.

## Follow one lesson

The learner selects an available node. The frontend calls `POST /api/lessons/{id}/attempts`. The backend checks the progression and hearts, then creates or resumes an attempt. It sends the current exercise without its answer.

The learner selects an answer and presses Check. The frontend sends `exercise_id` plus the selected payload. The backend locks the SQLite write transaction, checks whether that exercise already has a submitted answer, validates the payload, grades it, and saves the result. A mistake deducts one heart. The response contains the feedback and updated attempt state.

The frontend displays feedback before moving on. Continue updates the view to the next exercise. At the end, the frontend calls the completion endpoint. That transaction marks the attempt complete, awards XP to today's activity, and records skill completion if appropriate. Returning to the path reveals the next unlocked lesson.

## Why duplicate requests matter

A slow connection may lead someone to retry Check or Continue. Without protection, one wrong answer could deduct two hearts or one completed lesson could award double XP. The unique attempt/exercise record protects grading, and the attempt's completed state protects rewards. `BEGIN IMMEDIATE` ensures concurrent writes check the latest state before changing it.

## Why use daily activity

The daily rows record XP and completed lessons per local calendar date. They support daily goals, weekly rankings, total XP, and streaks without updating four separate counters that could disagree. Completing several lessons today increases XP, but today is still only one streak day.

## Deliberate simplifications

The learner is a shared default account, hearts refill for free through an explicitly mocked action, and the other leaderboard users are seeded. Wrong exercises reveal the correction and advance rather than adding a retry queue. These choices keep the assignment focused on its required lesson and persistence workflows.

## Explain these choices in the interview

- Why grading happens on the backend.
- How refresh recovery and duplicate submissions work.
- Why text normalization retains accents.
- How a calendar-day streak differs from a rolling 24-hour timer.
- Why the deployed SQLite database needs persistent storage.
- Which features are mocked and which are implemented end to end.

This is a first implementation. A successful source check is not proof of a working deployed app: dependency installation, API integration tests, the frontend build, and browser verification must also pass.

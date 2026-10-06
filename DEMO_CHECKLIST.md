# Local review and interview demo

Open http://127.0.0.1:3000/learn with both services running. The first skill is seeded complete. Browser verification has also completed the first lesson in First words, so that node now has a half-full ring.

1. Review the learning path: completed gold node, available green node with a progress ring, and grey locked nodes. Point out the streak, XP, gems, and hearts.
2. Open First words and complete its second lesson. Demonstrate one wrong answer and its feedback before proceeding. Hearts should drop by one.
3. Show word-bank translation, matching pairs, fill in the blank, and typing. Refresh midway to demonstrate server-side persistence.
4. Complete the lesson. The completion screen shows XP and accuracy. Returning to the path marks the skill complete and unlocks the next unit's first skill.
5. Visit Profile and Leaderboards. Explain that the learner's stats are live and the other leaderboard accounts are seeded.
6. Open hearts from the top bar and use the labeled demo refill. Explain the difference between a mocked refill and implemented heart-loss persistence.
7. Resize to mobile: stats remain accessible and navigation moves to the bottom.

## What to explain

Backend grading keeps answer validation and progress consistent. Transactions and unique constraints prevent double charges/rewards. Daily activity records allow XP totals, goals, weekly rankings, and calendar-based streaks to be derived consistently. SQLite is appropriate for this scoped assignment, and its file requires a persistent volume when hosted.

## Remaining delivery work

- Create and publish the public GitHub repository.
- Deploy FastAPI with persistent SQLite storage and the correct frontend CORS origin.
- Deploy Next.js with the hosted API URL configured before the build.
- Verify the hosted lesson flow and restart persistence.
- Add the public repository and demo URLs to the README.
- Rehearse explaining the implementation and its deliberate simplifications.

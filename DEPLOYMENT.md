# Deployment handoff

Local verification passes. The public GitHub repository and production services are not created yet. The user's existing accounts and hosting choice are still needed.

## Prepare the public repository

Publish this project with `frontend/`, `backend/`, the README, and the lockfiles. `.gitignore` excludes installed packages, local databases, browser profiles, screenshots, and secret environment files. The GitHub workflow runs backend tests and the frontend build on pushes and pull requests.

## Frontend configuration

Use a Next.js-compatible host. For Vercel, select `frontend` as the project root, use Node.js 22, and set `NEXT_PUBLIC_API_URL` to the public HTTPS backend URL before building. Use `npm ci` and `npm run build`.

Official references: [Vercel monorepo projects](https://vercel.com/docs/monorepos), [deployment environments](https://vercel.com/docs/deployments/environments).

## Backend configuration

Use a Python/Docker host with a persistent volume. `backend/Dockerfile` builds the API, installs the locked Python dependencies, and starts Uvicorn on the host's `PORT` environment variable. Select `backend` as the build context.

Example runtime configuration:

```text
DATABASE_URL=sqlite:////app/data/duolingo.db
CORS_ORIGINS=https://YOUR-FRONTEND-DOMAIN
```

Mount the persistent volume at `/app/data`. The application creates its schema and seeded course at startup. Use `/health` as the health check endpoint. Run one service instance with one worker for the scoped SQLite application.

Render supports persistent disks on paid services; its free web services cannot attach them. A free ephemeral filesystem would lose SQLite progress on redeploy/restart and would fail the assignment's persistence requirement. Confirm the hosting plan and cost with the user before provisioning any paid service.

Official references: [Render persistent disks](https://render.com/docs/disks), [free-service limitations](https://render.com/docs/free), [web-service configuration](https://render.com/docs/web-services).

## Verify the public demo

1. Load the path and start an available lesson.
2. Submit a wrong answer and confirm heart loss and correction feedback.
3. Complete the lesson and check the XP and next lesson unlock.
4. Refresh and open Profile and Leaderboards.
5. Restart the backend service and verify progress survives.
6. Check the mobile layout and hearts modal.
7. Verify the browser console has no API/CORS errors.
8. Add both the public GitHub URL and demo URL to the README and submission.

The Docker image and hosted service must still be verified on the selected host; successful local tests are not a deployment claim.

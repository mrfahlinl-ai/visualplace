# Phase 13 — Deployment (Docker Compose)

## Goal
Ship a production-capable container setup — without touching any live server
(deployment target: Docker Compose only, per the project decision).

## Delivered
- **`.dockerignore`** — lean build contexts (excludes node_modules, .venv,
  .next, var, .git, docs).
- **Backend image** (`docker/backend.Dockerfile`): multi-stage, non-root user,
  Pillow system libs + curl, container `HEALTHCHECK` on `/api/health`, and an
  **entrypoint that runs `alembic upgrade head` then starts uvicorn** with
  `--proxy-headers` (for use behind a reverse proxy).
- **Frontend image** (`docker/frontend.Dockerfile`): multi-stage Next.js
  standalone, non-root, with a **build arg `NEXT_PUBLIC_API_BASE_URL`** (public
  values are inlined at build time).
- **`docker-compose.yml`** (dev): db + redis + backend + frontend, upload volume,
  health-gated startup order.
- **`docker-compose.prod.yml`** (override): datastores not published, restart
  policies, env-driven Postgres credentials, app ports bound to `127.0.0.1`
  (front a reverse proxy / tunnel + TLS).
- **`docs/DEPLOY.md`** — configure → run (dev/prod) → migrations → backups →
  health → updates/rollback.

## Checks
- Both compose files parse cleanly (`services: db, redis, backend, frontend`).
- Entrypoint is LF-only and runs migrations + uvicorn.

## Honest note
- **Docker is not installed in this dev environment**, so the images were not
  built/run here — the Dockerfiles, entrypoint, and compose files are validated
  by syntax/parse only. Build them on a host with Docker via the commands in
  `docs/DEPLOY.md`. No changes were made to any live server (VPS/Cloudflare).

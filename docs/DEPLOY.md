# Deploying VisualPlace (Docker Compose)

VisualPlace ships as four containers — `db` (Postgres 16), `redis`, `backend`
(FastAPI), `frontend` (Next.js). The backend container applies database
migrations on startup, then serves the API.

## 1. Prerequisites
- Docker Engine + Docker Compose v2 on the host.
- Outbound network (for the AI vision provider and OSM/Nominatim geocoding).

## 2. Configure
```bash
cp .env.example .env
```
Set at minimum:
- `SECRET_KEY` — a long random string (salts audit IP hashes).
- `AI_API_KEY` — your Anthropic API key (required for the vision pipeline).
- `POSTGRES_USER` / `POSTGRES_PASSWORD` — production DB credentials (prod override).
- `NEXT_PUBLIC_API_BASE_URL` — the **public** URL the browser uses to reach the
  backend (baked into the frontend at build time), e.g. `https://api.example.com`.

Leave `MAP_PROVIDER=osm` and `SEARCH_PROVIDER=none` to run with zero paid map/search keys.

## 3. Run

**Development** (datastores exposed on localhost, hot values):
```bash
docker compose up --build
```
- Frontend → http://localhost:3000
- Backend  → http://localhost:8000 (docs at `/docs`)

**Production** (datastores not published; restart policies; localhost-bound app ports):
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
Put a reverse proxy or tunnel (nginx, Caddy, Cloudflare Tunnel) in front of the
localhost-bound `frontend` (:3000) and `backend` (:8000) ports and terminate TLS
there. In production the backend disables `/docs` and enables HSTS automatically.

## 4. Migrations
Applied automatically by the backend entrypoint (`alembic upgrade head`) on each
start. To run manually:
```bash
docker compose exec backend alembic upgrade head
```

## 5. Data & backups
- `db_data` volume — Postgres data. Back up with `pg_dump`:
  ```bash
  docker compose exec db pg_dump -U "$POSTGRES_USER" visualplace > backup.sql
  ```
- `uploads_data` volume — uploaded images (auto-deleted per `RETENTION_HOURS`;
  not retained unless `RETAIN_IMAGES=true`).

## 6. Health & observability
- `GET /api/health` reports per-component status (database + providers); the
  backend container's `HEALTHCHECK` uses it.
- Logs are structured JSON in production (`LOG_JSON=true`); secrets are redacted.

## 7. Updating
```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
Migrations run on backend startup. Roll back a bad migration with
`docker compose exec backend alembic downgrade -1`.

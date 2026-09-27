# Phase 2 — Database + Backend Foundation

## Goal
A production-shaped async persistence layer: all domain tables, portable ORM
models, migrations, repositories, and a DB-backed health check — verified
without needing a running database in this environment.

## Delivered

### Async data layer
- `app/db/base_class.py` — `DeclarativeBase` + `UUIDPrimaryKeyMixin`
  (`sa.Uuid`, native on PG) + `TimestampMixin` (tz-aware `created_at`/`updated_at`).
- `app/db/types.py` — `JSONB_OR_JSON` (JSONB on PG, JSON elsewhere).
- `app/db/session.py` — async engine + `async_sessionmaker`, `get_session`
  dependency (commit/rollback), `check_database()` probe.
- `app/db/base.py` — Alembic metadata target (imports all models).

### Models (spec §26) — `app/models/`
`User`, `Analysis`, `UploadedImage`, `ImageMetadata`, `VisualClue`, `Location`,
`Candidate`, `CandidateEvidence`, `ApiUsage`, `SearchCache`, `AuditLog`, plus
`enums.py` (mode, status, confidence band, clue/candidate/evidence categories).
Relationships + cascades wired (analysis → image → exif, clues, candidates →
evidence). Privacy fields (`deleted_at`, `expires_at`, `retained`), hashes for
dedup, cost/audit tables that never store secrets or raw IPs.

### Migrations — Alembic (async)
- `alembic.ini` + async `alembic/env.py` (URL injected from settings, not
  hard-coded) + `script.py.mako`.
- `versions/0001_initial_schema.py` — full schema, imports the enum classes so
  values can't drift from the models; portable UUID PKs, JSONB, indexes, and a
  partial unique index on `locations(provider, provider_place_id)`.

### Repositories
- `BaseRepository[ModelT]` (PEP 695 generics) — get/add/list/delete.
- `AnalysisRepository` — `get_with_relations` (eager loads image/clues/candidates),
  `set_status`.

### Health
- `GET /api/health` now reports a `database` component (SELECT 1), degrading to
  `down` when unreachable without taking the API offline.

## Checks
- `ruff check app tests alembic` — clean.
- `pytest` — 8 passed, incl. an ORM-graph roundtrip (analysis + image + exif +
  clue + candidate + evidence) on in-memory SQLite (`aiosqlite`).
- `alembic upgrade head --sql` — renders valid PostgreSQL DDL for all 11 tables
  (offline; no live DB needed to validate).

## Notes
- To apply against a real DB: `cp .env.example .env` → start Postgres →
  `alembic upgrade head` (from `backend/`).
- `mypy --strict` is configured but deferred to the testing phase (Phase 11);
  ruff + pytest are the gating checks for now.

# Phase 1 — Architecture + Project Initialization

## Goal
Stand up a clean, production-shaped monorepo with both services booting, config
driven entirely by environment variables, provider abstractions in place, and
green checks — without faking any external integration.

## Delivered

### Repo & tooling
- New git repo at `Desktop/VisualPlace`.
- `.gitignore` (secrets, Python, Node), `.env.example` (fully documented),
  `docker-compose.yml` + `docker/{backend,frontend}.Dockerfile`.
- `README.md` with setup, commands, roadmap, principles.

### Backend (FastAPI, Python 3.12)
- App factory (`app/main.py`) with lifespan startup logging, CORS, error
  handlers, `/api` router mount.
- **Env-driven config** (`app/core/config.py`): app, datastores, AI/map/search
  provider selection, upload limits, retention/privacy, rate/quota. Nothing
  reads `os.environ` directly.
- **Structured logging** (`app/core/logging.py`) with secret redaction.
- **Structured errors** (`app/core/errors.py`): single `{"error":{code,message}}`
  envelope; typed exceptions per failure mode.
- **Provider abstractions** (`app/services/providers/`): `AIVisionProvider`,
  `MapProvider`, `SearchProvider` ABCs + provider-agnostic result models; a
  registry selecting concrete impls from config.
  - Anthropic vision (default), OSM map (keyless default), null search (default).
  - Real external calls are **clearly marked integration points** for later
    phases — they raise honest errors, never fabricated results.
- `GET /api/health` reports per-provider status, degrading gracefully.
- Tests (`pytest`): health endpoint, error envelope, config parsing.

### Frontend (Next.js 16, TS, Tailwind 4)
- Design tokens with **light/dark** mode (class-based, persisted, no-flash init).
- Premium homepage hero + pipeline strip + upload CTA placeholder (full uploader
  is Phase 3).
- SEO: metadata, Open Graph, Twitter cards, `robots.ts`, `sitemap.ts`.
- Accessibility baseline: focus-visible rings, ARIA labels, reduced-motion.
- `next.config.ts` set to `standalone` output for lean Docker images.

## Checks
- Backend: `ruff check` clean · `pytest` 4 passed.
- Frontend: `next build` succeeds · TypeScript clean.

## Deferred to later phases (intentionally)
- DB models/migrations (Phase 2), upload endpoint (Phase 3), the real Anthropic
  vision call (Phase 4), EXIF/OCR (Phase 5), candidates (Phase 6), map/search
  clients (Phase 7), verification (Phase 8), result UI (Phase 9).

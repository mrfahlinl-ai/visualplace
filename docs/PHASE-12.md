# Phase 12 — Performance

## Goal
Keep the app fast and cheap under load (spec §25/§39), and make the cost/perf
measures explicit.

## Added this phase
- **Response compression**: `GZipMiddleware` (min 600 bytes) shrinks JSON result
  payloads (candidates + evidence can be sizeable).
- **DB connection pooling**: configurable `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` on
  the async engine (skipped for SQLite in tests/dev).

## Already in place (earlier phases)
- **Progressive, staged pipeline** — cheap vision analysis first; expensive
  work (geocoding, verification) only for the capped set of top candidates
  (spec §25).
- **Image downscaling** before the vision model (`prepare_for_vision`), so large
  uploads don't inflate token cost/latency.
- **Search/geocode caching** (`search_cache`) — repeated landmarks/coords never
  re-hit the provider.
- **Candidate cap** (`MAX_CANDIDATES`) bounds downstream work.
- **DB indexes** on all hot columns (status, analysis_id FKs, hashes, cache key,
  expiries) from the initial migration.
- **Frontend**: the Leaflet map is a dynamic (`ssr:false`) import, so map JS
  loads only on the result page, not the homepage.

## Checks
- `ruff` clean · `pytest` **54 passed** (+1: large responses are gzip-encoded).

## Notes
- Geocoding stays sequential by design (Nominatim's ~1 req/s usage policy);
  caching makes repeat work free rather than parallelising external calls.

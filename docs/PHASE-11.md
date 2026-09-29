# Phase 11 — Testing

## Goal
Broaden automated coverage across the risk surface (spec §34) and stand up a
frontend test runner.

## Delivered

### Backend (pytest) — now **53 passing**
Added:
- **Storage**: LocalStorage save/load/exists/delete roundtrip, idempotent
  delete, and **path-traversal rejection**.
- **Image validation**: PNG/JPEG/WEBP magic-byte sniffing, sha256 + phash
  present, unsupported-type and empty rejection, and the **decompression-bomb
  guard**.
- **Rate limiting**: per-IP limit enforced (429), independent scopes.

Existing coverage (earlier phases): EXIF extraction, AI clue parsing +
injection-as-data, candidate generation + scoring, verification, geocoding +
cache, full pipeline (COMPLETED + UNKNOWN), upload integration, security headers
/ body cap / IP hashing, health + error envelope, ORM roundtrip.

### Frontend (Vitest) — **8 passing**
- `vitest` set up (`vitest.config.mts`, `npm test`), Node env, `@/` alias.
- Tests for `format` (confidence %, band metadata, place line) and `upload`
  (byte formatting, type/extension/size validation).

## Checks
- Backend `pytest` 53 passed, `ruff` clean.
- Frontend `vitest run` 8 passed; `next build` + TypeScript clean.

## Notes
- Frontend deps installed with `--legacy-peer-deps` (vitest's optional
  `@types/node` peer vs. the pinned v20) — a harmless resolution.

# Phase 3 — Image Upload System

## Goal
A secure, end-to-end upload path: validated image in → persisted analysis +
stored binary out, with a premium uploader UI — verified live in the browser.

## Delivered

### Backend
- **Storage abstraction** (`app/services/storage/`): `StorageProvider` ABC +
  `LocalStorage` (default, path-traversal safe, app-generated keys) + registry;
  S3/GCS reserved.
- **Secure image validation** (`app/services/images/validation.py`):
  magic-byte sniffing (real format, not the client's filename/Content-Type),
  size limit, decompression-bomb guard (`MAX_IMAGE_PIXELS` + dimension check),
  corruption check, sha256 + perceptual aHash. HEIC accepted (decoded when
  `pillow-heif` is present, otherwise stored without fabricated dimensions).
- **Analysis service** (`app/services/analysis_service.py`): create (validate →
  store → persist Analysis + UploadedImage, sets retention `expires_at`), get,
  and privacy delete (removes the stored binary + soft-deletes the row).
- **Rate limiter** (`app/core/ratelimit.py`): in-process fixed-window per IP —
  the foundation; Redis-backed version comes in the security phase.
- **Endpoints** (`app/api/routes/analyze.py`): `POST /api/analyze`,
  `GET /api/analyze/{id}`, `DELETE /api/analyze/{id}`, with a streaming size cap.

### Frontend
- **`ImageUploader`** (`components/image-uploader.tsx`): drag & drop, browse,
  **paste**, and **camera capture**; client-side type/size validation; preview
  with filename, size and pixel dimensions; remove; mode toggle (Identify /
  Find exact); optional hint; upload with loading + done/error states.
- API client (`lib/api.ts`), shared types (`lib/types.ts`), upload utils
  (`lib/upload.ts`). Homepage now hosts the real uploader.

## Checks
- Backend: `ruff` clean · `pytest` **13 passed** (added upload integration
  tests: create/fetch/delete, reject non-image → 415, reject empty → 422,
  404s — on shared in-memory SQLite + temp storage).
- Frontend: `next build` + TypeScript clean.
- **Live browser E2E** (backend on a SQLite dev DB): uploaded an image via the
  UI → cross-origin `POST /api/analyze` succeeded → "queued · pending",
  analysis id shown; no console errors. Direct API also verified via curl:
  create 201 → get 200 → invalid 422 → delete 204 → get 404.

## Notes
- The created analysis stays `pending`; the evidence pipeline (AI/EXIF/OCR/
  candidates/scoring) fills it in Phases 4–8.

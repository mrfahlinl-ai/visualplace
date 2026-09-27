# Phase 5 — EXIF + OCR

## Goal
Extract trustworthy metadata evidence (EXIF/GPS) *before* AI inference, and put
OCR behind a swappable interface — never claiming metadata the image lacks.

## Delivered

### EXIF (spec §9)
- `images/exif.py` — `extract_exif`: GPS lat/lng (with N/S/E/W sign handling and
  DMS→decimal), capture time (DateTimeOriginal → DateTime fallback), camera
  make/model, software, orientation. **GPS is validated** (range + null-island
  rejection); invalid coordinates set `gps_valid=False` and are not surfaced.
  Best-effort — malformed/absent EXIF never raises.
- Wired into `AnalysisService.create` as step 3, **before** any AI (spec §9):
  persists an `image_metadata` row per upload.
- `AnalysisRead.image.exif` surfaces `has_gps` / `gps_valid` / coords / capture
  time / camera to the UI — so it can honestly say "GPS metadata found" vs "not
  available" (spec §9/§32).

### OCR (spec §8)
- `services/ocr/` — `OCRProvider` ABC (`raw_text` verbatim + separate additive
  `normalized_text`, language, confidence — never silently "corrects" text),
  `NullOCRProvider` default (the vision model already transcribes sign text),
  registry. Tesseract / cloud OCR reserved as a swap-in behind the interface.

## Checks
- `ruff` clean · `pytest` **29 passed** (+5): valid GPS, S/W hemisphere signs,
  null-island invalid, no-EXIF → no GPS, corrupt bytes don't raise; upload test
  now asserts EXIF is surfaced with `has_gps=false` for a generated PNG.

## Notes
- OCR stays a no-op by default (zero extra deps/cost); sign text comes from the
  vision stage. GPS EXIF becomes a high-confidence candidate source in Phase 6.

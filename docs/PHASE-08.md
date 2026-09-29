# Phase 8 — Candidate Verification + Finalize

## Goal
Cross-check candidates against the other evidence, re-score, and select the
result with an honest confidence band — comfortable saying "unable to determine"
(spec §14/§13/§33).

## Delivered

- **Verifier** (`pipeline/verification.py`) — records corroboration and
  **contradictions** as first-class evidence (spec §14), all from data already
  gathered (no extra API cost):
  - Country consistency vs. vision country clues.
  - EXIF proximity (haversine): non-GPS candidates near the photo's GPS point are
    corroborated; far ones contradicted.
  - Geocoding corroboration for named candidates that resolved to a real place.
  Street-view/imagery comparison is intentionally left as a future enhancement,
  not faked.
- **Finalize** (`run_finalize_stage`) — re-scores every candidate (sum of signed
  evidence), ranks, and picks the result. Below-threshold top score → band
  `UNKNOWN` and **no final location** (no misleading pin, spec §17/§33). Otherwise
  sets confidence, band, an approximate-area radius by band, and `final_location`
  (creating a Location from coords if needed). Status → `COMPLETED`.
- **Orchestration** — `run_full_pipeline` chains vision → candidates → geocode →
  finalize (injectable providers for tests). New endpoint
  `POST /api/analyze/{id}/verify` runs it.
- **Explanation** (`pipeline/explanation.py`) — "why we think this" (spec §16)
  from the top candidate's matching evidence, with contradictions surfaced too;
  exposed on `AnalysisRead.explanation`, alongside `final_location`.

## Checks
- `ruff` clean · `pytest` **40 passed** (+4): haversine sanity; verification
  corroboration/contradiction; **full pipeline reaches a COMPLETED result** with
  band + final location + explanation; low-evidence image → `UNKNOWN` with no
  final location.
- A real bug was caught and fixed: freshly-persisted clues weren't reflected in
  the in-memory relationship (identity-map staleness) — now appended to the
  collection so candidate generation sees them.

## Notes
- The backend pipeline is now complete end-to-end. A live `verify` run needs
  `AI_API_KEY` (+ outbound network for geocoding); without a key the analysis is
  marked `failed` with a structured, honest error.

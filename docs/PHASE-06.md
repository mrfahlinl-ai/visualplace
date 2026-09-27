# Phase 6 — Candidate Generation

## Goal
Turn evidence into **multiple** scored candidate locations, each backed by
explainable evidence — never just the first AI guess (spec §12), with a
transparent, sum-of-evidence score (spec §13).

## Delivered

- `pipeline/scoring.py` — transparent scoring: a candidate's score is the sum of
  its signed evidence weights (matches +, contradictions −), clamped to [0,1];
  tunable base weights per evidence category (EXIF GPS dominates). `confidence_band`
  maps score → user-facing band and only lets validated GPS reach `EXACT_GPS`
  (spec §1/§33).
- `pipeline/candidate_generation.py` — `CandidateGenerator.generate`:
  - Validated **EXIF GPS** → top candidate (`source=exif`, real coords).
  - **Landmarks** → `source=ai` candidates; **geographic clues** → region
    candidates; **business** clues → `source=search` candidates (geocoded later).
  - De-dupes by name, scales weight by clue confidence, caps at `MAX_CANDIDATES`
    (cost control §25), ranks by score.
- `AnalysisService.run_candidate_stage` — reloads relations, persists candidates
  + evidence.
- API now returns `candidates[]` (with per-candidate `evidence[]`, rank-ordered)
  on `AnalysisRead`; repo eager-loads candidates→evidence and final_location.

## Checks
- `ruff` clean · `pytest` **34 passed** (+5): EXIF GPS tops ranking; named
  candidates without GPS have no coords yet; dedupe + cap; contradiction lowers
  score; confidence-band thresholds.

## Notes
- Named candidates carry no coordinates until geocoded against the map/place
  provider (Phase 7); scores are provisional and re-computed after verification
  (Phase 8).

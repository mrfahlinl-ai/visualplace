# Phase 9 — Result UI

## Goal
Turn a completed analysis into a premium, transparent result experience — a map,
an honest confidence badge, "why we think this", evidence, alternatives, and
location details (spec §16–18) — so the user always understands *why*.

## Delivered

- **`/result/[id]`** page: fetches the analysis, runs the pipeline
  (`POST /verify`) if still pending while showing staged progress (spec §6), then
  renders the result. Handles `failed` (incl. a clear "AI not configured" note)
  and network errors gracefully.
- **`ResultView`** — location header with place + **confidence badge** (band
  label + %, colour-toned), interactive map, "Why we think this" (matches ✓ /
  contradictions ✗), location details (address, region, coords, type, "open in
  map"), **alternative candidates** with scores, and a categorized evidence list.
  For `unknown`/no-location it shows "Unable to pinpoint" rather than a fake pin
  (spec §17/§33).
- **`MapView`** (Leaflet + OSM tiles, keyless, client-only): primary pin, an
  **accuracy-radius circle** when the location is approximate, candidate pins,
  auto-fit bounds.
- **`AnalysisProgress`** — staged, animated progress list.
- Homepage uploader now redirects to `/result/[id]` after upload; frontend
  `AnalysisRead` types extended (final_location, candidates+evidence, exif,
  explanation) to match the backend schema; backend surfaces `error` on the
  response.

## Checks
- `next build` + TypeScript clean; new dynamic route `/result/[id]`.
- **Live browser verification** (backend on dev SQLite, a real COMPLETED analysis
  seeded via the pipeline with stub providers): the result page renders
  "Sylhet, Bangladesh · Shahjalal Bridge", 41% **Approximate area**, the OSM map
  with the pin, the three evidence reasons, and full location details — **0
  console errors**.

## Notes
- Map provider is OSM tiles (keyless), consistent with `MAP_PROVIDER=osm`.
- A live run from the homepage needs the backend to have `AI_API_KEY`; otherwise
  the result page shows the honest "couldn't complete the analysis" state.

# Phase 7 — Maps + Place Search

## Goal
Resolve named candidates (landmark/region/business) to **real coordinates** and
reusable location records, with caching so the pipeline is cheap and rate-limit
friendly (spec §7/§25).

## Delivered

- **Real OSM/Nominatim provider** (`providers/map/osm_provider.py`, keyless):
  `search_places` (`/search` jsonv2 + addressdetails) and `reverse_geocode`
  (`/reverse`), mapping results to the provider-agnostic `Place`; descriptive
  User-Agent per Nominatim policy; HTTP errors → `ProviderUnavailableError`.
- **Response cache** (`services/cache.py`) backed by `search_cache`: sha256 keys,
  TTL (30d default), so the same landmark/coord never re-hits the service.
- **Geocoding stage** (`pipeline/geocoding.py` + `run_geocoding_stage`):
  forward-geocodes named candidates → fills coords/city/country + a de-duplicated
  `locations` row (reused by `provider_place_id`); reverse-geocodes EXIF-coord
  candidates to fill city/country. One bad geocode is logged and skipped — it
  never fails the run.

## Checks
- `ruff` clean · `pytest` **36 passed** (+2): forward + reverse geocode fill
  coords/city and create a Location; cache prevents a repeat provider call for
  the same landmark across analyses.
- The cache test surfaced (and fixed) a real bug: SQLite returns naive datetimes,
  so the TTL comparison raised — now normalised to UTC.

## Notes
- Live Nominatim calls need outbound network; tests use a mock provider so they
  run offline. Provider is swappable to Mapbox/Google via `MAP_PROVIDER`.
- Candidates now have coordinates; final scoring + result selection is Phase 8.

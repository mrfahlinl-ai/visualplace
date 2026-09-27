# Phase 4 — AI Image Analysis

## Goal
Turn an uploaded image into structured, confidence-scored visual **evidence**
(spec §7) via a real vision provider — safe against prompt injection and tuned
for cost — without ever asserting a location.

## Delivered

### Vision provider (real integration)
- `AnthropicVisionProvider.analyze_image` now makes the real Messages API call
  via `anthropic.AsyncAnthropic` (SDK 1.8.0): base64 image block placed before
  the trusted text instruction, usage captured for cost tracking, SDK/network
  errors normalised to `ProviderUnavailableError`. Client is built lazily and
  the provider stays behind the `AIVisionProvider` interface.
- Model is env-configurable (`AI_MODEL`); default **`claude-sonnet-5`** for the
  cheap Stage-1 vision pass (spec §25) — set to `claude-opus-5` for maximum
  capability.

### Pipeline (Stage 1)
- `pipeline/schemas.py` — the §7 clue schema (`VisionClues`), every observation
  carrying its own confidence; partial responses validate (missing = empty, not
  invented).
- `pipeline/prompts.py` — **injection-safe** system prompt (spec §24): image
  text is untrusted data to transcribe, never instructions; user hint carried as
  UNVERIFIED (spec §20); strict JSON-only instruction.
- `pipeline/vision_analysis.py` — `VisionAnalyzer.extract_clues`: calls the
  provider, tolerantly parses JSON (fences/prose), validates to `VisionClues`,
  surfaces parse failures as clean errors (no fabricated clues).
- `images/processing.py` — `prepare_for_vision`: downscale to
  `VISION_MAX_DIMENSION` + normalise format (cost control, spec §25/§39).
- `pipeline/persistence.py` + `AnalysisService.run_vision_stage` — flatten clues
  into `visual_clues` rows, record an `api_usage` row (tokens), advance status;
  failures mark the analysis `failed` with a structured error.

## Checks
- `ruff` clean · `pytest` **24 passed** (+11): JSON parse tolerance, schema
  mapping, injection-text-as-data, hint-as-unverified, and a full vision-stage
  persistence test on SQLite + temp storage with a canned provider.
- SDK path sanity-checked: `anthropic 1.8.0`, `AsyncAnthropic` present, provider
  builds its client (no live call — tests use mock providers, so no key/spend).

## Notes
- The stage is invoked via `run_vision_stage`; wiring it into an async
  post-upload pipeline (with candidate generation/scoring) comes in Phases 6–8.
  A live end-to-end run needs `AI_API_KEY` set.

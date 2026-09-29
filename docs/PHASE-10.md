# Phase 10 — Security

## Goal
Harden the API to production standards (spec §22), building on protections
already in place from earlier phases.

## Already in place (earlier phases)
- Input validation + typed error envelope; file upload security (magic-byte
  sniffing, size cap, decompression-bomb guard, corruption check); app-generated
  storage keys (no user filenames / path traversal); per-endpoint rate limiting;
  CORS allow-list; API keys server-side only + secret redaction in logs;
  prompt-injection defence (image text treated as untrusted data).
- **SSRF**: no user-supplied URLs are ever fetched — geocoding hits a fixed
  Nominatim host from text queries; web search is disabled by default.

## Added this phase
- **Security headers** middleware: `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`,
  `Cross-Origin-Resource-Policy`, `Permissions-Policy`, and HSTS in production.
- **Request-size guard** middleware: rejects bodies over `MAX_REQUEST_BYTES`
  (defence in depth above the per-upload cap) with a 413 envelope.
- **Audit logging** (spec §22/§35): `analysis.create` / `.verify` / `.delete`
  recorded to `audit_logs` with a **salted, hashed IP** — never the raw IP,
  never secrets.
- `SECRET_KEY` config (salts IP hashes); startup logs an error if left at the
  dev default in production.

## Checks
- `ruff` clean · `pytest` **43 passed** (+3): security headers present,
  oversized body → 413, `hash_ip` salted/deterministic/non-reversible. Audit
  writes are exercised by the existing create/verify/delete tests.

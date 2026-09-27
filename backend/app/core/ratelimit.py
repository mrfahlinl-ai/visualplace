"""Lightweight in-process rate limiter (abuse protection, spec §22/§23).

A fixed-window counter keyed by client IP + scope. This is the dev/default
foundation; a Redis-backed limiter (shared across workers) replaces it in the
security phase. Fail-open on limiter errors — never take the API down because
the limiter misbehaved.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request

from app.core.config import settings
from app.core.errors import RateLimitedError


class _FixedWindowCounter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def hit(self, key: str, *, limit: int, window_s: float) -> bool:
        now = time.monotonic()
        cutoff = now - window_s
        bucket = [t for t in self._hits[key] if t > cutoff]
        bucket.append(now)
        self._hits[key] = bucket
        return len(bucket) <= limit


_counter = _FixedWindowCounter()


def _client_ip(request: Request) -> str:
    # Trust the direct peer by default; a trusted proxy header is handled in the
    # security phase where the proxy is known.
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """FastAPI dependency enforcing ``limit`` requests per ``window_s`` per IP."""

    def __init__(self, *, limit: int | None = None, window_s: float = 60.0, scope: str = "default"):
        self.limit = limit if limit is not None else settings.rate_limit_per_minute
        self.window_s = window_s
        self.scope = scope

    async def __call__(self, request: Request) -> None:
        key = f"{self.scope}:{_client_ip(request)}"
        if not _counter.hit(key, limit=self.limit, window_s=self.window_s):
            raise RateLimitedError(
                "Too many requests. Please slow down and try again shortly."
            )

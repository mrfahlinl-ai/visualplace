"""Rate limiter tests (spec §22/§23)."""

from __future__ import annotations

import pytest

from app.core.errors import RateLimitedError
from app.core.ratelimit import RateLimiter


class _FakeClient:
    host = "198.51.100.7"


class _FakeRequest:
    client = _FakeClient()


async def test_limit_enforced_per_ip() -> None:
    rl = RateLimiter(limit=2, window_s=60, scope="test-scope-a")
    req = _FakeRequest()
    await rl(req)  # 1
    await rl(req)  # 2
    with pytest.raises(RateLimitedError):
        await rl(req)  # 3 → over limit


async def test_separate_scopes_independent() -> None:
    a = RateLimiter(limit=1, window_s=60, scope="test-scope-b")
    b = RateLimiter(limit=1, window_s=60, scope="test-scope-c")
    req = _FakeRequest()
    await a(req)
    await b(req)  # different scope, still allowed
    with pytest.raises(RateLimitedError):
        await a(req)

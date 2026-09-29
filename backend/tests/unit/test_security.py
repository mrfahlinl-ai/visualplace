"""Security middleware + helpers (spec §22/§35)."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.security import hash_ip
from app.main import create_app


async def _client() -> AsyncClient:
    transport = ASGITransport(app=create_app())
    return AsyncClient(transport=transport, base_url="http://test")


async def test_security_headers_present() -> None:
    async with await _client() as c:
        resp = await c.get(f"{settings.api_prefix}/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "no-referrer"


async def test_oversized_body_rejected() -> None:
    original = settings.max_request_bytes
    settings.max_request_bytes = 16  # tiny cap so a small body trips it
    try:
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(f"{settings.api_prefix}/analyze", content=b"x" * 64)
    finally:
        settings.max_request_bytes = original
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "IMAGE_TOO_LARGE"


def test_hash_ip_is_salted_and_not_raw() -> None:
    h = hash_ip("203.0.113.5")
    assert h is not None
    assert "203.0.113.5" not in h
    assert len(h) == 64  # sha256 hex
    assert hash_ip("203.0.113.5") == h  # deterministic
    assert hash_ip("203.0.113.6") != h
    assert hash_ip(None) is None

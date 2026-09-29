"""Performance-related middleware tests."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def test_large_response_is_gzipped() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        # OpenAPI schema is large (>600 bytes) and available outside production.
        resp = await c.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
    assert resp.status_code == 200
    assert resp.headers.get("content-encoding") == "gzip"

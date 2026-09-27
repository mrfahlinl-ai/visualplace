"""Health endpoint and config sanity checks (Phase 1)."""

from __future__ import annotations

from httpx import AsyncClient

from app.core.config import settings


async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get(f"{settings.api_prefix}/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["version"]
    names = {c["name"] for c in body["components"]}
    assert names == {"ai", "map", "search"}


async def test_unknown_route_returns_error_envelope(client: AsyncClient) -> None:
    resp = await client.get(f"{settings.api_prefix}/does-not-exist")
    assert resp.status_code == 404
    assert "error" in resp.json()
    assert resp.json()["error"]["code"]


def test_cors_origins_parse() -> None:
    assert "http://localhost:3000" in settings.cors_origin_list


def test_allowed_image_types_parse() -> None:
    assert "image/jpeg" in settings.allowed_image_type_set

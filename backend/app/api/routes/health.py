"""Health & readiness endpoints (spec §27: GET /api/health)."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.db.session import check_database
from app.schemas.common import HealthComponent, HealthResponse
from app.services.providers.registry import (
    get_ai_provider,
    get_map_provider,
    get_search_provider,
)

router = APIRouter(tags=["health"])


async def _component(name: str) -> HealthComponent:
    """Resolve and probe one component, degrading gracefully on any failure."""
    try:
        match name:
            case "database":
                ok = await check_database()
            case "ai":
                ok = await get_ai_provider().health()
            case "map":
                ok = await get_map_provider().health()
            case "search":
                ok = await get_search_provider().health()
            case _:
                ok = False
    except Exception as exc:  # not configured / unreachable
        status_str = "down" if name == "database" else "not_configured"
        return HealthComponent(name=name, status=status_str, detail=str(exc))
    return HealthComponent(name=name, status="ok" if ok else "degraded")


@router.get("/health", response_model=HealthResponse, summary="Service health")
async def health() -> HealthResponse:
    components = [await _component(n) for n in ("database", "ai", "map", "search")]
    # The service itself is up; providers may be degraded/not configured without
    # taking the whole API down.
    overall = "ok" if all(c.status == "ok" for c in components) else "degraded"
    return HealthResponse(
        status=overall,
        version=__version__,
        environment=settings.environment.value,
        components=components,
    )

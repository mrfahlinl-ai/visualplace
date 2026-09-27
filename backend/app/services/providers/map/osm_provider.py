"""OpenStreetMap (Nominatim) map/place provider — the keyless default.

Full geocoding/search behaviour (rate-limit-friendly querying, result mapping)
is implemented in Phase 7 (maps + place search). Phase 1 provides a working
health check so the app can report provider status, and clearly marks the
search/geocode integration points (spec §44).
"""

from __future__ import annotations

from app.services.providers.base import MapProvider, Place


class OSMMapProvider(MapProvider):
    name = "osm"

    def __init__(self, *, base_url: str = "https://nominatim.openstreetmap.org") -> None:
        self._base_url = base_url

    async def search_places(
        self,
        query: str,
        *,
        near: tuple[float, float] | None = None,
        country_code: str | None = None,
        limit: int = 5,
    ) -> list[Place]:
        # Implemented in Phase 7 (Nominatim /search with proper User-Agent + caching).
        raise NotImplementedError("OSMMapProvider.search_places is wired in Phase 7.")

    async def reverse_geocode(self, latitude: float, longitude: float) -> Place | None:
        # Implemented in Phase 7 (Nominatim /reverse).
        raise NotImplementedError("OSMMapProvider.reverse_geocode is wired in Phase 7.")

    async def health(self) -> bool:
        # Keyless provider; treated as available. A live reachability probe is
        # added alongside the real client in Phase 7.
        return True

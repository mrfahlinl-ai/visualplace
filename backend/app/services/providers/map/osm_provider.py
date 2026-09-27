"""OpenStreetMap (Nominatim) map/place provider — the keyless default.

Implements geocoding (`/search`) and reverse geocoding (`/reverse`) against the
public Nominatim API. Per Nominatim's usage policy we send a descriptive
User-Agent and keep requests minimal; the pipeline additionally caches results
(spec §25) so repeated queries never re-hit the service.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.errors import ProviderUnavailableError
from app.services.providers.base import MapProvider, Place


class OSMMapProvider(MapProvider):
    name = "osm"

    def __init__(self, *, base_url: str = "https://nominatim.openstreetmap.org") -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "User-Agent": f"{settings.app_name}/1.0 (visual-geolocation)",
            "Accept": "application/json",
        }

    def _to_place(self, item: dict) -> Place | None:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, TypeError, ValueError):
            return None
        addr = item.get("address", {}) or {}
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("state")
        return Place(
            name=item.get("name") or item.get("display_name", "").split(",")[0] or "Unknown",
            latitude=lat,
            longitude=lon,
            address=item.get("display_name"),
            city=city,
            country=addr.get("country"),
            country_code=(addr.get("country_code") or None) and addr["country_code"].upper(),
            place_type=item.get("type") or item.get("category"),
            provider=self.name,
            provider_place_id=str(item.get("place_id")) if item.get("place_id") else None,
            raw=None,
        )

    async def search_places(
        self,
        query: str,
        *,
        near: tuple[float, float] | None = None,
        country_code: str | None = None,
        limit: int = 5,
    ) -> list[Place]:
        params: dict[str, str | int] = {
            "q": query,
            "format": "jsonv2",
            "limit": limit,
            "addressdetails": 1,
        }
        if country_code:
            params["countrycodes"] = country_code.lower()
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=self._headers) as client:
                resp = await client.get(f"{self._base_url}/search", params=params)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderUnavailableError(
                f"Map provider (OSM) request failed: {type(exc).__name__}"
            ) from exc
        if not isinstance(data, list):
            return []
        return [p for item in data if (p := self._to_place(item)) is not None]

    async def reverse_geocode(self, latitude: float, longitude: float) -> Place | None:
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "addressdetails": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=self._headers) as client:
                resp = await client.get(f"{self._base_url}/reverse", params=params)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderUnavailableError(
                f"Map provider (OSM) reverse geocode failed: {type(exc).__name__}"
            ) from exc
        if not isinstance(data, dict) or "lat" not in data:
            return None
        return self._to_place(data)

    async def health(self) -> bool:
        # Keyless provider; treated as available without spending a request.
        return True

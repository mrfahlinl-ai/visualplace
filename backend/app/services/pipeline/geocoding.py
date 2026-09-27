"""Geocoding stage (spec §7 map/place search).

Resolves named candidates (landmark/region/business) to real coordinates via the
map/place provider, and reverse-geocodes coordinate-only candidates (EXIF GPS)
to fill in city/country. Results are cached (spec §25) and de-duplicated into
reusable ``locations`` rows.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.candidate import Candidate
from app.models.location import Location
from app.services.cache import get_cached, make_key, set_cached
from app.services.providers.base import MapProvider, Place

log = get_logger(__name__)


class GeocodingStage:
    def __init__(self, session: AsyncSession, provider: MapProvider) -> None:
        self.session = session
        self.provider = provider

    async def _get_or_create_location(self, place: Place) -> Location:
        if place.provider_place_id:
            existing = await self.session.scalar(
                select(Location).where(
                    Location.provider == place.provider,
                    Location.provider_place_id == place.provider_place_id,
                )
            )
            if existing is not None:
                return existing
        loc = Location(
            name=place.name,
            latitude=place.latitude,
            longitude=place.longitude,
            address=place.address,
            city=place.city,
            country=place.country,
            country_code=place.country_code,
            place_type=place.place_type,
            provider=place.provider,
            provider_place_id=place.provider_place_id,
        )
        self.session.add(loc)
        await self.session.flush()
        return loc

    def _apply_place(self, candidate: Candidate, place: Place, location: Location) -> None:
        candidate.latitude = place.latitude
        candidate.longitude = place.longitude
        candidate.city = place.city
        candidate.country = place.country
        candidate.country_code = place.country_code
        candidate.place_type = place.place_type
        candidate.location_id = location.id

    async def _forward(self, candidate: Candidate) -> None:
        key = make_key("geocode", self.provider.name, candidate.name)
        cached = await get_cached(self.session, key)
        if cached is not None:
            place_data = cached.get("place")
            place = Place(**place_data) if place_data else None
        else:
            places = await self.provider.search_places(candidate.name, limit=1)
            place = places[0] if places else None
            await set_cached(
                self.session,
                key=key,
                provider=self.provider.name,
                query=candidate.name,
                response={"place": place.model_dump() if place else None},
            )
        if place is not None:
            location = await self._get_or_create_location(place)
            self._apply_place(candidate, place, location)

    async def _reverse(self, candidate: Candidate) -> None:
        if candidate.latitude is None or candidate.longitude is None:
            return
        coords = f"{candidate.latitude:.5f},{candidate.longitude:.5f}"
        key = make_key("reverse", self.provider.name, coords)
        cached = await get_cached(self.session, key)
        if cached is not None:
            place_data = cached.get("place")
            place = Place(**place_data) if place_data else None
        else:
            place = await self.provider.reverse_geocode(candidate.latitude, candidate.longitude)
            await set_cached(
                self.session,
                key=key,
                provider=self.provider.name,
                query=f"{candidate.latitude},{candidate.longitude}",
                response={"place": place.model_dump() if place else None},
            )
        if place is not None:
            location = await self._get_or_create_location(place)
            candidate.city = candidate.city or place.city
            candidate.country = candidate.country or place.country
            candidate.country_code = candidate.country_code or place.country_code
            candidate.location_id = candidate.location_id or location.id

    async def resolve(self, candidates: list[Candidate]) -> None:
        for cand in candidates:
            try:
                if cand.latitude is None:
                    await self._forward(cand)
                elif cand.city is None:
                    await self._reverse(cand)
            except Exception as exc:  # noqa: BLE001 - one bad geocode must not fail the run
                log.warning("geocode_failed", candidate=cand.name, error=type(exc).__name__)
        await self.session.flush()

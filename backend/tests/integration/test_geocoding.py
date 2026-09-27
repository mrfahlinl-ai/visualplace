"""Geocoding stage tests (SQLite, mock map provider — no network).

Verifies named candidates get coordinates + a reusable Location, EXIF-coord
candidates get reverse-geocoded city/country, and the cache prevents repeat
provider calls (spec §25).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.models.analysis import Analysis
from app.models.candidate import Candidate
from app.models.enums import CandidateSource
from app.models.location import Location
from app.services.analysis_service import AnalysisService
from app.services.providers.base import MapProvider, Place


class FakeMapProvider(MapProvider):
    name = "fake"

    def __init__(self) -> None:
        self.search_calls = 0
        self.reverse_calls = 0

    async def search_places(self, query, *, near=None, country_code=None, limit=5):
        self.search_calls += 1
        if "bridge" in query.lower():
            return [
                Place(
                    name="Shahjalal Bridge",
                    latitude=24.8949,
                    longitude=91.8687,
                    city="Sylhet",
                    country="Bangladesh",
                    country_code="BD",
                    place_type="bridge",
                    provider=self.name,
                    provider_place_id="p123",
                )
            ]
        return []

    async def reverse_geocode(self, latitude, longitude):
        self.reverse_calls += 1
        return Place(
            name="Near point",
            latitude=latitude,
            longitude=longitude,
            city="Sylhet",
            country="Bangladesh",
            country_code="BD",
            provider=self.name,
            provider_place_id="rev1",
        )

    async def health(self) -> bool:
        return True


@pytest.fixture
async def session() -> AsyncIterator:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def _make_analysis(session) -> Analysis:
    analysis = Analysis()
    session.add(analysis)
    await session.flush()
    named = Candidate(analysis_id=analysis.id, name="Shahjalal Bridge", source=CandidateSource.AI)
    gps = Candidate(
        analysis_id=analysis.id,
        name="Photo GPS location",
        source=CandidateSource.EXIF,
        latitude=24.90,
        longitude=91.87,
    )
    session.add_all([named, gps])
    await session.flush()
    return analysis


async def test_forward_and_reverse_geocode(session) -> None:
    analysis = await _make_analysis(session)
    provider = FakeMapProvider()
    service = AnalysisService(session)
    await service.run_geocoding_stage(analysis, map_provider=provider)
    await session.commit()

    named = await session.scalar(
        select(Candidate).where(Candidate.name == "Shahjalal Bridge")
    )
    assert named.latitude == pytest.approx(24.8949)
    assert named.city == "Sylhet"
    assert named.location_id is not None

    gps = await session.scalar(select(Candidate).where(Candidate.source == CandidateSource.EXIF))
    assert gps.city == "Sylhet"  # filled by reverse geocode

    loc_count = await session.scalar(select(func.count()).select_from(Location))
    assert loc_count and loc_count >= 1


async def test_cache_prevents_repeat_calls(session) -> None:
    provider = FakeMapProvider()
    service = AnalysisService(session)

    a1 = await _make_analysis(session)
    await service.run_geocoding_stage(a1, map_provider=provider)
    await session.commit()
    assert provider.search_calls == 1

    # A different analysis with the SAME landmark name resolves from cache —
    # no new provider search call.
    a2 = await _make_analysis(session)
    await service.run_geocoding_stage(a2, map_provider=provider)
    await session.commit()
    assert provider.search_calls == 1

    named2 = await session.scalar(
        select(Candidate).where(
            Candidate.analysis_id == a2.id, Candidate.name == "Shahjalal Bridge"
        )
    )
    assert named2.latitude == pytest.approx(24.8949)  # coords came from cache

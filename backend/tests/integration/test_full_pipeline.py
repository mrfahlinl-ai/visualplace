"""End-to-end pipeline test (SQLite + temp storage, canned providers).

create → vision → candidates → geocode → finalize, with no API key / network.
Asserts the analysis reaches a COMPLETED result with a confidence band, a final
location, and a human explanation — and that a low-evidence image yields UNKNOWN
with no final location (spec §33).
"""

from __future__ import annotations

import io
import json
from collections.abc import AsyncIterator

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base_class import Base
from app.models.enums import AnalysisMode, AnalysisStatus, ConfidenceBand
from app.services.analysis_service import AnalysisService
from app.services.pipeline.explanation import build_explanation
from app.services.pipeline.vision_analysis import VisionAnalyzer
from app.services.providers.base import AIVisionProvider, MapProvider, Place, VisionResult
from app.services.storage.registry import get_storage

RICH = json.dumps(
    {
        "scene_type": "urban riverside",
        "country_clues": [{"observation": "Bangladesh", "confidence": 0.7}],
        "landmarks": [
            {"name": "Shahjalal Bridge", "confidence": 0.85, "evidence": ["bridge"]}
        ],
        "sign_text": [{"observation": "Sylhet", "confidence": 0.7}],
        "visual_description": "A river bridge.",
    }
)
POOR = json.dumps({"scene_type": "indoor room", "visual_description": "A plain wall."})


class VisionStub(AIVisionProvider):
    name = "stub"

    def __init__(self, content: str) -> None:
        self._content = content

    async def analyze_image(self, **kwargs) -> VisionResult:
        return VisionResult(provider="stub", model="stub-1", content=self._content)

    async def health(self) -> bool:
        return True


class MapStub(MapProvider):
    name = "mapstub"

    async def search_places(self, query, *, near=None, country_code=None, limit=5):
        if "bridge" in query.lower():
            return [
                Place(
                    name="Shahjalal Bridge", latitude=24.8949, longitude=91.8687,
                    city="Sylhet", country="Bangladesh", country_code="BD",
                    place_type="bridge", provider=self.name, provider_place_id="b1",
                )
            ]
        return []

    async def reverse_geocode(self, latitude, longitude):
        return None

    async def health(self) -> bool:
        return True


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (120, 90), (40, 100, 150)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
async def session(tmp_path) -> AsyncIterator:
    settings.storage_local_dir = str(tmp_path / "uploads")
    get_storage.cache_clear()
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
    get_storage.cache_clear()


async def test_pipeline_reaches_result(session) -> None:
    service = AnalysisService(session)
    analysis = await service.create(
        data=_png(), declared_content_type="image/png",
        mode=AnalysisMode.FIND_EXACT, hint="Bangladesh",
    )
    await session.commit()

    result = await service.run_full_pipeline(
        analysis,
        analyzer=VisionAnalyzer(VisionStub(RICH)),
        map_provider=MapStub(),
    )
    await session.commit()

    assert result.status == AnalysisStatus.COMPLETED
    assert result.confidence_band is not None
    assert result.confidence and result.confidence > 0
    assert result.final_location_id is not None

    top = min(result.candidates, key=lambda c: c.rank or 999)
    assert top.name == "Shahjalal Bridge"
    assert top.latitude == pytest.approx(24.8949)

    explanation = build_explanation(result)
    assert explanation and any("landmark" in r.lower() for r in explanation)


async def test_low_evidence_is_unknown(session) -> None:
    service = AnalysisService(session)
    analysis = await service.create(
        data=_png(), declared_content_type="image/png", mode=AnalysisMode.IDENTIFY, hint=None
    )
    await session.commit()

    result = await service.run_full_pipeline(
        analysis,
        analyzer=VisionAnalyzer(VisionStub(POOR)),
        map_provider=MapStub(),
    )
    await session.commit()

    assert result.status == AnalysisStatus.COMPLETED
    assert result.confidence_band == ConfidenceBand.UNKNOWN
    assert result.final_location_id is None
    assert "couldn't" in " ".join(build_explanation(result)).lower()

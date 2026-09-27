"""Vision stage persistence test (SQLite + temp storage, canned provider).

Creates a real analysis (image stored), runs the vision stage with a fake
provider, and verifies clue rows + api_usage are persisted and the graph reads
back — without any API key or network.
"""

from __future__ import annotations

import io
import json
from collections.abc import AsyncIterator

import pytest
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base_class import Base
from app.models.clue import VisualClue
from app.models.enums import AnalysisMode, ClueCategory
from app.models.system import ApiUsage
from app.services.analysis_service import AnalysisService
from app.services.pipeline.vision_analysis import VisionAnalyzer
from app.services.providers.base import AIVisionProvider, VisionResult
from app.services.storage.registry import get_storage

CANNED = json.dumps(
    {
        "scene_type": "urban street",
        "landmarks": [
            {"name": "Shahjalal Bridge", "confidence": 0.82, "evidence": ["silhouette"]}
        ],
        "sign_text": [{"observation": "Sylhet", "confidence": 0.7}],
        "possible_regions": [{"observation": "Sylhet, BD", "confidence": 0.6}],
        "visual_description": "River bridge.",
    }
)


class CannedProvider(AIVisionProvider):
    name = "canned"

    async def analyze_image(self, **kwargs) -> VisionResult:
        return VisionResult(
            provider=self.name, model="canned-1", content=CANNED,
            input_tokens=120, output_tokens=64,
        )

    async def health(self) -> bool:
        return True


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (100, 80), (30, 90, 160)).save(buf, format="PNG")
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


async def test_vision_stage_persists_clues(session) -> None:
    service = AnalysisService(session)
    analysis = await service.create(
        data=_png(),
        declared_content_type="image/png",
        mode=AnalysisMode.IDENTIFY,
        hint="Sylhet",
    )
    await session.commit()

    await service.run_vision_stage(
        analysis, analyzer=VisionAnalyzer(CannedProvider())
    )
    await session.commit()

    clue_count = await session.scalar(
        select(func.count()).select_from(VisualClue).where(
            VisualClue.analysis_id == analysis.id
        )
    )
    assert clue_count and clue_count >= 4

    landmark = await session.scalar(
        select(VisualClue).where(
            VisualClue.analysis_id == analysis.id,
            VisualClue.category == ClueCategory.LANDMARK,
        )
    )
    assert landmark is not None
    assert landmark.value == "Shahjalal Bridge"
    assert landmark.extra == {"evidence": ["silhouette"]}

    usage = await session.scalar(
        select(ApiUsage).where(ApiUsage.analysis_id == analysis.id)
    )
    assert usage is not None
    assert usage.operation == "vision_analysis"
    assert usage.input_tokens == 120


async def test_vision_stage_failure_marks_failed(session) -> None:
    class BadProvider(AIVisionProvider):
        name = "bad"

        async def analyze_image(self, **kwargs) -> VisionResult:
            return VisionResult(provider="bad", model="x", content="not json")

        async def health(self) -> bool:
            return True

    service = AnalysisService(session)
    analysis = await service.create(
        data=_png(), declared_content_type="image/png", mode=AnalysisMode.IDENTIFY, hint=None
    )
    await session.commit()

    await service.run_vision_stage(analysis, analyzer=VisionAnalyzer(BadProvider()))
    await session.commit()

    assert analysis.status.value == "failed"
    assert analysis.error_code == "ANALYSIS_FAILED"

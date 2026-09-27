"""Analysis repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.analysis import Analysis
from app.models.enums import AnalysisStatus
from app.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository[Analysis]):
    model = Analysis

    async def get_with_relations(self, id_: uuid.UUID) -> Analysis | None:
        result = await self.session.execute(
            select(Analysis)
            .where(Analysis.id == id_)
            .options(
                selectinload(Analysis.image),
                selectinload(Analysis.clues),
                selectinload(Analysis.candidates),
            )
        )
        return result.scalar_one_or_none()

    async def set_status(self, analysis: Analysis, status: AnalysisStatus) -> Analysis:
        analysis.status = status
        await self.session.flush()
        return analysis

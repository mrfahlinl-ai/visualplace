"""Visual clue — one structured observation extracted from the image.

The structured analysis JSON (spec §7) is flattened into rows so clues are
queryable and each carries its own confidence and source. Uncertain
observations are marked, never presented as fact (spec §7).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JSONB_OR_JSON
from app.models.enums import ClueCategory, ClueSource

if TYPE_CHECKING:
    from app.models.analysis import Analysis


class VisualClue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "visual_clues"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )

    category: Mapped[ClueCategory] = mapped_column(
        Enum(ClueCategory, native_enum=False, length=20), nullable=False, index=True
    )
    source: Mapped[ClueSource] = mapped_column(
        Enum(ClueSource, native_enum=False, length=20), nullable=False
    )

    value: Mapped[str] = mapped_column(Text, nullable=False)
    # Model/OCR confidence in [0, 1]; None when not applicable.
    confidence: Mapped[float | None] = mapped_column(Float)

    # For OCR clues: preserve raw vs normalized text + language (spec §8).
    raw_text: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)

    extra: Mapped[dict | None] = mapped_column(JSONB_OR_JSON)

    analysis: Mapped[Analysis] = relationship(back_populates="clues")

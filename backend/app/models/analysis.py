"""Analysis — the central record of one geolocation run.

Ties together the uploaded image, extracted clues, generated candidates and the
final resolved location, plus status/error and privacy fields (soft delete,
retention).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AnalysisMode, AnalysisStatus, ConfidenceBand

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.clue import VisualClue
    from app.models.image import UploadedImage
    from app.models.location import Location


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyses"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    mode: Mapped[AnalysisMode] = mapped_column(
        Enum(AnalysisMode, native_enum=False, length=20),
        default=AnalysisMode.IDENTIFY,
        nullable=False,
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, native_enum=False, length=20),
        default=AnalysisStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Optional user-supplied search constraint (spec §20) — a hint, not a fact.
    hint: Mapped[str | None] = mapped_column(Text)

    # Final result (populated on completion).
    final_location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL")
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    confidence_band: Mapped[ConfidenceBand | None] = mapped_column(
        Enum(ConfidenceBand, native_enum=False, length=20)
    )

    # Failure info surfaced via the error envelope (spec §27/§32).
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)

    processing_ms: Mapped[int | None] = mapped_column(Integer)

    # Privacy (spec §21): soft delete + retention window for auto-purge.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    # Relationships
    image: Mapped[UploadedImage | None] = relationship(
        back_populates="analysis", uselist=False, cascade="all, delete-orphan"
    )
    clues: Mapped[list[VisualClue]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    candidates: Mapped[list[Candidate]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    final_location: Mapped[Location | None] = relationship(foreign_keys=[final_location_id])

"""Candidate locations + their evidence.

Multiple candidates are generated per analysis (spec §12) and scored
transparently (spec §13). Each piece of evidence either supports or contradicts
a candidate (spec §14) and carries the weight it contributed to the score, so
the final confidence can always be explained.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CandidateSource, EvidenceCategory, EvidenceKind

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.location import Location


class Candidate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidates"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="SET NULL")
    )

    name: Mapped[str] = mapped_column(String(512), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    city: Mapped[str | None] = mapped_column(String(256))
    country: Mapped[str | None] = mapped_column(String(256))
    country_code: Mapped[str | None] = mapped_column(String(2))
    place_type: Mapped[str | None] = mapped_column(String(128))

    source: Mapped[CandidateSource] = mapped_column(
        Enum(CandidateSource, native_enum=False, length=20), nullable=False
    )
    # Normalised score in [0, 1] and display rank (1 = most likely).
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, index=True)
    # Approximate-area radius in metres when the location is uncertain (spec §17).
    radius_m: Mapped[float | None] = mapped_column(Float)

    analysis: Mapped[Analysis] = relationship(back_populates="candidates")
    location: Mapped[Location | None] = relationship()
    evidence: Mapped[list[CandidateEvidence]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )


class CandidateEvidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_evidence"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )

    category: Mapped[EvidenceCategory] = mapped_column(
        Enum(EvidenceCategory, native_enum=False, length=32), nullable=False
    )
    kind: Mapped[EvidenceKind] = mapped_column(
        Enum(EvidenceKind, native_enum=False, length=16),
        default=EvidenceKind.MATCH,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Signed contribution to the candidate score (contradictions are negative).
    weight: Mapped[float | None] = mapped_column(Float)

    candidate: Mapped[Candidate] = relationship(back_populates="evidence")

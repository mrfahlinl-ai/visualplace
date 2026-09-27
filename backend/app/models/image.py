"""Uploaded image + its EXIF metadata.

The image binary lives in object/file storage (spec §21); the DB keeps only a
storage key plus small descriptors. Hashes support duplicate detection and
caching (spec §25). EXIF is stored in its own row and only the useful fields —
never more than needed (spec §21).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.analysis import Analysis


class UploadedImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uploaded_images"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True
    )

    storage_provider: Mapped[str] = mapped_column(String(20), default="local", nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)

    # Content + perceptual hashes for dedup / cache keys.
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    phash: Mapped[str | None] = mapped_column(String(64), index=True)

    retained: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    analysis: Mapped[Analysis] = relationship(back_populates="image")
    exif: Mapped[ImageMetadata | None] = relationship(
        back_populates="image", uselist=False, cascade="all, delete-orphan"
    )


class ImageMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Extracted EXIF fields (spec §9). Absence of GPS is recorded explicitly."""

    __tablename__ = "image_metadata"

    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("uploaded_images.id", ondelete="CASCADE"), unique=True, index=True
    )

    has_gps: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gps_latitude: Mapped[float | None] = mapped_column(Float)
    gps_longitude: Mapped[float | None] = mapped_column(Float)
    # Whether the GPS coordinates passed validation (spec §9: don't assume valid).
    gps_valid: Mapped[bool | None] = mapped_column(Boolean)

    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    camera_make: Mapped[str | None] = mapped_column(String(128))
    camera_model: Mapped[str | None] = mapped_column(String(128))
    software: Mapped[str | None] = mapped_column(String(128))
    orientation: Mapped[int | None] = mapped_column(Integer)

    image: Mapped[UploadedImage] = relationship(back_populates="exif")

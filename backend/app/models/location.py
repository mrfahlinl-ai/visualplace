"""Location — a resolved place record from a map/place provider.

Reusable across analyses and candidates. Only data from reliable sources is
stored (spec §18). A partial unique index (provider + provider_place_id) lets us
de-duplicate provider results; created in the migration.
"""

from __future__ import annotations

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JSONB_OR_JSON


class Location(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "locations"

    name: Mapped[str] = mapped_column(String(512), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(256))
    country: Mapped[str | None] = mapped_column(String(256))
    country_code: Mapped[str | None] = mapped_column(String(2), index=True)
    place_type: Mapped[str | None] = mapped_column(String(128))
    website: Mapped[str | None] = mapped_column(Text)

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_place_id: Mapped[str | None] = mapped_column(String(256))

    extra: Mapped[dict | None] = mapped_column(JSONB_OR_JSON)

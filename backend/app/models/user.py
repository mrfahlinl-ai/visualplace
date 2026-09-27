"""User model.

Accounts are a *future* feature (spec §42) — the app works fully anonymously —
but the table exists so analyses can be attributed once accounts land, without
a later migration reshuffle. Kept intentionally minimal (spec §26: no
unnecessary personal data).
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(String(320), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

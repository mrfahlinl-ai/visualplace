"""Declarative base and shared column mixins.

Types are chosen to be portable: :class:`sqlalchemy.Uuid` maps to native
``UUID`` on PostgreSQL and ``CHAR(32)`` elsewhere (so the unit-test SQLite
engine works), and enums are stored as ``VARCHAR`` + ``CHECK`` (``native_enum=
False``) rather than PostgreSQL enum types, which keeps migrations painless.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base for all ORM models."""


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

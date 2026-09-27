"""System/operational tables: API usage, search cache, audit log.

- ``api_usage`` tracks external calls + cost estimates for observability and
  cost control (spec §25, §35).
- ``search_cache`` caches provider responses by key to avoid repeat calls
  (spec §25).
- ``audit_logs`` records important actions; it never stores raw IPs or secrets
  (spec §22, §35) — IPs are hashed by the caller.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import JSONB_OR_JSON


class ApiUsage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_usage"

    analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("analyses.id", ondelete="SET NULL"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128))

    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    request_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cost_estimate_usd: Mapped[float | None] = mapped_column(Numeric(12, 6))
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class SearchCache(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "search_cache"

    cache_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[dict] = mapped_column(JSONB_OR_JSON, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("analyses.id", ondelete="SET NULL"), index=True
    )
    actor: Mapped[str | None] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    ip_hash: Mapped[str | None] = mapped_column(String(64))  # hashed, never raw
    extra: Mapped[dict | None] = mapped_column(JSONB_OR_JSON)

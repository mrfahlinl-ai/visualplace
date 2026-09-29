"""Audit logging for important actions (spec §22/§35).

Records who did what to which entity, with a hashed IP — never raw IPs, secrets,
or unnecessary personal data.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import AuditLog


async def record_audit(
    session: AsyncSession,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | str | None = None,
    analysis_id: uuid.UUID | None = None,
    ip_hash: str | None = None,
    extra: dict | None = None,
) -> None:
    session.add(
        AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            analysis_id=analysis_id,
            ip_hash=ip_hash,
            extra=extra,
        )
    )

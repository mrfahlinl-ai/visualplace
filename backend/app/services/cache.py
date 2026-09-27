"""Search/geocode response cache (spec §25).

Backed by the ``search_cache`` table so repeated provider queries (same landmark
across analyses, retries) don't re-hit external services — controlling both cost
and rate-limit pressure.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import SearchCache

DEFAULT_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days — place data is fairly stable


def make_key(*parts: str) -> str:
    raw = "\x1f".join(p.strip().lower() for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def get_cached(session: AsyncSession, key: str) -> dict | None:
    row = await session.scalar(select(SearchCache).where(SearchCache.cache_key == key))
    if row is None:
        return None
    exp = row.expires_at
    if exp is not None:
        # SQLite returns naive datetimes; normalise to UTC before comparing.
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < datetime.now(UTC):
            return None
    return row.response


async def set_cached(
    session: AsyncSession,
    *,
    key: str,
    provider: str,
    query: str,
    response: dict,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> None:
    expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
    existing = await session.scalar(select(SearchCache).where(SearchCache.cache_key == key))
    if existing is not None:
        existing.response = response
        existing.expires_at = expires_at
        return
    session.add(
        SearchCache(
            cache_key=key,
            provider=provider,
            query=query[:2000],
            response=response,
            expires_at=expires_at,
        )
    )

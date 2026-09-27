"""Integration tests for the analyze upload endpoints.

Runs the real FastAPI app with the DB dependency overridden to a shared
in-memory SQLite engine and storage pointed at a temp dir — so upload → fetch →
delete is exercised end-to-end without Postgres or object storage.
"""

from __future__ import annotations

import io
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base_class import Base
from app.db.session import get_session
from app.main import create_app
from app.services.storage.registry import get_storage


def _png_bytes(width: int = 64, height: int = 48, color=(10, 120, 200)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
async def client(tmp_path) -> AsyncIterator[AsyncClient]:
    # Storage → temp dir (reset the cached provider so it picks up the new path).
    settings.storage_local_dir = str(tmp_path / "uploads")
    get_storage.cache_clear()

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_session() -> AsyncIterator:
        async with maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await engine.dispose()
    get_storage.cache_clear()


async def test_upload_creates_analysis(client: AsyncClient) -> None:
    files = {"file": ("photo.png", _png_bytes(), "image/png")}
    resp = await client.post(
        f"{settings.api_prefix}/analyze", files=files, data={"mode": "find_exact"}
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["mode"] == "find_exact"
    assert body["image"]["mime_type"] == "image/png"
    assert body["image"]["width"] == 64 and body["image"]["height"] == 48

    # Fetch it back.
    got = await client.get(f"{settings.api_prefix}/analyze/{body['id']}")
    assert got.status_code == 200
    assert got.json()["id"] == body["id"]


async def test_upload_rejects_non_image(client: AsyncClient) -> None:
    files = {"file": ("evil.png", b"this is not an image", "image/png")}
    resp = await client.post(f"{settings.api_prefix}/analyze", files=files)
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


async def test_upload_rejects_empty(client: AsyncClient) -> None:
    files = {"file": ("empty.png", b"", "image/png")}
    resp = await client.post(f"{settings.api_prefix}/analyze", files=files)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_IMAGE"


async def test_delete_is_privacy_safe(client: AsyncClient) -> None:
    files = {"file": ("photo.png", _png_bytes(), "image/png")}
    created = (await client.post(f"{settings.api_prefix}/analyze", files=files)).json()
    aid = created["id"]

    deleted = await client.delete(f"{settings.api_prefix}/analyze/{aid}")
    assert deleted.status_code == 204

    # Gone afterwards.
    got = await client.get(f"{settings.api_prefix}/analyze/{aid}")
    assert got.status_code == 404


async def test_get_unknown_returns_404(client: AsyncClient) -> None:
    import uuid

    resp = await client.get(f"{settings.api_prefix}/analyze/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"

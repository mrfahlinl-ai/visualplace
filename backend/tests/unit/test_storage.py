"""LocalStorage provider tests (roundtrip + path-traversal safety)."""

from __future__ import annotations

import pytest

from app.core.errors import AppError
from app.services.storage.local import LocalStorage


async def test_roundtrip(tmp_path) -> None:
    store = LocalStorage(str(tmp_path))
    key = "analyses/abc/original.png"
    assert await store.exists(key) is False
    await store.save(key, b"hello", content_type="image/png")
    assert await store.exists(key) is True
    assert await store.load(key) == b"hello"
    await store.delete(key)
    assert await store.exists(key) is False


async def test_delete_is_idempotent(tmp_path) -> None:
    store = LocalStorage(str(tmp_path))
    await store.delete("nope/missing.png")  # must not raise


async def test_path_traversal_rejected(tmp_path) -> None:
    store = LocalStorage(str(tmp_path))
    with pytest.raises(AppError):
        await store.save("../escape.png", b"x", content_type="image/png")

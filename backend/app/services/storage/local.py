"""Local-filesystem storage provider (default).

Writes under ``settings.storage_local_dir``. Keys are app-generated and
validated to prevent path traversal — user filenames never touch the path
(spec §22: filename sanitization / path safety).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.errors import AppError, ErrorCode
from app.services.storage.base import StorageProvider


class LocalStorage(StorageProvider):
    name = "local"

    def __init__(self, root: str) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Reject absolute keys / traversal; keys are app-generated but validate anyway.
        candidate = (self._root / key).resolve()
        if not candidate.is_relative_to(self._root):
            raise AppError("Invalid storage key.", code=ErrorCode.VALIDATION_ERROR)
        return candidate

    async def save(self, key: str, data: bytes, *, content_type: str) -> None:
        path = self._resolve(key)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(_write)

    async def load(self, key: str) -> bytes:
        path = self._resolve(key)
        return await asyncio.to_thread(path.read_bytes)

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        await asyncio.to_thread(path.unlink, missing_ok=True)

    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(self._resolve(key).exists)

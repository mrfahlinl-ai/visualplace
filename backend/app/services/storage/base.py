"""Storage abstraction.

Image binaries live in pluggable storage (local disk by default; S3/GCS behind
the same interface — spec §3, §21). Nothing above this layer knows where bytes
physically live; it only holds a ``storage_key``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    name: str

    @abstractmethod
    async def save(self, key: str, data: bytes, *, content_type: str) -> None:
        ...

    @abstractmethod
    async def load(self, key: str) -> bytes:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete; must not raise if the key is already gone (idempotent)."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        ...

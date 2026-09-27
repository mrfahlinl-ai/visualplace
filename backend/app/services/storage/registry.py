"""Storage provider factory (config-driven)."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.errors import ProviderNotConfiguredError
from app.services.storage.base import StorageProvider
from app.services.storage.local import LocalStorage


@lru_cache
def get_storage() -> StorageProvider:
    match settings.storage_provider:
        case "local":
            return LocalStorage(settings.storage_local_dir)
        case "s3" | "gcs":
            raise ProviderNotConfiguredError(
                f"Storage provider '{settings.storage_provider}' is not yet "
                "implemented. Set STORAGE_PROVIDER=local."
            )
    raise ProviderNotConfiguredError(
        f"Unknown storage provider '{settings.storage_provider}'."
    )

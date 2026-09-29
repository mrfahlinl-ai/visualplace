"""Application configuration.

All behaviour that could differ between environments — and every external
provider choice (AI, maps, search) — is driven from here via environment
variables. Nothing downstream should read ``os.environ`` directly; it should
depend on :data:`settings` instead. This keeps the app vendor-neutral and
makes provider swaps a config change rather than a code change.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class AIProviderName(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class MapProviderName(StrEnum):
    OSM = "osm"          # OpenStreetMap / Nominatim — no key required
    MAPBOX = "mapbox"
    GOOGLE = "google"


class SearchProviderName(StrEnum):
    NONE = "none"        # web search disabled
    TAVILY = "tavily"
    SERPAPI = "serpapi"
    BING = "bing"


class Settings(BaseSettings):
    """Environment-driven settings.

    Reads from process environment and, for local dev, an ``.env`` file at the
    repo root or the backend directory (process env always wins).
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "VisualPlace"
    environment: Environment = Environment.LOCAL
    debug: bool = False
    api_prefix: str = "/api"
    log_level: str = "INFO"
    log_json: bool = True  # structured JSON logs; set False for pretty dev logs

    # Server-side secret. Used to hash IPs for audit logs (never stored raw).
    # MUST be overridden in production.
    secret_key: str = "dev-insecure-change-me"  # noqa: S105 - dev default, override in prod
    # Hard cap on request body size (bytes); a global guard above the upload cap.
    max_request_bytes: int = 20 * 1024 * 1024

    # CORS: comma-separated origins allowed to call the API.
    cors_origins: str = "http://localhost:3000"

    # --- Datastores ---
    database_url: str = "postgresql+asyncpg://visualplace:visualplace@localhost:5432/visualplace"
    redis_url: str = "redis://localhost:6379/0"

    # --- AI provider (vision) ---
    ai_provider: AIProviderName = AIProviderName.ANTHROPIC
    ai_api_key: str | None = None
    ai_model: str = "claude-sonnet-5"  # vision-capable default; overridable per env
    ai_max_output_tokens: int = 2048
    ai_timeout_seconds: float = 60.0

    # --- Map / place provider ---
    map_provider: MapProviderName = MapProviderName.OSM
    map_api_key: str | None = None
    # Public token exposed to the browser for client-side map rendering only
    # (tile display). Never put a secret/server key here.
    map_public_key: str | None = None

    # --- Web / image search provider ---
    search_provider: SearchProviderName = SearchProviderName.NONE
    search_api_key: str | None = None
    image_search_api_key: str | None = None

    # --- Uploads / limits ---
    max_upload_bytes: int = 15 * 1024 * 1024  # 15 MB
    allowed_image_types: str = "image/jpeg,image/png,image/webp,image/heic,image/heif"
    # Guard against decompression bombs: reject images whose pixel count exceeds this.
    max_image_pixels: int = 40_000_000
    # Images are resized before being sent to the (expensive) vision model.
    vision_max_dimension: int = 1568

    # --- Storage / retention ---
    storage_provider: str = "local"          # local | s3 | gcs
    storage_bucket: str | None = None
    storage_local_dir: str = "./var/uploads"
    # Automatic deletion window for uploaded images (privacy §21). 0 = delete
    # immediately after analysis completes.
    retention_hours: int = 24
    retain_images: bool = False              # keep images only if explicitly enabled

    # --- Abuse / cost control ---
    rate_limit_per_minute: int = 20
    analyze_daily_quota: int = 200

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_image_type_set(self) -> set[str]:
        return {t.strip().lower() for t in self.allowed_image_types.split(",") if t.strip()}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton (safe to import anywhere)."""
    return Settings()


settings = get_settings()

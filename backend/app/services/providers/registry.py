"""Provider registry / factory.

Resolves the configured AI, map and search providers from settings and hands
back the abstract interface. This is the *only* place that knows which concrete
class maps to which config value, so adding a vendor is a localized change.

Providers are cached per-process. Unknown/unsupported selections fail loudly at
resolution time rather than silently degrading.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import (
    AIProviderName,
    MapProviderName,
    SearchProviderName,
    settings,
)
from app.core.errors import ProviderNotConfiguredError
from app.services.providers.ai.anthropic_provider import AnthropicVisionProvider
from app.services.providers.base import AIVisionProvider, MapProvider, SearchProvider
from app.services.providers.map.osm_provider import OSMMapProvider
from app.services.providers.search.null_provider import NullSearchProvider


@lru_cache
def get_ai_provider() -> AIVisionProvider:
    match settings.ai_provider:
        case AIProviderName.ANTHROPIC:
            return AnthropicVisionProvider(
                api_key=settings.ai_api_key, model=settings.ai_model
            )
        case AIProviderName.OPENAI | AIProviderName.GOOGLE:
            # Interfaces reserved; concrete SDK wiring added when needed. Fail
            # clearly instead of pretending to support it.
            raise ProviderNotConfiguredError(
                f"AI provider '{settings.ai_provider}' is not yet implemented. "
                "Set AI_PROVIDER=anthropic."
            )
    raise ProviderNotConfiguredError(f"Unknown AI provider '{settings.ai_provider}'.")


@lru_cache
def get_map_provider() -> MapProvider:
    match settings.map_provider:
        case MapProviderName.OSM:
            return OSMMapProvider()
        case MapProviderName.MAPBOX | MapProviderName.GOOGLE:
            raise ProviderNotConfiguredError(
                f"Map provider '{settings.map_provider}' is not yet implemented. "
                "Set MAP_PROVIDER=osm."
            )
    raise ProviderNotConfiguredError(f"Unknown map provider '{settings.map_provider}'.")


@lru_cache
def get_search_provider() -> SearchProvider:
    match settings.search_provider:
        case SearchProviderName.NONE:
            return NullSearchProvider()
        case SearchProviderName.TAVILY | SearchProviderName.SERPAPI | SearchProviderName.BING:
            raise ProviderNotConfiguredError(
                f"Search provider '{settings.search_provider}' is not yet implemented. "
                "Set SEARCH_PROVIDER=none to disable web search."
            )
    raise ProviderNotConfiguredError(f"Unknown search provider '{settings.search_provider}'.")

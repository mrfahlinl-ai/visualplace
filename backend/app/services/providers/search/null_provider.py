"""No-op search provider.

Web/image search is optional (spec §15) and disabled by default so the app runs
with zero extra API keys and no surprise cost. Selecting SEARCH_PROVIDER=none
uses this provider, which returns no results rather than failing.
"""

from __future__ import annotations

from app.services.providers.base import SearchProvider, SearchResult


class NullSearchProvider(SearchProvider):
    name = "none"

    async def web_search(self, query: str, *, limit: int = 5) -> list[SearchResult]:
        return []

    async def image_search(self, query: str, *, limit: int = 5) -> list[SearchResult]:
        return []

    async def health(self) -> bool:
        return True

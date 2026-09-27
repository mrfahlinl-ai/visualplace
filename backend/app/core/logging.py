"""Structured logging setup (structlog).

Emits JSON in production for observability pipelines and pretty console logs in
dev. Never log secrets: a redaction processor drops known-sensitive keys before
anything is rendered (spec §35).
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.core.config import settings

# Keys whose values must never reach the logs.
_SENSITIVE_KEYS = {
    "api_key",
    "ai_api_key",
    "map_api_key",
    "search_api_key",
    "image_search_api_key",
    "authorization",
    "password",
    "token",
    "secret",
    "cookie",
}


def _redact_sensitive(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***redacted***"
    return event_dict


def configure_logging() -> None:
    """Configure structlog + stdlib logging once at startup."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _redact_sensitive,
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_json:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)

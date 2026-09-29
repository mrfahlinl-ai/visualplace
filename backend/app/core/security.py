"""Security middleware and helpers (spec §22).

- ``SecurityHeadersMiddleware`` adds hardening response headers.
- ``MaxBodySizeMiddleware`` rejects oversized requests early (defence in depth
  above the per-endpoint upload cap).
- ``hash_ip`` produces a salted, non-reversible IP hash for audit logs, so we
  never store raw client IPs (spec §21/§35).
"""

from __future__ import annotations

import hashlib

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.errors import ErrorCode

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-site",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject requests whose declared body exceeds the configured cap."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": ErrorCode.IMAGE_TOO_LARGE,
                                "message": "Request body exceeds the maximum allowed size.",
                            }
                        },
                    )
            except ValueError:
                pass
        return await call_next(request)


def hash_ip(ip: str | None) -> str | None:
    """Salted SHA-256 of a client IP for audit logging (never the raw IP)."""
    if not ip:
        return None
    return hashlib.sha256(f"{settings.secret_key}:{ip}".encode()).hexdigest()

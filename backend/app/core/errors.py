"""Structured application errors and FastAPI exception handlers.

All errors surface to clients in a single, predictable shape (spec §27)::

    {"error": {"code": "IMAGE_TOO_LARGE", "message": "..."}}

Domain code raises :class:`AppError` (or a subclass); handlers translate those
— and unexpected exceptions — into that envelope without leaking internals.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

log = get_logger(__name__)


class ErrorCode:
    """Stable, client-facing error codes."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    INVALID_IMAGE = "INVALID_IMAGE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """Base class for expected, client-facing errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = ErrorCode.INTERNAL_ERROR

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = ErrorCode.NOT_FOUND


class RateLimitedError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = ErrorCode.RATE_LIMITED


class ImageTooLargeError(AppError):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    code = ErrorCode.IMAGE_TOO_LARGE


class UnsupportedMediaTypeError(AppError):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    code = ErrorCode.UNSUPPORTED_MEDIA_TYPE


class InvalidImageError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = ErrorCode.INVALID_IMAGE


class ProviderNotConfiguredError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = ErrorCode.PROVIDER_NOT_CONFIGURED


class ProviderUnavailableError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = ErrorCode.PROVIDER_UNAVAILABLE


def _envelope(code: str, message: str, details: dict | None = None) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_req: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.details or None),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_req: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_envelope(
                ErrorCode.VALIDATION_ERROR,
                "Request validation failed.",
                {"errors": exc.errors()},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(_req: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = ErrorCode.NOT_FOUND if exc.status_code == 404 else ErrorCode.INTERNAL_ERROR
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code, str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_req: Request, exc: Exception) -> JSONResponse:
        # Log the real error; return a generic message so internals never leak.
        log.error("unhandled_exception", error=str(exc), error_type=type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope(ErrorCode.INTERNAL_ERROR, "An unexpected error occurred."),
        )

"""Unified exception hierarchy for the application.

All services raise typed exceptions instead of returning error dicts.
The global exception handler in main.py catches AppException subclasses
and returns a standardized JSON response.
"""
from __future__ import annotations


class AppException(Exception):
    """Base application exception.

    Attributes:
        status_code: HTTP status code to return.
        detail: Human-readable error message.
        error_code: Machine-readable error code string.
    """

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str = "", *, error_code: str | None = None):
        self.detail = detail
        if error_code is not None:
            self.error_code = error_code
        super().__init__(detail)


class NotFoundException(AppException):
    """Resource not found (404)."""

    status_code = 404
    error_code = "NOT_FOUND"


class ValidationError(AppException):
    """Invalid input or bad request parameters (422)."""

    status_code = 422
    error_code = "VALIDATION_ERROR"


class BusinessError(AppException):
    """Business rule violation or logical error (400)."""

    status_code = 400
    error_code = "BUSINESS_ERROR"


class ExternalServiceError(AppException):
    """Upstream / external service failure (502)."""

    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"

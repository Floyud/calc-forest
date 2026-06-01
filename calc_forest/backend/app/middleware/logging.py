"""Request/response logging middleware with correlation IDs.

Adds X-Request-ID to every request for end-to-end tracing.
Skips health checks, static files, and SSE streaming endpoints
to avoid buffering streaming responses.
"""
from __future__ import annotations

import time
import uuid
from typing import Callable

import structlog
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("access")

# Paths to skip entirely (no logging, no timing)
SKIP_PATHS: frozenset[str] = frozenset({
    "/health",
    "/api/health",
    "/favicon.ico",
})
SKIP_PREFIXES: tuple[str, ...] = ("/static/",)

# SSE/streaming endpoints — log start/end but do NOT wrap the body
STREAM_PATHS: frozenset[str] = frozenset({
    "/api/dify/pipeline-stream",
    "/api/diagnose-stream",
    "/api/stream",
})


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """FastAPI middleware: adds request_id, logs request/response."""
    path: str = request.url.path

    # Skip noisy paths entirely
    if path in SKIP_PATHS or any(path.startswith(p) for p in SKIP_PREFIXES):
        return await call_next(request)

    # --- correlation ID ---
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]

    # Bind to contextvars — ALL log calls in this request will include these
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=path,
        client_ip=request.client.host if request.client else "-",
    )

    # --- SSE/streaming: log start/end only, don't buffer ---
    if path in STREAM_PATHS:
        logger.info("stream_start", stream=path)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start) * 1000
            response.headers["X-Request-ID"] = request_id
            logger.info("stream_end", status_code=response.status_code, elapsed_ms=round(elapsed_ms, 1))
            return response
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception("stream_failed", elapsed_ms=round(elapsed_ms, 1))
            raise

    # --- normal request/response ---
    start = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Attach request_id to response so client can reference it
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            status_code=response.status_code,
            elapsed_ms=round(elapsed_ms, 1),
        )
        return response

    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request_failed",
            elapsed_ms=round(elapsed_ms, 1),
        )
        raise

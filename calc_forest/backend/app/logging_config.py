"""Structured logging configuration for 我的计算森林 API.

Uses structlog with stdlib integration via ProcessorFormatter.
- Console: colored human-readable output for development
- File: JSON format with RotatingFileHandler
- Contextvars for request ID propagation

Environment variables:
    LOG_LEVEL  — stdlib log level (default: INFO)
    LOG_FORMAT — "console" (colored) or "json" (default: console)
    LOG_DIR    — directory for rotating log files (default: data/logs/)
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog


def setup_logging() -> None:
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    log_format = os.getenv("LOG_FORMAT", "console")

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Console handler
    if log_format == "json":
        console_renderer = structlog.processors.JSONRenderer()
    else:
        console_renderer = structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                console_renderer,
            ],
            foreign_pre_chain=shared_processors,
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(console_handler)
    root.setLevel(log_level)

    for _noisy in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(_noisy).setLevel(logging.WARNING)

    for _uv in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        _uv_logger = logging.getLogger(_uv)
        _uv_logger.propagate = False
        if not _uv_logger.handlers:
            _uv_logger.addHandler(logging.StreamHandler(sys.stdout))
        _uv_logger.setLevel(log_level)

    log_dir = os.getenv("LOG_DIR", "")
    if not log_dir:
        _default = Path(__file__).resolve().parent.parent / "data" / "logs"
        log_dir = str(_default)

    _add_file_handler(log_dir, log_level, shared_processors)


def _add_file_handler(log_dir: str, log_level: int, shared_processors: list) -> None:
    log_path = Path(log_dir)
    try:
        log_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return

    handler = RotatingFileHandler(
        filename=log_path / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
            foreign_pre_chain=shared_processors,
        )
    )
    handler.setLevel(log_level)

    logging.getLogger().addHandler(handler)

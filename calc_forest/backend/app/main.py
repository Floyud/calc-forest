from __future__ import annotations

import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.exceptions import AppException

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# --- Structured logging setup (after dotenv) ---
from app.logging_config import setup_logging  # noqa: E402

setup_logging()

import structlog  # noqa: E402

_startup_logger = structlog.get_logger("startup")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _startup_logger.info("application_starting")
    from app.db import init_db, close_db

    await init_db()
    from app.services.timetable_service import ensure_timetable_table, seed_all_classes
    await ensure_timetable_table()
    await seed_all_classes()
    from app.services.knowledge_service import init_knowledge_index
    await init_knowledge_index()
    from app.services.ocr_service import init_ocr_engine
    init_ocr_engine()
    _startup_logger.info("application_ready")
    yield
    _startup_logger.info("application_shutting_down")
    from app.services.llm_client import llm_config
    await llm_config.close()
    await close_db()


app = FastAPI(
    title="我的计算森林 API",
    version="0.1.0",
    description="Dify-first tool API for 我的计算森林.",
    lifespan=lifespan,
)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    _exc_log = structlog.get_logger("exception")
    _exc_log.warning("app_exception", error_code=exc.error_code, detail=exc.detail, status_code=exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "status": exc.status_code,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    _exc_log = structlog.get_logger("exception")
    _exc_log.exception("unhandled_exception", error_type=type(exc).__name__, error_message=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "服务器内部错误", "status": 500}},
    )

# CORS: 从环境变量读取允许的域名
_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3002,"
    "http://127.0.0.1:3002,http://localhost:3001,http://127.0.0.1:3001",
).split(",")
_cors_origins = [o.strip() for o in _cors_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

app.add_middleware(GZipMiddleware, minimum_size=500)

from app.middleware.logging import logging_middleware  # noqa: E402

app.middleware("http")(logging_middleware)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response

from app.routers import auth, classroom, config, curriculum, diagnosis, homework, knowledge, quiz, student, student_auth, ocr, student_api, timetable  # noqa: E402

app.include_router(auth.router)
app.include_router(diagnosis.router)
app.include_router(homework.router)
app.include_router(quiz.router)
app.include_router(student.router)
app.include_router(classroom.router)
app.include_router(curriculum.router)
app.include_router(knowledge.router)
app.include_router(config.router)
app.include_router(student_auth.router)
app.include_router(ocr.router)
app.include_router(student_api.router)
app.include_router(timetable.router)

from fastapi.staticfiles import StaticFiles  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_uploads_dir = _Path(__file__).resolve().parent.parent / "data" / "uploads"
_uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(_uploads_dir)), name="uploads")

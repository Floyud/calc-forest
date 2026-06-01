from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse

from app.schemas import (
    EncouragementRule,
    HealthResponse,
    TTSRequest,
    TreeSpecies,
)
from app.services.growth import list_encouragement_rules, list_tree_species
from app.services.pdf_service import (
    generate_class_report_pdf,
    generate_student_report_pdf,
    list_class_reports,
    list_student_reports,
)

router = APIRouter(tags=["config"])

_frontend_logger = logging.getLogger("frontend")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/api/tree-species")
def tree_species():
    from fastapi.responses import JSONResponse
    from app.schemas import TreeSpecies as TS
    data = [m.model_dump() for m in list_tree_species()]
    return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=3600"})


@router.get("/api/encouragements")
def encouragements():
    from fastapi.responses import JSONResponse
    data = [m.model_dump() for m in list_encouragement_rules()]
    return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=3600"})


@router.get("/api/config/llm-status")
async def llm_status_endpoint():
    from app.services.llm_client import get_llm_status
    return get_llm_status()


@router.post("/api/config/llm-mode")
async def llm_mode_endpoint(
    mode: str | None = None,
    proxy_url: str | None = None,
    proxy_model: str | None = None,
    api_key: str | None = None,
):
    from app.services.llm_client import get_llm_status, llm_config

    if mode is not None:
        if mode not in ("official", "proxy", "glm", "mimo"):
            raise HTTPException(status_code=400, detail="模式必须为 'official'、'proxy'、'glm' 或 'mimo'")
        llm_config.mode = mode
    if proxy_url is not None:
        llm_config.proxy_url = proxy_url.rstrip("/")
    if proxy_model is not None:
        llm_config.proxy_model = proxy_model
    if api_key is not None:
        llm_config.api_key = api_key

    await llm_config.close()

    return get_llm_status()


@router.get("/api/config/dify-status")
async def dify_status():
    from app.services.dify_client import get_dify_status
    return get_dify_status()


@router.post("/api/tts/generate")
async def generate_tts_endpoint(request: TTSRequest):
    from app.services import tts_service

    try:
        audio_bytes = await tts_service.generate_tts(request.text, request.voice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning("TTS generation failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="TTS服务暂不可用，请使用浏览器语音",
        )
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.get("/api/pdfs/{pdf_id}")
async def serve_pdf_endpoint(pdf_id: str):
    from app.services.pdf_service import get_pdf_record

    record = await get_pdf_record(pdf_id)
    if not record:
        raise HTTPException(status_code=404, detail="PDF 不存在")
    pdf_path = record["pdf_path"]
    if not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF 文件缺失")
    student_name = record["student_id"] or "class"
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"homework_{student_name}.pdf",
    )


@router.post("/api/reports/{student_id}/generate")
async def generate_report_endpoint(
    student_id: str,
    report_type: str = "weekly",
    period_start: str | None = None,
    period_end: str | None = None,
):
    import os

    try:
        pdf_path = await generate_student_report_pdf(
            student_id=student_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
        )
        filename = os.path.basename(pdf_path)
        return FileResponse(pdf_path, media_type="application/pdf", filename=filename)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {e}")


@router.get("/api/reports/{student_id}")
async def list_reports_endpoint(student_id: str):
    reports = await list_student_reports(student_id)
    return {"student_id": student_id, "reports": reports}


@router.post("/api/reports/class/{class_id}/generate")
async def generate_class_report_endpoint(
    class_id: str,
    report_type: str = "monthly",
    period_start: str | None = None,
    period_end: str | None = None,
):
    import os

    try:
        pdf_path = await generate_class_report_pdf(
            class_id=class_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
        )
        filename = os.path.basename(pdf_path)
        return FileResponse(pdf_path, media_type="application/pdf", filename=filename)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {e}")


@router.get("/api/reports/class/{class_id}")
async def list_class_reports_endpoint(class_id: str):
    reports = await list_class_reports(class_id)
    return {"class_id": class_id, "reports": reports}


@router.post("/api/logs")
async def receive_frontend_logs(request: Request):
    """Receive batched error logs from the frontend."""
    try:
        body = await request.json()
        logs: list[dict[str, Any]] = body.get("logs", [])
        for entry in logs:
            level = entry.get("level", "info")
            event = entry.get("event", "unknown")
            data = {k: v for k, v in entry.items() if k not in ("level", "event")}
            if level == "error":
                _frontend_logger.error("frontend: %s | %s", event, data)
            elif level == "warn":
                _frontend_logger.warning("frontend: %s | %s", event, data)
            else:
                _frontend_logger.info("frontend: %s | %s", event, data)
        return {"received": len(logs)}
    except Exception:
        return {"received": 0}

from __future__ import annotations

import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.ocr_service import recognize_math_answer, recognize_work_image
from app.services.upload_service import save_upload

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/recognize")
async def ocr_recognize(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "请上传图片文件")

    image_bytes = await file.read()
    result = recognize_math_answer(image_bytes)

    return {
        "text": result.text,
        "confidence": result.confidence,
        "all_texts": result.all_texts,
    }


@router.post("/recognize-work")
async def ocr_recognize_work(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "请上传图片文件")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "文件大小不能超过 10MB")
    result = recognize_work_image(image_bytes)

    return {
        "text": result.text,
        "confidence": result.confidence,
        "all_texts": result.all_texts,
    }


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    student_id: str = Form(...),
    homework_id: str | None = Form(None),
):
    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "文件大小不能超过 10MB")
    result = await save_upload(student_id, image_bytes, file.filename or "photo.jpg", homework_id)
    return {
        "file_id": result.file_id,
        "path": result.path,
        "url": result.url,
        "size": result.size,
    }


@router.post("/baidu-correct")
async def baidu_correct_homework(
    file: UploadFile = File(...),
    only_split: bool = Form(False),
):
    baidu_api_key = os.getenv("BAIDU_OCR_API_KEY", "")
    baidu_secret = os.getenv("BAIDU_OCR_SECRET_KEY", "")
    if not baidu_api_key or not baidu_secret:
        raise HTTPException(503, "百度 OCR 未配置。请设置 BAIDU_OCR_API_KEY 和 BAIDU_OCR_SECRET_KEY 环境变量。")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "请上传图片文件")

    image_bytes = await file.read()

    from app.services.baidu_ocr_service import configure, correct_homework
    configure(baidu_api_key, baidu_secret)

    try:
        result = await correct_homework(image_bytes, only_split=only_split)
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    except TimeoutError as e:
        raise HTTPException(504, str(e))

    return {
        "task_id": result.task_id,
        "status": result.status,
        "subject": result.images[0].subject if result.images else "",
        "is_all_finished": result.is_all_finished,
        "stat_result": result.stat_result,
        "images": [
            {
                "image_id": img.image_id,
                "image_url": img.image_url,
                "subject": img.subject,
                "questions": [
                    {
                        "question_id": q.question_id,
                        "sequence": q.sequence,
                        "type": q.question_type,
                        "correct_result": q.correct_result,
                        "is_finished": q.is_finished,
                        "crop_url": q.crop_url,
                        "slots": [
                            {
                                "slot_id": s.slot_id,
                                "sequence": s.sequence,
                                "correct_result": s.correct_result,
                                "reason": s.reason,
                            }
                            for s in q.slots
                        ],
                    }
                    for q in img.questions
                ],
            }
            for img in result.images
        ],
    }

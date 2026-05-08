from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from app.db import get_db
from app.schemas import ArchiveStatus, HomeworkStatus, OCRUploadRequest, RecognitionStatus
from app.services.grading_service import grade_homework, submit_homework
from app.services.homework_service import get_homework


def _utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


def _parse_payload(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _build_task_response(scan_row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    diagnosis = payload.get("diagnosis")
    return {
        "scan_id": scan_row["id"],
        "homework_id": scan_row["homework_id"],
        "student_id": scan_row["student_id"],
        "recognition_status": scan_row["ocr_status"],
        "grading_status": scan_row["graded_status"],
        "archive_status": ArchiveStatus.ARCHIVED.value if scan_row["graded_status"] == HomeworkStatus.ARCHIVED.value else ArchiveStatus.PENDING.value,
        "review_status": payload.get("review_status", "pending_teacher_review"),
        "uploaded_at": scan_row["uploaded_at"],
        "reviewed_at": scan_row["reviewed_at"],
        "recognized_answers": payload.get("recognized_answers", []),
        "submission_id": payload.get("submission_id"),
        "diagnosis": diagnosis,
    }


async def upload_simulated_scan(request: OCRUploadRequest) -> dict[str, Any]:
    homework = await get_homework(request.homework_id)
    if not homework:
        return {"error": "homework not found"}

    scan_id = f"SCAN{uuid.uuid4().hex[:8].upper()}"
    payload = {
        "source_label": request.source_label,
        "simulated_answers": [answer.model_dump() for answer in request.answers],
        "recognized_answers": [],
        "submission_id": None,
        "diagnosis": None,
        "review_status": "pending_teacher_review",
    }

    uploaded_at = _utc_now()
    async with get_db() as db:
        await db.execute(
            """INSERT INTO scanned_submissions
               (id, student_id, homework_id, pdf_path, ocr_status, ocr_result_json, graded_status, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scan_id,
                request.student_id,
                request.homework_id,
                f"simulated://{request.homework_id}/{request.student_id}/{scan_id}",
                RecognitionStatus.QUEUED.value,
                json.dumps(payload, ensure_ascii=False),
                HomeworkStatus.SUBMITTED.value,
                uploaded_at,
            ),
        )
        await db.commit()

    return {
        "scan_id": scan_id,
        "homework_id": request.homework_id,
        "student_id": request.student_id,
        "recognition_status": RecognitionStatus.QUEUED.value,
        "grading_status": HomeworkStatus.SUBMITTED.value,
        "archive_status": ArchiveStatus.PENDING.value,
        "review_status": "pending_teacher_review",
        "uploaded_at": uploaded_at,
        "reviewed_at": None,
        "recognized_answers": [],
        "submission_id": None,
        "diagnosis": None,
    }


async def get_scan_status(scan_id: str) -> dict[str, Any] | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM scanned_submissions WHERE id = ?", (scan_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        scan_row = dict(row)

    payload = _parse_payload(scan_row.get("ocr_result_json"))

    if scan_row["ocr_status"] == RecognitionStatus.QUEUED.value:
        async with get_db() as db:
            await db.execute(
                "UPDATE scanned_submissions SET ocr_status = ? WHERE id = ?",
                (RecognitionStatus.PROCESSING.value, scan_id),
            )
            await db.commit()
        scan_row["ocr_status"] = RecognitionStatus.PROCESSING.value
        return _build_task_response(scan_row, payload)

    if scan_row["ocr_status"] == RecognitionStatus.PROCESSING.value:
        recognized_answers = [
            {
                "problem_sequence": item["problem_sequence"],
                "raw_answer": item["raw_answer"],
                "recognized_answer": item["raw_answer"].strip(),
                "confidence": 0.93,
                "review_status": "pending_teacher_review",
            }
            for item in payload.get("simulated_answers", [])
        ]
        payload["recognized_answers"] = recognized_answers
        async with get_db() as db:
            await db.execute(
                "UPDATE scanned_submissions SET ocr_status = ?, ocr_result_json = ? WHERE id = ?",
                (RecognitionStatus.RECOGNIZED.value, json.dumps(payload, ensure_ascii=False), scan_id),
            )
            await db.commit()
        scan_row["ocr_status"] = RecognitionStatus.RECOGNIZED.value
        return _build_task_response(scan_row, payload)

    if scan_row["ocr_status"] == RecognitionStatus.RECOGNIZED.value and scan_row["graded_status"] == HomeworkStatus.SUBMITTED.value:
        recognized_answers = payload.get("recognized_answers", [])
        submission = await submit_homework(
            scan_row["homework_id"],
            scan_row["student_id"],
            [
                {
                    "problem_sequence": str(item["problem_sequence"]),
                    "student_answer": item["recognized_answer"],
                }
                for item in recognized_answers
            ],
        )
        if "error" in submission:
            payload["diagnosis"] = {"error": submission["error"]}
        else:
            payload["submission_id"] = submission.get("submission_id")
            payload["diagnosis"] = await grade_homework(scan_row["homework_id"], scan_row["student_id"])

        async with get_db() as db:
            await db.execute(
                "UPDATE scanned_submissions SET graded_status = ?, ocr_result_json = ? WHERE id = ?",
                (HomeworkStatus.GRADED.value, json.dumps(payload, ensure_ascii=False), scan_id),
            )
            await db.commit()
        scan_row["graded_status"] = HomeworkStatus.GRADED.value
        return _build_task_response(scan_row, payload)

    if scan_row["graded_status"] == HomeworkStatus.GRADED.value:
        reviewed_at = _utc_now()
        async with get_db() as db:
            await db.execute(
                "UPDATE scanned_submissions SET graded_status = ?, reviewed_at = ? WHERE id = ?",
                (HomeworkStatus.ARCHIVED.value, reviewed_at, scan_id),
            )
            await db.commit()
        scan_row["graded_status"] = HomeworkStatus.ARCHIVED.value
        scan_row["reviewed_at"] = reviewed_at
        return _build_task_response(scan_row, payload)

    return _build_task_response(scan_row, payload)


async def list_homework_scans(homework_id: str) -> list[dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM scanned_submissions WHERE homework_id = ? ORDER BY uploaded_at DESC",
            (homework_id,),
        )
        rows = await cursor.fetchall()

    results = []
    for row in rows:
        scan_row = dict(row)
        payload = _parse_payload(scan_row.get("ocr_result_json"))
        results.append(_build_task_response(scan_row, payload))
    return results

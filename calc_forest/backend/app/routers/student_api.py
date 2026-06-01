from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.db import get_db
from app.services.student_dashboard_service import get_student_dashboard
from app.services.student_practice_service import (
    start_practice,
    get_next_problem,
    submit_practice_answer,
    end_practice,
)

router = APIRouter(prefix="/api/students", tags=["student-api"])


@router.get("/{student_id}/dashboard")
async def student_dashboard(student_id: str):
    result = await get_student_dashboard(student_id)
    if result is None:
        raise HTTPException(404, "学生不存在")
    return result


@router.get("/{student_id}/pending-homework")
async def pending_homework(student_id: str):
    from app.services.student_dashboard_service import _get_pending_homework
    async with get_db() as db:
        items = await _get_pending_homework(db, student_id)
    return items


@router.get("/{student_id}/homework/{homework_id}/problems")
async def homework_problems_for_student(student_id: str, homework_id: str):
    async with get_db() as db:
        cur = await db.execute(
            """
            SELECT sequence, problem, difficulty, knowledge_point, target_error_code
            FROM homework_problems WHERE homework_id = ?
            ORDER BY sequence
            """,
            (homework_id,),
        )
        rows = await cur.fetchall()
        if not rows:
            raise HTTPException(404, "作业不存在")
        return [
            {
                "sequence": r["sequence"],
                "problem": r["problem"],
                "difficulty": r["difficulty"],
                "knowledge_point": r["knowledge_point"],
            }
            for r in rows
        ]


@router.post("/{student_id}/practice/start")
async def practice_start(student_id: str, body: PracticeStartRequest | None = None):
    error_codes = body.error_codes if body else None
    result = await start_practice(student_id, error_codes)
    if result is None:
        raise HTTPException(404, "学生不存在")
    return result


@router.get("/{student_id}/practice/{session_id}/next")
async def practice_next_problem(student_id: str, session_id: str):
    result = await get_next_problem(student_id, session_id)
    if result is None:
        raise HTTPException(404, "没有进行中的练习会话或没有更多题目")
    return result


@router.post("/{student_id}/practice/{session_id}/answer")
async def practice_submit_answer(student_id: str, session_id: str, body: PracticeAnswerRequest):
    return await submit_practice_answer(student_id, session_id, body.problem_id, body.answer)


@router.post("/{student_id}/practice/{session_id}/end")
async def practice_end(student_id: str, session_id: str):
    return await end_practice(student_id, session_id)


class PracticeStartRequest(BaseModel):
    error_codes: list[str] | None = None


class PracticeAnswerRequest(BaseModel):
    problem_id: str
    answer: str


@router.get("/{student_id}/homework/{homework_id}/pdf")
async def student_homework_pdf(student_id: str, homework_id: str):
    async with get_db() as db:
        cur = await db.execute("SELECT name, class_id FROM students WHERE id = ?", (student_id,))
        stu = await cur.fetchone()
        if not stu:
            raise HTTPException(404, "学生不存在")

        cur2 = await db.execute("SELECT class_id FROM homework WHERE id = ?", (homework_id,))
        hw = await cur2.fetchone()
        if not hw:
            raise HTTPException(404, "作业不存在")

    from app.services.pdf_service import generate_homework_pdf

    try:
        pdf_path = await generate_homework_pdf(
            homework_id=homework_id,
            class_id=hw["class_id"],
            student_id=student_id,
            student_name=stu["name"],
        )
    except Exception as e:
        raise HTTPException(500, f"PDF 生成失败: {e}")

    from pathlib import Path
    if not Path(pdf_path).exists():
        raise HTTPException(500, "PDF 生成后未找到文件")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"homework_{homework_id}_{stu['name']}.pdf",
    )


@router.post("/{student_id}/homework/{homework_id}/scan-grade")
async def scan_and_grade(
    student_id: str,
    homework_id: str,
    file: UploadFile = File(...),
):
    from app.routers.homework import scan_and_grade_endpoint
    return await scan_and_grade_endpoint(homework_id=homework_id, file=file, student_id=student_id)

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_db
from app.schemas import (
    QuizGenerateRequest,
    QuizResponse,
    QuizResponseRecord,
    QuizSummary,
)

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


class QuizStudentAnswerRequest(BaseModel):
    student_id: str
    problem_sequence: int
    student_answer: str


@router.post("/generate")
async def quiz_generate_endpoint(request: QuizGenerateRequest):
    from app.services.quiz_service import generate_quiz
    result = await generate_quiz(
        class_id=request.class_id,
        grade=request.grade,
        error_codes_target=request.error_codes_target or None,
        problem_count=request.problem_count,
        difficulty=request.difficulty,
    )
    return result


@router.get("/{quiz_id}", response_model=QuizResponse)
async def quiz_get_endpoint(quiz_id: str):
    from app.services.quiz_service import get_quiz
    quiz = await get_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="测验不存在")
    return quiz


@router.post("/{quiz_id}/response")
async def quiz_response_endpoint(quiz_id: str, record: QuizResponseRecord):
    from app.services.quiz_service import get_quiz, record_response
    quiz = await get_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="测验不存在")
    await record_response(quiz_id, record.problem_sequence, record.class_response, record.notes)
    return {"ok": True}


@router.get("/{quiz_id}/summary", response_model=QuizSummary)
async def quiz_summary_endpoint(quiz_id: str):
    from app.services.quiz_service import get_quiz_summary
    summary = await get_quiz_summary(quiz_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="测验不存在")
    return summary


@router.post("/{quiz_id}/student-answer")
async def quiz_student_answer_endpoint(quiz_id: str, req: QuizStudentAnswerRequest):
    async with get_db() as db:
        cur = await db.execute("SELECT id FROM quiz_sessions WHERE id = ?", (quiz_id,))
        if await cur.fetchone() is None:
            raise HTTPException(404, "测验不存在")

        cur2 = await db.execute(
            "SELECT correct_answer FROM quiz_problems WHERE quiz_id = ? AND sequence = ?",
            (quiz_id, req.problem_sequence),
        )
        problem = await cur2.fetchone()
        if problem is None:
            raise HTTPException(404, "题目不存在")

        is_correct = req.student_answer.strip() == problem["correct_answer"].strip()
        answer_id = f"QSA{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()

        await db.execute(
            """
            INSERT OR REPLACE INTO quiz_student_answers (id, quiz_id, student_id, problem_sequence, student_answer, is_correct, answered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (answer_id, quiz_id, req.student_id, req.problem_sequence, req.student_answer, int(is_correct), now),
        )
        await db.commit()

    return {"is_correct": is_correct, "correct_answer": problem["correct_answer"] if not is_correct else None}


@router.get("/{quiz_id}/live-stats")
async def quiz_live_stats_endpoint(quiz_id: str):
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM quiz_sessions WHERE id = ?", (quiz_id,))
        quiz = await cur.fetchone()
        if quiz is None:
            raise HTTPException(404, "测验不存在")

        class_id = quiz["class_id"]

        cur2 = await db.execute("SELECT id, name FROM students WHERE class_id = ?", (class_id,))
        all_students = await cur2.fetchall()

        cur3 = await db.execute(
            "SELECT DISTINCT student_id FROM quiz_student_answers WHERE quiz_id = ?",
            (quiz_id,),
        )
        responded = {r["student_id"] for r in await cur3.fetchall()}

        cur4 = await db.execute(
            """
            SELECT problem_sequence,
                   SUM(is_correct) as correct_count,
                   COUNT(*) as total_count
            FROM quiz_student_answers
            WHERE quiz_id = ?
            GROUP BY problem_sequence
            ORDER BY problem_sequence
            """,
            (quiz_id,),
        )
        problem_stats = await cur4.fetchall()

        cur5 = await db.execute("SELECT COUNT(*) as cnt FROM quiz_problems WHERE quiz_id = ?", (quiz_id,))
        total_problems = (await cur5.fetchone())["cnt"]

    return {
        "quiz_id": quiz_id,
        "total_students": len(all_students),
        "responded_count": len(responded),
        "total_problems": total_problems,
        "problem_stats": [
            {
                "sequence": r["problem_sequence"],
                "correct_count": r["correct_count"],
                "wrong_count": r["total_count"] - r["correct_count"],
                "total_count": r["total_count"],
            }
            for r in problem_stats
        ],
        "student_progress": [
            {
                "student_id": s["id"],
                "name": s["name"],
                "completed": s["id"] in responded,
            }
            for s in all_students
        ],
    }

from __future__ import annotations

import logging
import uuid
from datetime import date
from typing import Any

from app.db import get_db
from app.exceptions import NotFoundException
from app.schemas import HomeworkAnswerInput

logger = logging.getLogger(__name__)


async def submit_homework(
    homework_id: str,
    student_id: str,
    answers: list[HomeworkAnswerInput] | list[dict[str, str]],
) -> dict[str, Any]:
    today = date.today().isoformat()
    submission_id = f"SUB{uuid.uuid4().hex[:8].upper()}"

    async with get_db() as db:
        hw = await db.execute("SELECT * FROM homework WHERE id = ?", (homework_id,))
        hw_row = await hw.fetchone()
        if not hw_row:
            raise NotFoundException(f"作业 {homework_id} 不存在")

        await db.execute(
            """INSERT INTO homework_submissions (id, homework_id, student_id, submitted_at, status)
               VALUES (?, ?, ?, ?, 'submitted')""",
            (submission_id, homework_id, student_id, today),
        )

        problems_cursor = await db.execute(
            "SELECT * FROM homework_problems WHERE homework_id = ? ORDER BY sequence",
            (homework_id,),
        )
        problems = await problems_cursor.fetchall()

        answer_records = []
        for ans in answers:
            if isinstance(ans, HomeworkAnswerInput):
                seq = ans.problem_sequence
                student_answer = ans.raw_answer
            else:
                seq = int(ans.get("problem_sequence", 0))
                student_answer = ans.get("raw_answer", "") or ans.get("student_answer", "")

            problem = None
            for p in problems:
                if p["sequence"] == seq:
                    problem = dict(p)
                    break

            if not problem:
                continue

            aid = f"SA{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO student_answers
                   (id, submission_id, homework_id, student_id, problem_sequence,
                    problem, correct_answer, student_answer, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    aid, submission_id, homework_id, student_id, seq,
                    problem["problem"], problem["correct_answer"], student_answer,
                    date.today().isoformat(),
                ),
            )
            answer_records.append({
                "id": aid,
                "problem": problem["problem"],
                "correct_answer": problem["correct_answer"],
                "student_answer": student_answer,
            })

        await db.execute(
            "UPDATE homework SET status = 'in_progress' WHERE id = ? AND status = 'assigned'",
            (homework_id,),
        )
        await db.commit()

    return {"submission_id": submission_id, "answer_count": len(answer_records)}


async def grade_homework(
    homework_id: str,
    student_id: str,
) -> dict[str, Any]:
    from app.pipeline.grading_pipeline import create_grading_pipeline

    pipeline = create_grading_pipeline()
    context: dict[str, Any] = {
        "homework_id": homework_id,
        "student_id": student_id,
    }
    result = await pipeline.run(context)

    if result.get("_errors"):
        first_error = result["_errors"][0]
        if first_error.get("node") == "fetch_answers":
            raise NotFoundException(first_error.get("error", "获取失败"))

    top_errors = result.get("_top_errors", [])
    next_suggestion = None
    if top_errors:
        next_suggestion = f"建议重点练习 {top_errors[0]} 类型的题目"

    return {
        "homework_id": homework_id,
        "student_id": student_id,
        "total_problems": result.get("_total", 0),
        "correct_count": result.get("_correct_count", 0),
        "accuracy": round(result.get("_accuracy", 0.0), 2),
        "primary_errors": top_errors,
        "profile_updated": result.get("_profile_updated", False),
        "growth_updated": result.get("_growth_updated", False),
        "next_suggestion": next_suggestion,
        "ai_analysis": result.get("_ai_analysis"),
    }

from __future__ import annotations

import json
import logging
import uuid
from collections import Counter
from datetime import date
from typing import Any

from app.db import get_db
from app.schemas import AnswerRecord

logger = logging.getLogger(__name__)


async def submit_homework(
    homework_id: str,
    student_id: str,
    answers: list[dict[str, str]],
) -> dict[str, Any]:
    today = date.today().isoformat()
    submission_id = f"SUB{uuid.uuid4().hex[:8].upper()}"

    async with get_db() as db:
        hw = await db.execute("SELECT * FROM homework WHERE id = ?", (homework_id,))
        hw_row = await hw.fetchone()
        if not hw_row:
            return {"error": "homework not found"}

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
            seq = int(ans.get("problem_sequence", 0))
            student_answer = ans.get("student_answer", "")

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
                    problem, correct_answer, student_answer)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    aid, submission_id, homework_id, student_id, seq,
                    problem["problem"], problem["correct_answer"], student_answer,
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
    from app.services.diagnosis import diagnose_answer
    from app.pipeline.profile_update_node import ProfileUpdateNode
    from app.pipeline.growth_update_node import GrowthUpdateNode

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT sa.*, h.grade as problem_grade
               FROM student_answers sa
               JOIN homework h ON sa.homework_id = h.id
               WHERE sa.homework_id = ? AND sa.student_id = ? AND sa.error_code IS NULL
               ORDER BY sa.problem_sequence""",
            (homework_id, student_id),
        )
        answers = await cursor.fetchall()

        if not answers:
            return {"error": "no ungraded answers found"}

        total = len(answers)
        correct_count = 0
        error_codes = []
        diagnosis_results = []

        for ans in answers:
            a = dict(ans)
            record = AnswerRecord(
                student_id=student_id,
                grade=a.get("problem_grade") or 6,
                problem=a["problem"],
                correct_answer=a["correct_answer"],
                student_answer=a["student_answer"],
            )

            diagnosis = diagnose_answer(record)
            diagnosis_results.append((a["id"], record, diagnosis))

            is_correct = 1 if diagnosis.is_correct else 0
            if diagnosis.is_correct:
                correct_count += 1
            else:
                error_codes.append(diagnosis.primary_error.code.value)

            await db.execute(
                """UPDATE student_answers SET
                   is_correct = ?, error_code = ?, error_label = ?,
                   confidence = ?, evidence = ?, teacher_action = ?, student_feedback = ?
                   WHERE id = ?""",
                (
                    is_correct,
                    diagnosis.primary_error.code.value,
                    diagnosis.primary_error.label,
                    diagnosis.primary_error.confidence,
                    diagnosis.primary_error.evidence,
                    diagnosis.primary_error.teacher_action,
                    diagnosis.primary_error.student_feedback,
                    a["id"],
                ),
            )

        accuracy = correct_count / total if total > 0 else 0.0

        top_errors = [code for code, _ in Counter(error_codes).most_common(3)]

        await db.execute(
            "UPDATE homework_submissions SET status = 'graded' WHERE homework_id = ? AND student_id = ?",
            (homework_id, student_id),
        )

        all_graded = await db.execute(
            "SELECT COUNT(*) FROM student_answers WHERE homework_id = ? AND error_code IS NOT NULL",
            (homework_id,),
        )
        graded_count = (await all_graded.fetchone())[0]
        all_answers = await db.execute(
            "SELECT COUNT(*) FROM student_answers WHERE homework_id = ?",
            (homework_id,),
        )
        total_answers = (await all_answers.fetchone())[0]

        await db.commit()

    profile_updated = False
    growth_updated = False
    try:
        from app.services.student_service import update_error_stats

        for _ans_id, _record, diagnosis in diagnosis_results:
            await update_error_stats(student_id, diagnosis.primary_error.code.value, diagnosis.is_correct)
    except Exception:
        logger.warning("Failed to update error stats for student %s", student_id, exc_info=True)

    try:
        from app.schemas import DiagnosisResponse, ErrorTag, ErrorCode, GuidanceMode

        tag = ErrorTag(
            code=ErrorCode(top_errors[0]) if top_errors else ErrorCode.CORRECT,
            label="",
            confidence=0.9,
            evidence="",
            teacher_action="",
            student_feedback="",
        )
        mock_diagnosis = DiagnosisResponse(
            record_id=None,
            student_id=student_id,
            is_correct=accuracy >= 0.8,
            primary_error=tag,
            teacher_summary="",
            guidance_mode=GuidanceMode.STANDARD,
            review_status="pending_teacher_review",
        )
        profile_node = ProfileUpdateNode()
        pr = await profile_node.execute({
            "diagnosis": mock_diagnosis,
            "student_id": student_id,
            "grade": 6,
            "problem": f"homework:{homework_id}",
            "correct_answer": str(correct_count),
            "student_answer": str(total),
        })
        profile_updated = pr.success

        growth_node = GrowthUpdateNode()
        gr = await growth_node.execute({
            "diagnosis": mock_diagnosis,
            "student_id": student_id,
            "grade": 6,
        })
        growth_updated = gr.success
    except Exception:
        logger.warning("Failed to update profile/growth for student %s", student_id, exc_info=True)

    next_suggestion = None
    if top_errors:
        next_suggestion = f"建议重点练习 {top_errors[0]} 类型的题目"

    return {
        "homework_id": homework_id,
        "student_id": student_id,
        "total_problems": total,
        "correct_count": correct_count,
        "accuracy": round(accuracy, 2),
        "primary_errors": top_errors,
        "profile_updated": profile_updated,
        "growth_updated": growth_updated,
        "next_suggestion": next_suggestion,
    }

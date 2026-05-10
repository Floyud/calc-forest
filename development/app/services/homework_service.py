from __future__ import annotations
import json
import uuid
from datetime import date
from typing import Any

from app.db import get_db
from app.services.problem_generator import generate_quiz_problems


async def get_class_top_errors(class_id: str, limit: int = 3) -> list[str]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT error_code, COUNT(*) as cnt FROM diagnosis_history
               WHERE class_id = ? AND is_correct = 0
               GROUP BY error_code ORDER BY cnt DESC LIMIT ?""",
            (class_id, limit),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_student_top_errors(student_id: str, limit: int = 3) -> list[str]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT error_code, COUNT(*) as cnt FROM diagnosis_history
               WHERE student_id = ? AND is_correct = 0
               GROUP BY error_code ORDER BY cnt DESC LIMIT ?""",
            (student_id, limit),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def _get_student_accuracy(student_id: str) -> float | None:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT SUM(total_attempts) as total,
                      SUM(correct_count) as correct
               FROM student_error_stats WHERE student_id = ?""",
            (student_id,),
        )
        row = await cursor.fetchone()
        if row and row["total"] and row["total"] > 0:
            return row["correct"] / row["total"]
    return None


def _difficulty_distribution_for(accuracy: float) -> dict[str, float]:
    if accuracy < 0.6:
        return {"A": 0.6, "B": 0.4}
    if accuracy < 0.8:
        return {"A": 0.3, "B": 0.5, "C": 0.2}
    return {"B": 0.4, "C": 0.6}


async def generate_homework(
    class_id: str,
    grade: int = 6,
    student_id: str | None = None,
    error_codes_target: list[str] | None = None,
    problem_count: int = 5,
    difficulty: str = "A",
) -> dict[str, Any]:
    if not error_codes_target:
        if student_id:
            error_codes_target = await get_student_top_errors(student_id)
        else:
            error_codes_target = await get_class_top_errors(class_id)

    if not error_codes_target:
        error_codes_target = ["E03"]

    diff_dist: dict[str, float] | None = None
    if student_id:
        accuracy = await _get_student_accuracy(student_id)
        if accuracy is not None:
            diff_dist = _difficulty_distribution_for(accuracy)

    problems = generate_quiz_problems(
        error_codes=error_codes_target,
        difficulty=difficulty,
        total_count=problem_count,
        difficulty_distribution=diff_dist,
    )

    homework_id = f"HW{uuid.uuid4().hex[:8].upper()}"
    today = date.today().isoformat()

    async with get_db() as db:
        await db.execute(
            """INSERT INTO homework (id, class_id, student_id, grade, knowledge_points,
               error_codes_target, status, generated_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'draft', 'system', ?)""",
            (
                homework_id,
                class_id,
                student_id,
                grade,
                json.dumps(list({p.knowledge_point for p in problems})),
                json.dumps(error_codes_target),
                today,
            ),
        )

        for i, p in enumerate(problems, 1):
            pid = f"HP{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO homework_problems (id, homework_id, sequence, problem,
                   correct_answer, knowledge_point, target_error_code, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (pid, homework_id, i, p.problem, p.correct_answer,
                 p.knowledge_point, p.error_code, p.difficulty),
            )

        await db.commit()

    return await get_homework(homework_id)


async def get_homework(homework_id: str) -> dict[str, Any] | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM homework WHERE id = ?", (homework_id,))
        row = await cursor.fetchone()
        if not row:
            return None

        result = dict(row)
        result["homework_id"] = result["id"]
        result["knowledge_points"] = json.loads(result.get("knowledge_points", "[]"))
        result["error_codes_target"] = json.loads(result.get("error_codes_target", "[]"))

        pcursor = await db.execute(
            "SELECT * FROM homework_problems WHERE homework_id = ? ORDER BY sequence",
            (homework_id,),
        )
        problems = await pcursor.fetchall()
        result["problems"] = [dict(p) for p in problems]

        return result


async def assign_homework(homework_id: str, due_date: str | None = None) -> bool:
    today = date.today().isoformat()
    async with get_db() as db:
        await db.execute(
            "UPDATE homework SET status = 'assigned', assigned_date = ?, due_date = ? WHERE id = ?",
            (today, due_date, homework_id),
        )
        await db.commit()
    return True

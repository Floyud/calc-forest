"""Repository for homework CRUD operations."""
from __future__ import annotations

import aiosqlite


async def get_homework(db: aiosqlite.Connection, homework_id: str) -> dict | None:
    """Fetch a homework row by ID."""
    cursor = await db.execute("SELECT * FROM homework WHERE id = ?", (homework_id,))
    return await cursor.fetchone()


async def get_ungraded_answers(
    db: aiosqlite.Connection,
    homework_id: str,
    student_id: str,
) -> list[dict]:
    """Fetch ungraded student answers with problem grade and class_id."""
    cursor = await db.execute(
        """SELECT sa.*, h.grade as problem_grade, h.class_id
           FROM student_answers sa
           JOIN homework h ON sa.homework_id = h.id
           WHERE sa.homework_id = ? AND sa.student_id = ? AND sa.error_code IS NULL
           ORDER BY sa.problem_sequence""",
        (homework_id, student_id),
    )
    return await cursor.fetchall()


async def get_homework_info(
    db: aiosqlite.Connection,
    homework_id: str,
) -> dict | None:
    """Fetch class_id, grade, cycle_id for a homework."""
    cursor = await db.execute(
        "SELECT class_id, grade, cycle_id FROM homework WHERE id = ?",
        (homework_id,),
    )
    return await cursor.fetchone()


async def update_answer_diagnosis(
    db: aiosqlite.Connection,
    answer_id: str,
    is_correct: bool,
    error_code: str,
    error_label: str,
    confidence: float,
    evidence: str,
    teacher_action: str,
    student_feedback: str,
) -> None:
    """Write diagnosis fields to a student_answer row."""
    await db.execute(
        """UPDATE student_answers SET
           is_correct = ?, error_code = ?, error_label = ?,
           confidence = ?, evidence = ?, teacher_action = ?, student_feedback = ?
           WHERE id = ?""",
        (1 if is_correct else 0, error_code, error_label, confidence, evidence, teacher_action, student_feedback, answer_id),
    )


async def mark_submission_graded(
    db: aiosqlite.Connection,
    homework_id: str,
    student_id: str,
) -> None:
    """Transition a submission to graded status."""
    await db.execute(
        "UPDATE homework_submissions SET status = 'graded' WHERE homework_id = ? AND student_id = ?",
        (homework_id, student_id),
    )


async def transition_homework_if_all_graded(
    db: aiosqlite.Connection,
    homework_id: str,
) -> bool:
    """Transition homework to 'graded' if all answers are graded. Returns True if transitioned."""
    graded_cursor = await db.execute(
        "SELECT COUNT(*) FROM student_answers WHERE homework_id = ? AND error_code IS NOT NULL",
        (homework_id,),
    )
    graded_count = (await graded_cursor.fetchone())[0]

    total_cursor = await db.execute(
        "SELECT COUNT(*) FROM student_answers WHERE homework_id = ?",
        (homework_id,),
    )
    total_count = (await total_cursor.fetchone())[0]

    if graded_count >= total_count:
        await db.execute(
            "UPDATE homework SET status = 'graded' WHERE id = ? AND status = 'in_progress'",
            (homework_id,),
        )
        return True
    return False

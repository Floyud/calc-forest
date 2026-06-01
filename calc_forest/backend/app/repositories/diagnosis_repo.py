"""Repository for diagnosis_history operations."""
from __future__ import annotations

import uuid

import aiosqlite


async def batch_insert(
    db: aiosqlite.Connection,
    records: list[dict],
) -> int:
    """Insert multiple diagnosis records. Returns count inserted."""
    count = 0
    for rec in records:
        await db.execute(
            """INSERT INTO diagnosis_history
               (id, student_id, class_id, grade, problem, correct_answer, student_answer,
                is_correct, error_code, error_label, confidence, evidence,
                teacher_action, student_feedback)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                rec["student_id"],
                rec.get("class_id"),
                rec.get("grade", 6),
                rec["problem"],
                rec["correct_answer"],
                rec["student_answer"],
                1 if rec["is_correct"] else 0,
                rec["error_code"],
                rec.get("error_label", ""),
                rec.get("confidence", 0.0),
                rec.get("evidence", ""),
                rec.get("teacher_action", ""),
                rec.get("student_feedback", ""),
            ),
        )
        count += 1
    return count

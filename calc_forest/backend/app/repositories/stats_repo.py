"""Repository for student_error_stats operations."""
from __future__ import annotations

import uuid

import aiosqlite


async def batch_update_error_stats(
    db: aiosqlite.Connection,
    student_id: str,
    results: list[tuple[str, bool]],
) -> None:
    """Update error stats from a batch of (error_code, is_correct) results."""
    for error_code, is_correct in results:
        await db.execute(
            """INSERT INTO student_error_stats
                   (id, student_id, error_code, total_attempts, correct_count, last_seen_at)
               VALUES (?, ?, ?, 1, ?, datetime('now'))
               ON CONFLICT(student_id, error_code) DO UPDATE SET
                 total_attempts = total_attempts + 1,
                 correct_count = correct_count + ?,
                 last_seen_at = datetime('now')""",
            (
                f"SES{uuid.uuid4().hex[:8].upper()}",
                student_id,
                error_code,
                1 if is_correct else 0,
                1 if is_correct else 0,
            ),
        )


async def get_student_accuracy(db: aiosqlite.Connection, student_id: str) -> float | None:
    """Get overall accuracy for a student."""
    cursor = await db.execute(
        "SELECT SUM(total_attempts), SUM(correct_count) FROM student_error_stats WHERE student_id = ?",
        (student_id,),
    )
    row = await cursor.fetchone()
    if row and row[0] and row[0] > 0:
        return row[1] / row[0]
    return None


async def get_error_code_accuracy(db: aiosqlite.Connection, student_id: str) -> dict[str, float]:
    """Get per-error-code accuracy for a student."""
    cursor = await db.execute(
        "SELECT error_code, total_attempts, correct_count FROM student_error_stats WHERE student_id = ?",
        (student_id,),
    )
    rows = await cursor.fetchall()
    result: dict[str, float] = {}
    for row in rows:
        if row["total_attempts"] > 0:
            result[row["error_code"]] = row["correct_count"] / row["total_attempts"]
    return result

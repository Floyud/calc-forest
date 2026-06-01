"""Student dashboard aggregation for mobile home page."""
from __future__ import annotations

import json

from app.db import get_db


async def get_student_dashboard(student_id: str) -> dict:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT id, name, grade, class_id FROM students WHERE id = ?",
            (student_id,),
        )
        student = await cur.fetchone()
        if student is None:
            return None

        pending_hw = await _get_pending_homework(db, student_id)
        recent_results = await _get_recent_results(db, student_id)
        growth = await _get_growth_summary(db, student_id)
        weak_areas = await _get_weak_areas(db, student_id)
        today_practice = await _get_today_practice(db, student_id)

        return {
            "student": {
                "id": student["id"],
                "name": student["name"],
                "grade": student["grade"],
                "class_id": student["class_id"],
            },
            "pending_homework": pending_hw,
            "recent_results": recent_results,
            "growth_summary": growth,
            "weak_areas": weak_areas,
            "today_practice": today_practice,
        }


async def _get_pending_homework(db, student_id: str) -> list[dict]:
    cur = await db.execute(
        """
        SELECT h.id, h.status, h.assigned_date, h.due_date,
               COUNT(hp.id) as problem_count
        FROM homework h
        JOIN homework_problems hp ON hp.homework_id = h.id
        WHERE h.class_id = (SELECT class_id FROM students WHERE id = ?)
          AND h.status = 'assigned'
          AND NOT EXISTS (
              SELECT 1 FROM homework_submissions hs
              WHERE hs.homework_id = h.id AND hs.student_id = ?
          )
        GROUP BY h.id
        ORDER BY h.due_date ASC
        LIMIT 10
        """,
        (student_id, student_id),
    )
    rows = await cur.fetchall()
    return [
        {
            "homework_id": r["id"],
            "status": r["status"],
            "assigned_date": r["assigned_date"],
            "due_date": r["due_date"],
            "problem_count": r["problem_count"],
        }
        for r in rows
    ]


async def _get_recent_results(db, student_id: str) -> list[dict]:
    cur = await db.execute(
        """
        SELECT h.id as homework_id, h.assigned_date,
               SUM(sa.is_correct) as correct,
               COUNT(sa.id) as total,
               ROUND(AVG(sa.is_correct) * 100) as accuracy
        FROM student_answers sa
        JOIN homework h ON h.id = sa.homework_id
        WHERE sa.student_id = ? AND sa.is_correct IS NOT NULL
        GROUP BY h.id
        ORDER BY h.assigned_date DESC
        LIMIT 5
        """,
        (student_id,),
    )
    rows = await cur.fetchall()
    return [
        {
            "homework_id": r["homework_id"],
            "date": r["assigned_date"],
            "correct": r["correct"],
            "total": r["total"],
            "accuracy": r["accuracy"],
        }
        for r in rows
    ]


async def _get_growth_summary(db, student_id: str) -> dict:
    cur = await db.execute(
        """
        SELECT current_stage, days_completed, tree_species_id
        FROM student_cycle_progress scp
        JOIN academic_cycles ac ON ac.id = scp.cycle_id
        WHERE scp.student_id = ?
        ORDER BY ac.start_date DESC LIMIT 1
        """,
        (student_id,),
    )
    row = await cur.fetchone()
    if row is None:
        return {"stage": "seed", "days_completed": 0, "tree_species": None}

    return {
        "stage": row["current_stage"],
        "days_completed": row["days_completed"],
        "tree_species": row["tree_species_id"],
    }


async def _get_weak_areas(db, student_id: str) -> list[dict]:
    cur = await db.execute(
        """
        SELECT error_code, total_attempts, correct_count,
               ROUND(CASE WHEN total_attempts > 0 THEN correct_count * 1.0 / total_attempts ELSE 0 END, 2) as accuracy
        FROM student_error_stats
        WHERE student_id = ? AND total_attempts > 0 AND error_code != 'OK'
        ORDER BY accuracy ASC
        LIMIT 5
        """,
        (student_id,),
    )
    from app.schemas import ERROR_LABELS, ErrorCode
    rows = await cur.fetchall()
    result = []
    for r in rows:
        code = r["error_code"]
        try:
            label = ERROR_LABELS[ErrorCode(code)] if code != "OK" else "答案正确"
        except (ValueError, KeyError):
            label = code
        result.append({
            "error_code": code,
            "label": label,
            "accuracy": r["accuracy"],
            "total_attempts": r["total_attempts"],
        })
    return result


async def _get_today_practice(db, student_id: str) -> dict:
    from datetime import date
    today = date.today().isoformat()
    cur = await db.execute(
        """
        SELECT COUNT(*) as cnt FROM student_answers
        WHERE student_id = ? AND created_at >= ?
        """,
        (student_id, today),
    )
    row = await cur.fetchone()
    return {"completed": row["cnt"] if row else 0, "target": 10}

from __future__ import annotations

import json
from typing import Any

from app.db import get_db


async def get_units(grade: int = 6, semester: int = 2) -> list[dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM teaching_units WHERE grade = ? AND semester = ? ORDER BY sort_order, unit_number",
            (grade, semester),
        )
        rows = await cursor.fetchall()
        units = [dict(r) for r in rows]
        top_level = [u for u in units if not u.get("parent_id")]
        for u in top_level:
            u["children"] = [c for c in units if c.get("parent_id") == u["id"]]
        return top_level


async def get_schedule(class_id: str) -> list[dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT ts.*, tu.title as unit_title, tu.domain, tu.hours_planned
               FROM teaching_schedule ts
               JOIN teaching_units tu ON ts.unit_id = tu.id
               WHERE ts.class_id = ?
               ORDER BY ts.week_number""",
            (class_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]


async def update_schedule(class_id: str, updates: list[dict[str, Any]]) -> int:
    count = 0
    async with get_db() as db:
        for u in updates:
            await db.execute(
                """INSERT OR REPLACE INTO teaching_schedule
                   (id, class_id, week_number, unit_id, start_date, end_date, status, notes, is_custom)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    f"SCH_{class_id}_W{u['week_number']:02d}",
                    class_id,
                    u["week_number"],
                    u["unit_id"],
                    u.get("start_date", ""),
                    u.get("end_date", ""),
                    u.get("status", "planned"),
                    u.get("notes", ""),
                ),
            )
            count += 1
        await db.commit()
    return count


async def get_calendar(academic_year: str, semester: int = 2) -> list[dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM calendar_weeks WHERE academic_year = ? AND semester = ? ORDER BY week_number",
            (academic_year, semester),
        )
        return [dict(r) for r in await cursor.fetchall()]


async def get_student_trajectory(student_id: str) -> list[dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT trajectory.*, tu.title as unit_title, tu.unit_number
               FROM student_error_trajectory trajectory
               LEFT JOIN teaching_units tu ON trajectory.unit_id = tu.id
               WHERE trajectory.student_id = ?
               ORDER BY trajectory.week_number, tu.sort_order""",
            (student_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]


async def update_student_profile(
    student_id: str,
    personality_tags: list[str] | None = None,
    learning_style: str | None = None,
    notes: str | None = None,
) -> bool:
    async with get_db() as db:
        updates = []
        values = []
        if personality_tags is not None:
            updates.append("personality_tags = ?")
            values.append(json.dumps(personality_tags))
        if learning_style is not None:
            updates.append("learning_style = ?")
            values.append(learning_style)
        if notes is not None:
            updates.append("notes = ?")
            values.append(notes)
        if not updates:
            return False
        values.append(student_id)
        await db.execute(f"UPDATE students SET {', '.join(updates)} WHERE id = ?", values)
        await db.commit()
    return True

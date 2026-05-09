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
            """SELECT error_code,
                      COUNT(*) as total_count,
                      SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as error_count,
                      SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                      ROUND(AVG(CASE WHEN is_correct = 1 THEN 1.0 ELSE 0.0 END), 4) as accuracy
               FROM diagnosis_history
               WHERE student_id = ? AND error_code != 'OK'
               GROUP BY error_code
               ORDER BY error_count DESC""",
            (student_id,),
        )
        rows = await cursor.fetchall()

        result = []
        for i, r in enumerate(rows):
            result.append({
                "id": f"TRAJ_{student_id}_{i}",
                "student_id": student_id,
                "unit_id": None,
                "unit_title": None,
                "unit_number": None,
                "week_number": None,
                "error_code": r["error_code"],
                "error_count": r["error_count"],
                "correct_count": r["correct_count"],
                "accuracy": r["accuracy"] or 0.0,
                "total_count": r["total_count"],
                "notes": "",
                "created_at": "",
            })

        sa_cursor = await db.execute(
            """SELECT error_code,
                      COUNT(*) as total_count,
                      SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as error_count,
                      SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                      ROUND(AVG(CASE WHEN is_correct = 1 THEN 1.0 ELSE 0.0 END), 4) as accuracy
               FROM student_answers
               WHERE student_id = ? AND error_code IS NOT NULL AND error_code != 'OK'
               GROUP BY error_code
               ORDER BY error_count DESC""",
            (student_id,),
        )
        sa_rows = await sa_cursor.fetchall()

        existing = {r["error_code"]: r for r in result}
        for r in sa_rows:
            code = r["error_code"]
            if code in existing:
                existing[code]["error_count"] = (existing[code].get("error_count") or 0) + (r["error_count"] or 0)
                existing[code]["correct_count"] = (existing[code].get("correct_count") or 0) + (r["correct_count"] or 0)
                existing[code]["total_count"] = (existing[code].get("total_count") or 0) + (r["total_count"] or 0)
                tc = existing[code]["total_count"]
                cc = existing[code]["correct_count"]
                existing[code]["accuracy"] = round(cc / tc, 4) if tc > 0 else 0.0
            else:
                result.append({
                    "id": f"TRAJ_{student_id}_SA_{len(result)}",
                    "student_id": student_id,
                    "unit_id": None,
                    "unit_title": None,
                    "unit_number": None,
                    "week_number": None,
                    "error_code": code,
                    "error_count": r["error_count"],
                    "correct_count": r["correct_count"],
                    "accuracy": r["accuracy"] or 0.0,
                    "total_count": r["total_count"],
                    "notes": "",
                    "created_at": "",
                })

        result.sort(key=lambda x: x.get("error_count", 0), reverse=True)
        return result


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

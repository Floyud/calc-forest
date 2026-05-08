from __future__ import annotations

import json
from datetime import date

from app.db import get_db
from app.schemas import AcademicCycle, StudentCycleProgress


def _row_to_cycle(row) -> AcademicCycle:
    species = json.loads(row["available_tree_species"]) if row["available_tree_species"] else []
    return AcademicCycle(
        id=row["id"],
        cycle_type=row["cycle_type"],
        academic_year=row["academic_year"],
        grade=row["grade"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        total_days=row["total_days"],
        practice_goal_days=row["practice_goal_days"],
        available_tree_species=species,
    )


def _row_to_progress(row) -> StudentCycleProgress:
    return StudentCycleProgress(
        id=row["id"],
        student_id=row["student_id"],
        cycle_id=row["cycle_id"],
        tree_species_id=row["tree_species_id"],
        days_completed=row["days_completed"],
        current_stage=row["current_stage"],
        last_practice_date=row["last_practice_date"],
    )


async def get_cycle(cycle_id: str) -> AcademicCycle | None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM academic_cycles WHERE id = ?", (cycle_id,)
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_cycle(row)


async def get_current_cycle(grade: int) -> AcademicCycle | None:
    today = date.today().isoformat()
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM academic_cycles "
            "WHERE grade = ? AND start_date <= ? AND end_date >= ?",
            (grade, today, today),
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_cycle(row)


async def get_student_growth(student_id: str) -> StudentCycleProgress | None:
    from app.services.student_service import get_student

    student = await get_student(student_id)
    if student is None:
        return None

    cycle = await get_current_cycle(student.grade)
    if cycle is None:
        return None

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM student_cycle_progress "
            "WHERE student_id = ? AND cycle_id = ?",
            (student_id, cycle.id),
        )
        row = await cursor.fetchone()

    if row is None:
        return StudentCycleProgress(
            id=f"{student_id}_{cycle.id}",
            student_id=student_id,
            cycle_id=cycle.id,
        )

    return _row_to_progress(row)

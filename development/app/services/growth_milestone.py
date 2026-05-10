"""Growth milestone service — tree growth auto-progression logic.

Handles stage computation, practice-day recording, and milestone detection
for the student_cycle_progress table.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date

from app.db import get_db
from app.schemas import GrowthMilestone

logger = logging.getLogger(__name__)

STAGE_THRESHOLDS = [1, 3, 7, 14, 21, 30, 45, 60, 90]
STAGE_KEYS = [
    "seed", "sprout", "first_leaf", "taller", "branching",
    "sturdy", "bud", "flowering", "mature",
]


def compute_stage(days_completed: int) -> str:
    """Map days_completed to a named growth stage via threshold lookup."""
    for i in range(len(STAGE_THRESHOLDS) - 1, -1, -1):
        if days_completed >= STAGE_THRESHOLDS[i]:
            return STAGE_KEYS[i]
    return "seed"


async def record_practice_day(student_id: str) -> dict:
    """Record a practice day for a student and detect stage changes.

    Called when a student completes a practice session (homework/quiz).
    - Finds or creates the student_cycle_progress row for the current cycle
    - If last_practice_date != today, increments days_completed
    - Recomputes current_stage using compute_stage()
    - If stage changed, returns change info with encouragement
    """
    from app.services.cycle_service import get_current_cycle
    from app.services.student_service import get_student

    student = await get_student(student_id)
    if student is None:
        return {"stage_changed": False, "current_stage": "seed", "error": "student not found"}

    cycle = await get_current_cycle(student.grade)
    if cycle is None:
        return {"stage_changed": False, "current_stage": "seed", "error": "no current cycle"}

    today = date.today().isoformat()
    progress_id = f"{student_id}_{cycle.id}"

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM student_cycle_progress WHERE student_id = ? AND cycle_id = ?",
            (student_id, cycle.id),
        )
        row = await cursor.fetchone()

        if row is None:
            new_id = f"SCP{uuid.uuid4().hex[:8].upper()}"
            new_stage = compute_stage(1)
            await db.execute(
                """INSERT INTO student_cycle_progress
                   (id, student_id, cycle_id, tree_species_id, days_completed,
                    current_stage, last_practice_date)
                   VALUES (?, ?, ?, NULL, 1, ?, ?)""",
                (new_id, student_id, cycle.id, new_stage, today),
            )
            await db.commit()
            return {
                "stage_changed": True,
                "old_stage": "seed",
                "new_stage": new_stage,
                "days_completed": 1,
                "milestone": None,
            }

        old_stage = row["current_stage"]
        last_practice = row["last_practice_date"]
        days_completed = row["days_completed"]

        if last_practice == today:
            return {
                "stage_changed": False,
                "current_stage": old_stage,
                "days_completed": days_completed,
            }

        days_completed += 1
        new_stage = compute_stage(days_completed)

        await db.execute(
            """UPDATE student_cycle_progress
               SET days_completed = ?, current_stage = ?, last_practice_date = ?
               WHERE student_id = ? AND cycle_id = ?""",
            (days_completed, new_stage, today, student_id, cycle.id),
        )
        await db.commit()

    stage_changed = old_stage != new_stage
    encouragement = None
    if stage_changed:
        from app.services.growth import get_encouragement_message
        encouragement = get_encouragement_message(trigger="growth_milestone")

    return {
        "stage_changed": stage_changed,
        "old_stage": old_stage if stage_changed else None,
        "new_stage": new_stage if stage_changed else None,
        "current_stage": new_stage,
        "days_completed": days_completed,
        "milestone": encouragement if stage_changed else None,
    }


async def get_growth_milestone(student_id: str) -> GrowthMilestone | None:
    """Build GrowthMilestone for a student by querying student_cycle_progress + academic_cycles."""
    from app.services.cycle_service import get_current_cycle
    from app.services.student_service import get_student

    student = await get_student(student_id)
    if student is None:
        return None

    cycle = await get_current_cycle(student.grade)
    if cycle is None:
        return None

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM student_cycle_progress WHERE student_id = ? AND cycle_id = ?",
            (student_id, cycle.id),
        )
        row = await cursor.fetchone()

    if row is None:
        return GrowthMilestone(
            current_stage="seed",
            days_completed=0,
            total_days_in_cycle=cycle.total_days,
            cycle_type=cycle.cycle_type,
            tree_species_id=None,
        )

    return GrowthMilestone(
        current_stage=row["current_stage"],
        days_completed=row["days_completed"],
        total_days_in_cycle=cycle.total_days,
        cycle_type=cycle.cycle_type,
        tree_species_id=row["tree_species_id"],
    )


async def assign_tree_species(student_id: str, cycle_id: str, species_id: str) -> None:
    """Assign a tree species to a student for the given cycle."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM student_cycle_progress WHERE student_id = ? AND cycle_id = ?",
            (student_id, cycle_id),
        )
        row = await cursor.fetchone()

        if row:
            await db.execute(
                "UPDATE student_cycle_progress SET tree_species_id = ? WHERE student_id = ? AND cycle_id = ?",
                (species_id, student_id, cycle_id),
            )
        else:
            new_id = f"SCP{uuid.uuid4().hex[:8].upper()}"
            new_stage = "seed"
            await db.execute(
                """INSERT INTO student_cycle_progress
                   (id, student_id, cycle_id, tree_species_id, days_completed,
                    current_stage, last_practice_date)
                   VALUES (?, ?, ?, ?, 0, ?, NULL)""",
                (new_id, student_id, cycle_id, species_id, new_stage),
            )
        await db.commit()

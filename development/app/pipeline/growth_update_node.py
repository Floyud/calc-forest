from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from app.db import get_db
from app.pipeline import BaseNode, NodeResult, NodeStatus

MILESTONE_THRESHOLDS = [
    ("seed", 0),
    ("sprout", 3),
    ("first_leaf", 7),
    ("taller", 14),
    ("branching", 21),
    ("sturdy", 30),
    ("bud", 45),
    ("flowering", 60),
    ("mature", 90),
]


def _compute_stage(days: int) -> str:
    stage = "seed"
    for name, threshold in MILESTONE_THRESHOLDS:
        if days >= threshold:
            stage = name
    return stage


class GrowthUpdateNode(BaseNode):
    @property
    def name(self) -> str:
        return "growth_update"

    @property
    def description(self) -> str:
        return "Record practice day and advance growth milestone"

    async def should_run(self, context: dict[str, Any]) -> bool:
        return "diagnosis" in context

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        diagnosis = context.get("diagnosis")
        student_id = context.get(
            "student_id", diagnosis.student_id if diagnosis else None
        )
        if student_id is None:
            return NodeResult(
                NodeStatus.FAILED, error="Cannot determine student_id"
            )

        grade = context.get("grade", 6)
        today = date.today().isoformat()

        async with get_db() as db:
            row = await db.execute(
                "SELECT id FROM academic_cycles "
                "WHERE grade = ? AND start_date <= ? AND end_date >= ?",
                (grade, today, today),
            )
            cycle = await row.fetchone()
            if not cycle:
                return NodeResult(
                    NodeStatus.SKIPPED,
                    output={"growth_updated": False, "reason": "no active cycle"},
                )

            cycle_id = cycle[0]

            progress_row = await db.execute(
                "SELECT id, days_completed, last_practice_date "
                "FROM student_cycle_progress "
                "WHERE student_id = ? AND cycle_id = ?",
                (student_id, cycle_id),
            )
            progress = await progress_row.fetchone()

            if progress:
                progress_id, days_completed, last_date = (
                    progress[0],
                    progress[1],
                    progress[2],
                )
                if last_date != today:
                    days_completed += 1
                new_stage = _compute_stage(days_completed)
                await db.execute(
                    "UPDATE student_cycle_progress "
                    "SET days_completed = ?, current_stage = ?, last_practice_date = ? "
                    "WHERE id = ?",
                    (days_completed, new_stage, today, progress_id),
                )
            else:
                progress_id = f"scp_{uuid.uuid4().hex[:8]}"
                days_completed = 1
                new_stage = _compute_stage(1)
                await db.execute(
                    "INSERT INTO student_cycle_progress "
                    "(id, student_id, cycle_id, days_completed, current_stage, last_practice_date) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (progress_id, student_id, cycle_id, days_completed, new_stage, today),
                )

            await db.commit()

        return NodeResult(
            NodeStatus.SUCCESS,
            output={
                "growth_updated": True,
                "days_completed": days_completed,
                "current_stage": new_stage,
                "cycle_id": cycle_id,
            },
        )

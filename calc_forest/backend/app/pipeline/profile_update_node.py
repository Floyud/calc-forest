from __future__ import annotations

import json
import uuid
from typing import Any

from app.db import get_db
from app.pipeline import BaseNode, NodeResult, NodeStatus
from app.schemas import DiagnosisResponse


class ProfileUpdateNode(BaseNode):
    @property
    def name(self) -> str:
        return "profile_update"

    @property
    def description(self) -> str:
        return "Persist diagnosis result to student history and update profile"

    async def should_run(self, context: dict[str, Any]) -> bool:
        return "diagnosis" in context

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        diagnosis: DiagnosisResponse = context["diagnosis"]

        record_id = diagnosis.record_id or f"R{uuid.uuid4().hex[:8].upper()}"

        async with get_db() as db:
            existing = await db.execute(
                "SELECT 1 FROM diagnosis_history WHERE id = ?", (record_id,)
            )
            if await existing.fetchone():
                return NodeResult(
                    NodeStatus.SKIPPED, output={"history_id": record_id}
                )

            record = context.get("record")
            steps = (
                json.dumps(record.student_steps, ensure_ascii=False)
                if record and hasattr(record, "student_steps")
                else "[]"
            )

            await db.execute(
                """INSERT INTO diagnosis_history
                   (id, student_id, class_id, grade, problem, correct_answer,
                    student_answer, student_steps, is_correct, error_code,
                    error_label, confidence, evidence, teacher_action,
                    student_feedback, teacher_summary, guidance_mode, review_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record_id,
                    diagnosis.student_id,
                    context.get("class_id"),
                    context.get("grade", 6),
                    context.get("problem", ""),
                    context.get("correct_answer", ""),
                    context.get("student_answer", ""),
                    steps,
                    1 if diagnosis.is_correct else 0,
                    diagnosis.primary_error.code.value,
                    diagnosis.primary_error.label,
                    diagnosis.primary_error.confidence,
                    diagnosis.primary_error.evidence,
                    diagnosis.primary_error.teacher_action,
                    diagnosis.primary_error.student_feedback,
                    diagnosis.teacher_summary,
                    diagnosis.guidance_mode.value,
                    diagnosis.review_status,
                ),
            )
            await db.commit()

        return NodeResult(NodeStatus.SUCCESS, output={"history_id": record_id})

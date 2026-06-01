from __future__ import annotations

import logging
from typing import Any

from app.pipeline import BaseNode, NodeResult, NodeStatus
from app.schemas import DiagnosisResponse

logger = logging.getLogger(__name__)


class TeacherSummaryNode(BaseNode):
    @property
    def name(self) -> str:
        return "teacher_summary"

    @property
    def description(self) -> str:
        return "AI-enhanced teacher summary via Dify workflow"

    async def should_run(self, context: dict[str, Any]) -> bool:
        return "diagnosis" in context

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        diagnosis: DiagnosisResponse = context["diagnosis"]

        diagnosis_dict = {
            "is_correct": diagnosis.is_correct,
            "error_code": diagnosis.primary_error.code.value,
            "error_label": diagnosis.primary_error.label,
            "evidence": diagnosis.primary_error.evidence,
            "teacher_summary": diagnosis.teacher_summary,
        }
        if diagnosis.secondary_errors:
            diagnosis_dict["secondary_errors"] = [
                {"code": e.code.value, "label": e.label}
                for e in diagnosis.secondary_errors
            ]

        student_id = context.get("student_id", "system")
        grade = context.get("grade", 6)
        student_info = f"学生{student_id} {grade}年级"

        try:
            from app.services.dify_client import generate_teacher_summary

            result = await generate_teacher_summary(
                diagnosis=diagnosis_dict,
                session_history="",
                student_info=student_info,
                student_id=student_id,
            )
            return NodeResult(
                NodeStatus.SUCCESS, output={"teacher_summary_dify": result}
            )
        except Exception as exc:
            logger.warning("Dify teacher summary failed: %s", exc)
            return NodeResult(
                NodeStatus.SUCCESS, output={"teacher_summary_dify": None}
            )

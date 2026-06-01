from __future__ import annotations

from typing import Any

from app.pipeline import BaseNode, NodeResult, NodeStatus
from app.schemas import DiagnosisResponse, GuidanceMode, PracticeRecommendationResponse
from app.services.practice import recommend_practice


class PracticeNode(BaseNode):
    @property
    def name(self) -> str:
        return "practice"

    @property
    def description(self) -> str:
        return "Recommend practice items based on diagnosis error code"

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        raw = context.get("diagnosis")
        if raw is None:
            return NodeResult(NodeStatus.FAILED, error="Missing 'diagnosis' in context")
        if isinstance(raw, dict):
            diagnosis = DiagnosisResponse(**raw)
        elif isinstance(raw, DiagnosisResponse):
            diagnosis = raw
        else:
            return NodeResult(
                NodeStatus.FAILED,
                error=f"Expected DiagnosisResponse, got {type(raw).__name__}",
            )

        grade = context.get("grade")
        if grade is None and hasattr(context.get("record"), "grade"):
            grade = context["record"].grade
        if grade is None:
            return NodeResult(NodeStatus.FAILED, error="Missing 'grade' in context")

        guidance_mode = context.get("guidance_mode", GuidanceMode.STANDARD)
        if isinstance(guidance_mode, str):
            guidance_mode = GuidanceMode(guidance_mode)

        try:
            practice: PracticeRecommendationResponse = recommend_practice(
                error_code=diagnosis.primary_error.code,
                grade=grade,
                guidance_mode=guidance_mode,
            )
        except Exception as exc:
            return NodeResult(NodeStatus.FAILED, error=str(exc))
        return NodeResult(NodeStatus.SUCCESS, output={"practice": practice})

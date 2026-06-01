from __future__ import annotations
from typing import Any
from app.pipeline import BaseNode, NodeResult, NodeStatus
from app.services.homework_service import generate_homework


class HomeworkGenNode(BaseNode):
    @property
    def name(self) -> str:
        return "homework_gen"

    @property
    def description(self) -> str:
        return "Generate personalized homework based on error diagnostics"

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        result = await generate_homework(
            class_id=context.get("class_id", "G6C1"),
            grade=context.get("grade", 6),
            student_id=context.get("student_id"),
            error_codes_target=context.get("error_codes_target"),
            problem_count=context.get("problem_count", 5),
            difficulty=context.get("difficulty", "A"),
        )
        return NodeResult(NodeStatus.SUCCESS, output={"homework": result})

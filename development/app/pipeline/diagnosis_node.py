from __future__ import annotations

from typing import Any

from app.pipeline import BaseNode, NodeResult, NodeStatus
from app.schemas import AnswerRecord, DiagnosisResponse
from app.services.diagnosis import diagnose_answer


class DiagnosisNode(BaseNode):
    @property
    def name(self) -> str:
        return "diagnosis"

    @property
    def description(self) -> str:
        return "Rule-based error diagnosis for calculation problems"

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        raw = context.get("record")
        if raw is None:
            return NodeResult(NodeStatus.FAILED, error="Missing 'record' in context")
        if isinstance(raw, dict):
            record = AnswerRecord(**raw)
        elif isinstance(raw, AnswerRecord):
            record = raw
        else:
            return NodeResult(
                NodeStatus.FAILED,
                error=f"Expected AnswerRecord or dict, got {type(raw).__name__}",
            )
        try:
            diagnosis: DiagnosisResponse = diagnose_answer(record)
        except Exception as exc:
            return NodeResult(NodeStatus.FAILED, error=str(exc))
        return NodeResult(NodeStatus.SUCCESS, output={"diagnosis": diagnosis})

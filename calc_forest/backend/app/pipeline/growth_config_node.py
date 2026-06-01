from __future__ import annotations

from typing import Any

from app.pipeline import BaseNode, NodeResult, NodeStatus
from app.services.growth import get_encouragement_message, get_tree_species_by_id


class GrowthConfigNode(BaseNode):
    @property
    def name(self) -> str:
        return "growth_config"

    @property
    def description(self) -> str:
        return "Load tree species config and encouragement message"

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        tree_species_id = context.get("tree_species_id")
        grade = context.get("grade")

        try:
            tree_species = get_tree_species_by_id(tree_species_id)
            encouragement = get_encouragement_message(
                trigger="practice_completed",
                start_grade=grade,
            )
        except Exception as exc:
            return NodeResult(NodeStatus.FAILED, error=str(exc))

        return NodeResult(
            NodeStatus.SUCCESS,
            output={
                "tree_species": tree_species,
                "encouragement_message": encouragement,
            },
        )

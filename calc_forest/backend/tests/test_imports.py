"""Smoke test — verify all modified modules import without errors."""


def test_all_imports():
    from app.services.grading_service import grade_homework
    from app.services.growth import list_tree_species, list_encouragement_rules
    from app.services.forest_service import get_class_forest
    from app.services.class_service import get_class_summary
    from app.services.cycle_service import get_current_cycle
    from app.services.growth_milestone import compute_stage, STAGE_THRESHOLDS
    from app.pipeline.growth_update_node import GrowthUpdateNode
    from app.services.dify_client import (
        _retry_request, _conversation_cache, WORKFLOW_TIMEOUTS,
        clear_conversation, DEFAULT_TIMEOUT,
    )
    from app.services.utils import json_column, placeholders
    from app.schemas import (
        HomeworkGenerateRequest, QuizGenerateRequest,
        QuizResponseRecord, WeakKnowledgePoint,
    )

    assert DEFAULT_TIMEOUT == 45
    assert "student_guidance" in WORKFLOW_TIMEOUTS
    assert len(_conversation_cache) == 0
    assert callable(json_column)
    assert placeholders(3) == "?,?,?"
    assert len(STAGE_THRESHOLDS) == 9
    assert compute_stage(0) == "seed"
    assert compute_stage(100) == "mature"

from __future__ import annotations

from app.pipeline import Pipeline
from app.pipeline.diagnosis_node import DiagnosisNode
from app.pipeline.teacher_summary_node import TeacherSummaryNode
from app.pipeline.practice_node import PracticeNode
from app.pipeline.growth_config_node import GrowthConfigNode


def create_session_draft_pipeline() -> Pipeline:
    """Create the standard session draft pipeline (diagnosis -> teacher_summary -> practice -> growth config)."""
    pipeline = Pipeline("session_draft")
    pipeline.add(DiagnosisNode())
    pipeline.add(TeacherSummaryNode())
    pipeline.add(PracticeNode())
    pipeline.add(GrowthConfigNode())
    return pipeline


def create_full_pipeline() -> Pipeline:
    """Create the full pipeline with profile persistence and growth tracking."""
    from app.pipeline.profile_update_node import ProfileUpdateNode
    from app.pipeline.growth_update_node import GrowthUpdateNode

    pipeline = Pipeline("full_diagnosis")
    pipeline.add(DiagnosisNode())
    pipeline.add(TeacherSummaryNode())
    pipeline.add(PracticeNode())
    pipeline.add(GrowthConfigNode())
    pipeline.add(ProfileUpdateNode())
    pipeline.add(GrowthUpdateNode())
    return pipeline

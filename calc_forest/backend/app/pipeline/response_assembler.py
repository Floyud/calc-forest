from __future__ import annotations

from app.pipeline.student_feedback_builder import build_student_guidance
from app.schemas import (
    DifySessionDraftRequest,
    DifySessionDraftResponse,
    GuidanceMode,
)


def assemble_response(
    context: dict,
    request: DifySessionDraftRequest,
) -> DifySessionDraftResponse:
    if context["_errors"]:
        from fastapi import HTTPException
        raise HTTPException(502, f"Pipeline errors: {context['_errors']}")

    diagnosis = context["diagnosis"]
    diagnosis.guidance_mode = request.guidance_mode
    practice = context["practice"]

    student_feedback = build_student_guidance(
        code=diagnosis.primary_error.code,
        guidance_mode=request.guidance_mode,
        diagnosis_feedback=diagnosis.primary_error.student_feedback,
        is_correct=diagnosis.is_correct,
        practice_count=len(practice.items),
    )

    teacher_summary = diagnosis.teacher_summary
    if practice.items:
        teacher_summary += f" 建议先使用 {practice.estimated_minutes} 分钟以内的 {len(practice.items)} 道短练习。"
    if request.guidance_mode != GuidanceMode.STANDARD:
        teacher_summary += f" 当前引导模式为 {request.guidance_mode.value}。"

    dify_summary = context.get("teacher_summary_dify")
    if dify_summary is not None and "teacher_summary" in dify_summary:
        teacher_summary += f"\n\n---\n\n### AI 深度分析\n{dify_summary['teacher_summary']}"

    return DifySessionDraftResponse(
        diagnosis=diagnosis,
        practice=practice,
        teacher_summary=teacher_summary,
        student_feedback=student_feedback,
        tree_species=context.get("tree_species"),
        encouragement_message=context.get("encouragement_message"),
    )

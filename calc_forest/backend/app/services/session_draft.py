from __future__ import annotations

from app.schemas import AnswerRecord, DifySessionDraftRequest, DifySessionDraftResponse
from app.pipeline.session_draft_pipeline import create_session_draft_pipeline
from app.pipeline.response_assembler import assemble_response


async def build_session_draft(request: DifySessionDraftRequest) -> DifySessionDraftResponse:
    student_steps = []
    if request.student_steps_text:
        student_steps = [line.strip() for line in request.student_steps_text.splitlines() if line.strip()]

    record = AnswerRecord(
        student_id=request.student_id,
        grade=request.grade,
        problem=request.problem_text,
        correct_answer=request.correct_answer_text,
        student_answer=request.student_answer_text,
        student_steps=student_steps,
        source=request.source,
    )

    pipeline = create_session_draft_pipeline()
    context = await pipeline.run({
        "record": record,
        "student_id": request.student_id,
        "grade": request.grade,
        "guidance_mode": request.guidance_mode,
        "class_id": None,
        "tree_species_id": request.tree_species_id,
        "problem": request.problem_text,
        "correct_answer": request.correct_answer_text,
        "student_answer": request.student_answer_text,
    })

    return assemble_response(context, request)

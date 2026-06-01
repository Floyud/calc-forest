"""Tests for pipeline nodes — TeacherSummaryNode, response_assembler, student_feedback_builder."""

import pytest
from unittest.mock import AsyncMock, patch

from app.pipeline import NodeStatus
from app.pipeline.teacher_summary_node import TeacherSummaryNode
from app.pipeline.response_assembler import assemble_response
from app.pipeline.student_feedback_builder import build_student_guidance
from app.schemas import (
    DiagnosisResponse,
    DifySessionDraftRequest,
    ErrorCode,
    ErrorTag,
    GuidanceMode,
    PracticeItem,
    PracticeRecommendationResponse,
    StudentGuidance,
)


def _make_diagnosis(
    error_code: ErrorCode = ErrorCode.BORROW,
    is_correct: bool = False,
) -> DiagnosisResponse:
    return DiagnosisResponse(
        record_id="R001",
        student_id="S001",
        is_correct=is_correct,
        error_code=error_code.value,
        error_label="退位错误",
        confidence=0.9,
        primary_error=ErrorTag(
            code=error_code,
            label="退位错误",
            confidence=0.9,
            evidence="Test evidence",
            teacher_action="Check borrowing",
            student_feedback="Check if you borrowed correctly",
        ),
        teacher_summary="Student made a borrow error.",
        guidance_mode=GuidanceMode.STANDARD,
    )


def _make_practice() -> PracticeRecommendationResponse:
    return PracticeRecommendationResponse(
        grade=6,
        guidance_mode=GuidanceMode.STANDARD,
        level="basic",
        target_error="E03",
        items=[
            PracticeItem(problem="100-37=", reason="Practice borrowing"),
            PracticeItem(problem="200-58=", reason="Practice borrowing"),
        ],
        estimated_minutes=5,
    )


def _make_request() -> DifySessionDraftRequest:
    return DifySessionDraftRequest(
        student_id="S001",
        grade=6,
        problem_text="1002-478=",
        correct_answer_text="524",
        student_answer_text="634",
        guidance_mode=GuidanceMode.STANDARD,
    )


# ---------------------------------------------------------------------------
# TeacherSummaryNode
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_teacher_summary_node_fallback():
    node = TeacherSummaryNode()
    diagnosis = _make_diagnosis()
    context = {"diagnosis": diagnosis, "student_id": "S001", "grade": 6}

    with patch(
        "app.services.dify_client.generate_teacher_summary",
        new_callable=AsyncMock,
        side_effect=Exception("Dify is down"),
    ):
        result = await node.execute(context)

    assert result.status == NodeStatus.SUCCESS
    assert result.output["teacher_summary_dify"] is None


@pytest.mark.asyncio
async def test_teacher_summary_node_success():
    node = TeacherSummaryNode()
    diagnosis = _make_diagnosis()
    context = {"diagnosis": diagnosis, "student_id": "S001", "grade": 6}

    mock_dify_result = {"teacher_summary": "AI 分析：学生退位概念不清晰，建议加强借位训练。"}

    with patch(
        "app.services.dify_client.generate_teacher_summary",
        new_callable=AsyncMock,
        return_value=mock_dify_result,
    ):
        result = await node.execute(context)

    assert result.status == NodeStatus.SUCCESS
    assert result.output["teacher_summary_dify"] == mock_dify_result


@pytest.mark.asyncio
async def test_teacher_summary_node_should_run_with_diagnosis():
    node = TeacherSummaryNode()
    assert await node.should_run({"diagnosis": _make_diagnosis()}) is True


@pytest.mark.asyncio
async def test_teacher_summary_node_should_run_without_diagnosis():
    node = TeacherSummaryNode()
    assert await node.should_run({}) is False


# ---------------------------------------------------------------------------
# response_assembler
# ---------------------------------------------------------------------------

def test_response_assembler_with_dify():
    context = {
        "_errors": [],
        "diagnosis": _make_diagnosis(),
        "practice": _make_practice(),
        "teacher_summary_dify": {"teacher_summary": "AI 深度分析结果"},
        "tree_species": None,
        "encouragement_message": None,
    }
    request = _make_request()
    response = assemble_response(context, request)
    assert "AI 深度分析" in response.teacher_summary
    assert response.diagnosis.primary_error.code == ErrorCode.BORROW
    assert len(response.practice.items) == 2


def test_response_assembler_without_dify():
    context = {
        "_errors": [],
        "diagnosis": _make_diagnosis(),
        "practice": _make_practice(),
        "teacher_summary_dify": None,
        "tree_species": None,
        "encouragement_message": None,
    }
    request = _make_request()
    response = assemble_response(context, request)
    assert "AI 深度分析" not in response.teacher_summary
    assert response.student_feedback.guiding_questions


def test_response_assembler_exploration_mode():
    context = {
        "_errors": [],
        "diagnosis": _make_diagnosis(),
        "practice": _make_practice(),
        "teacher_summary_dify": None,
        "tree_species": None,
        "encouragement_message": None,
    }
    request = DifySessionDraftRequest(
        student_id="S001",
        grade=6,
        problem_text="1002-478=",
        correct_answer_text="524",
        student_answer_text="634",
        guidance_mode=GuidanceMode.EXPLORATION,
    )
    response = assemble_response(context, request)
    assert "exploration" in response.teacher_summary or "探索" in response.student_feedback.next_step


# ---------------------------------------------------------------------------
# student_feedback_builder
# ---------------------------------------------------------------------------

def test_student_feedback_builder_borrow_error():
    guidance = build_student_guidance(
        code=ErrorCode.BORROW,
        guidance_mode=GuidanceMode.STANDARD,
        diagnosis_feedback="Check borrowing step",
        is_correct=False,
        practice_count=3,
    )
    assert isinstance(guidance, StudentGuidance)
    assert guidance.message
    assert len(guidance.guiding_questions) == 2
    assert "3" in guidance.next_step


def test_student_feedback_builder_correct():
    guidance = build_student_guidance(
        code=ErrorCode.CORRECT,
        guidance_mode=GuidanceMode.STANDARD,
        diagnosis_feedback="",
        is_correct=True,
        practice_count=2,
    )
    assert "做对" in guidance.message or "做对" in guidance.key_takeaway


def test_student_feedback_builder_exploration_mode():
    guidance = build_student_guidance(
        code=ErrorCode.CARRY,
        guidance_mode=GuidanceMode.EXPLORATION,
        diagnosis_feedback="Check carry",
        is_correct=False,
        practice_count=4,
    )
    assert "变式" in guidance.next_step or "4" in guidance.next_step


def test_student_feedback_builder_challenge_mode():
    guidance = build_student_guidance(
        code=ErrorCode.BASIC_FACT,
        guidance_mode=GuidanceMode.CHALLENGE,
        diagnosis_feedback="Fact error",
        is_correct=False,
        practice_count=5,
    )
    assert "别的方法" in guidance.next_step or "5" in guidance.next_step


def test_student_feedback_builder_unknown_error_code():
    guidance = build_student_guidance(
        code=ErrorCode.UNKNOWN,
        guidance_mode=GuidanceMode.STANDARD,
        diagnosis_feedback="Unknown error",
        is_correct=False,
        practice_count=1,
    )
    assert guidance.message
    assert guidance.key_takeaway


def test_student_feedback_builder_all_error_codes():
    for code in ErrorCode:
        guidance = build_student_guidance(
            code=code,
            guidance_mode=GuidanceMode.STANDARD,
            diagnosis_feedback="feedback",
            is_correct=False,
            practice_count=2,
        )
        assert isinstance(guidance, StudentGuidance)
        assert guidance.message
        assert guidance.guiding_questions

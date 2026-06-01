"""Grading pipeline — decomposes grade_homework into composable nodes."""
from __future__ import annotations

import logging
import uuid
from collections import Counter
from typing import Any

from app.db import get_db
from app.pipeline import BaseNode, NodeResult, NodeStatus
from app.repositories import diagnosis_repo, homework_repo, stats_repo
from app.schemas import AnswerRecord

logger = logging.getLogger(__name__)


class FetchAnswersNode(BaseNode):
    name = "fetch_answers"

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        homework_id = context["homework_id"]
        student_id = context["student_id"]

        async with get_db() as db:
            answers = await homework_repo.get_ungraded_answers(db, homework_id, student_id)
            if not answers:
                return NodeResult(NodeStatus.FAILED, error="no ungraded answers found")

            hw_info = await homework_repo.get_homework_info(db, homework_id)

        context["_answers"] = [dict(a) for a in answers]
        context["_hw_info"] = dict(hw_info) if hw_info else None
        return NodeResult(NodeStatus.SUCCESS, output={
            "answer_count": len(answers),
        })


class DiagnoseAnswersNode(BaseNode):
    name = "diagnose_answers"

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        from app.services.diagnosis import diagnose_answer

        answers = context["_answers"]
        student_id = context["student_id"]

        diagnosis_results = []
        correct_count = 0
        error_codes = []

        for ans in answers:
            record = AnswerRecord(
                student_id=student_id,
                grade=ans.get("problem_grade") or 6,
                problem=ans["problem"],
                correct_answer=ans["correct_answer"],
                student_answer=ans["student_answer"],
            )

            diagnosis = diagnose_answer(record)
            diagnosis_results.append((ans["id"], record, diagnosis))

            if diagnosis.is_correct:
                correct_count += 1
            else:
                error_codes.append(diagnosis.primary_error.code.value)

        total = len(answers)
        accuracy = correct_count / total if total > 0 else 0.0
        top_errors = [code for code, _ in Counter(error_codes).most_common(3)]

        context["_diagnosis_results"] = diagnosis_results
        context["_correct_count"] = correct_count
        context["_total"] = total
        context["_accuracy"] = accuracy
        context["_top_errors"] = top_errors

        return NodeResult(NodeStatus.SUCCESS, output={
            "total": total,
            "correct_count": correct_count,
            "accuracy": accuracy,
        })


class WriteResultsNode(BaseNode):
    name = "write_results"

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        homework_id = context["homework_id"]
        student_id = context["student_id"]
        hw_info = context.get("_hw_info")
        diagnosis_results = context["_diagnosis_results"]

        async with get_db() as db:
            for ans_id, _record, diag in diagnosis_results:
                await homework_repo.update_answer_diagnosis(
                    db,
                    ans_id,
                    diag.is_correct,
                    diag.primary_error.code.value,
                    diag.primary_error.label,
                    diag.primary_error.confidence,
                    diag.primary_error.evidence,
                    diag.primary_error.teacher_action,
                    diag.primary_error.student_feedback,
                )

            if hw_info:
                records = []
                for _ans_id, record, diag in diagnosis_results:
                    records.append({
                        "student_id": student_id,
                        "class_id": hw_info.get("class_id"),
                        "grade": hw_info.get("grade", 6),
                        "problem": record.problem,
                        "correct_answer": record.correct_answer,
                        "student_answer": record.student_answer,
                        "is_correct": diag.is_correct,
                        "error_code": diag.primary_error.code.value,
                        "error_label": diag.primary_error.label,
                        "confidence": diag.primary_error.confidence,
                        "evidence": diag.primary_error.evidence,
                        "teacher_action": diag.primary_error.teacher_action,
                        "student_feedback": diag.primary_error.student_feedback,
                    })
                await diagnosis_repo.batch_insert(db, records)

            await homework_repo.mark_submission_graded(db, homework_id, student_id)
            await homework_repo.transition_homework_if_all_graded(db, homework_id)

            batch_results = [
                (diag.primary_error.code.value, diag.is_correct)
                for _ans_id, _record, diag in diagnosis_results
            ]
            await stats_repo.batch_update_error_stats(db, student_id, batch_results)

            await db.commit()

        return NodeResult(NodeStatus.SUCCESS)


class UpdateGrowthNode(BaseNode):
    name = "update_growth"

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        from app.pipeline.profile_update_node import ProfileUpdateNode
        from app.pipeline.growth_update_node import GrowthUpdateNode
        from app.schemas import DiagnosisResponse, ErrorTag, ErrorCode, GuidanceMode

        homework_id = context["homework_id"]
        student_id = context["student_id"]
        accuracy = context["_accuracy"]
        top_errors = context["_top_errors"]
        correct_count = context["_correct_count"]
        total = context["_total"]
        diagnosis_results = context["_diagnosis_results"]

        profile_updated = False
        growth_updated = False

        try:
            from app.services.student_service import batch_update_error_stats
        except ImportError:
            pass

        try:
            from app.services.growth_milestone import record_practice_day
            await record_practice_day(student_id)
        except Exception:
            logger.warning("Failed to record practice day for student %s", student_id, exc_info=True)

        try:
            tag = ErrorTag(
                code=ErrorCode(top_errors[0]) if top_errors else ErrorCode.CORRECT,
                label="",
                confidence=0.9,
                evidence="",
                teacher_action="",
                student_feedback="",
            )
            mock_diagnosis = DiagnosisResponse(
                record_id=None,
                student_id=student_id,
                is_correct=accuracy >= 0.8,
                primary_error=tag,
                teacher_summary="",
                guidance_mode=GuidanceMode.STANDARD,
                review_status="pending_teacher_review",
            )

            profile_node = ProfileUpdateNode()
            pr = await profile_node.execute({
                "diagnosis": mock_diagnosis,
                "student_id": student_id,
                "grade": 6,
                "problem": f"homework:{homework_id}",
                "correct_answer": str(correct_count),
                "student_answer": str(total),
            })
            profile_updated = pr.success

            growth_node = GrowthUpdateNode()
            gr = await growth_node.execute({
                "diagnosis": mock_diagnosis,
                "student_id": student_id,
                "grade": 6,
            })
            growth_updated = gr.success
        except Exception:
            logger.warning("Failed to update profile/growth for student %s", student_id, exc_info=True)

        context["_profile_updated"] = profile_updated
        context["_growth_updated"] = growth_updated

        return NodeResult(NodeStatus.SUCCESS, output={
            "profile_updated": profile_updated,
            "growth_updated": growth_updated,
        })


class AIAnalysisNode(BaseNode):
    name = "ai_analysis"

    async def should_run(self, context: dict[str, Any]) -> bool:
        return True

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        student_id = context["student_id"]
        diagnosis_results = context.get("_diagnosis_results", [])

        ai_analysis = None
        try:
            from app.services.dify_client import ai_grade_answers
            from app.services.student_service import get_student

            student = await get_student(student_id)
            student_info = {
                "student_id": student_id,
                "name": student.name if student else "",
                "grade": 6,
            }
            grading_input = {
                "results": [
                    {
                        "sequence": i + 1,
                        "problem": str(record.problem),
                        "student_answer": str(record.student_answer),
                        "correct_answer": str(record.correct_answer),
                        "is_correct": diagnosis.is_correct,
                        "error_code": diagnosis.primary_error.code.value,
                    }
                    for i, (_ans_id, record, diagnosis) in enumerate(diagnosis_results)
                ]
            }
            ai_result = await ai_grade_answers(
                grading_results=grading_input,
                student_info=student_info,
                student_id=student_id,
            )
            if ai_result and not ai_result.get("parse_error"):
                ai_analysis = ai_result
        except Exception:
            logger.warning("AI grading analysis failed for student %s", student_id, exc_info=True)

        context["_ai_analysis"] = ai_analysis
        return NodeResult(NodeStatus.SUCCESS, output={"ai_analysis": ai_analysis})


def create_grading_pipeline() -> "Pipeline":
    from app.pipeline import Pipeline
    return Pipeline("grading", stop_on_fail=True).add(FetchAnswersNode()).add(DiagnoseAnswersNode()).add(WriteResultsNode()).add(UpdateGrowthNode()).add(AIAnalysisNode())

"""AI-powered grading — rule-based diagnosis + LLM per-question and class-level feedback."""
from __future__ import annotations

import json
import logging
import uuid
from collections import Counter
from typing import Any

from app.db import get_db
from app.services.llm_client import call_deepseek

logger = logging.getLogger(__name__)

# Fallback template comments keyed by error code
_FALLBACK_COMMENTS: dict[str, str] = {
    "E01": "口算基础还要多练哦，每天5分钟口算卡片会很有帮助！",
    "E02": "进位的时候别忘了加上去，试试在竖式旁边标小数字提醒自己。",
    "E03": "退位减法有点难，用数位表一步步来就不会出错啦。",
    "E04": "数位要对齐哦，建议用方格纸列竖式练习。",
    "E05": "混合运算记住先乘除后加减，有括号先算括号里的！",
    "E06": "小数点和分数单位要仔细，先统一单位再计算。",
    "E07": "题目里的数字抄对了吗？下次圈出题目数字再写算式。",
    "E08": "中间步骤不要跳哦，把每一步都写出来会更准确。",
    "E09": "这个方法选得不太对，试试画图理解一下算理。",
    "E10": "先读懂题意再下笔，把关键信息画出来会更好。",
    "E11": "做完记得验算！估算一下看看结果合不合理。",
    "E99": "这道题有点特别，我们一起来看看哪里出了问题。",
    "OK": "完全正确，继续保持！",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def ai_grade_homework(
    homework_id: str,
    class_id: str = "G6A1",
) -> dict[str, Any]:
    """Grade all students' homework with rule-based + LLM analysis."""
    from app.services.grading_service import grade_homework
    from app.services.student_service import list_students

    # Step 1: Load homework info
    homework_info = await _load_homework_info(homework_id)
    if not homework_info:
        return {"error": "homework not found", "homework_id": homework_id}

    # Step 2: Get students who submitted answers
    student_ids = await _get_submitted_students(homework_id)
    if not student_ids:
        # Fall back to all class students
        students = await list_students(class_id)
        student_ids = [s.id for s in students]

    # Step 3: Run rule-based grading for each student
    grading_results: list[dict[str, Any]] = []
    for sid in student_ids:
        try:
            result = await grade_homework(homework_id, sid)
            if "error" not in result:
                grading_results.append(result)
        except Exception:
            logger.warning("Rule-based grading failed for student %s", sid, exc_info=True)

    if not grading_results:
        return {"error": "no grading results produced", "homework_id": homework_id}

    # Step 4: LLM class-level analysis
    class_analysis = await _generate_class_analysis(grading_results, homework_info)

    # Step 5: Assemble report
    avg_accuracy = (
        sum(r.get("accuracy", 0) for r in grading_results) / len(grading_results)
        if grading_results else 0.0
    )
    return {
        "homework_id": homework_id,
        "class_id": class_id,
        "homework_info": homework_info,
        "student_count": len(grading_results),
        "avg_accuracy": round(avg_accuracy, 4),
        "student_results": grading_results,
        "class_analysis": class_analysis,
        "review_status": "pending_teacher_review",
    }


async def ai_grade_single_student(
    homework_id: str,
    student_id: str,
) -> dict[str, Any]:
    """Grade one student's homework with per-question LLM feedback."""
    from app.services.grading_service import grade_homework

    # Step 1: Rule-based grading
    grading_result = await grade_homework(homework_id, student_id)
    if "error" in grading_result:
        return grading_result

    # Step 2: Load wrong answers for per-question feedback
    wrong_answers = await _load_wrong_answers(homework_id, student_id)

    # Step 3: Generate LLM feedback for each wrong answer
    comments: list[dict[str, Any]] = []
    for wa in wrong_answers:
        feedback = await _generate_question_feedback(
            problem=wa["problem"],
            correct=wa["correct_answer"],
            student_answer=wa["student_answer"],
            error_code=wa.get("error_code", "E99"),
            error_evidence=wa.get("evidence", ""),
        )
        comments.append({
            "homework_id": homework_id,
            "student_id": student_id,
            "problem_sequence": wa["problem_sequence"],
            "ai_comment": feedback.get("comment", ""),
            "error_code": wa.get("error_code", "E99"),
            "confidence": wa.get("confidence", 0.5),
        })

    # Step 4: Save comments to DB
    if comments:
        await save_grading_comments(homework_id, comments)

    return {
        "homework_id": homework_id,
        "student_id": student_id,
        "grading_result": grading_result,
        "ai_comments": comments,
        "review_status": "pending_teacher_review",
    }


async def save_grading_comments(
    homework_id: str,
    comments: list[dict[str, Any]],
) -> None:
    """Persist AI grading comments to the grading_comments table."""
    async with get_db() as db:
        for c in comments:
            cid = f"GC{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO grading_comments
                   (id, homework_id, student_id, problem_sequence,
                    ai_comment, error_code, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       ai_comment = excluded.ai_comment,
                       confidence = excluded.confidence""",
                (
                    cid,
                    c["homework_id"],
                    c["student_id"],
                    c["problem_sequence"],
                    c.get("ai_comment", ""),
                    c.get("error_code", ""),
                    c.get("confidence", 0.5),
                ),
            )
        await db.commit()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _load_homework_info(homework_id: str) -> dict[str, Any] | None:
    """Load homework metadata + problem count."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM homework WHERE id = ?",
            (homework_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        hw = dict(row)

        pcursor = await db.execute(
            "SELECT COUNT(*) FROM homework_problems WHERE homework_id = ?",
            (homework_id,),
        )
        count_row = await pcursor.fetchone()
        hw["problem_count"] = count_row[0] if count_row else 0
    return hw


async def _get_submitted_students(homework_id: str) -> list[str]:
    """Get student IDs who submitted answers for this homework."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT DISTINCT student_id FROM student_answers WHERE homework_id = ?",
            (homework_id,),
        )
        rows = await cursor.fetchall()
    return [r["student_id"] for r in rows]


async def _load_wrong_answers(
    homework_id: str,
    student_id: str,
) -> list[dict[str, Any]]:
    """Load wrong answers with diagnosis details for a student."""
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT problem_sequence, problem, correct_answer, student_answer,
                      error_code, evidence, confidence
               FROM student_answers
               WHERE homework_id = ? AND student_id = ? AND is_correct = 0
               ORDER BY problem_sequence""",
            (homework_id, student_id),
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def _generate_class_analysis(
    grading_results: list[dict[str, Any]],
    homework_info: dict[str, Any],
) -> dict[str, Any]:
    """Call LLM for class-level analysis of all grading results."""
    # Build summary data
    student_summaries: list[str] = []
    all_errors: list[str] = []
    accuracies: list[float] = []

    for g in grading_results:
        sid = g.get("student_id", "?")
        acc = g.get("accuracy", 0.0)
        errors = g.get("primary_errors", [])
        correct = g.get("correct_count", 0)
        total = g.get("total_problems", 0)
        student_summaries.append(
            f"  学生{sid}: 正确{correct}/{total}题，正确率{acc * 100:.0f}%，"
            f"主要错因: {', '.join(errors) if errors else '无'}"
        )
        accuracies.append(acc)
        all_errors.extend(errors)

    error_distribution = Counter(all_errors)
    error_dist_str = ", ".join(
        f"{code}: {cnt}次" for code, cnt in error_distribution.most_common()
    )

    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

    # Students with lowest accuracy
    sorted_by_acc = sorted(grading_results, key=lambda x: x.get("accuracy", 1.0))
    weak_students = sorted_by_acc[:5]

    weak_str = "\n".join(
        f"  学生{g.get('student_id', '?')}: 正确率{g.get('accuracy', 0) * 100:.0f}%，"
        f"错因: {', '.join(g.get('primary_errors', []))}"
        for g in weak_students
    )

    homework_title = homework_info.get("id", "未知作业")
    problem_count = homework_info.get("problem_count", 0)
    student_count = len(grading_results)

    messages = [
        {
            "role": "system",
            "content": "你是一位经验丰富的小学数学教师，刚批完一班学生的计算作业。请基于数据给出专业、温暖的分析。",
        },
        {
            "role": "user",
            "content": (
                f"作业信息：{homework_title}, {problem_count}道题\n"
                f"全班{student_count}名学生的批改结果如下（全班平均正确率{avg_accuracy * 100:.0f}%）：\n"
                + "\n".join(student_summaries)
                + f"\n\n全班错误分布：{error_dist_str or '无错误'}\n"
                + f"\n薄弱学生（正确率较低）：\n{weak_str or '无'}\n\n"
                "请你：\n"
                "1. 总结全班的整体表现（2-3句话）\n"
                "2. 指出全班最普遍的1-2个错因类型，分析可能的教学原因\n"
                "3. 对3-5名薄弱学生给出个性化的辅导建议（每生1-2句话）\n"
                "4. 给出下一步教学建议\n\n"
                '返回JSON：\n{\n  "class_summary": "全班表现总结",\n'
                '  "common_errors_analysis": "常见错因分析",\n'
                '  "student_recommendations": [{"student_id": "", "comment": ""}],\n'
                '  "teaching_suggestions": "下一步教学建议"\n}'
            ),
        },
    ]

    try:
        raw = await call_deepseek(
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        content = raw["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        analysis = json.loads(content)
        return analysis
    except Exception:
        logger.warning("LLM class analysis failed, using template", exc_info=True)
        top_errors = [code for code, _ in error_distribution.most_common(2)]
        return {
            "class_summary": f"全班{student_count}名学生完成作业，平均正确率{avg_accuracy * 100:.0f}%。",
            "common_errors_analysis": f"最常见的错因类型为{', '.join(top_errors)}，建议加强相关练习。" if top_errors else "无明显集中错因。",
            "student_recommendations": [
                {"student_id": g.get("student_id", ""), "comment": f"建议重点练习{', '.join(g.get('primary_errors', ['基础计算']))}类型题目。"}
                for g in weak_students[:5]
            ],
            "teaching_suggestions": "建议针对高频错因设计专项练习，关注薄弱学生的个别辅导。",
        }


async def _generate_question_feedback(
    problem: str,
    correct: str,
    student_answer: str,
    error_code: str,
    error_evidence: str,
) -> dict[str, str]:
    """Call LLM for per-question teacher-like feedback."""
    messages = [
        {
            "role": "system",
            "content": "你是一位温柔但有要求的小学数学老师，正在给学生的计算题写批改评语。所有内容用中文。",
        },
        {
            "role": "user",
            "content": (
                f"题目：{problem}\n"
                f"正确答案：{correct}\n"
                f"学生写了：{student_answer}\n"
                f"系统诊断：{error_code} - {error_evidence}\n\n"
                "请写一句简短的批改评语（不超过50字），要求：\n"
                "- 先肯定做得好的地方\n"
                "- 温柔但明确地指出问题\n"
                "- 给一个小提示帮助改进\n\n"
                '返回JSON：{"comment": "批改评语"}'
            ),
        },
    ]

    try:
        raw = await call_deepseek(
            messages=messages,
            temperature=0.7,
            max_tokens=256,
            response_format={"type": "json_object"},
        )
        content = raw["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(content)
    except Exception:
        logger.warning("LLM per-question feedback failed, using template", exc_info=True)
        fallback = _FALLBACK_COMMENTS.get(error_code, _FALLBACK_COMMENTS["E99"])
        return {"comment": fallback}

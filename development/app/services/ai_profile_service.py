"""AI student profiling — analyzes grading data to build learning portraits."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from app.db import get_db
from app.services.llm_client import call_deepseek

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def ai_analyze_student(
    student_id: str,
    homework_id: str | None = None,
) -> dict[str, Any]:
    """Analyze a single student via LLM using their error history and trajectory."""
    student_data = await _load_student_data(student_id, homework_id)
    if not student_data:
        return {"error": "student not found", "student_id": student_id}

    messages, _prompt_text = _build_student_analysis_prompt(student_data)
    analysis = await _call_llm_json(messages, student_id, "ai_analysis")

    if analysis:
        await _save_profile_snapshot(student_id, "ai_analysis", analysis)

    return {
        "student_id": student_id,
        "student_data_summary": {
            "name": student_data.get("name", ""),
            "accuracy": student_data.get("accuracy", 0.0),
            "trend": student_data.get("trend", "stable"),
            "error_codes_count": len(student_data.get("error_code_accuracy", {})),
        },
        "analysis": analysis or _fallback_student_analysis(student_data),
    }


async def ai_analyze_class(
    class_id: str = "G6C1",
) -> dict[str, Any]:
    """Analyze all students in a class, returning per-student snapshots."""
    from app.services.student_service import list_students

    students = await list_students(class_id)
    if not students:
        return {"error": "class not found or empty", "class_id": class_id}

    snapshots: list[dict[str, Any]] = []
    for s in students:
        try:
            result = await ai_analyze_student(s.student_id)
            snapshots.append(result)
        except Exception:
            logger.warning("Failed to analyze student %s", s.student_id, exc_info=True)
            snapshots.append({"student_id": s.student_id, "error": "analysis failed"})

    with_analysis = [s for s in snapshots if "analysis" in s and "error" not in s.get("analysis", {})]
    avg_acc = 0.0
    if with_analysis:
        accs = [
            s.get("student_data_summary", {}).get("accuracy", 0.0)
            for s in with_analysis
        ]
        avg_acc = sum(accs) / len(accs) if accs else 0.0

    return {
        "class_id": class_id,
        "student_count": len(snapshots),
        "analyzed_count": len(with_analysis),
        "average_accuracy": round(avg_acc, 4),
        "students": snapshots,
    }


async def ai_update_profiles_after_grading(
    homework_id: str,
) -> dict[str, Any]:
    """For each student who submitted homework, run LLM profile analysis and update DB."""
    from app.services.ai_grading_service import _get_submitted_students

    student_ids = await _get_submitted_students(homework_id)
    if not student_ids:
        return {"error": "no submissions found", "homework_id": homework_id}

    updated: list[dict[str, Any]] = []
    for sid in student_ids:
        try:
            result = await ai_analyze_student(sid, homework_id=homework_id)
            analysis = result.get("analysis")
            if analysis:
                await _update_student_profile(sid, analysis)
                updated.append({"student_id": sid, "status": "updated"})
            else:
                updated.append({"student_id": sid, "status": "no_analysis"})
        except Exception:
            logger.warning("Profile update failed for student %s", sid, exc_info=True)
            updated.append({"student_id": sid, "status": "error"})

    return {
        "homework_id": homework_id,
        "students_profiled": len(student_ids),
        "updated_count": sum(1 for u in updated if u["status"] == "updated"),
        "results": updated,
    }


# ---------------------------------------------------------------------------
# Internal: data loading
# ---------------------------------------------------------------------------

async def _load_student_data(
    student_id: str,
    homework_id: str | None = None,
) -> dict[str, Any] | None:
    """Load student info, error stats, trajectory, and optional homework results."""
    async with get_db() as db:
        s_cursor = await db.execute(
            "SELECT * FROM students WHERE id = ?", (student_id,),
        )
        s_row = await s_cursor.fetchone()
        if not s_row:
            return None
        student = dict(s_row)

        ses_cursor = await db.execute(
            """SELECT error_code, total_attempts, correct_count
               FROM student_error_stats WHERE student_id = ?""",
            (student_id,),
        )
        error_stats = [dict(r) for r in await ses_cursor.fetchall()]

        traj_cursor = await db.execute(
            """SELECT error_code, error_count, correct_count, accuracy, week_number
               FROM student_error_trajectory WHERE student_id = ?
               ORDER BY week_number DESC LIMIT 10""",
            (student_id,),
        )
        trajectory = [dict(r) for r in await traj_cursor.fetchall()]

        dh_cursor = await db.execute(
            """SELECT problem, correct_answer, student_answer, is_correct,
                      error_code, evidence, created_at
               FROM diagnosis_history WHERE student_id = ?
               ORDER BY created_at DESC LIMIT 20""",
            (student_id,),
        )
        recent_records = [dict(r) for r in await dh_cursor.fetchall()]

    total_attempts = sum(e["total_attempts"] for e in error_stats)
    total_correct = sum(e["correct_count"] for e in error_stats)
    accuracy = total_correct / total_attempts if total_attempts > 0 else 0.0

    error_code_accuracy: dict[str, float] = {}
    for e in error_stats:
        if e["total_attempts"] > 0:
            error_code_accuracy[e["error_code"]] = round(
                e["correct_count"] / e["total_attempts"], 4
            )

    recent_correct = sum(1 for r in recent_records if r.get("is_correct"))
    recent_total = len(recent_records)
    recent_acc = recent_correct / recent_total if recent_total > 0 else 0.0

    if total_attempts >= 10:
        trend = "improving" if recent_acc > accuracy + 0.1 else (
            "declining" if recent_acc < accuracy - 0.1 else "stable"
        )
    else:
        trend = "stable"

    data: dict[str, Any] = {
        "student_id": student_id,
        "name": student.get("name", ""),
        "grade": student.get("grade", 6),
        "personality_tags": json.loads(student.get("personality_tags", "[]")),
        "learning_style": student.get("learning_style", ""),
        "total_attempts": total_attempts,
        "total_correct": total_correct,
        "accuracy": round(accuracy, 4),
        "trend": trend,
        "error_code_accuracy": error_code_accuracy,
        "trajectory": trajectory,
        "recent_records": recent_records[:10],
    }

    if homework_id:
        async with get_db() as db:
            hw_cursor = await db.execute(
                """SELECT problem_sequence, problem, correct_answer, student_answer,
                          is_correct, error_code, evidence
                   FROM student_answers
                   WHERE homework_id = ? AND student_id = ?
                   ORDER BY problem_sequence""",
                (homework_id, student_id),
            )
            hw_answers = [dict(r) for r in await hw_cursor.fetchall()]
            data["homework_results"] = hw_answers

    return data


# ---------------------------------------------------------------------------
# Internal: prompt building
# ---------------------------------------------------------------------------

def _build_student_analysis_prompt(
    student_data: dict[str, Any],
) -> tuple[list[dict[str, str]], str]:
    """Build LLM messages for student analysis. Returns (messages, prompt_text)."""
    name = student_data.get("name", "未知")
    sid = student_data.get("student_id", "?")
    acc = student_data.get("accuracy", 0.0) * 100
    trend_map = {"improving": "进步中↑", "declining": "有所下滑↓", "stable": "保持稳定→"}
    trend = trend_map.get(student_data.get("trend", "stable"), "保持稳定→")

    eca = student_data.get("error_code_accuracy", {})
    if eca:
        eca_lines = [
            f"  {code}: {round(rate * 100, 1)}%正确率"
            for code, rate in sorted(eca.items(), key=lambda x: x[1])
        ]
        eca_table = "\n".join(eca_lines)
    else:
        eca_table = "  暂无错因统计数据"

    recent = student_data.get("recent_records", [])
    recent_count = len(recent)
    if recent:
        recent_lines = [
            f"  {r.get('problem', '?')} = {r.get('student_answer', '?')} "
            f"({'✓' if r.get('is_correct') else '✗ ' + str(r.get('error_code', ''))})"
            for r in recent[:8]
        ]
        recent_str = "\n".join(recent_lines)
    else:
        recent_str = "  暂无"

    hw = student_data.get("homework_results")
    hw_section = ""
    if hw:
        hw_correct = sum(1 for a in hw if a.get("is_correct"))
        hw_lines = [
            f"  第{a.get('problem_sequence', '?')}题: {a.get('problem', '?')} "
            f"→ 写了{a.get('student_answer', '?')} "
            f"({'✓' if a.get('is_correct') else '✗ ' + str(a.get('error_code', ''))})"
            for a in hw[:10]
        ]
        hw_section = (
            f"\n本次作业结果（{hw_correct}/{len(hw)}正确）：\n"
            + "\n".join(hw_lines) + "\n"
        )

    prompt = (
        f"学生：{name} ({sid})\n"
        f"年级：六年级\n"
        f"总体正确率：{acc:.1f}%\n"
        f"最近趋势：{trend}\n\n"
        f"各错因类型正确率（从低到高）：\n{eca_table}\n\n"
        f"最近{recent_count}次作答记录：\n{recent_str}\n"
        f"{hw_section}\n"
        "请分析：\n"
        "1. 学习画像（一句话概括）\n"
        "2. 主要薄弱环节（列出top 3错因，每项给出原因分析）\n"
        "3. 学习风格推断（视觉型/听觉型/动手型，基于错误模式推断）\n"
        "4. 近期进步和退步的地方\n"
        "5. 下一步教学建议（3条具体可执行的建议）\n"
        "6. 成长叙事（用2-3句话描述这个学生的成长故事，温暖鼓励的语调）\n\n"
        '返回JSON：\n{\n  "portrait_summary": "一句话画像",\n'
        '  "weaknesses": [{"error_code": "", "description": "", "cause_analysis": ""}],\n'
        '  "learning_style": "",\n'
        '  "improvements": "进步的地方",\n'
        '  "regressions": "退步的地方",\n'
        '  "teaching_suggestions": ["建议1", "建议2", "建议3"],\n'
        '  "growth_narrative": "成长叙事",\n'
        '  "personality_tags": ["标签1", "标签2", "标签3"]\n}'
    )

    messages = [
        {
            "role": "system",
            "content": (
                "你是一位教育数据分析师，专门分析小学生的数学学习情况。"
                "你的分析要基于数据说话，语言简洁，适合老师快速阅读。"
                "所有内容用中文。personality_tags必须是正面、温暖的标签，"
                "例如'细心观察者'、'勇于尝试'、'稳步进步中'，"
                "绝对不能使用'粗心'、'基础差'、'差生'等负面标签。"
            ),
        },
        {"role": "user", "content": prompt},
    ]
    return messages, prompt


# ---------------------------------------------------------------------------
# Internal: LLM calls
# ---------------------------------------------------------------------------

async def _call_llm_json(
    messages: list[dict[str, str]],
    student_id: str,
    snapshot_type: str,
) -> dict[str, Any] | None:
    """Call LLM and parse JSON response. Returns None on failure."""
    try:
        raw = await call_deepseek(
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        content = raw["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(content)
    except Exception:
        logger.warning(
            "LLM analysis failed for student %s (%s)", student_id, snapshot_type, exc_info=True,
        )
        return None


def _fallback_student_analysis(student_data: dict[str, Any]) -> dict[str, Any]:
    """Template analysis when LLM is unavailable."""
    eca = student_data.get("error_code_accuracy", {})
    sorted_errors = sorted(eca.items(), key=lambda x: x[1])
    top_weak = sorted_errors[:3]

    weaknesses = [
        {
            "error_code": code,
            "description": f"正确率{round(rate * 100, 1)}%",
            "cause_analysis": "需要加强该类型题目的针对性练习",
        }
        for code, rate in top_weak
    ]

    trend = student_data.get("trend", "stable")
    acc = student_data.get("accuracy", 0.0)

    if trend == "improving":
        tags = ["稳步进步中", "潜力股"]
        improvements = "近期正确率有明显提升"
        regressions = ""
    elif trend == "declining":
        tags = ["需要关注", "可以更好"]
        improvements = ""
        regressions = "近期正确率有所下滑，建议增加练习频次"
    else:
        tags = ["踏实努力", "值得期待"]
        improvements = "表现稳定"
        regressions = ""

    if acc >= 0.8:
        tags.insert(0, "细心观察者")
    elif acc >= 0.6:
        tags.insert(0, "勇于尝试")
    else:
        tags.insert(0, "坚持不懈")

    return {
        "portrait_summary": (
            f"正确率{acc * 100:.1f}%，"
            + ("持续进步中" if trend == "improving" else "保持稳定中" if trend == "stable" else "需要更多关注")
        ),
        "weaknesses": weaknesses,
        "learning_style": "需要更多数据来推断",
        "improvements": improvements,
        "regressions": regressions,
        "teaching_suggestions": [
            "保持每日少量计算练习的习惯",
            "针对薄弱错因类型做专项练习",
            "鼓励学生说出计算过程，帮助理解算理",
        ],
        "growth_narrative": "这位同学在计算练习中展现了坚持的品质，继续加油，每一点进步都值得肯定！",
        "personality_tags": tags[:3],
    }


# ---------------------------------------------------------------------------
# Internal: persistence
# ---------------------------------------------------------------------------

async def _save_profile_snapshot(
    student_id: str,
    snapshot_type: str,
    analysis: dict[str, Any],
) -> None:
    """Insert a profile snapshot record."""
    sid = f"PS{uuid.uuid4().hex[:8].upper()}"
    async with get_db() as db:
        await db.execute(
            """INSERT INTO profile_snapshots
               (id, student_id, snapshot_type, analysis_json,
                portrait_summary, personality_tags, growth_narrative)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                sid,
                student_id,
                snapshot_type,
                json.dumps(analysis, ensure_ascii=False),
                analysis.get("portrait_summary", ""),
                json.dumps(analysis.get("personality_tags", []), ensure_ascii=False),
                analysis.get("growth_narrative", ""),
            ),
        )
        await db.commit()


async def _update_student_profile(
    student_id: str,
    analysis: dict[str, Any],
) -> None:
    """Update students table with new personality_tags and learning_style from analysis."""
    tags = analysis.get("personality_tags", [])
    style = analysis.get("learning_style", "")
    narrative = analysis.get("growth_narrative", "")

    async with get_db() as db:
        await db.execute(
            """UPDATE students SET
               personality_tags = ?,
               learning_style = ?,
               notes = ?
               WHERE id = ?""",
            (
                json.dumps(tags, ensure_ascii=False),
                style,
                narrative,
                student_id,
            ),
        )
        await db.commit()

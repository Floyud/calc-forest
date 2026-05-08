"""作业全生命周期编排器 — 串联 生成→模拟→批改→画像 四个阶段。

每个阶段可独立运行，也可通过 run_full_lifecycle 一键执行。
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def run_full_lifecycle(
    class_id: str = "G6A1",
    *,
    grade: int = 6,
    problem_count: int = 5,
    error_codes: list[str] | None = None,
    difficulty: str = "B",
    unit_title: str = "",
    use_llm: bool = False,
    simulate: bool = True,
    ai_grade: bool = True,
    ai_profile: bool = True,
) -> dict[str, Any]:
    """编排完整的作业生命周期: 生成 → 模拟 → 批改 → 画像。

    Args:
        class_id: 班级ID
        grade: 年级
        problem_count: 题目数量
        error_codes: 目标错因代码列表
        difficulty: 难度 (A/B/C)
        unit_title: 单元标题
        use_llm: 是否使用 LLM 生成题目
        simulate: 是否运行模拟阶段
        ai_grade: 是否运行 AI 批改阶段
        ai_profile: 是否运行 AI 画像阶段

    Returns:
        包含所有阶段结果的完整报告
    """
    steps_completed: list[str] = []

    # === Step 1: 生成作业 ===
    from app.services.homework_service import generate_homework, assign_homework

    hw = await generate_homework(
        class_id=class_id,
        grade=grade,
        error_codes_target=error_codes,
        problem_count=problem_count,
        difficulty=difficulty,
    )
    await assign_homework(hw["homework_id"])
    steps_completed.append("generate")

    sim_result: dict[str, Any] = {"student_count": 0, "summary": {}}
    grading_result: dict[str, Any] = {}
    profiling_result: dict[str, Any] = {}

    # === Step 2: 模拟学生作答 ===
    if simulate:
        from app.services.student_simulator import simulate_class_answers
        from app.services.grading_service import submit_homework

        sim = await simulate_class_answers(hw["homework_id"], class_id)
        student_answers = sim.get("student_answers") or sim.get("answers", {})
        for student_id, answers in student_answers.items():
            await submit_homework(hw["homework_id"], student_id, answers)

        sim_result = {
            "student_count": len(student_answers),
            "summary": sim.get("summary", {}),
        }
        steps_completed.append("simulate")

    # === Step 3: AI 批改 ===
    if ai_grade:
        from app.services.ai_grading_service import ai_grade_homework

        grading_result = await ai_grade_homework(hw["homework_id"], class_id)
        steps_completed.append("grade")

    # === Step 4: AI 画像 ===
    if ai_profile:
        from app.services.ai_profile_service import ai_update_profiles_after_grading

        profiling_result = await ai_update_profiles_after_grading(hw["homework_id"])
        steps_completed.append("profile")

    return {
        "homework_id": hw["homework_id"],
        "class_id": class_id,
        "generation": hw,
        "simulation": sim_result,
        "grading": grading_result,
        "profiling": profiling_result,
        "lifecycle_status": "completed",
        "steps_completed": steps_completed,
    }


async def run_single_step(step: str, homework_id: str, **kwargs: Any) -> dict[str, Any]:
    """运行生命周期的单个阶段。

    Args:
        step: 阶段名称 ("generate", "simulate", "grade", "profile")
        homework_id: 作业ID
        **kwargs: 各阶段所需的额外参数

    Returns:
        该阶段的执行结果
    """
    if step == "generate":
        from app.services.homework_service import generate_homework, assign_homework

        hw = await generate_homework(
            class_id=kwargs.get("class_id", "G6A1"),
            grade=kwargs.get("grade", 6),
            error_codes_target=kwargs.get("error_codes"),
            problem_count=kwargs.get("problem_count", 5),
            difficulty=kwargs.get("difficulty", "B"),
        )
        await assign_homework(hw["homework_id"])
        return {"step": "generate", "result": hw}

    elif step == "simulate":
        from app.services.student_simulator import simulate_class_answers
        from app.services.grading_service import submit_homework

        class_id = kwargs.get("class_id", "G6A1")
        sim = await simulate_class_answers(homework_id, class_id)
        submitted = {}
        for student_id, answers in sim["answers"].items():
            result = await submit_homework(homework_id, student_id, answers)
            submitted[student_id] = result
        return {
            "step": "simulate",
            "result": {"simulation": sim["summary"], "submissions": submitted},
        }

    elif step == "grade":
        from app.services.ai_grading_service import ai_grade_homework

        class_id = kwargs.get("class_id", "G6A1")
        result = await ai_grade_homework(homework_id, class_id)
        return {"step": "grade", "result": result}

    elif step == "profile":
        from app.services.ai_profile_service import ai_update_profiles_after_grading

        result = await ai_update_profiles_after_grading(homework_id)
        return {"step": "profile", "result": result}

    else:
        return {"error": f"未知步骤: {step}", "valid_steps": ["generate", "simulate", "grade", "profile"]}


async def get_lifecycle_status(homework_id: str) -> dict[str, Any]:
    """查询一份作业的生命周期完成状态。

    检查: 作业是否存在 → 是否有提交 → 是否已批改 → 是否已生成画像
    """
    from app.db import get_db

    async with get_db() as db:
        # 作业是否存在
        hw_cursor = await db.execute("SELECT * FROM homework WHERE id = ?", (homework_id,))
        hw = await hw_cursor.fetchone()
        if not hw:
            return {"homework_id": homework_id, "exists": False}

        # 是否有学生提交
        sub_cursor = await db.execute(
            "SELECT COUNT(DISTINCT student_id) FROM student_answers WHERE homework_id = ?",
            (homework_id,),
        )
        submission_count = (await sub_cursor.fetchone())[0]

        # 是否已批改（有 error_code 的答案数）
        graded_cursor = await db.execute(
            "SELECT COUNT(*) FROM student_answers WHERE homework_id = ? AND error_code IS NOT NULL",
            (homework_id,),
        )
        graded_count = (await graded_cursor.fetchone())[0]

        # 是否已生成 AI 评语
        comments_cursor = await db.execute(
            "SELECT COUNT(*) FROM grading_comments WHERE homework_id = ?",
            (homework_id,),
        )
        comments_count = (await comments_cursor.fetchone())[0]

        # 是否已生成画像
        profile_cursor = await db.execute(
            "SELECT COUNT(*) FROM profile_snapshots WHERE snapshot_type = 'post_homework' AND id IN "
            "(SELECT id FROM profile_snapshots WHERE analysis_json LIKE ?)",
            (f'%{homework_id}%',),
        )
        profile_count = 0
        # 更可靠的查询：通过学生ID关联
        student_cursor = await db.execute(
            "SELECT DISTINCT student_id FROM student_answers WHERE homework_id = ?",
            (homework_id,),
        )
        student_ids = [r[0] for r in await student_cursor.fetchall()]
        if student_ids:
            placeholders = ",".join("?" for _ in student_ids)
            profile_cursor = await db.execute(
                f"SELECT COUNT(DISTINCT student_id) FROM profile_snapshots "
                f"WHERE student_id IN ({placeholders}) AND snapshot_type = 'post_homework'",
                student_ids,
            )
            profile_count = (await profile_cursor.fetchone())[0]

    steps = ["generate"]
    if submission_count > 0:
        steps.append("simulate")
    if graded_count > 0:
        steps.append("grade")
    if profile_count > 0:
        steps.append("profile")

    return {
        "homework_id": homework_id,
        "exists": True,
        "status": dict(hw).get("status", "unknown"),
        "submission_count": submission_count,
        "graded_answer_count": graded_count,
        "ai_comments_count": comments_count,
        "profiled_student_count": profile_count,
        "steps_completed": steps,
        "lifecycle_status": "completed" if len(steps) == 4 else "partial",
    }

from __future__ import annotations
import json
import uuid
from datetime import date
from typing import Any

from app.db import get_db
from app.services.problem_generator import (
    generate_problems_by_exercise_type,
    generate_quiz_problems,
)


_EXERCISE_TYPE_IDS: dict[str, list[str]] = {
    "口算": ["ET-0105", "ET-0106", "ET-0107"],
    "竖式计算": ["ET-0205", "ET-0206", "ET-0203"],
    "脱式计算": ["ET-0304", "ET-0305", "ET-0705"],
    "简便运算": ["ET-0408", "ET-0403", "ET-0410", "ET-0405"],
    "列式计算": ["ET-0502", "ET-0503", "ET-0504", "ET-0505"],
    "图形计算": ["ET-0601", "ET-0602", "ET-0603", "ET-0604", "ET-0605"],
    "分数运算": ["ET-0703", "ET-0704", "ET-0705", "ET-0708", "ET-0710", "ET-0711", "ET-0712"],
    "比与比例": ["ET-0901", "ET-0902", "ET-0903", "ET-0904", "ET-0905", "ET-0906"],
}


async def validate_class_exists(class_id: str) -> None:
    """Raise ValueError if class_id not found."""
    async with get_db() as db:
        cursor = await db.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
        if await cursor.fetchone() is None:
            raise ValueError(f"班级 {class_id} 不存在")


async def get_class_top_errors(class_id: str, limit: int = 3) -> list[str]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT error_code, COUNT(*) as cnt FROM diagnosis_history
               WHERE class_id = ? AND is_correct = 0
               GROUP BY error_code ORDER BY cnt DESC LIMIT ?""",
            (class_id, limit),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_student_top_errors(student_id: str, limit: int = 3) -> list[str]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT error_code, COUNT(*) as cnt FROM diagnosis_history
               WHERE student_id = ? AND is_correct = 0
               GROUP BY error_code ORDER BY cnt DESC LIMIT ?""",
            (student_id, limit),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def _get_student_accuracy(student_id: str) -> float | None:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT SUM(total_attempts) as total,
                      SUM(correct_count) as correct
               FROM student_error_stats WHERE student_id = ?""",
            (student_id,),
        )
        row = await cursor.fetchone()
        if row and row["total"] and row["total"] > 0:
            return row["correct"] / row["total"]
    return None


def _difficulty_distribution_for(accuracy: float) -> dict[str, float]:
    if accuracy < 0.6:
        return {"A": 0.6, "B": 0.4}
    if accuracy < 0.8:
        return {"A": 0.3, "B": 0.5, "C": 0.2}
    return {"B": 0.4, "C": 0.6}


def _difficulty_distribution_for_strategy(
    strategy: str,
    fixed_difficulty: str,
    accuracy: float | None,
) -> dict[str, float] | None:
    if strategy in {"A", "B", "C"}:
        return {strategy: 1.0}
    if strategy == "mixed":
        return {"A": 0.2, "B": 0.4, "C": 0.4}
    if strategy == "auto" and accuracy is not None:
        return _difficulty_distribution_for(accuracy)
    return None if fixed_difficulty in {"A", "B", "C"} else {"B": 1.0}


def _expand_difficulties(
    total_count: int,
    difficulty: str,
    distribution: dict[str, float] | None,
) -> list[str]:
    if not distribution:
        return [difficulty] * total_count

    sequence: list[str] = []
    remaining = total_count
    levels = list(distribution.keys())
    for idx, level in enumerate(levels):
        if idx == len(levels) - 1:
            count = remaining
        else:
            count = max(0, round(total_count * distribution[level]))
            remaining -= count
        sequence.extend([level] * count)

    if len(sequence) < total_count:
        sequence.extend([difficulty] * (total_count - len(sequence)))
    return sequence[:total_count]


def _generate_by_exercise_types(
    exercise_types: list[str],
    total_count: int,
    difficulty: str,
    difficulty_distribution: dict[str, float] | None,
) -> list:
    type_groups = [
        _EXERCISE_TYPE_IDS[exercise_type]
        for exercise_type in exercise_types
        if exercise_type in _EXERCISE_TYPE_IDS
    ]
    if not type_groups:
        return []

    difficulties = _expand_difficulties(total_count, difficulty, difficulty_distribution)
    problems = []
    seen: set[str] = set()
    group_offsets = [0] * len(type_groups)
    attempts = 0

    while len(problems) < total_count and attempts < total_count * 24:
        group_index = len(problems) % len(type_groups)
        group = type_groups[group_index]
        type_id = group[group_offsets[group_index] % len(group)]
        group_offsets[group_index] += 1
        diff = difficulties[len(problems) % len(difficulties)]
        generated = generate_problems_by_exercise_type(
            exercise_type_id=type_id,
            difficulty=diff,
            count=1,
            seed=uuid.uuid4().int % (2**31),
        )
        attempts += 1
        if not generated:
            continue
        problem = generated[0]
        if problem.problem in seen:
            continue
        seen.add(problem.problem)
        problems.append(problem)

    return problems


async def generate_homework(
    class_id: str,
    grade: int = 6,
    student_id: str | None = None,
    error_codes_target: list[str] | None = None,
    problem_count: int = 5,
    difficulty: str = "A",
    exercise_types: list[str] | None = None,
    difficulty_strategy: str = "auto",
) -> dict[str, Any]:
    if not error_codes_target:
        if student_id:
            error_codes_target = await get_student_top_errors(student_id)
        else:
            error_codes_target = await get_class_top_errors(class_id)

    if not error_codes_target:
        error_codes_target = ["E03"]

    accuracy: float | None = None
    if student_id:
        accuracy = await _get_student_accuracy(student_id)

    diff_dist = _difficulty_distribution_for_strategy(
        difficulty_strategy,
        difficulty,
        accuracy,
    )

    problems = _generate_by_exercise_types(
        exercise_types=exercise_types or [],
        total_count=problem_count,
        difficulty=difficulty,
        difficulty_distribution=diff_dist,
    )
    if len(problems) < problem_count:
        problems.extend(
            generate_quiz_problems(
                error_codes=error_codes_target,
                difficulty=difficulty,
                total_count=problem_count - len(problems),
                difficulty_distribution=diff_dist,
            )
        )

    homework_id = f"HW{uuid.uuid4().hex[:8].upper()}"
    today = date.today().isoformat()

    async with get_db() as db:
        await db.execute(
            """INSERT INTO homework (id, class_id, student_id, grade, knowledge_points,
               error_codes_target, status, generated_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'draft', 'system', ?)""",
            (
                homework_id,
                class_id,
                student_id,
                grade,
                json.dumps(list({p.knowledge_point for p in problems})),
                json.dumps(error_codes_target),
                today,
            ),
        )

        for i, p in enumerate(problems, 1):
            pid = f"HP{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO homework_problems (id, homework_id, sequence, problem,
                   correct_answer, knowledge_point, target_error_code, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (pid, homework_id, i, p.problem, p.correct_answer,
                 p.knowledge_point, p.error_code, p.difficulty),
            )

        await db.commit()

    return await get_homework(homework_id)


async def get_homework(homework_id: str) -> dict[str, Any] | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM homework WHERE id = ?", (homework_id,))
        row = await cursor.fetchone()
        if not row:
            return None

        result = dict(row)
        result["homework_id"] = result["id"]
        result["knowledge_points"] = json.loads(result.get("knowledge_points", "[]"))
        result["error_codes_target"] = json.loads(result.get("error_codes_target", "[]"))

        pcursor = await db.execute(
            "SELECT * FROM homework_problems WHERE homework_id = ? ORDER BY sequence",
            (homework_id,),
        )
        problems = await pcursor.fetchall()
        result["problems"] = [dict(p) for p in problems]

        return result


async def assign_homework(homework_id: str, due_date: str | None = None) -> bool:
    today = date.today().isoformat()
    async with get_db() as db:
        await db.execute(
            "UPDATE homework SET status = 'assigned', assigned_date = ?, due_date = ? WHERE id = ?",
            (today, due_date, homework_id),
        )
        await db.commit()
    return True


async def generate_and_insert_homework(
    class_id: str,
    grade: int,
    difficulty: str,
    problem_count: int,
    use_llm: bool,
    semester: int = 1,
    unit_title: str = "",
    error_codes: list[str] | None = None,
) -> dict:
    if use_llm:
        from app.services.llm_client import generate_math_problems

        try:
            raw_problems = await generate_math_problems(
                grade=grade, semester=semester,
                difficulty=difficulty, count=problem_count,
                unit_title=unit_title,
            )
        except Exception as e:
            raise RuntimeError(f"DeepSeek API 调用失败: {e}")
    else:
        if error_codes is None:
            top_errors = await get_class_top_errors(class_id)
            target_codes = top_errors[:3] if top_errors else ["E03"]
        else:
            target_codes = error_codes

        generated = generate_quiz_problems(
            error_codes=target_codes, difficulty=difficulty, total_count=problem_count,
        )
        raw_problems = [
            {
                "problem": p.problem,
                "problem_plain": p.problem,
                "correct_answer": p.correct_answer,
                "knowledge_point": p.knowledge_point,
                "target_error_code": p.error_code,
                "difficulty": difficulty,
            }
            for p in generated
        ]

    homework_id = f"HW{uuid.uuid4().hex[:8].upper()}"
    today = date.today().isoformat()
    generated_by = "deepseek" if use_llm else "system"

    async with get_db() as db:
        cursor = await db.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
        row = await cursor.fetchone()
        class_name = row["name"] if row else class_id

        await db.execute(
            """INSERT INTO homework (id, class_id, grade, knowledge_points,
               error_codes_target, status, generated_by, created_at)
               VALUES (?, ?, ?, ?, ?, 'assigned', ?, ?)""",
            (
                homework_id, class_id, grade,
                json.dumps(list({p.get("knowledge_point", "") for p in raw_problems})),
                json.dumps(list({p.get("target_error_code", "") for p in raw_problems})),
                generated_by,
                today,
            ),
        )

        for i, p in enumerate(raw_problems, 1):
            pid = f"HP{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO homework_problems (id, homework_id, sequence, problem,
                   correct_answer, knowledge_point, target_error_code, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (pid, homework_id, i,
                 p.get("problem_plain", p.get("problem", "")),
                 p.get("correct_answer", ""),
                 p.get("knowledge_point", ""),
                 p.get("target_error_code", ""),
                 p.get("difficulty", difficulty)),
            )
        await db.commit()

    return {
        "homework_id": homework_id,
        "class_id": class_id,
        "class_name": class_name,
        "raw_problems": raw_problems,
        "generated_by": generated_by,
    }

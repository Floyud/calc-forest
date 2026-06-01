from __future__ import annotations

import json
import uuid
from collections import Counter
from typing import Any

from app.db import get_db
from app.services.problem_generator import generate_quiz_problems
from app.services.homework_service import get_class_top_errors


async def generate_quiz(
    class_id: str,
    grade: int = 6,
    error_codes_target: list[str] | None = None,
    problem_count: int = 5,
    difficulty: str = "B",
) -> dict[str, Any]:
    if not error_codes_target:
        error_codes_target = await get_class_top_errors(class_id)
    if not error_codes_target:
        error_codes_target = ["E03"]

    problems = generate_quiz_problems(
        error_codes=error_codes_target,
        difficulty=difficulty,
        total_count=problem_count,
    )

    quiz_id = f"QZ{uuid.uuid4().hex[:8].upper()}"
    title_parts = [f"{code}" for code in error_codes_target[:3]]
    title = f"随堂练习·{'·'.join(title_parts)}"

    async with get_db() as db:
        await db.execute(
            """INSERT INTO quiz_sessions (id, class_id, title, status, target_error_codes, problem_count, difficulty, grade)
               VALUES (?, ?, ?, 'draft', ?, ?, ?, ?)""",
            (quiz_id, class_id, title, json.dumps(error_codes_target), len(problems), difficulty, grade),
        )
        for i, p in enumerate(problems, 1):
            pid = f"QP{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO quiz_problems (id, quiz_id, sequence, problem, correct_answer, target_error_code, difficulty, knowledge_point, hint)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (pid, quiz_id, i, p.problem, p.correct_answer, p.error_code, p.difficulty, p.knowledge_point, p.hint),
            )
        await db.commit()

    return await get_quiz(quiz_id)


async def get_quiz(quiz_id: str) -> dict[str, Any] | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM quiz_sessions WHERE id = ?", (quiz_id,))
        row = await cursor.fetchone()
        if not row:
            return None

        result = dict(row)
        result["target_error_codes"] = json.loads(result.get("target_error_codes", "[]"))
        result["quiz_id"] = result.pop("id")

        pcursor = await db.execute(
            "SELECT * FROM quiz_problems WHERE quiz_id = ? ORDER BY sequence",
            (quiz_id,),
        )
        problems = await pcursor.fetchall()
        result["problems"] = [dict(p) for p in problems]

        return result


async def record_response(
    quiz_id: str,
    problem_sequence: int,
    class_response: str = "mixed",
    notes: str = "",
) -> bool:
    resp_id = f"QR{uuid.uuid4().hex[:8].upper()}"
    async with get_db() as db:
        await db.execute(
            """INSERT INTO quiz_responses (id, quiz_id, problem_sequence, class_response, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (resp_id, quiz_id, problem_sequence, class_response, notes),
        )
        await db.commit()
    return True


async def get_quiz_summary(quiz_id: str) -> dict[str, Any] | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM quiz_sessions WHERE id = ?", (quiz_id,))
        quiz_row = await cursor.fetchone()
        if not quiz_row:
            return None

        quiz = dict(quiz_row)

        pcursor = await db.execute(
            "SELECT * FROM quiz_problems WHERE quiz_id = ? ORDER BY sequence",
            (quiz_id,),
        )
        problems = [dict(p) for p in await pcursor.fetchall()]

        rcursor = await db.execute(
            "SELECT * FROM quiz_responses WHERE quiz_id = ? ORDER BY problem_sequence",
            (quiz_id,),
        )
        responses = [dict(r) for r in await rcursor.fetchall()]

        error_dist: dict[str, int] = Counter()
        mostly_correct = 0
        mixed = 0
        mostly_wrong = 0
        for resp in responses:
            cr = resp["class_response"]
            if cr == "mostly_correct":
                mostly_correct += 1
            elif cr == "mostly_wrong":
                mostly_wrong += 1
            else:
                mixed += 1
            seq = resp["problem_sequence"]
            for p in problems:
                if p["sequence"] == seq and p.get("target_error_code"):
                    error_dist[p["target_error_code"]] += 1

        weak_codes = [code for code, _ in Counter(error_dist).most_common(2) if code]
        recommendation = ""
        if weak_codes:
            recommendation = f"建议重点练习 {', '.join(weak_codes)} 类型题目，可生成针对性作业巩固。"
        elif mostly_correct == len(problems):
            recommendation = "全班掌握良好，可以进入下一知识点。"

        return {
            "quiz_id": quiz_id,
            "class_id": quiz["class_id"],
            "total_problems": len(problems),
            "responses": responses,
            "error_distribution": dict(error_dist),
            "mostly_correct_count": mostly_correct,
            "mixed_count": mixed,
            "mostly_wrong_count": mostly_wrong,
            "recommendation": recommendation,
        }

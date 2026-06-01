"""Rolling practice session management for students."""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from app.db import get_db
from app.services.problem_generator import generate_problems
from app.services.diagnosis import diagnose_answer, AnswerRecord


async def start_practice(student_id: str, error_codes: list[str] | None = None) -> dict:
    async with get_db() as db:
        cur = await db.execute("SELECT grade, class_id FROM students WHERE id = ?", (student_id,))
        student = await cur.fetchone()
        if student is None:
            return None

        if not error_codes:
            cur2 = await db.execute(
                """
                SELECT error_code FROM student_error_stats
                WHERE student_id = ? AND total_attempts > 0
                ORDER BY (correct_count * 1.0 / total_attempts) ASC
                LIMIT 3
                """,
                (student_id,),
            )
            rows = await cur2.fetchall()
            error_codes = [r["error_code"] for r in rows] if rows else ["E03", "E02"]

        session_id = f"PS{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            INSERT INTO student_practice_sessions (id, student_id, error_codes, difficulty, started_at, status)
            VALUES (?, ?, ?, 'A', ?, 'active')
            """,
            (session_id, student_id, json.dumps(error_codes), now),
        )
        await db.commit()

        return {
            "session_id": session_id,
            "student_id": student_id,
            "error_codes": error_codes,
            "started_at": now,
            "status": "active",
        }


async def get_next_problem(student_id: str, session_id: str) -> dict | None:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT * FROM student_practice_sessions WHERE id = ? AND student_id = ? AND status = 'active'",
            (session_id, student_id),
        )
        session = await cur.fetchone()
        if session is None:
            return None

        error_codes = json.loads(session["error_codes"])
        grade = 6
        cur2 = await db.execute("SELECT grade FROM students WHERE id = ?", (student_id,))
        s = await cur2.fetchone()
        if s:
            grade = s["grade"]

        target_code = error_codes[0] if error_codes else "E03"
        problems = generate_problems(
            error_code=target_code,
            difficulty=session["difficulty"],
            count=1,
        )
        if not problems:
            return None

        p = problems[0]
        problem_id = f"PP{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            INSERT INTO student_practice_problems
            (id, session_id, sequence, problem, correct_answer, target_error_code, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (problem_id, session_id, session["problems_done"] + 1, p["problem"], p["correct_answer"], target_code, session["difficulty"]),
        )
        await db.commit()

        return {
            "problem_id": problem_id,
            "sequence": session["problems_done"] + 1,
            "problem": p["problem"],
            "difficulty": session["difficulty"],
        }


async def submit_practice_answer(student_id: str, session_id: str, problem_id: str, answer: str) -> dict:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT * FROM student_practice_problems WHERE id = ? AND session_id = ?",
            (problem_id, session_id),
        )
        problem = await cur.fetchone()
        if problem is None:
            return {"error": "Problem not found"}

        correct_answer = problem["correct_answer"]
        is_correct = answer.strip() == correct_answer.strip()
        error_code = "OK" if is_correct else None
        error_label = ""

        if not is_correct:
            record = AnswerRecord(
                grade=6,
                problem=problem["problem"],
                correct_answer=correct_answer,
                student_answer=answer,
            )
            diag = diagnose_answer(record)
            error_code = diag.primary_error.code.value if diag.primary_error else "E99"
            error_label = diag.primary_error.label if diag.primary_error else ""

        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            UPDATE student_practice_problems
            SET student_answer = ?, is_correct = ?, error_code = ?, answered_at = ?
            WHERE id = ?
            """,
            (answer, int(is_correct), error_code, now, problem_id),
        )
        await db.execute(
            """
            UPDATE student_practice_sessions
            SET problems_done = problems_done + 1,
                correct_count = correct_count + ?
            WHERE id = ?
            """,
            (int(is_correct), session_id),
        )
        await db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": correct_answer if not is_correct else None,
            "error_code": error_code,
            "error_label": error_label,
        }


async def end_practice(student_id: str, session_id: str) -> dict:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT * FROM student_practice_sessions WHERE id = ? AND student_id = ?",
            (session_id, student_id),
        )
        session = await cur.fetchone()
        if session is None:
            return {"error": "Session not found"}

        now = datetime.utcnow().isoformat()
        await db.execute(
            "UPDATE student_practice_sessions SET status = 'ended', ended_at = ? WHERE id = ?",
            (now, session_id),
        )
        await db.commit()

        total = session["problems_done"]
        correct = session["correct_count"]
        return {
            "session_id": session_id,
            "total": total,
            "correct": correct,
            "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
        }

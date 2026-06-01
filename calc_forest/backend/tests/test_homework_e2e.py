"""E2E closed-loop tests: generate → assign → submit → grade → verify diagnosis."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.services.diagnosis import _subtract_without_borrow, _add_without_carry

client = TestClient(app)


def _generate_hw(
    class_id: str = "G6A1",
    student_id: str | None = "S001",
    error_codes: list[str] | None = None,
    difficulty: str = "B",
    problem_count: int = 3,
) -> dict:
    """POST /api/homework/generate and return JSON."""
    payload: dict = {
        "class_id": class_id,
        "grade": 6,
        "error_codes_target": error_codes or ["E03"],
        "problem_count": problem_count,
        "difficulty": difficulty,
    }
    if student_id:
        payload["student_id"] = student_id
    r = client.post("/api/homework/generate", json=payload)
    assert r.status_code == 200, f"generate failed: {r.text}"
    return r.json()


def _assign(hw_id: str) -> dict:
    r = client.post("/api/homework/assign", json={"homework_id": hw_id})
    assert r.status_code == 200, f"assign failed: {r.text}"
    return r.json()


def _submit(hw_id: str, student_id: str, answers: list[dict]) -> dict:
    r = client.post(
        "/api/homework/submit",
        json={
            "homework_id": hw_id,
            "student_id": student_id,
            "answers": answers,
        },
    )
    assert r.status_code == 200, f"submit failed: {r.text}"
    return r.json()


def _grade(hw_id: str, student_id: str) -> dict:
    r = client.post(
        f"/api/homework/grade?homework_id={hw_id}&student_id={student_id}"
    )
    assert r.status_code == 200, f"grade failed: {r.text}"
    return r.json()


def _borrow_wrong_answer(problem: str, correct_answer: str) -> str:
    """Return the no-borrow subtraction result to trigger E03."""
    expr = problem.rstrip("=")
    if "-" not in expr:
        return "0"
    parts = expr.split("-")
    try:
        a, b = int(parts[0]), int(parts[1])
        return str(_subtract_without_borrow(a, b))
    except (ValueError, IndexError):
        return "0"


def _carry_wrong_answer(problem: str, correct_answer: str) -> str:
    """For addition a+b=, return the no-carry result (triggers E02)."""
    expr = problem.rstrip("=")
    if "+" not in expr:
        return "0"
    parts = expr.split("+")
    try:
        a, b = int(parts[0]), int(parts[1])
        return str(_add_without_carry(a, b))
    except (ValueError, IndexError):
        return "0"


def _operation_order_wrong_answer(problem: str, correct_answer: str) -> str:
    """For mixed ops like a+b×c=, return the left-to-right result (triggers E05)."""
    from fractions import Fraction
    import re
    expr = problem.rstrip("=")
    tokens = re.findall(r"\d+(?:\.\d+)?|[+\-*/×÷]", expr)
    if not tokens:
        return "0"
    try:
        value = Fraction(tokens[0])
        idx = 1
        ops = {
            "+": lambda x, y: x + y,
            "-": lambda x, y: x - y,
            "*": lambda x, y: x * y,
            "×": lambda x, y: x * y,
            "/": lambda x, y: x / y,
            "÷": lambda x, y: x / y,
        }
        while idx < len(tokens) - 1:
            op_fn = ops.get(tokens[idx])
            if op_fn is None:
                return "0"
            value = op_fn(value, Fraction(tokens[idx + 1]))
            idx += 2
        if value.denominator == 1:
            return str(value.numerator)
        return str(float(value))
    except Exception:
        return "0"


class TestHomeworkClosedLoop:
    """E2E closed-loop tests: generate → assign → submit → grade → verify."""

    def test_generate_assign_grade_cycle(self):
        """Full cycle with E01-E05, mixed correct/wrong, verify diagnosis and DB writes."""
        error_codes = ["E01", "E02", "E03", "E04", "E05"]

        hw = _generate_hw(
            error_codes=error_codes,
            difficulty="B",
            problem_count=10,
        )
        hw_id = hw["homework_id"]
        problems = hw["problems"]

        assert hw["status"] == "draft"
        assert len(problems) == 10
        for p in problems:
            assert p["problem"].strip(), f"problem {p['sequence']} is empty"
            assert p["correct_answer"].strip(), f"problem {p['sequence']} has no answer"

        assign_result = _assign(hw_id)
        assert assign_result["status"] == "assigned"

        answers = []
        for p in problems:
            target_ec = p.get("target_error_code", "")
            prob_text = p["problem"]

            if target_ec == "E03" and "-" in prob_text:
                wrong = _borrow_wrong_answer(prob_text, p["correct_answer"])
            elif target_ec == "E02" and "+" in prob_text:
                wrong = _carry_wrong_answer(prob_text, p["correct_answer"])
            elif target_ec == "E05":
                wrong = _operation_order_wrong_answer(prob_text, p["correct_answer"])
            else:
                wrong = "99999"

            if p["sequence"] % 5 == 1:
                wrong = p["correct_answer"]

            answers.append({"problem_sequence": p["sequence"], "raw_answer": wrong})

        sub_result = _submit(hw_id, "S001", answers)
        assert "submission_id" in sub_result
        assert sub_result["answer_count"] == 10

        grade_result = _grade(hw_id, "S001")
        assert grade_result["total_problems"] == 10
        assert isinstance(grade_result["correct_count"], int)
        assert 0 < grade_result["accuracy"] < 1.0
        assert isinstance(grade_result["primary_errors"], list)
        assert len(grade_result["primary_errors"]) > 0

        detected_codes = set(grade_result["primary_errors"])
        assert detected_codes & {"E02", "E03", "E05"}, (
            f"Expected at least one of E02/E03/E05 in primary_errors, "
            f"got {detected_codes}"
        )

        async def _check_stats():
            from app.db import get_db
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT error_code, total_attempts, correct_count "
                    "FROM student_error_stats WHERE student_id = ?",
                    ("S001",),
                )
                rows = await cursor.fetchall()
                return {row["error_code"]: dict(row) for row in rows}

        stats = asyncio.get_event_loop().run_until_complete(_check_stats())
        assert len(stats) > 0, "student_error_stats should have records after grading"
        for code, row in stats.items():
            assert row["total_attempts"] > 0
            assert row["correct_count"] >= 0
            assert row["correct_count"] <= row["total_attempts"]

        async def _check_history():
            from app.db import get_db
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT error_code, is_correct FROM student_answers "
                    "WHERE homework_id = ? AND student_id = ?",
                    (hw_id, "S001"),
                )
                return await cursor.fetchall()

        history = asyncio.get_event_loop().run_until_complete(_check_history())
        assert len(history) > 0, "diagnosis_history should have records"
        incorrect_rows = [h for h in history if h["is_correct"] == 0]
        assert len(incorrect_rows) > 0, "should have incorrect answers in history"

    def test_diagnosis_detects_borrow_error(self):
        """E03: no-borrow answers → E03 detected."""
        hw = _generate_hw(error_codes=["E03"], difficulty="B", problem_count=5)
        hw_id = hw["homework_id"]
        problems = hw["problems"]

        _assign(hw_id)

        answers = []
        for p in problems:
            wrong = _borrow_wrong_answer(p["problem"], p["correct_answer"])
            if wrong == "0" and "-" not in p["problem"]:
                wrong = "99999"
            answers.append({"problem_sequence": p["sequence"], "raw_answer": wrong})

        _submit(hw_id, "S001", answers)
        grade_result = _grade(hw_id, "S001")

        assert "E03" in grade_result["primary_errors"], (
            f"E03 (borrow) should be detected, got {grade_result['primary_errors']}"
        )
        assert grade_result["correct_count"] == 0
        assert grade_result["accuracy"] == 0.0

    def test_diagnosis_detects_carry_error(self):
        """E02: no-carry answers → E02 detected."""
        hw = _generate_hw(error_codes=["E02"], difficulty="B", problem_count=5)
        hw_id = hw["homework_id"]
        problems = hw["problems"]

        _assign(hw_id)

        answers = []
        for p in problems:
            wrong = _carry_wrong_answer(p["problem"], p["correct_answer"])
            if wrong == "0" and "+" not in p["problem"]:
                wrong = "99999"
            answers.append({"problem_sequence": p["sequence"], "raw_answer": wrong})

        _submit(hw_id, "S001", answers)
        grade_result = _grade(hw_id, "S001")

        assert "E02" in grade_result["primary_errors"], (
            f"E02 (carry) should be detected, got {grade_result['primary_errors']}"
        )
        assert grade_result["accuracy"] == 0.0

    def test_diagnosis_detects_operation_order_error(self):
        """E05: left-to-right answers → errors detected."""
        hw = _generate_hw(error_codes=["E05"], difficulty="B", problem_count=5)
        hw_id = hw["homework_id"]
        problems = hw["problems"]

        _assign(hw_id)

        answers = []
        for p in problems:
            wrong = _operation_order_wrong_answer(p["problem"], p["correct_answer"])
            answers.append({"problem_sequence": p["sequence"], "raw_answer": wrong})

        _submit(hw_id, "S001", answers)
        grade_result = _grade(hw_id, "S001")

        assert len(grade_result["primary_errors"]) > 0, (
            "Should detect errors for all-wrong E05 submission"
        )
        assert grade_result["accuracy"] == 0.0

    def test_all_correct_no_errors(self):
        """All correct → accuracy=1.0, no primary errors."""
        hw = _generate_hw(error_codes=["E01", "E03"], difficulty="A", problem_count=4)
        hw_id = hw["homework_id"]
        problems = hw["problems"]

        _assign(hw_id)

        answers = [
            {"problem_sequence": p["sequence"], "raw_answer": p["correct_answer"]}
            for p in problems
        ]
        _submit(hw_id, "S001", answers)
        grade_result = _grade(hw_id, "S001")

        assert grade_result["correct_count"] == grade_result["total_problems"]
        assert grade_result["accuracy"] == 1.0
        assert grade_result["primary_errors"] == []

    def test_adaptive_difficulty_escalation(self):
        """Poor round 1 → low accuracy tracked → round 2 generates OK.

        _difficulty_distribution_for(accuracy):
        accuracy < 0.6 → {A: 0.6, B: 0.4}
        """
        hw1 = _generate_hw(error_codes=["E03"], difficulty="B", problem_count=5)
        hw1_id = hw1["homework_id"]
        problems1 = hw1["problems"]

        _assign(hw1_id)

        answers1 = []
        for p in problems1:
            wrong = _borrow_wrong_answer(p["problem"], p["correct_answer"])
            if wrong == "0" and "-" not in p["problem"]:
                wrong = "99999"
            answers1.append({"problem_sequence": p["sequence"], "raw_answer": wrong})

        _submit(hw1_id, "S001", answers1)
        grade1 = _grade(hw1_id, "S001")
        assert grade1["accuracy"] == 0.0

        hw2 = _generate_hw(
            error_codes=["E03"],
            difficulty="B",
            problem_count=5,
        )
        problems2 = hw2["problems"]

        assert len(problems2) == 5
        for p in problems2:
            assert p["problem"].strip()
            assert p["correct_answer"].strip()

        async def _check_accuracy():
            from app.db import get_db
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT SUM(total_attempts) as total, "
                    "SUM(correct_count) as correct "
                    "FROM student_error_stats WHERE student_id = ?",
                    ("S001",),
                )
                row = await cursor.fetchone()
                if row and row["total"] and row["total"] > 0:
                    return row["correct"] / row["total"]
            return None

        accuracy = asyncio.get_event_loop().run_until_complete(_check_accuracy())
        assert accuracy is not None, "Student should have error stats after grading"
        assert accuracy < 0.6, (
            f"Accuracy should be low after all-wrong round, got {accuracy}"
        )

"""Tests for the grading pipeline — diagnosis_history writes, homework status transitions."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _generate_homework(error_codes=None, difficulty="A", count=3):
    error_codes = error_codes or ["E03"]
    gen_r = client.post(
        "/api/homework/generate",
        json={
            "class_id": "G6A1",
            "student_id": "S001",
            "grade": 6,
            "error_codes_target": error_codes,
            "problem_count": count,
            "difficulty": difficulty,
        },
    )
    assert gen_r.status_code == 200
    return gen_r.json()


def _assign_and_submit(hw_id, problems, student_id="S001", answer_fn=None):
    assign_r = client.post(
        "/api/homework/assign",
        json={"homework_id": hw_id},
    )
    assert assign_r.status_code == 200

    answers = []
    for p in problems:
        raw = answer_fn(p) if answer_fn else p["correct_answer"]
        answers.append({"problem_sequence": p["sequence"], "raw_answer": raw})

    submit_r = client.post(
        "/api/homework/submit",
        json={
            "homework_id": hw_id,
            "student_id": student_id,
            "answers": answers,
        },
    )
    assert submit_r.status_code == 200


def test_diagnosis_history_written_on_grade():
    hw = _generate_homework(error_codes=["E03"], count=3)
    hw_id = hw["homework_id"]
    problems = hw["problems"]

    def _first_wrong(p):
        return "999" if p["sequence"] == problems[0]["sequence"] else p["correct_answer"]

    _assign_and_submit(hw_id, problems, answer_fn=_first_wrong)

    grade_r = client.post(f"/api/homework/grade?homework_id={hw_id}&student_id=S001")
    assert grade_r.status_code == 200
    gd = grade_r.json()
    assert gd["total_problems"] == 3

    from app.db import get_db
    import asyncio

    async def _check():
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM diagnosis_history WHERE student_id = ?",
                ("S001",),
            )
            count = (await cursor.fetchone())[0]
            return count

    count = asyncio.get_event_loop().run_until_complete(_check())
    assert count > 0, "diagnosis_history should have records after grading"


def test_homework_status_transitions():
    gen_r = client.post(
        "/api/homework/generate",
        json={
            "class_id": "G6A1",
            "grade": 6,
            "error_codes_target": ["E01"],
            "problem_count": 2,
            "difficulty": "A",
        },
    )
    assert gen_r.status_code == 200
    hw = gen_r.json()
    hw_id = hw["homework_id"]
    assert hw["status"] == "draft"

    assign_r = client.post(
        "/api/homework/assign",
        json={"homework_id": hw_id},
    )
    assert assign_r.status_code == 200
    assert assign_r.json()["status"] == "assigned"

    problems = hw["problems"]
    submit_r = client.post(
        "/api/homework/submit",
        json={
            "homework_id": hw_id,
            "student_id": "S001",
            "answers": [
                {"problem_sequence": problems[0]["sequence"], "raw_answer": problems[0]["correct_answer"]},
                {"problem_sequence": problems[1]["sequence"], "raw_answer": "0"},
            ],
        },
    )
    assert submit_r.status_code == 200

    grade_r = client.post(f"/api/homework/grade?homework_id={hw_id}&student_id=S001")
    assert grade_r.status_code == 200
    gd = grade_r.json()
    assert gd["correct_count"] >= 1
    assert 0 <= gd["accuracy"] <= 1.0


def test_grade_result_has_expected_fields():
    hw = _generate_homework(error_codes=["E01", "E02"], count=3)
    hw_id = hw["homework_id"]
    problems = hw["problems"]

    _assign_and_submit(hw_id, problems, answer_fn=lambda p: "0")

    grade_r = client.post(f"/api/homework/grade?homework_id={hw_id}&student_id=S001")
    assert grade_r.status_code == 200
    gd = grade_r.json()
    assert "homework_id" in gd
    assert "student_id" in gd
    assert "total_problems" in gd
    assert "correct_count" in gd
    assert "accuracy" in gd
    assert "primary_errors" in gd
    assert isinstance(gd["primary_errors"], list)


def test_grade_all_wrong():
    hw = _generate_homework(error_codes=["E03"], count=3)
    hw_id = hw["homework_id"]
    problems = hw["problems"]

    _assign_and_submit(hw_id, problems, answer_fn=lambda p: "99999")

    grade_r = client.post(f"/api/homework/grade?homework_id={hw_id}&student_id=S001")
    assert grade_r.status_code == 200
    gd = grade_r.json()
    assert gd["correct_count"] == 0
    assert gd["accuracy"] == 0.0
    assert len(gd["primary_errors"]) > 0


def test_grade_all_correct():
    hw = _generate_homework(error_codes=["E01"], count=3)
    hw_id = hw["homework_id"]
    problems = hw["problems"]

    _assign_and_submit(hw_id, problems)

    grade_r = client.post(f"/api/homework/grade?homework_id={hw_id}&student_id=S001")
    assert grade_r.status_code == 200
    gd = grade_r.json()
    assert gd["correct_count"] == gd["total_problems"]
    assert gd["accuracy"] == 1.0

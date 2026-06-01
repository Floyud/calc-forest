import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import AnswerRecord, ErrorCode
from app.services.diagnosis import diagnose_answer


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_correct_answer() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="5/6÷2/3=",
            correct_answer="5/4",
            student_answer="5/4",
        )
    )
    assert result.is_correct is True
    assert result.primary_error.code == ErrorCode.CORRECT


def test_carry_error() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="367+458=",
            correct_answer="825",
            student_answer="715",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code == ErrorCode.CARRY


def test_borrow_error() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="1002-478=",
            correct_answer="524",
            student_answer="634",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code == ErrorCode.BORROW


def test_operation_order_error() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="18+6×3=",
            correct_answer="36",
            student_answer="72",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code == ErrorCode.OPERATION_ORDER


def test_basic_fact_error() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="7×8=",
            correct_answer="56",
            student_answer="54",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code == ErrorCode.BASIC_FACT


def test_api_diagnose() -> None:
    response = client.post(
        "/api/diagnose",
        json={
            "student_id": "S001",
            "grade": 6,
            "problem": "1002-478=",
            "correct_answer": "524",
            "student_answer": "634",
            "student_steps": [],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["review_status"] == "pending_teacher_review"
    assert payload["primary_error"]["code"] == "E03"
    assert payload["guidance_mode"] == "standard"


def test_api_practice_recommend() -> None:
    response = client.post(
        "/api/practice/recommend",
        json={
            "error_code": "E03",
            "grade": 6,
            "guidance_mode": "exploration",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["target_error"] == "E03"
    assert payload["guidance_mode"] == "exploration"
    assert payload["estimated_minutes"] == 5
    assert len(payload["items"]) >= 2


def test_api_tree_species() -> None:
    response = client.get("/api/tree-species")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 8
    assert any(item["id"] == "cherry" for item in payload)


def test_growth_config_files_exist() -> None:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    tree_species = json.loads((data_dir / "tree_species.json").read_text(encoding="utf-8"))
    encouragements = json.loads((data_dir / "encouragements.json").read_text(encoding="utf-8"))
    assert len(tree_species) == 8
    assert any(item["trigger"] == "self_corrected" for item in encouragements)


def test_api_dify_session_draft() -> None:
    response = client.post(
        "/api/dify/session-draft",
        json={
            "student_id": "S001",
            "grade": 6,
            "problem_text": "1002-478=",
            "correct_answer_text": "524",
            "student_answer_text": "634",
            "guidance_mode": "standard",
            "tree_species_id": "cherry",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["diagnosis"]["primary_error"]["code"] == "E03"
    assert payload["practice"]["target_error"] == "E03"
    assert payload["student_feedback"]["guiding_questions"]
    assert payload["tree_species"]["id"] == "cherry"


def test_parenthesis_ignored() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="(2+3)×4=",
            correct_answer="20",
            student_answer="14",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code == ErrorCode.OPERATION_ORDER


def test_partial_product_forgot_shift() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="12×34=",
            correct_answer="408",
            student_answer="84",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code == ErrorCode.PLACE_VALUE_ALIGNMENT


def test_partial_product_cross_term_miss() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="23×45=",
            correct_answer="1035",
            student_answer="815",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code == ErrorCode.MISSING_STEP


def test_conceptual_square_vs_double() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="7×7=",
            correct_answer="49",
            student_answer="14",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code == ErrorCode.CONCEPTUAL_UNDERSTANDING


def test_wording_multiply_read_as_add() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="5×8=",
            correct_answer="40",
            student_answer="13",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code == ErrorCode.WORDING_UNIT


def test_partial_product_tens_only() -> None:
    result = diagnose_answer(
        AnswerRecord(
            grade=6,
            problem="23×45=",
            correct_answer="1035",
            student_answer="915",
        )
    )
    assert result.is_correct is False
    assert result.primary_error.code in (ErrorCode.PLACE_VALUE_ALIGNMENT, ErrorCode.MISSING_STEP)


def test_homework_submit_and_grade_loop() -> None:
    """Test the submit → grade flow (replaces removed OCR simulation loop)."""
    generate = client.post(
        "/api/homework/generate",
        json={
            "class_id": "G6A1",
            "student_id": "S001",
            "grade": 6,
            "error_codes_target": ["E03"],
            "problem_count": 2,
            "difficulty": "A",
        },
    )
    assert generate.status_code == 200
    homework_id = generate.json()["homework_id"]

    detail = client.get(f"/api/homework/{homework_id}")
    assert detail.status_code == 200
    problems = detail.json()["problems"]
    assert len(problems) == 2

    assign = client.post(f"/api/homework/assign?homework_id={homework_id}")
    assert assign.status_code == 200

    # Submit answers: one correct, one wrong
    submit = client.post(
        "/api/homework/submit",
        json={
            "homework_id": homework_id,
            "student_id": "S001",
            "answers": [
                {"problem_sequence": problems[0]["sequence"], "raw_answer": problems[0]["correct_answer"]},
                {"problem_sequence": problems[1]["sequence"], "raw_answer": "999"},
            ],
        },
    )
    assert submit.status_code == 200

    # Grade the homework
    grade = client.post(f"/api/homework/grade?homework_id={homework_id}&student_id=S001")
    assert grade.status_code == 200
    result = grade.json()
    assert result["total_problems"] == 2
    assert result["correct_count"] == 1  # one correct, one wrong

    # Verify the grade response is valid
    assert result["accuracy"] == 0.5  # 1/2 correct

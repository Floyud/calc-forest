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


def test_homework_ocr_simulation_loop() -> None:
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

    upload = client.post(
        "/api/ocr/upload",
        json={
            "homework_id": homework_id,
            "student_id": "S001",
            "answers": [
                {"problem_sequence": problems[0]["sequence"], "raw_answer": problems[0]["correct_answer"]},
                {"problem_sequence": problems[1]["sequence"], "raw_answer": "999"},
            ],
        },
    )
    assert upload.status_code == 200
    scan_id = upload.json()["scan_id"]
    assert upload.json()["recognition_status"] == "queued"

    first = client.get(f"/api/ocr/submissions/{scan_id}")
    assert first.status_code == 200
    assert first.json()["recognition_status"] == "processing"

    second = client.get(f"/api/ocr/submissions/{scan_id}")
    assert second.status_code == 200
    assert second.json()["recognition_status"] == "recognized"
    assert len(second.json()["recognized_answers"]) == 2

    third = client.get(f"/api/ocr/submissions/{scan_id}")
    assert third.status_code == 200
    assert third.json()["grading_status"] == "graded"
    assert third.json()["diagnosis"]["total_problems"] == 2

    fourth = client.get(f"/api/ocr/submissions/{scan_id}")
    assert fourth.status_code == 200
    assert fourth.json()["archive_status"] == "archived"

    submissions = client.get(f"/api/homework/{homework_id}/submissions")
    assert submissions.status_code == 200
    assert len(submissions.json()) >= 1

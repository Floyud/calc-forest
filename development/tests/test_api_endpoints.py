"""Tests for FastAPI endpoints via TestClient — no running server required."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["service"] == "primary-math-diagnosis-agent"


def test_tree_species():
    r = client.get("/api/tree-species")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 8
    species_ids = {item["species_id"] for item in data}
    assert "cherry" in species_ids
    for item in data:
        assert item["name"]
        assert item["category"]
        assert item["emoji"]


def test_encouragements():
    r = client.get("/api/encouragements")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    triggers = {item["trigger"] for item in data}
    assert "self_corrected" in triggers
    for item in data:
        assert item["message"]


def test_class_forest():
    r = client.get("/api/classes/G6A1/forest")
    assert r.status_code == 200
    data = r.json()
    assert data["class_id"] == "G6A1"
    assert data["class_name"]
    assert isinstance(data["trees"], list)
    if data["trees"]:
        tree = data["trees"][0]
        assert "student_id" in tree
        assert "current_stage" in tree
        assert "overall_accuracy" in tree


def test_student_profile():
    r = client.get("/api/students/S001/profile")
    assert r.status_code == 200
    data = r.json()
    assert data["student_id"] == "S001"
    assert "accuracy" in data
    assert "weekly_accuracy" in data
    assert isinstance(data["accuracy"], float)
    assert isinstance(data["weekly_accuracy"], list)


def test_class_summary():
    r = client.get("/api/classes/G6C1/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["class_id"] == "G6C1"
    assert data["class_name"]
    assert isinstance(data["total_students"], int)
    assert isinstance(data["class_accuracy"], float)


def test_curriculum_units():
    r = client.get("/api/curriculum/units")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        unit = data[0]
        assert "unit_number" in unit or "id" in unit


def test_knowledge_search():
    r = client.get("/api/knowledge/search?q=分数")
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert isinstance(data["results"], list)


def test_knowledge_search_empty_query():
    r = client.get("/api/knowledge/search?q=")
    assert r.status_code == 200
    data = r.json()
    assert data["results"] == []


def test_curriculum_calendar():
    r = client.get("/api/curriculum/calendar")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_homework_generate():
    r = client.post(
        "/api/homework/generate",
        json={
            "class_id": "G6A1",
            "grade": 6,
            "error_codes_target": ["E01", "E02"],
            "problem_count": 3,
            "difficulty": "A",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["homework_id"]
    assert len(data["problems"]) == 3
    assert data["status"] == "draft"
    for p in data["problems"]:
        assert p["problem"].strip()
        assert p["correct_answer"].strip()


def test_homework_assign_and_submit_and_grade():
    generate_r = client.post(
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
    assert generate_r.status_code == 200
    hw = generate_r.json()
    hw_id = hw["homework_id"]
    problems = hw["problems"]

    assign_r = client.post(
        "/api/homework/assign",
        json={"homework_id": hw_id},
    )
    assert assign_r.status_code == 200
    assert assign_r.json()["status"] == "assigned"

    submit_r = client.post(
        "/api/homework/submit",
        json={
            "homework_id": hw_id,
            "student_id": "S001",
            "answers": [
                {"problem_sequence": problems[0]["sequence"], "raw_answer": problems[0]["correct_answer"]},
                {"problem_sequence": problems[1]["sequence"], "raw_answer": "999"},
            ],
        },
    )
    assert submit_r.status_code == 200
    assert "submission_id" in submit_r.json()

    grade_r = client.post(
        f"/api/homework/grade?homework_id={hw_id}&student_id=S001",
    )
    assert grade_r.status_code == 200
    gd = grade_r.json()
    assert gd["total_problems"] == 2
    assert gd["correct_count"] == 1
    assert gd["accuracy"] == 0.5


def test_student_trajectory():
    r = client.get("/api/students/S001/trajectory")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_ocr_stub():
    r = client.get("/api/ocr/stub")
    assert r.status_code == 200
    data = r.json()
    assert data["review_status"] == "pending_teacher_review"


def test_exercise_types():
    r = client.get("/api/exercise-types")
    assert r.status_code == 200
    data = r.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)


def test_homework_detail_not_found():
    r = client.get("/api/homework/NONEXISTENT999")
    assert r.status_code == 404


def test_quiz_not_found():
    r = client.get("/api/quiz/NONEXISTENT999")
    assert r.status_code == 404

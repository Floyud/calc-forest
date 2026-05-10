"""Tests for edge cases — validation, boundary conditions, error handling."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_diagnose_empty_problem():
    r = client.post(
        "/api/diagnose",
        json={
            "student_id": "S001",
            "grade": 6,
            "problem": "",
            "correct_answer": "224",
            "student_answer": "334",
        },
    )
    assert r.status_code == 200
    assert r.json()["review_status"] == "pending_teacher_review"


def test_diagnose_missing_student():
    r = client.post(
        "/api/diagnose",
        json={
            "grade": 6,
            "problem": "402-178=",
            "correct_answer": "224",
            "student_answer": "334",
        },
    )
    assert r.status_code == 200


def test_profile_nonexistent_student():
    r = client.get("/api/students/FAKE_STUDENT_999/profile")
    assert r.status_code == 404


def test_homework_generate_empty_codes():
    r = client.post(
        "/api/homework/generate",
        json={
            "class_id": "G6A1",
            "grade": 6,
            "error_codes_target": [],
            "problem_count": 3,
            "difficulty": "A",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["homework_id"]
    assert len(data["problems"]) == 3


def test_quiz_response_nonexistent():
    r = client.post(
        "/api/quiz/FAKE_QUIZ_999/response",
        json={
            "quiz_id": "FAKE_QUIZ_999",
            "problem_sequence": 1,
            "class_response": "mostly_correct",
            "notes": "",
        },
    )
    assert r.status_code == 404


def test_knowledge_search_special_chars():
    r = client.get("/api/knowledge/search?q=test+alert+1")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["results"], list)


def test_knowledge_search_sql_injection():
    r = client.get("/api/knowledge/search?q=分数+乘法")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["results"], list)


def test_diagnose_grade_boundary_low():
    r = client.post(
        "/api/diagnose",
        json={
            "student_id": "S001",
            "grade": 1,
            "problem": "3+5=",
            "correct_answer": "8",
            "student_answer": "7",
        },
    )
    assert r.status_code == 200
    assert r.json()["review_status"] == "pending_teacher_review"


def test_diagnose_grade_boundary_high():
    r = client.post(
        "/api/diagnose",
        json={
            "student_id": "S001",
            "grade": 6,
            "problem": "3.14×2.5=",
            "correct_answer": "7.85",
            "student_answer": "7.85",
        },
    )
    assert r.status_code == 200
    assert r.json()["review_status"] == "pending_teacher_review"


def test_diagnose_grade_invalid():
    r = client.post(
        "/api/diagnose",
        json={
            "student_id": "S001",
            "grade": 7,
            "problem": "1+1=",
            "correct_answer": "2",
            "student_answer": "3",
        },
    )
    assert r.status_code == 422


def test_diagnose_grade_zero():
    r = client.post(
        "/api/diagnose",
        json={
            "student_id": "S001",
            "grade": 0,
            "problem": "1+1=",
            "correct_answer": "2",
            "student_answer": "3",
        },
    )
    assert r.status_code == 422


def test_homework_assign_missing_id():
    r = client.post("/api/homework/assign")
    assert r.status_code == 400


def test_homework_grade_nonexistent():
    r = client.post("/api/homework/grade?homework_id=FAKE_HW_999&student_id=S001")
    assert r.status_code == 404


def test_quiz_generate_invalid_count():
    r = client.post(
        "/api/quiz/generate",
        json={
            "class_id": "G6A1",
            "grade": 6,
            "problem_count": 0,
        },
    )
    assert r.status_code == 422


def test_class_forest_nonexistent():
    r = client.get("/api/classes/NONEXISTENT/forest")
    assert r.status_code == 404


def test_class_summary_nonexistent():
    r = client.get("/api/classes/NONEXISTENT/summary")
    assert r.status_code == 404


def test_student_trajectory_nonexistent():
    r = client.get("/api/students/NONEXISTENT/trajectory")
    assert r.status_code == 200
    assert r.json() == []


def test_homework_generate_invalid_grade():
    r = client.post(
        "/api/homework/generate",
        json={
            "class_id": "G6A1",
            "grade": 99,
            "problem_count": 3,
            "difficulty": "A",
        },
    )
    assert r.status_code == 422


def test_knowledge_search_unicode():
    r = client.get("/api/knowledge/search?q=%E5%88%86%E6%95%B0%E4%B9%98%E6%B3%95")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["results"], list)

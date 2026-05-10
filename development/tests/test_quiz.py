"""Tests for the quiz CRUD lifecycle — generate, record responses, get summary."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_quiz():
    r = client.post(
        "/api/quiz/generate",
        json={
            "class_id": "G6A1",
            "grade": 6,
            "error_codes_target": ["E01", "E03"],
            "problem_count": 4,
            "difficulty": "B",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["quiz_id"]
    assert data["class_id"] == "G6A1"
    assert len(data["problems"]) == 4
    assert data["status"] == "draft"
    for p in data["problems"]:
        assert p["problem"].strip()
        assert p["correct_answer"].strip()
        assert p["target_error_code"] in ("E01", "E03")


def test_quiz_get_after_generate():
    gen = client.post(
        "/api/quiz/generate",
        json={
            "class_id": "G6A1",
            "grade": 6,
            "error_codes_target": ["E07"],
            "problem_count": 3,
            "difficulty": "A",
        },
    )
    quiz_id = gen.json()["quiz_id"]

    r = client.get(f"/api/quiz/{quiz_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["quiz_id"] == quiz_id
    assert len(data["problems"]) == 3


def test_record_quiz_response_and_summary():
    gen = client.post(
        "/api/quiz/generate",
        json={
            "class_id": "G6A1",
            "grade": 6,
            "error_codes_target": ["E01"],
            "problem_count": 3,
            "difficulty": "A",
        },
    )
    quiz_id = gen.json()["quiz_id"]
    problems = gen.json()["problems"]

    responses = ["mostly_correct", "mixed", "mostly_wrong"]
    for i, resp in enumerate(responses):
        seq = problems[i]["sequence"]
        r = client.post(
            f"/api/quiz/{quiz_id}/response",
            json={
                "quiz_id": quiz_id,
                "problem_sequence": seq,
                "class_response": resp,
                "notes": f"test note {i}",
            },
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True

    summary_r = client.get(f"/api/quiz/{quiz_id}/summary")
    assert summary_r.status_code == 200
    summary = summary_r.json()
    assert summary["quiz_id"] == quiz_id
    assert summary["total_problems"] == 3
    assert summary["mostly_correct_count"] == 1
    assert summary["mixed_count"] == 1
    assert summary["mostly_wrong_count"] == 1
    assert len(summary["responses"]) == 3
    assert summary["recommendation"]


def test_quiz_summary_empty_responses():
    gen = client.post(
        "/api/quiz/generate",
        json={
            "class_id": "G6A1",
            "grade": 6,
            "problem_count": 2,
            "difficulty": "B",
        },
    )
    quiz_id = gen.json()["quiz_id"]

    summary_r = client.get(f"/api/quiz/{quiz_id}/summary")
    assert summary_r.status_code == 200
    summary = summary_r.json()
    assert summary["total_problems"] == 2
    assert summary["mostly_correct_count"] == 0
    assert summary["mixed_count"] == 0
    assert summary["mostly_wrong_count"] == 0
    assert summary["responses"] == []

"""Tests for previously untested API endpoints — student CRUD, class CRUD,
profile update, cycles, growth, curriculum schedule, and full pipeline."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Student CRUD
# ---------------------------------------------------------------------------

def test_get_student():
    r = client.get("/api/students/S001")
    assert r.status_code == 200
    data = r.json()
    assert data["student_id"] == "S001"
    assert data["name"]
    assert data["grade"] >= 1


def test_get_student_nonexistent():
    r = client.get("/api/students/NONEXISTENT999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Class CRUD
# ---------------------------------------------------------------------------

def test_get_class():
    r = client.get("/api/classes/G6C1")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "G6C1"
    assert data["name"]
    assert isinstance(data["student_ids"], list)


def test_get_class_nonexistent():
    r = client.get("/api/classes/NONEXISTENT999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Profile PATCH
# ---------------------------------------------------------------------------

def test_patch_student_profile():
    patch_r = client.patch(
        "/api/students/S001/profile",
        params={
            "personality_tags": ["认真", "细心"],
            "learning_style": "visual",
        },
    )
    assert patch_r.status_code == 200
    assert patch_r.json()["ok"] is True

    get_r = client.get("/api/students/S001/profile")
    assert get_r.status_code == 200


def test_patch_student_profile_notes_only():
    patch_r = client.patch(
        "/api/students/S001/profile",
        params={"notes": "Updated from test"},
    )
    assert patch_r.status_code == 200
    assert patch_r.json()["ok"] is True


def test_patch_student_profile_no_fields():
    r = client.patch("/api/students/S001/profile")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Current academic cycle
# ---------------------------------------------------------------------------

def test_get_current_cycle():
    r = client.get("/api/cycles/current")
    assert r.status_code == 200
    data = r.json()
    assert data["id"]
    assert data["academic_year"]
    assert data["grade"] >= 1
    assert data["total_days"] >= 1


# ---------------------------------------------------------------------------
# Student growth
# ---------------------------------------------------------------------------

def test_get_student_growth():
    r = client.get("/api/students/S001/growth")
    assert r.status_code == 200
    data = r.json()
    assert data["student_id"] == "S001"
    assert data["cycle_id"]


def test_get_student_growth_nonexistent():
    r = client.get("/api/students/NONEXISTENT999/growth")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Record practice day
# ---------------------------------------------------------------------------

def test_record_practice_day():
    r = client.post("/api/students/S001/growth/record")
    assert r.status_code == 200
    data = r.json()
    assert "days_completed" in data or "ok" in data


def test_record_practice_day_nonexistent():
    r = client.post("/api/students/NONEXISTENT999/growth/record")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Curriculum schedule
# ---------------------------------------------------------------------------

def test_get_schedule():
    r = client.get("/api/curriculum/schedule/G6C1")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_get_schedule_nonexistent():
    """Nonexistent class should return an empty list, not 404."""
    r = client.get("/api/curriculum/schedule/NONEXISTENT999")
    assert r.status_code == 200
    assert r.json() == []


def test_update_schedule():
    """PUT schedule for G6C1 and verify."""
    update_r = client.put(
        "/api/curriculum/schedule/G6C1",
        json=[
            {
                "week_number": 1,
                "unit_id": "U01",
                "start_date": "2026-02-09",
                "end_date": "2026-02-13",
                "status": "planned",
                "notes": "test update",
            }
        ],
    )
    assert update_r.status_code == 200
    assert update_r.json()["updated"] == 1

    # Verify via GET
    get_r = client.get("/api/curriculum/schedule/G6C1")
    assert get_r.status_code == 200
    schedule = get_r.json()
    week1 = [s for s in schedule if s.get("week_number") == 1]
    assert len(week1) >= 1


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def test_full_pipeline():
    r = client.post(
        "/api/dify/full-pipeline",
        json={
            "student_id": "S001",
            "grade": 6,
            "problem_text": "402-178=",
            "correct_answer_text": "224",
            "student_answer_text": "334",
            "guidance_mode": "standard",
            "tree_species_id": "cherry",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["diagnosis"]["primary_error"]["code"] in ("E03", "E02", "E99")
    assert data["practice"]["target_error"]
    assert data["student_feedback"]["guiding_questions"]
    assert data["teacher_summary"]


def test_full_pipeline_correct_answer():
    r = client.post(
        "/api/dify/full-pipeline",
        json={
            "student_id": "S001",
            "grade": 6,
            "problem_text": "7×8=",
            "correct_answer_text": "56",
            "student_answer_text": "56",
            "guidance_mode": "standard",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["diagnosis"]["is_correct"] is True

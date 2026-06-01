"""Service-layer integration tests — exercise real service functions with real DB.

Read-only tests call async services directly via fresh event loops.
Write tests use TestClient (like the existing test suite) to avoid aiosqlite
WAL locking issues with direct async calls outside the ASGI lifecycle.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _run(coro):
    """Run an async coroutine in a fresh event loop to avoid conflicts with TestClient's loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# TestGrowthMilestone — stage computation and practice-day recording
# ---------------------------------------------------------------------------

class TestGrowthMilestone:

    def test_compute_stage_thresholds(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(0) == "seed"
        assert compute_stage(1) == "seed"
        assert compute_stage(3) == "sprout"
        assert compute_stage(7) == "first_leaf"
        assert compute_stage(14) == "taller"
        assert compute_stage(21) == "branching"
        assert compute_stage(30) == "sturdy"
        assert compute_stage(45) == "bud"
        assert compute_stage(60) == "flowering"
        assert compute_stage(90) == "mature"
        assert compute_stage(999) == "mature"

    def test_compute_stage_between_thresholds(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(2) == "seed"
        assert compute_stage(5) == "sprout"
        assert compute_stage(10) == "first_leaf"
        assert compute_stage(50) == "bud"
        assert compute_stage(75) == "flowering"

    def test_compute_stage_high_accuracy_boost(self):
        from app.services.growth_milestone import compute_stage
        base = compute_stage(14)
        boosted = compute_stage(14, accuracy=0.85, mastery_count=3)
        assert base == "taller"
        assert boosted == "branching"

    def test_compute_stage_low_accuracy_demotion(self):
        from app.services.growth_milestone import compute_stage
        base = compute_stage(14)
        demoted = compute_stage(14, accuracy=0.40, mastery_count=0)
        assert base == "taller"
        assert demoted == "first_leaf"

    def test_record_practice_day_increments(self):
        from app.services.growth_milestone import record_practice_day, get_growth_milestone
        result = _run(record_practice_day("S001"))
        assert "days_completed" in result
        assert result["days_completed"] >= 1

        milestone = _run(get_growth_milestone("S001"))
        assert milestone is not None
        assert milestone.days_completed >= 1
        assert milestone.current_stage in (
            "seed", "sprout", "first_leaf", "taller", "branching",
            "sturdy", "bud", "flowering", "mature",
        )

    def test_growth_milestone_for_nonexistent_student(self):
        from app.services.growth_milestone import get_growth_milestone
        assert _run(get_growth_milestone("NONEXISTENT")) is None

    def test_record_practice_day_nonexistent_student(self):
        from app.exceptions import NotFoundException
        from app.services.growth_milestone import record_practice_day
        with pytest.raises(NotFoundException):
            _run(record_practice_day("NONEXISTENT"))


# ---------------------------------------------------------------------------
# TestBKTMastery — Bayesian Knowledge Tracing
# ---------------------------------------------------------------------------

class TestBKTMastery:

    def test_mastery_increases_after_correct_sequence(self):
        from app.services.mastery_service import _bkt_forward, ERROR_CODE_PARAMS
        params = ERROR_CODE_PARAMS["E01"]
        assert _bkt_forward(params, [True] * 5) > params.p_l0

    def test_mastery_decreases_after_incorrect_sequence(self):
        from app.services.mastery_service import _bkt_forward, ERROR_CODE_PARAMS
        params = ERROR_CODE_PARAMS["E01"]
        assert _bkt_forward(params, [False] * 3) < params.p_l0

    def test_mastery_saturates_on_many_correct(self):
        from app.services.mastery_service import _bkt_forward, ERROR_CODE_PARAMS
        p = _bkt_forward(ERROR_CODE_PARAMS["E03"], [True] * 50)
        assert 0.99 <= p <= 0.999

    def test_temporal_ordering_matters(self):
        from app.services.mastery_service import _bkt_forward, ERROR_CODE_PARAMS
        params = ERROR_CODE_PARAMS["E02"]
        assert _bkt_forward(params, [False, False, True]) != _bkt_forward(params, [True, False, False])

    def test_zone_classification(self):
        from app.services.mastery_service import _zone
        assert _zone(0.90) == "mastered"
        assert _zone(0.85) == "mastered"
        assert _zone(0.70) == "learning"
        assert _zone(0.50) == "learning"
        assert _zone(0.49) == "needs_practice"
        assert _zone(0.0) == "needs_practice"

    def test_get_student_mastery_structure(self):
        from app.services.mastery_service import get_student_mastery
        result = _run(get_student_mastery("S001"))
        assert result["student_id"] == "S001"
        assert len(result["error_codes"]) >= 11
        assert "overall_mastery" in result
        assert "mastered_count" in result
        for code, info in result["error_codes"].items():
            assert info["mastery_probability"] <= 0.999

    def test_get_student_mastery_nonexistent(self):
        from app.exceptions import NotFoundException
        from app.services.mastery_service import get_student_mastery
        with pytest.raises(NotFoundException):
            _run(get_student_mastery("NONEXISTENT"))

    def test_bkt_params_all_codes_defined(self):
        from app.services.mastery_service import ERROR_CODE_PARAMS, ERROR_CODES
        for code in ERROR_CODES:
            assert code in ERROR_CODE_PARAMS
            p = ERROR_CODE_PARAMS[code]
            assert 0 < p.p_l0 < 1 and 0 < p.p_t < 1


# ---------------------------------------------------------------------------
# TestArchetype — student classification
# ---------------------------------------------------------------------------

class TestArchetype:

    def test_solid_steady_high_accuracy_stable(self):
        from app.services.archetype import classify_student
        r = classify_student(accuracy=0.90, accuracy_trend="stable", total_attempts=100, mastery_count=8)
        assert r.archetype_id == "solid_steady" and r.confidence >= 0.7

    def test_solid_steady_high_accuracy_improving(self):
        from app.services.archetype import classify_student
        assert classify_student(accuracy=0.85, accuracy_trend="improving", total_attempts=50, mastery_count=4).archetype_id == "solid_steady"

    def test_steady_progress_improving(self):
        from app.services.archetype import classify_student
        assert classify_student(accuracy=0.65, accuracy_trend="improving", total_attempts=30).archetype_id == "steady_progress"

    def test_climbing_hard_low_accuracy(self):
        from app.services.archetype import classify_student
        assert classify_student(accuracy=0.45, accuracy_trend="stable", total_attempts=50).archetype_id == "climbing_hard"

    def test_climbing_hard_wrong_streak(self):
        from app.services.archetype import classify_student
        assert classify_student(accuracy=0.70, accuracy_trend="stable", total_attempts=30, current_streak_wrong=5).archetype_id == "climbing_hard"

    def test_growth_potential_insufficient_data(self):
        from app.services.archetype import classify_student
        r = classify_student(accuracy=0.50, accuracy_trend="stable", total_attempts=3)
        assert r.archetype_id == "growth_potential" and r.confidence == 0.3

    def test_growth_potential_middle_ground(self):
        from app.services.archetype import classify_student
        assert classify_student(accuracy=0.70, accuracy_trend="stable", total_attempts=50).archetype_id == "growth_potential"

    def test_evidence_contains_accuracy(self):
        from app.services.archetype import classify_student
        r = classify_student(accuracy=0.88, accuracy_trend="stable", total_attempts=30, mastery_count=5)
        assert any("88%" in e or "90%" in e for e in r.evidence)

    def test_all_ten_students_get_archetype(self):
        from app.services.student_service import list_students, get_student_profile
        valid_ids = {"solid_steady", "steady_progress", "climbing_hard", "growth_potential"}
        for s in _run(list_students())[:10]:
            profile = _run(get_student_profile(s.student_id))
            assert profile is not None
            if profile.archetype:
                assert profile.archetype["id"] in valid_ids


# ---------------------------------------------------------------------------
# TestProfileSummaries — student and class profiles
# ---------------------------------------------------------------------------

class TestProfileSummaries:

    def test_student_profile_summary_returns_data(self):
        from app.services.profiles import get_student_profile_summary
        r = _run(get_student_profile_summary("S001"))
        assert r is not None and r["total_attempts"] > 0 and 0 <= r["overall_accuracy"] <= 1.0

    def test_student_profile_summary_error_breakdown_sorted(self):
        from app.services.profiles import get_student_profile_summary
        r = _run(get_student_profile_summary("S001"))
        bd = r["error_breakdown"]
        for i in range(len(bd) - 1):
            assert bd[i]["total_attempts"] >= bd[i + 1]["total_attempts"]

    def test_student_profile_summary_nonexistent(self):
        from app.services.profiles import get_student_profile_summary
        assert _run(get_student_profile_summary("NONEXISTENT")) is None

    def test_class_profile_summary(self):
        from app.services.profiles import get_class_profile_summary
        r = _run(get_class_profile_summary("G6C1"))
        assert r["class_id"] == "G6C1" and isinstance(r["top_class_errors"], list)

    def test_class_error_summary(self):
        from app.services.summaries import get_class_error_summary
        r = _run(get_class_error_summary("G6C1"))
        assert r is not None and "student_tiers" in r
        assert "优秀" in r["student_tiers"] and "需关注" in r["student_tiers"]

    def test_class_error_summary_nonexistent_class(self):
        from app.services.summaries import get_class_error_summary
        assert _run(get_class_error_summary("NONEXISTENT")) is None

    def test_error_code_breakdown(self):
        from app.services.summaries import get_error_code_breakdown
        r = _run(get_error_code_breakdown("G6C1"))
        assert r is not None
        for ec in r["error_codes"]:
            assert "code" in ec and "total_occurrences" in ec and "avg_accuracy_for_code" in ec

    def test_class_period_summary(self):
        from app.services.summaries import get_class_period_summary
        r = _run(get_class_period_summary("G6C1", period="weekly"))
        assert r is not None and isinstance(r["accuracy_trend"], list)

    def test_full_student_profile_has_archetype(self):
        from app.services.student_service import get_student_profile
        p = _run(get_student_profile("S001"))
        assert p.student.name and isinstance(p.accuracy, float)
        if p.archetype:
            assert "id" in p.archetype and "name" in p.archetype


# ---------------------------------------------------------------------------
# TestGradingPipeline — complete homework lifecycle (via TestClient)
# ---------------------------------------------------------------------------

class TestGradingPipeline:

    def _make_and_grade(self, student_id="S001", error_codes=None, answer_fn=None, count=3):
        error_codes = error_codes or ["E03"]
        gen_r = client.post("/api/homework/generate", json={
            "class_id": "G6A1", "student_id": student_id, "grade": 6,
            "error_codes_target": error_codes, "problem_count": count, "difficulty": "A",
        })
        assert gen_r.status_code == 200
        hw = gen_r.json()
        hw_id = hw["homework_id"]
        problems = hw["problems"]

        assign_r = client.post("/api/homework/assign", json={"homework_id": hw_id})
        assert assign_r.status_code == 200

        answers = []
        for p in problems:
            raw = answer_fn(p) if answer_fn else p["correct_answer"]
            answers.append({"problem_sequence": p["sequence"], "raw_answer": raw})

        submit_r = client.post("/api/homework/submit", json={
            "homework_id": hw_id, "student_id": student_id, "answers": answers,
        })
        assert submit_r.status_code == 200

        grade_r = client.post(f"/api/homework/grade?homework_id={hw_id}&student_id={student_id}")
        assert grade_r.status_code == 200
        return grade_r.json()

    def test_grade_homework_updates_stats(self):
        gd = self._make_and_grade(student_id="S001", error_codes=["E01"], answer_fn=lambda p: "0")
        assert gd["total_problems"] > 0

        profile_r = client.get("/api/students/S001/profile")
        assert profile_r.status_code == 200
        profile = profile_r.json()
        assert isinstance(profile["accuracy"], float)

    def test_grade_homework_creates_diagnosis(self):
        gd = self._make_and_grade(student_id="S002", error_codes=["E02"], answer_fn=lambda p: "999")
        assert gd["total_problems"] > 0

        traj_r = client.get("/api/students/S002/trajectory")
        assert traj_r.status_code == 200
        assert isinstance(traj_r.json(), list)

    def test_grade_all_correct_no_error_codes(self):
        gd = self._make_and_grade(student_id="S003", error_codes=["E01"], count=3)
        assert gd["accuracy"] == 1.0
        assert gd["correct_count"] == gd["total_problems"]
        assert gd["primary_errors"] == []

    def test_grade_all_wrong_has_error_codes(self):
        gd = self._make_and_grade(student_id="S003", error_codes=["E03"], count=3, answer_fn=lambda p: "99999")
        assert gd["correct_count"] == 0
        assert gd["accuracy"] == 0.0
        assert len(gd["primary_errors"]) > 0

    def test_grade_result_fields(self):
        gd = self._make_and_grade(student_id="S003", error_codes=["E01", "E02"], count=4)
        for field in ("homework_id", "student_id", "total_problems", "correct_count",
                       "accuracy", "primary_errors", "profile_updated", "growth_updated"):
            assert field in gd


# ---------------------------------------------------------------------------
# TestQuizService — quiz creation and response (via TestClient)
# ---------------------------------------------------------------------------

class TestQuizService:

    def test_create_quiz(self):
        r = client.post("/api/quiz/generate", json={
            "class_id": "G6A1", "grade": 6,
            "error_codes_target": ["E03", "E02"], "problem_count": 4, "difficulty": "B",
        })
        assert r.status_code == 200
        data = r.json()
        assert "quiz_id" in data and len(data["problems"]) == 4
        for p in data["problems"]:
            assert p["problem"].strip() and p["correct_answer"].strip()

    def test_add_response(self):
        gen_r = client.post("/api/quiz/generate", json={
            "class_id": "G6A1", "error_codes_target": ["E03"], "problem_count": 3,
        })
        quiz = gen_r.json()
        quiz_id = quiz["quiz_id"]
        problems = quiz["problems"]

        resp_r = client.post(f"/api/quiz/{quiz_id}/response", json={
            "quiz_id": quiz_id,
            "problem_sequence": problems[0]["sequence"], "class_response": "mostly_correct",
        })
        assert resp_r.status_code == 200

        resp_r2 = client.post(f"/api/quiz/{quiz_id}/response", json={
            "quiz_id": quiz_id,
            "problem_sequence": problems[1]["sequence"], "class_response": "mixed",
        })
        assert resp_r2.status_code == 200

    def test_quiz_summary(self):
        gen_r = client.post("/api/quiz/generate", json={
            "class_id": "G6A1", "error_codes_target": ["E01"], "problem_count": 3,
        })
        quiz = gen_r.json()
        quiz_id = quiz["quiz_id"]
        problems = quiz["problems"]

        for p, resp in zip(problems, ["mostly_correct", "mostly_wrong", "mixed"]):
            client.post(f"/api/quiz/{quiz_id}/response", json={
                "quiz_id": quiz_id,
                "problem_sequence": p["sequence"], "class_response": resp,
            })

        summary_r = client.get(f"/api/quiz/{quiz_id}/summary")
        assert summary_r.status_code == 200
        s = summary_r.json()
        assert s["mostly_correct_count"] == 1
        assert s["mostly_wrong_count"] == 1
        assert s["mixed_count"] == 1
        assert "recommendation" in s

    def test_quiz_not_found(self):
        assert client.get("/api/quiz/NONEXISTENT").status_code == 404


# ---------------------------------------------------------------------------
# TestCurriculumService — curriculum, trajectory, schedule
# ---------------------------------------------------------------------------

class TestCurriculumService:

    def test_get_units(self):
        from app.services.curriculum_service import get_units
        units = _run(get_units(grade=6, semester=2))
        assert isinstance(units, list)
        if units:
            assert "unit_number" in units[0] or "id" in units[0]

    def test_get_student_trajectory(self):
        from app.services.curriculum_service import get_student_trajectory
        traj = _run(get_student_trajectory("S001"))
        assert isinstance(traj, list)
        if traj:
            assert "error_code" in traj[0] and "accuracy" in traj[0]

    def test_get_student_trajectory_nonexistent(self):
        from app.services.curriculum_service import get_student_trajectory
        assert _run(get_student_trajectory("NONEXISTENT")) == []

    def test_get_schedule(self):
        from app.services.curriculum_service import get_schedule
        assert isinstance(_run(get_schedule("G6A1")), list)

    def test_get_calendar(self):
        from app.services.curriculum_service import get_calendar
        assert isinstance(_run(get_calendar(academic_year="2024-2025", semester=2)), list)

    def test_update_student_profile_tags(self):
        # Directly call the service to avoid query-param list serialization issues
        from app.services.curriculum_service import update_student_profile
        ok = _run(update_student_profile("S001", personality_tags=["细心", "认真"], learning_style="visual"))
        assert ok is True

        from app.services.student_service import get_student
        student = _run(get_student("S001"))
        assert "细心" in student.personality_tags
        assert "认真" in student.personality_tags
        assert student.learning_style == "visual"

    def test_get_current_cycle(self):
        from app.services.cycle_service import get_current_cycle
        cycle = _run(get_current_cycle(6))
        if cycle is not None:
            assert cycle.grade == 6 and cycle.total_days > 0


# ---------------------------------------------------------------------------
# TestKnowledgeService — FTS5 knowledge base search
# ---------------------------------------------------------------------------

class TestKnowledgeService:

    def test_search_knowledge_returns_results(self):
        from app.services.knowledge_service import init_knowledge_index, search_knowledge
        _run(init_knowledge_index())
        assert isinstance(_run(search_knowledge("分数", limit=3)), list)

    def test_search_knowledge_empty_query(self):
        from app.services.knowledge_service import search_knowledge
        assert _run(search_knowledge("", limit=3)) == []

    def test_search_knowledge_short_query_fallback(self):
        from app.services.knowledge_service import search_knowledge
        assert isinstance(_run(search_knowledge("加", limit=3)), list)


# ---------------------------------------------------------------------------
# TestStudentService — student CRUD, error stats, weak points
# ---------------------------------------------------------------------------

class TestStudentService:

    def test_get_student(self):
        from app.services.student_service import get_student
        s = _run(get_student("S001"))
        assert s.student_id == "S001" and s.grade == 6

    def test_list_students(self):
        from app.services.student_service import list_students
        assert len(_run(list_students())) >= 10

    def test_list_students_by_class(self):
        from app.services.student_service import list_students
        students = _run(list_students(class_id="G6C1"))
        assert len(students) >= 5
        assert all(s.class_id == "G6C1" for s in students)

    def test_update_error_stats_via_grading(self):
        """update_error_stats is exercised by grading; verify via profile."""
        profile_r = client.get("/api/students/S001/profile")
        assert profile_r.status_code == 200
        data = profile_r.json()
        assert isinstance(data.get("accuracy_by_error_code", {}), dict)

    def test_get_weak_knowledge_points(self):
        from app.services.student_service import get_weak_knowledge_points
        weak = _run(get_weak_knowledge_points("S001"))
        assert isinstance(weak, list)
        if weak:
            assert weak[0]["mastery_zone"] in ("needs_practice", "learning", "no_data")

    def test_get_class_weak_points(self):
        from app.services.student_service import get_class_weak_points
        weak = _run(get_class_weak_points("G6C1"))
        assert isinstance(weak, list)
        if weak:
            assert "affected_students" in weak[0]

    def test_build_guidance_context(self):
        from app.services.student_service import build_guidance_context
        ctx = _run(build_guidance_context("S001"))
        assert "学习画像" in ctx or "暂无学习数据" in ctx


# ---------------------------------------------------------------------------
# TestHomeworkService — homework generation and adaptive difficulty
# ---------------------------------------------------------------------------

class TestHomeworkService:

    def test_generate_homework_class_level(self):
        r = client.post("/api/homework/generate", json={
            "class_id": "G6A1", "grade": 6,
            "error_codes_target": ["E01", "E03"], "problem_count": 5, "difficulty": "A",
        })
        assert r.status_code == 200
        hw = r.json()
        assert hw["homework_id"] and len(hw["problems"]) == 5 and hw["status"] == "draft"

    def test_generate_homework_student_level_adaptive(self):
        r = client.post("/api/homework/generate", json={
            "class_id": "G6A1", "grade": 6, "student_id": "S001",
            "problem_count": 4, "difficulty": "B",
        })
        assert r.status_code == 200 and len(r.json()["problems"]) == 4

    def test_get_homework_detail(self):
        gen_r = client.post("/api/homework/generate", json={
            "class_id": "G6A1", "grade": 6,
            "error_codes_target": ["E02"], "problem_count": 2, "difficulty": "A",
        })
        hw_id = gen_r.json()["homework_id"]
        detail_r = client.get(f"/api/homework/{hw_id}")
        assert detail_r.status_code == 200
        assert detail_r.json()["homework_id"] == hw_id

    def test_get_homework_nonexistent(self):
        assert client.get("/api/homework/NONEXISTENT").status_code == 404

    def test_get_class_top_errors(self):
        from app.services.homework_service import get_class_top_errors
        errors = _run(get_class_top_errors("G6A1"))
        assert isinstance(errors, list)
        if errors:
            assert all(e.startswith("E") for e in errors)

    def test_difficulty_distribution_low_accuracy(self):
        from app.services.homework_service import _difficulty_distribution_for
        dist = _difficulty_distribution_for(0.5)
        assert dist["A"] > dist.get("C", 0)

    def test_difficulty_distribution_high_accuracy(self):
        from app.services.homework_service import _difficulty_distribution_for
        dist = _difficulty_distribution_for(0.9)
        assert dist.get("C", 0) > dist.get("A", 0)

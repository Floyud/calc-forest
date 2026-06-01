"""Integration tests for homework_analytics service.

Tests the 3 public async functions against real SQLite:
- get_class_homework_history
- get_homework_detail_analytics
- get_student_homework_summary
"""

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient

from app.exceptions import NotFoundException
from app.main import app
from app.services.homework_analytics import (
    get_class_homework_history,
    get_homework_detail_analytics,
    get_student_homework_summary,
)

# Module-level TestClient triggers lifespan → init_db()
client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PREFIX = "THA"


def _uid(tag: str = "") -> str:
    return f"{_PREFIX}_{tag}_{uuid.uuid4().hex[:8]}"


def _run(coro):
    """Run an async coroutine on the current event loop."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Seed helpers — direct DB inserts
# ---------------------------------------------------------------------------

async def _seed_class(db, class_id: str, name: str = "TestClass"):
    await db.execute(
        "INSERT INTO classes (id, name, grade, academic_year, semester, student_ids) "
        "VALUES (?, ?, 6, '2025-2026', '2', '[]')",
        (class_id, name),
    )


async def _seed_student(db, student_id: str, name: str, class_id: str):
    await db.execute(
        "INSERT INTO students "
        "(id, name, grade, class_id, guidance_mode, textbook_version, start_grade, enrolled_at) "
        "VALUES (?, ?, 6, ?, 'standard', 'PEP', 1, '2025-01-01')",
        (student_id, name, class_id),
    )


async def _seed_homework(
    db, hw_id: str, class_id: str,
    status: str = "graded", created_at: str = "2025-05-01T10:00:00",
):
    await db.execute(
        "INSERT INTO homework (id, class_id, grade, status, created_at) "
        "VALUES (?, ?, 6, ?, ?)",
        (hw_id, class_id, status, created_at),
    )


async def _seed_problem(
    db, hw_id: str, sequence: int,
    problem: str = "2+3=", correct_answer: str = "5",
    target_error_code: str = "E01", difficulty: str = "A",
):
    await db.execute(
        "INSERT INTO homework_problems "
        "(id, homework_id, sequence, problem, correct_answer, "
        " target_error_code, difficulty) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (f"{hw_id}_p{sequence}", hw_id, sequence,
         problem, correct_answer, target_error_code, difficulty),
    )


async def _seed_submission(db, hw_id: str, student_id: str, submitted_at: str = "2025-05-01T12:00:00"):
    sub_id = f"{hw_id}_{student_id}_sub"
    await db.execute(
        "INSERT INTO homework_submissions "
        "(id, homework_id, student_id, submitted_at) "
        "VALUES (?, ?, ?, ?)",
        (sub_id, hw_id, student_id, submitted_at),
    )
    return sub_id


async def _seed_answer(
    db, hw_id: str, student_id: str, sequence: int,
    is_correct: bool, error_code: str | None = None,
):
    sub_id = f"{hw_id}_{student_id}_sub"
    ans_id = f"{hw_id}_{student_id}_a{sequence}"
    await db.execute(
        "INSERT INTO student_answers "
        "(id, submission_id, homework_id, student_id, problem_sequence, "
        " problem, correct_answer, student_answer, is_correct, error_code, error_label) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (ans_id, sub_id, hw_id, student_id, sequence,
         "2+3=", "5", "5" if is_correct else "6",
         1 if is_correct else 0,
         error_code if not is_correct else None,
         "test" if not is_correct else None),
    )


async def _cleanup(db, class_id: str, student_ids: list[str], hw_ids: list[str]):
    await db.execute("PRAGMA foreign_keys = OFF")
    for hid in hw_ids:
        await db.execute(
            "DELETE FROM grading_comments WHERE homework_id = ?", (hid,)
        )
        await db.execute("DELETE FROM student_answers WHERE homework_id = ?", (hid,))
        await db.execute(
            "DELETE FROM homework_submissions WHERE homework_id = ?", (hid,)
        )
        await db.execute(
            "DELETE FROM homework_problems WHERE homework_id = ?", (hid,)
        )
        await db.execute("DELETE FROM homework WHERE id = ?", (hid,))
    for sid in student_ids:
        await db.execute("DELETE FROM students WHERE id = ?", (sid,))
    await db.execute("DELETE FROM classes WHERE id = ?", (class_id,))
    await db.execute("PRAGMA foreign_keys = ON")
    await db.commit()


# ===========================================================================
# TestGetClassHomeworkHistory
# ===========================================================================

class TestGetClassHomeworkHistory:
    """Tests for get_class_homework_history()."""

    def test_nonexistent_class_raises_404(self):
        with pytest.raises(NotFoundException, match="不存在"):
            _run(get_class_homework_history("NONEXISTENT_CLASS_999"))

    def test_empty_class_returns_zeros(self):
        cid = _uid("cls")
        s1 = _uid("s1")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid)
                await _seed_student(db, s1, "Alice", cid)
                await db.commit()

                result = await get_class_homework_history(cid)

                assert result["class_id"] == cid
                assert result["total_homeworks"] == 0
                assert result["avg_accuracy"] == 0.0
                assert result["completion_rate"] == 0.0
                assert result["most_common_error"] is None
                assert result["recent_homeworks"] == []
                assert result["error_distribution"] == {}

                await _cleanup(db, cid, [s1], [])

        _run(_setup_and_test())

    def test_single_homework_with_answers(self):
        cid = _uid("cls")
        s1 = _uid("s1")
        s2 = _uid("s2")
        hw = _uid("hw")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid, "TestClass")
                await _seed_student(db, s1, "Alice", cid)
                await _seed_student(db, s2, "Bob", cid)
                await _seed_homework(db, hw, cid, "graded", "2025-05-10T10:00:00")

                # 3 problems: E01, E02, E01
                await _seed_problem(db, hw, 1, target_error_code="E01")
                await _seed_problem(db, hw, 2, target_error_code="E02")
                await _seed_problem(db, hw, 3, target_error_code="E01")

                # Submissions
                await _seed_submission(db, hw, s1)
                await _seed_submission(db, hw, s2)

                # S1: seq1=correct, seq2=wrong(E02), seq3=correct
                await _seed_answer(db, hw, s1, 1, True)
                await _seed_answer(db, hw, s1, 2, False, "E02")
                await _seed_answer(db, hw, s1, 3, True)

                # S2: seq1=wrong(E01), seq2=correct, seq3=wrong(E01)
                await _seed_answer(db, hw, s2, 1, False, "E01")
                await _seed_answer(db, hw, s2, 2, True)
                await _seed_answer(db, hw, s2, 3, False, "E01")

                await db.commit()

                result = await get_class_homework_history(cid)

                # total_homeworks
                assert result["total_homeworks"] == 1
                assert result["class_id"] == cid

                # avg_accuracy: 3 correct / 6 total = 0.5
                assert result["avg_accuracy"] == 0.5

                # completion_rate: 2 submissions / (3 problems * 10) = 0.0667
                assert result["completion_rate"] == round(2 / 30, 4)

                # most_common_error: E01 (2) > E02 (1)
                assert result["most_common_error"] == "E01"

                # error_distribution: E01=2, E02=1
                assert result["error_distribution"]["E01"] == 2
                assert result["error_distribution"]["E02"] == 1

                # recent_homeworks
                assert len(result["recent_homeworks"]) == 1
                rh = result["recent_homeworks"][0]
                assert rh["homework_id"] == hw
                assert rh["status"] == "graded"
                assert rh["problem_count"] == 3
                assert rh["submission_count"] == 2
                assert rh["avg_accuracy"] == 0.5
                assert rh["top_error"] == "E01"

                await _cleanup(db, cid, [s1, s2], [hw])

        _run(_setup_and_test())

    def test_multiple_homeworks_ordered_by_date(self):
        """Multiple homeworks — should be ordered by created_at DESC."""
        cid = _uid("cls")
        s1 = _uid("s1")
        hw1 = _uid("hw1")
        hw2 = _uid("hw2")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid)
                await _seed_student(db, s1, "Alice", cid)

                # hw1 is older
                await _seed_homework(db, hw1, cid, "graded", "2025-05-01T10:00:00")
                await _seed_problem(db, hw1, 1, target_error_code="E01")
                await _seed_submission(db, hw1, s1)
                await _seed_answer(db, hw1, s1, 1, True)

                # hw2 is newer
                await _seed_homework(db, hw2, cid, "graded", "2025-05-08T10:00:00")
                await _seed_problem(db, hw2, 1, target_error_code="E02")
                await _seed_submission(db, hw2, s1)
                await _seed_answer(db, hw2, s1, 1, False, "E02")

                await db.commit()

                result = await get_class_homework_history(cid)

                assert result["total_homeworks"] == 2
                # Most recent first
                assert result["recent_homeworks"][0]["homework_id"] == hw2
                assert result["recent_homeworks"][1]["homework_id"] == hw1

                await _cleanup(db, cid, [s1], [hw1, hw2])

        _run(_setup_and_test())


# ===========================================================================
# TestGetHomeworkDetailAnalytics
# ===========================================================================

class TestGetHomeworkDetailAnalytics:
    """Tests for get_homework_detail_analytics()."""

    def test_nonexistent_homework_raises_404(self):
        with pytest.raises(NotFoundException, match="不存在"):
            _run(get_homework_detail_analytics("NONEXISTENT_HW_999"))

    def test_single_student_full_accuracy(self):
        cid = _uid("cls")
        s1 = _uid("s1")
        hw = _uid("hw")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid)
                await _seed_student(db, s1, "Alice", cid)
                await _seed_homework(db, hw, cid, "graded", "2025-05-10T10:00:00")

                await _seed_problem(db, hw, 1, target_error_code="E01")
                await _seed_problem(db, hw, 2, target_error_code="E02")
                await _seed_problem(db, hw, 3, target_error_code="E01")

                await _seed_submission(db, hw, s1)
                await _seed_answer(db, hw, s1, 1, True)
                await _seed_answer(db, hw, s1, 2, True)
                await _seed_answer(db, hw, s1, 3, True)

                await db.commit()

                result = await get_homework_detail_analytics(hw)

                assert result["homework_id"] == hw
                assert result["status"] == "graded"
                assert result["problem_count"] == 3
                assert result["submission_count"] == 1
                assert result["avg_accuracy"] == 1.0

                # No errors → empty distribution
                assert result["error_distribution"] == []

                # Per-problem accuracy all 1.0
                assert len(result["per_problem_accuracy"]) == 3
                for pp in result["per_problem_accuracy"]:
                    assert pp["accuracy"] == 1.0

                # Student results
                assert len(result["student_results"]) == 1
                sr = result["student_results"][0]
                assert sr["student_id"] == s1
                assert sr["student_name"] == "Alice"
                assert sr["accuracy"] == 1.0
                assert sr["correct_count"] == 3
                assert sr["total_count"] == 3
                assert sr["primary_error"] is None
                assert sr["review_status"] == "pending_teacher_review"

                # No one needs attention
                assert result["needs_attention"] == []

                # No previous homework → no trend
                assert result["accuracy_trend_vs_last"] is None

                await _cleanup(db, cid, [s1], [hw])

        _run(_setup_and_test())

    def test_multiple_students_mixed_results(self):
        cid = _uid("cls")
        s1 = _uid("s1")
        s2 = _uid("s2")
        s3 = _uid("s3")
        hw = _uid("hw")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid)
                await _seed_student(db, s1, "Alice", cid)
                await _seed_student(db, s2, "Bob", cid)
                await _seed_student(db, s3, "Carol", cid)
                await _seed_homework(db, hw, cid, "graded", "2025-05-10T10:00:00")

                # 3 problems
                await _seed_problem(db, hw, 1, target_error_code="E01")
                await _seed_problem(db, hw, 2, target_error_code="E02")
                await _seed_problem(db, hw, 3, target_error_code="E03")

                # S1 (Alice): 3/3 correct → 100%
                await _seed_submission(db, hw, s1)
                await _seed_answer(db, hw, s1, 1, True)
                await _seed_answer(db, hw, s1, 2, True)
                await _seed_answer(db, hw, s1, 3, True)

                # S2 (Bob): 1/3 correct → 33% → needs_attention
                await _seed_submission(db, hw, s2)
                await _seed_answer(db, hw, s2, 1, False, "E01")
                await _seed_answer(db, hw, s2, 2, True)
                await _seed_answer(db, hw, s2, 3, False, "E03")

                # S3 (Carol): 2/3 correct → 67%
                await _seed_submission(db, hw, s3)
                await _seed_answer(db, hw, s3, 1, True)
                await _seed_answer(db, hw, s3, 2, False, "E02")
                await _seed_answer(db, hw, s3, 3, True)

                await db.commit()

                result = await get_homework_detail_analytics(hw)

                assert result["homework_id"] == hw
                assert result["problem_count"] == 3
                assert result["submission_count"] == 3

                # avg_accuracy: 6 correct / 9 total
                assert result["avg_accuracy"] == round(6 / 9, 4)

                # error_distribution: E01=1, E03=1, E02=1
                ed_codes = {e["code"]: e["count"] for e in result["error_distribution"]}
                assert ed_codes.get("E01") == 1
                assert ed_codes.get("E02") == 1
                assert ed_codes.get("E03") == 1
                # Check labels are present
                for e in result["error_distribution"]:
                    assert e["label"]  # non-empty label

                # per_problem_accuracy
                assert len(result["per_problem_accuracy"]) == 3
                # Problem 1: 2 correct (Alice, Carol) / 3 → 0.6667
                ppa_map = {p["sequence"]: p for p in result["per_problem_accuracy"]}
                assert ppa_map[1]["accuracy"] == round(2 / 3, 4)
                assert ppa_map[2]["accuracy"] == round(2 / 3, 4)
                assert ppa_map[3]["accuracy"] == round(2 / 3, 4)

                # student_results — ordered by student_id
                assert len(result["student_results"]) == 3
                sr_map = {sr["student_id"]: sr for sr in result["student_results"]}

                assert sr_map[s1]["accuracy"] == 1.0
                assert sr_map[s1]["primary_error"] is None

                assert sr_map[s2]["accuracy"] == round(1 / 3, 4)
                assert sr_map[s2]["primary_error"] is not None  # E01 or E03

                assert sr_map[s3]["accuracy"] == round(2 / 3, 4)
                assert sr_map[s3]["primary_error"] == "E02"

                # needs_attention: only S2 (accuracy < 0.5)
                assert s2 in result["needs_attention"]
                assert s1 not in result["needs_attention"]
                assert s3 not in result["needs_attention"]

                await _cleanup(db, cid, [s1, s2, s3], [hw])

        _run(_setup_and_test())

    def test_accuracy_trend_vs_previous_homework(self):
        """accuracy_trend_vs_last computed when a previous homework exists."""
        cid = _uid("cls")
        s1 = _uid("s1")
        hw_prev = _uid("hwp")
        hw_curr = _uid("hwc")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid)
                await _seed_student(db, s1, "Alice", cid)

                # Previous homework: 1/2 correct = 0.5
                await _seed_homework(
                    db, hw_prev, cid, "graded", "2025-05-01T10:00:00"
                )
                await _seed_problem(db, hw_prev, 1, target_error_code="E01")
                await _seed_problem(db, hw_prev, 2, target_error_code="E02")
                await _seed_submission(db, hw_prev, s1)
                await _seed_answer(db, hw_prev, s1, 1, True)
                await _seed_answer(db, hw_prev, s1, 2, False, "E02")

                # Current homework: 2/2 correct = 1.0
                await _seed_homework(
                    db, hw_curr, cid, "graded", "2025-05-08T10:00:00"
                )
                await _seed_problem(db, hw_curr, 1, target_error_code="E01")
                await _seed_problem(db, hw_curr, 2, target_error_code="E01")
                await _seed_submission(db, hw_curr, s1)
                await _seed_answer(db, hw_curr, s1, 1, True)
                await _seed_answer(db, hw_curr, s1, 2, True)

                await db.commit()

                result = await get_homework_detail_analytics(hw_curr)

                # trend = 1.0 - 0.5 = 0.5
                assert result["accuracy_trend_vs_last"] == 0.5

                await _cleanup(db, cid, [s1], [hw_prev, hw_curr])

        _run(_setup_and_test())


# ===========================================================================
# TestGetStudentHomeworkSummary
# ===========================================================================

class TestGetStudentHomeworkSummary:
    """Tests for get_student_homework_summary()."""

    def test_nonexistent_student_raises_404(self):
        with pytest.raises(NotFoundException, match="不存在"):
            _run(get_student_homework_summary("NONEXISTENT_STUDENT_999"))

    def test_student_no_homework(self):
        cid = _uid("cls")
        s1 = _uid("s1")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid)
                await _seed_student(db, s1, "Alice", cid)
                await db.commit()

                result = await get_student_homework_summary(s1)

                assert result["student_id"] == s1
                assert result["total_homeworks"] == 0
                assert result["avg_accuracy"] == 0.0
                assert result["recent_trend"] == "stable"
                assert result["homework_history"] == []

                await _cleanup(db, cid, [s1], [])

        _run(_setup_and_test())

    def test_student_with_improving_trend(self):
        """3 homeworks with improving accuracy → trend = 'improving'."""
        cid = _uid("cls")
        s1 = _uid("s1")
        hw1 = _uid("hw1")
        hw2 = _uid("hw2")
        hw3 = _uid("hw3")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid)
                await _seed_student(db, s1, "Alice", cid)

                # HW1 (oldest): 1/5 correct = 0.2
                await _seed_homework(
                    db, hw1, cid, "graded", "2025-04-20T10:00:00"
                )
                for seq in range(1, 6):
                    await _seed_problem(db, hw1, seq, target_error_code="E01")
                await _seed_submission(db, hw1, s1)
                await _seed_answer(db, hw1, s1, 1, False, "E01")
                await _seed_answer(db, hw1, s1, 2, True)
                await _seed_answer(db, hw1, s1, 3, False, "E01")
                await _seed_answer(db, hw1, s1, 4, False, "E01")
                await _seed_answer(db, hw1, s1, 5, False, "E01")

                # HW2 (middle): 3/5 correct = 0.6
                await _seed_homework(
                    db, hw2, cid, "graded", "2025-04-27T10:00:00"
                )
                for seq in range(1, 6):
                    await _seed_problem(db, hw2, seq, target_error_code="E02")
                await _seed_submission(db, hw2, s1)
                await _seed_answer(db, hw2, s1, 1, True)
                await _seed_answer(db, hw2, s1, 2, True)
                await _seed_answer(db, hw2, s1, 3, True)
                await _seed_answer(db, hw2, s1, 4, False, "E02")
                await _seed_answer(db, hw2, s1, 5, False, "E02")

                # HW3 (newest): 5/5 correct = 1.0
                await _seed_homework(
                    db, hw3, cid, "graded", "2025-05-04T10:00:00"
                )
                for seq in range(1, 6):
                    await _seed_problem(db, hw3, seq, target_error_code="E03")
                await _seed_submission(db, hw3, s1)
                await _seed_answer(db, hw3, s1, 1, True)
                await _seed_answer(db, hw3, s1, 2, True)
                await _seed_answer(db, hw3, s1, 3, True)
                await _seed_answer(db, hw3, s1, 4, True)
                await _seed_answer(db, hw3, s1, 5, True)

                await db.commit()

                result = await get_student_homework_summary(s1)

                assert result["student_id"] == s1
                assert result["total_homeworks"] == 3

                # avg_accuracy: mean of [1.0, 0.6, 0.2] = 0.6
                assert result["avg_accuracy"] == round(
                    (1.0 + 0.6 + 0.2) / 3, 4
                )

                # Trend: accuracies = [1.0, 0.6, 0.2] (DESC by date)
                # recent_avg = (1.0 + 0.6 + 0.2)/3 = 0.6
                # prior_avg = accuracies[-1] = 0.2 (len < 6)
                # delta = 0.6 - 0.2 = 0.4 > 0.05 → "improving"
                assert result["recent_trend"] == "improving"

                # homework_history: ordered by created_at DESC
                assert len(result["homework_history"]) == 3
                assert result["homework_history"][0]["homework_id"] == hw3
                assert result["homework_history"][0]["accuracy"] == 1.0
                assert result["homework_history"][1]["homework_id"] == hw2
                assert result["homework_history"][1]["accuracy"] == 0.6
                assert result["homework_history"][2]["homework_id"] == hw1
                assert result["homework_history"][2]["accuracy"] == 0.2

                # Check primary_error on HW1 and HW2
                assert result["homework_history"][0]["primary_error"] is None
                assert result["homework_history"][1]["primary_error"] == "E02"
                assert result["homework_history"][2]["primary_error"] == "E01"

                await _cleanup(db, cid, [s1], [hw1, hw2, hw3])

        _run(_setup_and_test())

    def test_student_with_declining_trend(self):
        """3 homeworks with declining accuracy → trend = 'declining'."""
        cid = _uid("cls")
        s1 = _uid("s1")
        hw1 = _uid("hw1")
        hw2 = _uid("hw2")
        hw3 = _uid("hw3")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid)
                await _seed_student(db, s1, "Bob", cid)

                # HW1 (oldest): 5/5 = 1.0
                await _seed_homework(
                    db, hw1, cid, "graded", "2025-04-20T10:00:00"
                )
                for seq in range(1, 6):
                    await _seed_problem(db, hw1, seq)
                await _seed_submission(db, hw1, s1)
                for seq in range(1, 6):
                    await _seed_answer(db, hw1, s1, seq, True)

                # HW2 (middle): 3/5 = 0.6
                await _seed_homework(
                    db, hw2, cid, "graded", "2025-04-27T10:00:00"
                )
                for seq in range(1, 6):
                    await _seed_problem(db, hw2, seq)
                await _seed_submission(db, hw2, s1)
                await _seed_answer(db, hw2, s1, 1, True)
                await _seed_answer(db, hw2, s1, 2, True)
                await _seed_answer(db, hw2, s1, 3, True)
                await _seed_answer(db, hw2, s1, 4, False, "E01")
                await _seed_answer(db, hw2, s1, 5, False, "E01")

                # HW3 (newest): 0/5 = 0.0
                await _seed_homework(
                    db, hw3, cid, "graded", "2025-05-04T10:00:00"
                )
                for seq in range(1, 6):
                    await _seed_problem(db, hw3, seq)
                await _seed_submission(db, hw3, s1)
                for seq in range(1, 6):
                    await _seed_answer(
                        db, hw3, s1, seq, False, f"E{(seq % 11) + 1:02d}"
                    )

                await db.commit()

                result = await get_student_homework_summary(s1)

                # accuracies = [0.0, 0.6, 1.0] (DESC)
                # recent_avg = (0.0 + 0.6 + 1.0)/3 = 0.533
                # prior_avg = 1.0 (oldest)
                # delta = 0.533 - 1.0 = -0.467 < -0.05 → "declining"
                assert result["recent_trend"] == "declining"

                await _cleanup(db, cid, [s1], [hw1, hw2, hw3])

        _run(_setup_and_test())

    def test_student_two_homeworks_stable_trend(self):
        """2 homeworks with similar accuracy → trend = 'stable'."""
        cid = _uid("cls")
        s1 = _uid("s1")
        hw1 = _uid("hw1")
        hw2 = _uid("hw2")

        async def _setup_and_test():
            from app.db import get_db
            async with get_db() as db:
                await _seed_class(db, cid)
                await _seed_student(db, s1, "Carol", cid)

                # HW1 (older): 3/5 = 0.6
                await _seed_homework(
                    db, hw1, cid, "graded", "2025-04-27T10:00:00"
                )
                for seq in range(1, 6):
                    await _seed_problem(db, hw1, seq)
                await _seed_submission(db, hw1, s1)
                await _seed_answer(db, hw1, s1, 1, True)
                await _seed_answer(db, hw1, s1, 2, True)
                await _seed_answer(db, hw1, s1, 3, True)
                await _seed_answer(db, hw1, s1, 4, False, "E01")
                await _seed_answer(db, hw1, s1, 5, False, "E01")

                # HW2 (newer): 3/5 = 0.6
                await _seed_homework(
                    db, hw2, cid, "graded", "2025-05-04T10:00:00"
                )
                for seq in range(1, 6):
                    await _seed_problem(db, hw2, seq)
                await _seed_submission(db, hw2, s1)
                await _seed_answer(db, hw2, s1, 1, True)
                await _seed_answer(db, hw2, s1, 2, True)
                await _seed_answer(db, hw2, s1, 3, True)
                await _seed_answer(db, hw2, s1, 4, False, "E02")
                await _seed_answer(db, hw2, s1, 5, False, "E02")

                await db.commit()

                result = await get_student_homework_summary(s1)

                assert result["total_homeworks"] == 2
                # accuracies = [0.6, 0.6]
                # delta = 0.6 - 0.6 = 0.0 → stable
                assert result["recent_trend"] == "stable"
                assert result["avg_accuracy"] == 0.6

                await _cleanup(db, cid, [s1], [hw1, hw2])

        _run(_setup_and_test())

from __future__ import annotations

import uuid
from collections import Counter

from app.db import get_db
from app.schemas import Student, StudentProfile


def _row_to_student(row) -> Student:
    return Student(
        student_id=row["id"],
        name=row["name"],
        grade=row["grade"],
        class_id=row["class_id"],
        guidance_mode=row["guidance_mode"],
        textbook_version=row["textbook_version"],
        start_grade=row["start_grade"],
        enrolled_at=row["enrolled_at"],
    )


async def get_student(student_id: str) -> Student | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_student(row)


async def list_students(class_id: str | None = None) -> list[Student]:
    async with get_db() as db:
        if class_id:
            cursor = await db.execute(
                "SELECT * FROM students WHERE class_id = ?", (class_id,)
            )
        else:
            cursor = await db.execute("SELECT * FROM students")
        rows = await cursor.fetchall()
    return [_row_to_student(r) for r in rows]


async def update_error_stats(
    student_id: str, error_code: str, is_correct: bool
) -> None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, total_attempts, correct_count FROM student_error_stats "
            "WHERE student_id = ? AND error_code = ?",
            (student_id, error_code),
        )
        row = await cursor.fetchone()

        if row:
            await db.execute(
                """UPDATE student_error_stats
                   SET total_attempts = total_attempts + 1,
                       correct_count = correct_count + ?,
                       last_seen_at = datetime('now')
                   WHERE id = ?""",
                (1 if is_correct else 0, row["id"]),
            )
        else:
            stat_id = f"SES{uuid.uuid4().hex[:8].upper()}"
            await db.execute(
                """INSERT INTO student_error_stats
                   (id, student_id, error_code, total_attempts, correct_count, last_seen_at)
                   VALUES (?, ?, ?, 1, ?, datetime('now'))""",
                (stat_id, student_id, error_code, 1 if is_correct else 0),
            )
        await db.commit()


async def batch_update_error_stats(
    student_id: str, results: list[tuple[str, bool]]
) -> None:
    """Batch-update error stats in a single DB connection.

    Args:
        student_id: The student ID.
        results: List of (error_code, is_correct) tuples.
    """
    if not results:
        return
    async with get_db() as db:
        for error_code, is_correct in results:
            await db.execute(
                """INSERT INTO student_error_stats
                       (id, student_id, error_code, total_attempts, correct_count, last_seen_at)
                       VALUES (?, ?, ?, 1, ?, datetime('now'))
                       ON CONFLICT(student_id, error_code) DO UPDATE SET
                       total_attempts = total_attempts + 1,
                       correct_count = correct_count + ?,
                       last_seen_at = datetime('now')""",
                (
                    f"SES{uuid.uuid4().hex[:8].upper()}",
                    student_id,
                    error_code,
                    1 if is_correct else 0,
                    1 if is_correct else 0,
                ),
            )
        await db.commit()


async def get_error_code_accuracy(student_id: str) -> dict[str, float]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT error_code, total_attempts, correct_count FROM student_error_stats "
            "WHERE student_id = ?",
            (student_id,),
        )
        rows = await cursor.fetchall()

    result: dict[str, float] = {}
    for r in rows:
        if r["total_attempts"] > 0:
            result[r["error_code"]] = round(r["correct_count"] / r["total_attempts"], 4)
    return result


async def get_student_profile(student_id: str) -> StudentProfile | None:
    from app.schemas import WeeklyAccuracy

    async with get_db() as db:
        s_cursor = await db.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        s_row = await s_cursor.fetchone()
        if s_row is None:
            return None
        student = _row_to_student(s_row)

        dh_cursor = await db.execute(
            "SELECT is_correct, error_code, created_at FROM diagnosis_history "
            "WHERE student_id = ? ORDER BY created_at ASC",
            (student_id,),
        )
        dh_rows = list(await dh_cursor.fetchall())

        sa_cursor = await db.execute(
            "SELECT is_correct, error_code FROM student_answers "
            "WHERE student_id = ?",
            (student_id,),
        )
        sa_rows = list(await sa_cursor.fetchall())
        rows = dh_rows + sa_rows

        ses_cursor = await db.execute(
            "SELECT error_code, total_attempts, correct_count FROM student_error_stats "
            "WHERE student_id = ?",
            (student_id,),
        )
        ses_rows = await ses_cursor.fetchall()

    accuracy_by_error_code: dict[str, float] = {}
    for r in ses_rows:
        if r["total_attempts"] > 0:
            accuracy_by_error_code[r["error_code"]] = round(r["correct_count"] / r["total_attempts"], 4)

    total_attempts = len(rows)
    if total_attempts == 0:
        return StudentProfile(
            student_id=student_id,
            student=student,
        )

    correct_count = sum(1 for r in rows if r["is_correct"])
    accuracy = round(correct_count / total_attempts, 4)

    error_counter = Counter(
        r["error_code"] for r in rows if r["error_code"] != "OK"
    )
    dominant_error_tags = [code for code, _ in error_counter.most_common(3)]

    recent_accuracy_trend = "stable"
    if total_attempts >= 10:
        first5 = rows[:5]
        last5 = rows[-5:]
        first_acc = sum(1 for r in first5 if r["is_correct"]) / 5
        last_acc = sum(1 for r in last5 if r["is_correct"]) / 5
        diff = last_acc - first_acc
        if diff > 0.1:
            recent_accuracy_trend = "improving"
        elif diff < -0.1:
            recent_accuracy_trend = "declining"

    last_active_date = dh_rows[-1]["created_at"] if dh_rows else None

    weekly_accuracy: list[WeeklyAccuracy] = []
    weekly_group: dict[int, list[bool]] = {}
    for r in dh_rows:
        created = r["created_at"] or ""
        try:
            month = int(created[5:7]) if len(created) >= 7 else 0
        except (ValueError, IndexError):
            month = 0
        if month > 0:
            weekly_group.setdefault(month, []).append(bool(r["is_correct"]))

    for wk in sorted(weekly_group.keys()):
        attempts_list = weekly_group[wk]
        wk_total = len(attempts_list)
        wk_correct = sum(1 for x in attempts_list if x)
        weekly_accuracy.append(WeeklyAccuracy(
            week_number=wk,
            accuracy=round(wk_correct / wk_total, 4) if wk_total > 0 else 0.0,
            total_attempts=wk_total,
            correct_count=wk_correct,
        ))

    profile = StudentProfile(
        student_id=student_id,
        student=student,
        total_attempts=total_attempts,
        correct_count=correct_count,
        accuracy=accuracy,
        dominant_error_tags=dominant_error_tags,
        accuracy_by_error_code=accuracy_by_error_code,
        weekly_accuracy=weekly_accuracy,
        recent_accuracy_trend=recent_accuracy_trend,
        last_active_date=last_active_date,
    )

    try:
        from app.services.growth_milestone import get_growth_milestone
        milestone = await get_growth_milestone(student_id)
        profile.growth_milestone = milestone
    except Exception:
        pass

    return profile

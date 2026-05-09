from __future__ import annotations

import json
from collections import Counter

from app.db import get_db
from app.schemas import Class, ClassSummary


def _row_to_class(row) -> Class:
    student_ids = json.loads(row["student_ids"]) if row["student_ids"] else []
    return Class(
        id=row["id"],
        name=row["name"],
        grade=row["grade"],
        academic_year=row["academic_year"],
        semester=row["semester"],
        student_ids=student_ids,
    )


async def get_class(class_id: str) -> Class | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_class(row)


async def get_class_summary(class_id: str) -> ClassSummary | None:
    async with get_db() as db:
        cls_cursor = await db.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        cls_row = await cls_cursor.fetchone()
        if cls_row is None:
            return None

        student_ids = json.loads(cls_row["student_ids"]) if cls_row["student_ids"] else []
        class_name = cls_row["name"]

        diag_cursor = await db.execute(
            "SELECT dh.student_id, dh.is_correct, dh.error_code FROM diagnosis_history dh "
            "WHERE dh.student_id IN (SELECT id FROM students WHERE class_id = ?)",
            (class_id,),
        )
        rows = await diag_cursor.fetchall()

        sa_cursor = await db.execute(
            "SELECT sa.student_id, sa.is_correct, sa.error_code FROM student_answers sa "
            "WHERE sa.student_id IN (SELECT id FROM students WHERE class_id = ?)",
            (class_id,),
        )
        sa_rows = await sa_cursor.fetchall()
        rows = list(rows) + list(sa_rows)

    total_students = len(student_ids)
    total_attempts = len(rows)

    if total_attempts == 0:
        return ClassSummary(
            class_id=class_id,
            class_name=class_name,
            total_students=total_students,
            teacher_brief=f"{class_name}共{total_students}名学生，暂无诊断记录。",
        )

    correct_count = sum(1 for r in rows if r["is_correct"])
    class_accuracy = round(correct_count / total_attempts, 4)

    error_counter = Counter(r["error_code"] for r in rows if r["error_code"] != "OK")
    top_error_tags = [
        {"code": code, "count": count}
        for code, count in error_counter.most_common(5)
    ]

    student_stats: dict[str, int | float] = {}
    for r in rows:
        sid = r["student_id"]
        if sid not in student_stats:
            student_stats[sid] = {"total": 0, "correct": 0}
        student_stats[sid]["total"] += 1
        if r["is_correct"]:
            student_stats[sid]["correct"] += 1

    students_needing_attention = [
        sid
        for sid, stats in student_stats.items()
        if stats["correct"] / stats["total"] < 0.6
    ]

    top_err_str = "、".join(
        f"{t['code']}({t['count']}次)" for t in top_error_tags[:3]
    )
    teacher_brief = (
        f"{class_name}共{total_students}名学生，累计{total_attempts}次作答，"
        f"全班正确率{class_accuracy:.0%}。"
        f"高频错因：{top_err_str or '无'}。"
        f"需关注学生{len(students_needing_attention)}人。"
    )

    return ClassSummary(
        class_id=class_id,
        class_name=class_name,
        total_students=total_students,
        total_attempts=total_attempts,
        class_accuracy=class_accuracy,
        top_error_tags=top_error_tags,
        students_needing_attention=students_needing_attention,
        teacher_brief=teacher_brief,
    )

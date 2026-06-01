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

        cursor = await db.execute("SELECT id FROM students WHERE class_id = ?", (class_id,))
        db_student_ids = [r["id"] for r in await cursor.fetchall()]

    total_students = len(student_ids)

    if not db_student_ids:
        return ClassSummary(
            class_id=class_id,
            class_name=class_name,
            total_students=total_students,
            teacher_brief=f"{class_name}共{total_students}名学生，暂无诊断记录。",
        )

    sid_tuple = tuple(db_student_ids)
    ph = ",".join("?" for _ in sid_tuple)

    async with get_db() as db:
        stats_cursor = await db.execute(
            f"""SELECT
                    SUM(total_attempts) as total,
                    SUM(correct_count) as correct,
                    GROUP_CONCAT(error_code || ':' || total_attempts || ':' || correct_count) as error_breakdown
                FROM student_error_stats
                WHERE student_id IN ({ph})""",
            sid_tuple,
        )
        agg = await stats_cursor.fetchone()

        per_student_cursor = await db.execute(
            f"""SELECT student_id,
                       SUM(total_attempts) as total,
                       SUM(correct_count) as correct
                FROM student_error_stats
                WHERE student_id IN ({ph})
                GROUP BY student_id""",
            sid_tuple,
        )
        per_student = {r["student_id"]: dict(r) for r in await per_student_cursor.fetchall()}

    total_attempts = agg["total"] or 0
    correct_count = agg["correct"] or 0

    if total_attempts == 0:
        return ClassSummary(
            class_id=class_id,
            class_name=class_name,
            total_students=total_students,
            teacher_brief=f"{class_name}共{total_students}名学生，暂无诊断记录。",
        )

    class_accuracy = round(correct_count / total_attempts, 4)

    error_counter: Counter = Counter()
    if agg["error_breakdown"]:
        for part in agg["error_breakdown"].split(","):
            pieces = part.split(":")
            if len(pieces) == 3:
                ec, att, cor = pieces[0], int(pieces[1]), int(pieces[2])
                err_count = att - cor
                if ec and ec != "OK" and err_count > 0:
                    error_counter[ec] += err_count

    top_error_tags = [
        {"code": code, "count": count}
        for code, count in error_counter.most_common(5)
    ]

    students_needing_attention = [
        sid
        for sid, stats in per_student.items()
        if stats["total"] > 0 and stats["correct"] / stats["total"] < 0.6
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

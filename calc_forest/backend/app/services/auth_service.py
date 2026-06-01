from __future__ import annotations

import json

from app.db import get_db
from app.schemas import Class, Teacher


async def authenticate_teacher(
    teacher_id: str | None = None,
    phone: str | None = None,
) -> Teacher | None:
    async with get_db() as db:
        if teacher_id:
            cur = await db.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,))
        elif phone:
            cur = await db.execute("SELECT * FROM teachers WHERE phone = ?", (phone,))
        else:
            cur = await db.execute("SELECT * FROM teachers LIMIT 1")

        row = await cur.fetchone()
        if row is None:
            return None

        return Teacher(
            id=row["id"],
            name=row["name"],
            phone=row["phone"],
            avatar=row["avatar"],
            class_ids=json.loads(row["class_ids"]),
            created_at=row["created_at"],
        )


async def get_teacher_classes(teacher: Teacher) -> list[Class]:
    class_ids = teacher.class_ids
    if not class_ids:
        return []

    async with get_db() as db:
        ph = ",".join(["?"] * len(class_ids))
        cur = await db.execute(f"SELECT * FROM classes WHERE id IN ({ph})", class_ids)
        rows = await cur.fetchall()
        return [
            Class(
                id=c["id"], name=c["name"], grade=c["grade"],
                academic_year=c["academic_year"], semester=c["semester"],
                student_ids=json.loads(c["student_ids"]),
            )
            for c in rows
        ]


async def get_teacher(teacher_id: str) -> Teacher | None:
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,))
        row = await cur.fetchone()
        if row is None:
            return None
        return Teacher(
            id=row["id"], name=row["name"], phone=row["phone"],
            avatar=row["avatar"], class_ids=json.loads(row["class_ids"]),
            created_at=row["created_at"],
        )

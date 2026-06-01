"""Student authentication service — simple ID-based login for demo."""
from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass, field

from app.db import get_db

_SESSION_TTL = 3600 * 2  # 2 小时过期
_MAX_SESSIONS = 1000  # 最大会话数


@dataclass
class StudentSession:
    student_id: str
    name: str
    class_id: str
    grade: int
    token: str
    created_at: float = field(default_factory=time.time)


_sessions: dict[str, StudentSession] = {}


def _cleanup_expired() -> None:
    """清理过期会话，防止内存泄漏"""
    now = time.time()
    expired = [t for t, s in _sessions.items() if now - s.created_at > _SESSION_TTL]
    for t in expired:
        del _sessions[t]
    # 如果超过上限，删除最旧的会话
    if len(_sessions) > _MAX_SESSIONS:
        sorted_tokens = sorted(_sessions.keys(), key=lambda t: _sessions[t].created_at)
        for t in sorted_tokens[:len(_sessions) - _MAX_SESSIONS]:
            del _sessions[t]


async def login_student(student_id: str, class_id: str | None = None) -> StudentSession | None:
    _cleanup_expired()  # 每次登录时清理过期会话
    async with get_db() as db:
        if class_id:
            cur = await db.execute(
                "SELECT id, name, grade, class_id FROM students WHERE id = ? AND class_id = ?",
                (student_id, class_id),
            )
        else:
            cur = await db.execute(
                "SELECT id, name, grade, class_id FROM students WHERE id = ?",
                (student_id,),
            )
        row = await cur.fetchone()
        if row is None:
            return None

        token = f"student-{student_id}-{secrets.token_hex(8)}"
        session = StudentSession(
            student_id=row["id"],
            name=row["name"],
            class_id=row["class_id"],
            grade=row["grade"],
            token=token,
        )
        _sessions[token] = session
        return session


def get_session_by_token(token: str) -> StudentSession | None:
    return _sessions.get(token)


async def get_class_students(class_id: str) -> list[dict]:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT id, name, grade, class_id, student_number FROM students WHERE class_id = ? ORDER BY name",
            (class_id,),
        )
        rows = await cur.fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "grade": r["grade"],
                "class_id": r["class_id"],
                "student_number": r["student_number"],
            }
            for r in rows
        ]

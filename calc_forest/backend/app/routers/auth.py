from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException

from app.schemas import (
    TeacherLoginRequest,
    TeacherLoginResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TeacherLoginResponse)
async def teacher_login(request: TeacherLoginRequest):
    from app.services.auth_service import authenticate_teacher, get_teacher_classes
    from app.services.utils import verify_password

    teacher = await authenticate_teacher(
        teacher_id=request.teacher_id,
        phone=request.phone,
    )
    if teacher is None:
        raise HTTPException(status_code=401, detail="教师不存在")

    from app.db import get_db
    async with get_db() as db:
        if request.teacher_id:
            cur = await db.execute("SELECT password_hash FROM teachers WHERE id = ?", (request.teacher_id,))
        elif request.phone:
            cur = await db.execute("SELECT password_hash FROM teachers WHERE phone = ?", (request.phone,))
        else:
            cur = await db.execute("SELECT password_hash FROM teachers LIMIT 1")
        row = await cur.fetchone()

    if not row or not verify_password(request.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="密码错误")

    classes = await get_teacher_classes(teacher)

    token = f"dev-token-{secrets.token_hex(8)}"
    return TeacherLoginResponse(teacher=teacher, token=token, classes=classes)


@router.get("/me")
async def get_current_teacher(teacher_id: str = "T001"):
    from app.services.auth_service import get_teacher

    teacher = await get_teacher(teacher_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="教师不存在")
    return teacher

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.student_auth_service import login_student, get_session_by_token, get_class_students

router = APIRouter(prefix="/api/student-auth", tags=["student-auth"])


class StudentLoginRequest(BaseModel):
    student_id: str
    class_id: str | None = None


@router.post("/login")
async def student_login(req: StudentLoginRequest):
    session = await login_student(req.student_id, req.class_id)
    if session is None:
        raise HTTPException(404, "Student not found")
    return {
        "student": {
            "id": session.student_id,
            "name": session.name,
            "grade": session.grade,
            "class_id": session.class_id,
        },
        "token": session.token,
    }


@router.get("/me")
async def student_me(token: str):
    session = get_session_by_token(token)
    if session is None:
        raise HTTPException(401, "令牌无效或已过期")
    return {
        "student": {
            "id": session.student_id,
            "name": session.name,
            "grade": session.grade,
            "class_id": session.class_id,
        },
        "token": session.token,
    }


@router.get("/class-list/{class_id}")
async def class_student_list(class_id: str):
    students = await get_class_students(class_id)
    return {"class_id": class_id, "students": students}

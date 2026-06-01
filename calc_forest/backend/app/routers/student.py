from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import Student, StudentProfile
from app.services.curriculum_service import get_student_trajectory, update_student_profile
from app.services.cycle_service import get_student_growth
from app.services.student_service import get_student as svc_get_student
from app.services.student_service import get_student_profile

router = APIRouter(tags=["student"])


@router.get("/api/students/{student_id}", response_model=Student)
async def get_student_endpoint(student_id: str):
    student = await svc_get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


@router.get("/api/students/{student_id}/profile", response_model=StudentProfile)
async def get_student_profile_endpoint(student_id: str):
    profile = await get_student_profile(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return profile


@router.patch("/api/students/{student_id}/profile")
async def student_profile_update_endpoint(
    student_id: str,
    personality_tags: list[str] | None = None,
    learning_style: str | None = None,
    notes: str | None = None,
    guidance_mode: str | None = None,
):
    ok = await update_student_profile(student_id, personality_tags, learning_style, notes, guidance_mode)
    if ok is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if not ok:
        raise HTTPException(status_code=400, detail="没有可更新的字段")
    return {"ok": True}


@router.get("/api/students/{student_id}/growth")
async def get_student_growth_endpoint(student_id: str):
    from app.schemas import StudentCycleProgress

    progress = await get_student_growth(student_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="学生或当前学习周期不存在")
    return progress


@router.post("/api/students/{student_id}/growth/record")
async def record_growth(student_id: str):
    from app.services.growth_milestone import record_practice_day
    result = await record_practice_day(student_id)
    return result


@router.get("/api/students/{student_id}/trajectory")
async def student_trajectory_endpoint(student_id: str):
    student = await svc_get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return await get_student_trajectory(student_id)


@router.get("/api/students/{student_id}/mastery")
async def get_student_mastery_endpoint(student_id: str):
    from app.services import mastery_service

    result = await mastery_service.get_student_mastery(student_id)
    return result


@router.get("/api/students/{student_id}/ai-analysis")
async def ai_student_analysis(student_id: str, homework_id: str | None = None):
    from app.services.ai_profile_service import ai_analyze_student
    return await ai_analyze_student(student_id, homework_id)


@router.get("/api/students/{student_id}/homework-summary")
async def student_homework_summary_endpoint(student_id: str, limit: int = 10):
    from app.exceptions import NotFoundException
    from app.services.homework_analytics import get_student_homework_summary

    try:
        return await get_student_homework_summary(student_id, limit)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.detail)


@router.get("/api/guidance/context/{student_id}")
async def get_guidance_context(student_id: str):
    from app.services.student_service import build_guidance_context

    context = await build_guidance_context(student_id)
    return {"student_id": student_id, "context": context, "length": len(context)}

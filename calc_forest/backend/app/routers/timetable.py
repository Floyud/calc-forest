from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.timetable_service import (
    auto_assign_homework,
    get_full_weekly_schedule,
    get_timetable,
    get_today_math_classes,
    get_weekly_math_schedule,
    manual_assign_homework,
    update_timetable,
)

router = APIRouter(prefix="/api/timetable", tags=["timetable"])


class TimetableEntry(BaseModel):
    day_of_week: int
    period_number: int = 1
    subject: str = "math"
    teacher: str = ""
    is_active: bool = True


class TimetableUpdateRequest(BaseModel):
    entries: list[TimetableEntry]


class ManualAssignRequest(BaseModel):
    grade: int = 6
    problem_count: int = 5
    error_codes: list[str] | None = None
    difficulty: str = "B"
    unit_title: str = ""


@router.get("/{class_id}")
async def get_timetable_endpoint(class_id: str):
    return await get_timetable(class_id)


@router.put("/{class_id}")
async def update_timetable_endpoint(class_id: str, req: TimetableUpdateRequest):
    entries = [e.model_dump() for e in req.entries]
    count = await update_timetable(class_id, entries)
    return {"updated": count}


@router.get("/{class_id}/week-view")
async def week_view_endpoint(class_id: str):
    """Legacy math-only week view (backward compatible)."""
    return await get_weekly_math_schedule(class_id)


@router.get("/{class_id}/full-week-view")
async def full_week_view_endpoint(class_id: str):
    """Full week view with all subjects, period times, break info."""
    return await get_full_weekly_schedule(class_id)


@router.get("/{class_id}/today")
async def today_endpoint(class_id: str):
    classes = await get_today_math_classes(class_id)
    return {"day_of_week": __import__("datetime").date.today().isoweekday(), "math_classes": classes}


@router.post("/{class_id}/auto-assign")
async def auto_assign_endpoint(class_id: str):
    result = await auto_assign_homework(class_id)
    if result is None:
        raise HTTPException(500, "自动布置失败")
    return result


@router.post("/{class_id}/assign")
async def manual_assign_endpoint(class_id: str, req: ManualAssignRequest):
    result = await manual_assign_homework(
        class_id,
        grade=req.grade,
        problem_count=req.problem_count,
        error_codes=req.error_codes,
        difficulty=req.difficulty,
        unit_title=req.unit_title,
    )
    return result

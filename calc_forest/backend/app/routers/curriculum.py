from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas import AcademicCycle
from app.services.curriculum_service import (
    get_calendar,
    get_schedule,
    get_units,
    update_schedule,
)
from app.services.cycle_service import get_current_cycle

router = APIRouter(tags=["curriculum"])


@router.get("/api/curriculum/units")
async def curriculum_units_endpoint(grade: int = 6, semester: int = 2):
    data = await get_units(grade, semester)
    return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=3600"})


@router.get("/api/curriculum/schedule/{class_id}")
async def curriculum_schedule_endpoint(class_id: str):
    data = await get_schedule(class_id)
    return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=300"})


@router.put("/api/curriculum/schedule/{class_id}")
async def curriculum_schedule_update_endpoint(class_id: str, updates: list[dict]):
    count = await update_schedule(class_id, updates)
    return {"updated": count}


@router.get("/api/curriculum/calendar")
async def curriculum_calendar_endpoint(academic_year: str = "2025-2026", semester: int = 2):
    data = await get_calendar(academic_year, semester)
    return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=3600"})


@router.get("/api/cycles/current", response_model=AcademicCycle)
async def get_current_cycle_endpoint(grade: int = 6):
    cycle = await get_current_cycle(grade)
    if cycle is None:
        raise HTTPException(status_code=404, detail="该年级当前没有学习周期")
    return cycle


@router.get("/api/curriculum/week-calc")
async def week_calc_endpoint(
    week: int = 1, grade: int = 6, semester: int = 1,
):
    from app.services.knowledge_rag_service import get_week_calc_type

    result = await get_week_calc_type(week, grade, semester)
    if result is None:
        raise HTTPException(status_code=404, detail="本周没有对应的映射数据")
    return result

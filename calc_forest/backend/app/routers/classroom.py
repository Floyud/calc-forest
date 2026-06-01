from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import Class, ClassForestResponse, ClassSummary
from app.services.class_service import get_class as svc_get_class
from app.services.class_service import get_class_summary
from app.services.summaries import get_class_error_summary

router = APIRouter(prefix="/api/classes", tags=["classroom"])


@router.get("/{class_id}", response_model=Class)
async def get_class_endpoint(class_id: str):
    cls = await svc_get_class(class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return cls


@router.get("/{class_id}/summary", response_model=ClassSummary)
async def get_class_summary_endpoint(class_id: str):
    from app.services.student_service import get_class_weak_points

    enriched = await get_class_error_summary(class_id)
    if enriched is None:
        raise HTTPException(status_code=404, detail="班级不存在")

    tiers = enriched.get("student_tiers", {})
    attention_ids = tiers.get("需关注", [])

    class_weak_points = await get_class_weak_points(class_id)

    return ClassSummary(
        class_id=class_id,
        class_name=enriched["class_name"],
        total_students=enriched["total_students"],
        total_attempts=enriched.get("total_attempts", 0),
        class_accuracy=enriched.get("class_accuracy", 0.0),
        top_error_tags=enriched.get("error_distribution", []),
        students_needing_attention=attention_ids,
        class_weak_points=class_weak_points,
        teacher_brief=f"{enriched['class_name']}共{enriched['total_students']}名学生，"
                      f"全班正确率{enriched.get('class_accuracy', 0.0):.0%}。"
                      f"优秀{len(tiers.get('优秀', []))}人，"
                      f"良好{len(tiers.get('良好', []))}人，"
                      f"需关注{len(attention_ids)}人。",
    )


@router.get("/{class_id}/forest", response_model=ClassForestResponse)
async def get_class_forest_endpoint(class_id: str):
    from app.services.forest_service import get_class_forest
    forest = await get_class_forest(class_id)
    if forest is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return forest


@router.get("/{class_id}/homework-pdfs")
async def class_homework_pdfs_endpoint(class_id: str):
    from app.services.pdf_service import get_class_homework_pdfs
    return await get_class_homework_pdfs(class_id)


@router.get("/{class_id}/ai-portrait")
async def ai_class_portrait(class_id: str):
    from app.services.ai_profile_service import ai_analyze_class
    return await ai_analyze_class(class_id)

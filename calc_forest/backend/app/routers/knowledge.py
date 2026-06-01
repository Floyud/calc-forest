from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(tags=["knowledge"])


@router.get("/api/knowledge/search")
async def knowledge_search_endpoint(q: str = "", limit: int = 5):
    from app.services.knowledge_service import search_knowledge

    if not q:
        return {"results": []}
    results = await search_knowledge(q, limit)
    return JSONResponse(content={"results": results}, headers={"Cache-Control": "public, max-age=600"})


@router.get("/api/knowledge/points")
async def knowledge_points_endpoint(
    error_code: str | None = None, unit_number: int | None = None,
):
    from app.services.knowledge_rag_service import get_knowledge_points_by_error_code
    from app.services.knowledge_service import list_knowledge_points

    if error_code:
        data = await get_knowledge_points_by_error_code(error_code)
        return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=3600"})

    data = await list_knowledge_points(unit_number)
    return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=600"})


@router.get("/api/knowledge/graph")
async def knowledge_graph_endpoint(kp_id: str = "KP_E01_01", depth: int = 2):
    from app.services.knowledge_rag_service import (
        get_knowledge_point_by_id,
        get_related_concepts,
    )

    kp = await get_knowledge_point_by_id(kp_id)
    if kp is None:
        raise HTTPException(status_code=404, detail="知识点不存在")
    related = await get_related_concepts(kp_id, max_depth=depth)
    return JSONResponse(content={"root": kp, "related": related}, headers={"Cache-Control": "public, max-age=3600"})


@router.get("/api/exercise-types")
async def list_exercise_types_endpoint(category: str | None = None):
    from app.services.knowledge_service import list_exercise_types
    categories = await list_exercise_types(category)
    return JSONResponse(content={"categories": categories}, headers={"Cache-Control": "public, max-age=3600"})


@router.get("/api/exercise-types/{type_id}")
async def get_exercise_type_endpoint(type_id: str):
    from app.services.knowledge_service import get_exercise_type

    result = await get_exercise_type(type_id)
    if result is None:
        raise HTTPException(status_code=404, detail="题型不存在")
    return result

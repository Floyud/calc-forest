from __future__ import annotations

import json
import time
import uuid
from typing import Any

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.pipeline import NodeResult, NodeStatus
from app.schemas import (
    DifySessionDraftRequest,
    DifySessionDraftResponse,
    DiagnosisRequest,
    DiagnosisResponse,
    PracticeRecommendationRequest,
    PracticeRecommendationResponse,
)
from app.services.diagnosis import diagnose_answer
from app.services.practice import recommend_practice
from app.services.session_draft import build_session_draft

router = APIRouter(tags=["diagnosis"])


@router.post("/api/diagnose", response_model=DiagnosisResponse)
def diagnose(request: DiagnosisRequest) -> DiagnosisResponse:
    return diagnose_answer(request)


@router.post("/api/dify/chat")
async def dify_chat_proxy(body: dict[str, Any]) -> dict[str, Any]:
    import os

    from app.services.llm_client import call_deepseek

    base_url = os.getenv("DIFY_BASE_URL", "http://127.0.0.1:18080")
    api_key = os.getenv(
        "DIFY_WORKFLOW_GUIDANCE_KEY",
        os.getenv("LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY", ""),
    )

    query = body.get("query", "")
    student_context = body.get("inputs", {}).get("student_context", "")
    history = body.get("history", [])

    # Track 1: Dify (local or cloud) — only if key is configured
    if api_key:
        payload = {
            "inputs": body.get("inputs", {}),
            "query": query,
            "response_mode": "blocking",
            "user": body.get("user", "student-unknown"),
        }
        if body.get("conversation_id"):
            payload["conversation_id"] = body["conversation_id"]

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    f"{base_url}/v1/chat-messages",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                return resp.json()
        except Exception:
            pass  # fall through to LLM

    # Track 2: LLM direct (MiMo / GLM / DeepSeek — uses llm_client configured provider)
    system_prompt = (
        "你是「我的计算森林」的树精灵朋友。用温暖简短的语言和学生聊天。"
        "当学生遇到计算题时，你一步步引导他们思考，永远不直接给答案。"
        "用生活化的比喻帮助理解算理。"
        "每次只聚焦一个关键步骤，不要一次灌输太多。"
        "先肯定学生的努力和正确部分，再温和指出问题。"
    )
    if student_context:
        system_prompt += f"\n\n【学生情况】{student_context}"

    messages = [{"role": "system", "content": system_prompt}]

    # Replay conversation history from frontend
    for entry in history:
        role = entry.get("role", "user")
        content = entry.get("content", "")
        if not content:
            continue
        messages.append({"role": "assistant" if role in ("bot", "assistant") else "user", "content": content})

    messages.append({"role": "user", "content": query})

    try:
        data = await call_deepseek(
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        answer = data["choices"][0]["message"]["content"].strip()
        conversation_id = body.get("conversation_id") or str(uuid.uuid4())
        return {"answer": answer, "conversation_id": conversation_id}
    except Exception:
        return {"answer": "树精灵暂时离线，请稍后再试 🌿", "conversation_id": ""}


@router.post("/api/practice/recommend", response_model=PracticeRecommendationResponse)
def practice_recommend(
    request: PracticeRecommendationRequest,
) -> PracticeRecommendationResponse:
    return recommend_practice(request.error_code, request.grade, request.guidance_mode)


@router.post("/api/dify/session-draft", response_model=DifySessionDraftResponse)
async def dify_session_draft(request: DifySessionDraftRequest) -> DifySessionDraftResponse:
    return await build_session_draft(request)


@router.post("/api/dify/full-pipeline", response_model=DifySessionDraftResponse)
async def full_pipeline_endpoint(request: DifySessionDraftRequest) -> DifySessionDraftResponse:
    from app.pipeline.session_draft_pipeline import create_full_pipeline
    from app.pipeline.response_assembler import assemble_response
    from app.schemas import AnswerRecord

    student_steps = []
    if request.student_steps_text:
        student_steps = [line.strip() for line in request.student_steps_text.splitlines() if line.strip()]

    record = AnswerRecord(
        student_id=request.student_id,
        grade=request.grade,
        problem=request.problem_text,
        correct_answer=request.correct_answer_text,
        student_answer=request.student_answer_text,
        student_steps=student_steps,
        source=request.source,
    )

    pipeline = create_full_pipeline()
    context = await pipeline.run({
        "record": record,
        "student_id": request.student_id,
        "grade": request.grade,
        "guidance_mode": request.guidance_mode,
        "class_id": None,
        "tree_species_id": request.tree_species_id,
        "problem": request.problem_text,
        "correct_answer": request.correct_answer_text,
        "student_answer": request.student_answer_text,
    })

    return assemble_response(context, request)


@router.post("/api/dify/pipeline-stream")
async def pipeline_stream_endpoint(request: DifySessionDraftRequest):
    from app.pipeline.session_draft_pipeline import create_full_pipeline
    from app.pipeline.response_assembler import assemble_response
    from app.schemas import AnswerRecord

    NODE_META = {
        "diagnosis": {"label": "错因诊断", "progress_msg": "正在分析学生作答..."},
        "teacher_summary": {"label": "AI 教师摘要", "progress_msg": "正在生成深度分析..."},
        "practice": {"label": "练习推荐", "progress_msg": "正在生成针对性练习..."},
        "growth_config": {"label": "成长配置", "progress_msg": "正在加载成长配置..."},
        "profile_update": {"label": "更新画像", "progress_msg": "正在更新学生画像..."},
        "growth_update": {"label": "更新成长", "progress_msg": "正在记录成长进度..."},
    }

    def _sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def event_generator():
        student_steps = []
        if request.student_steps_text:
            student_steps = [line.strip() for line in request.student_steps_text.splitlines() if line.strip()]

        record = AnswerRecord(
            student_id=request.student_id,
            grade=request.grade,
            problem=request.problem_text,
            correct_answer=request.correct_answer_text,
            student_answer=request.student_answer_text,
            student_steps=student_steps,
            source=request.source,
        )

        context = {
            "record": record,
            "student_id": request.student_id,
            "grade": request.grade,
            "guidance_mode": request.guidance_mode,
            "class_id": None,
            "tree_species_id": request.tree_species_id,
            "problem": request.problem_text,
            "correct_answer": request.correct_answer_text,
            "student_answer": request.student_answer_text,
        }

        pipeline = create_full_pipeline()

        yield _sse("start", {"message": "开始诊断流水线...", "total_nodes": len(pipeline._nodes)})

        ctx = dict(context)
        ctx.setdefault("_results", {})
        ctx.setdefault("_errors", [])

        for node in pipeline._nodes:
            meta = NODE_META.get(node.name, {"label": node.name, "progress_msg": f"正在执行 {node.name}..."})

            yield _sse("node_progress", {"node": node.name, "label": meta["label"], "message": meta["progress_msg"]})

            t0 = time.monotonic()
            try:
                if not await node.should_run(ctx):
                    elapsed = int((time.monotonic() - t0) * 1000)
                    ctx["_results"][node.name] = NodeResult(NodeStatus.SKIPPED)
                    yield _sse("node_complete", {"node": node.name, "status": "skipped", "duration_ms": elapsed})
                    continue
                result = await node.execute(ctx)
                elapsed = int((time.monotonic() - t0) * 1000)
                ctx["_results"][node.name] = result
                if result.output:
                    ctx.update(result.output)

                summary: dict = {"node": node.name, "status": "complete", "duration_ms": elapsed}

                if node.name == "diagnosis" and result.success:
                    diag = result.output.get("diagnosis")
                    if diag:
                        if hasattr(diag, "primary_error"):
                            summary["error_code"] = diag.primary_error.code.value
                            summary["error_label"] = diag.primary_error.label
                            summary["confidence"] = diag.primary_error.confidence
                            summary["is_correct"] = diag.is_correct
                        elif isinstance(diag, dict):
                            pe = diag.get("primary_error", {})
                            summary["error_code"] = pe.get("code", "")
                            summary["error_label"] = pe.get("label", "")
                            summary["confidence"] = pe.get("confidence", 0)
                            summary["is_correct"] = diag.get("is_correct", False)

                elif node.name == "practice" and result.success:
                    prac = result.output.get("practice")
                    if prac:
                        count = len(prac.items) if hasattr(prac, "items") else 0
                        summary["practice_count"] = count

                elif node.name == "growth_config" and result.success:
                    ts = result.output.get("tree_species")
                    if ts and hasattr(ts, "name"):
                        summary["tree_species"] = ts.name

                elif node.name == "profile_update" and result.success:
                    summary["history_id"] = result.output.get("history_id", "")

                elif node.name == "growth_update" and result.success:
                    summary["days_completed"] = result.output.get("days_completed", 0)
                    summary["current_stage"] = result.output.get("current_stage", "")

                yield _sse("node_complete", summary)

                if not result.success:
                    ctx["_errors"].append({"node": node.name, "error": result.error})
                    if pipeline.stop_on_fail:
                        yield _sse("error", {"node": node.name, "error": result.error})
                        break

            except Exception as exc:
                elapsed = int((time.monotonic() - t0) * 1000)
                ctx["_results"][node.name] = NodeResult(NodeStatus.FAILED, error=str(exc))
                ctx["_errors"].append({"node": node.name, "error": str(exc)})
                yield _sse("node_complete", {"node": node.name, "status": "failed", "error": str(exc), "duration_ms": elapsed})
                if pipeline.stop_on_fail:
                    yield _sse("error", {"node": node.name, "error": str(exc)})
                    break

        try:
            final_response = assemble_response(ctx, request)
            response_dict = final_response.model_dump()
            yield _sse("done", {"message": "诊断完成", "result": response_dict})
        except Exception as exc:
            yield _sse("error", {"message": f"组装响应失败: {exc}"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")

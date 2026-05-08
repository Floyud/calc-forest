from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_ENABLED = os.getenv("DIFY_ENABLED", "false").lower() in ("true", "1", "yes")

LOCAL_DIFY_BASE_URL = os.getenv("LOCAL_DIFY_BASE_URL", "http://127.0.0.1:18080/v1")
LOCAL_DIFY_ENABLED = os.getenv("LOCAL_DIFY_ENABLED", "false").lower() in ("true", "1", "yes")

DEFAULT_TIMEOUT = 60
MAX_CONCURRENT_REQUESTS = int(os.getenv("DIFY_MAX_CONCURRENCY", "5"))

# chatflow 类型标记 — student_guidance 用 /chat-messages，其余用 /workflows/run
CHATFLOW_KEYS: set[str] = {"student_guidance"}


class _DifyTrack:

    def __init__(self, *, base_url: str, enabled: bool) -> None:
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None

    def get_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        return self._semaphore

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=float(DEFAULT_TIMEOUT),
                    write=10.0,
                    pool=5.0,
                ),
                limits=httpx.Limits(
                    max_connections=MAX_CONCURRENT_REQUESTS + 2,
                    max_keepalive_connections=MAX_CONCURRENT_REQUESTS,
                    keepalive_expiry=120.0,
                ),
                http2=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


class DifyConfig:

    def __init__(self) -> None:
        self.local = _DifyTrack(base_url=LOCAL_DIFY_BASE_URL, enabled=LOCAL_DIFY_ENABLED)
        self.cloud = _DifyTrack(base_url=DIFY_BASE_URL, enabled=DIFY_ENABLED)

    async def close(self) -> None:
        await self.local.close()
        await self.cloud.close()


dify_config = DifyConfig()


WORKFLOWS: dict[str, dict[str, str]] = {
    "student_guidance": {
        "api_key": os.getenv("DIFY_WORKFLOW_GUIDANCE_KEY", ""),
        "prompt_system": (
            "你是小学数学学习助手，目标是帮助学生理解错误原因并学会修正。\n"
            "你不能羞辱、责备或给学生贴标签。\n"
            "你不能只给最终答案，应优先用问题引导学生发现关键关系。\n"
            "解释必须符合小学生年级水平，句子短，步骤清楚。\n"
            "输出必须严格遵守 JSON 格式。"
        ),
        "prompt_user_template": (
            "请给学生一段温和、清楚、可操作的反馈。\n\n"
            "题目：{problem}\n"
            "学生作答：{student_answer}\n"
            "诊断：{diagnosis}\n\n"
            "要求：\n"
            "1. 先肯定学生已经写出的可用步骤。\n"
            "2. 指出关键错误时要具体说明是哪个关系或步骤。\n"
            "3. 按\"想一想 -> 修正方法 -> 小结\"组织。\n"
            "4. 不要输出太长，每段 1 到 3 句。\n\n"
            "输出 JSON：\n"
            '{{"student_message": "", "key_takeaway": "", "next_step": ""}}'
        ),
    },
    "teacher_summary": {
        "api_key": os.getenv("DIFY_WORKFLOW_SUMMARY_KEY", ""),
        "prompt_system": (
            "你是一位教学分析助手，帮助教师快速了解学生错误模式。\n"
            "用客观语言描述证据，区分本次错误和长期能力判断，不要过度推断。\n"
            "输出必须严格遵守 JSON 格式。"
        ),
        "prompt_user_template": (
            "请生成教师可读的诊断摘要，帮助教师快速了解学生错误模式。\n\n"
            "诊断数据：{diagnosis}\n"
            "会话历史：{session_history}\n\n"
            "要求：\n"
            "1. 用客观语言描述证据。\n"
            "2. 区分本次错误和长期能力判断，不要过度推断。\n"
            "3. 给出下一步教学建议。\n\n"
            "输出 JSON：\n"
            '{{"teacher_summary": "", "observed_evidence": [], '
            '"recommended_intervention": "", "risk_note": ""}}'
        ),
    },
    "ai_grading": {
        "api_key": os.getenv("DIFY_WORKFLOW_GRADING_KEY", ""),
        "prompt_system": (
            "你是一位小学数学批改助手。\n"
            "根据规则引擎的批改结果，对学生的答案进行语义分析和补充评价。\n"
            "注意：规则引擎已经判断了计算正确性，你的任务是补充分析可能的原因和建议。\n"
            "输出必须严格遵守 JSON 格式。"
        ),
        "prompt_user_template": (
            "请根据以下批改结果，分析学生的错误模式。\n\n"
            "批改结果：{grading_results}\n"
            "学生信息：{student_info}\n\n"
            "要求：\n"
            "1. 归纳本份作业中反复出现的错误模式。\n"
            "2. 判断是概念性错误还是计算习惯问题。\n"
            "3. 给出针对性建议。\n\n"
            "输出 JSON：\n"
            '{{"pattern_summary": "", "error_type": "", '
            '"suggestion": "", "priority": "high|medium|low"}}'
        ),
    },
    "ai_profile": {
        "api_key": os.getenv("DIFY_WORKFLOW_PROFILE_KEY", ""),
        "prompt_system": (
            "你是一位学习分析助手，根据学生的历史做题数据生成学习画像。\n"
            "客观分析，不贴标签，关注可改进行动。\n"
            "输出必须严格遵守 JSON 格式。"
        ),
        "prompt_user_template": (
            "请根据学生的历史数据生成学习画像分析。\n\n"
            "学生数据：{student_data}\n"
            "错因统计：{error_stats}\n"
            "准确率趋势：{accuracy_trend}\n\n"
            "要求：\n"
            "1. 总结学生的计算能力特点。\n"
            "2. 识别最需要关注的 1-2 个错因。\n"
            "3. 给出分阶段改进建议。\n\n"
            "输出 JSON：\n"
            '{{"strengths": [], "weaknesses": [], '
            '"focus_areas": [], "suggested_actions": []}}'
        ),
    },
    "problem_generation": {
        "api_key": os.getenv("DIFY_WORKFLOW_PROBLEM_KEY", ""),
        "prompt_system": (
            "你是一位小学数学教师，擅长根据学生错因生成针对性练习题。\n"
            "所有题目必须是纯计算题（不含应用题），覆盖人教版对应年级的计算内容。\n"
            "返回严格 JSON 数组，不要加 markdown 代码块标记。"
        ),
        "prompt_user_template": (
            "请生成针对性练习题。\n\n"
            "错因类型：{error_codes}\n"
            "难度：{difficulty}\n"
            "题量：{count}道\n"
            "年级：{grade}年级\n\n"
            "每道题返回如下 JSON 格式：\n"
            '{{"problem": "题目表达式", '
            '"problem_plain": "纯文本题目", '
            '"correct_answer": "标准答案", '
            '"knowledge_point": "知识点", '
            '"target_error_code": "针对的错因代码", '
            '"difficulty": "{difficulty}"}}\n'
            "返回纯 JSON 数组，不要任何额外文字。"
        ),
    },
}

LOCAL_WORKFLOWS: dict[str, dict[str, str]] = {
    "student_guidance": {
        "api_key": os.getenv("LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY", ""),
    },
    "teacher_summary": {
        "api_key": os.getenv("LOCAL_DIFY_WORKFLOW_SUMMARY_KEY", ""),
    },
    "ai_grading": {
        "api_key": os.getenv("LOCAL_DIFY_WORKFLOW_GRADING_KEY", ""),
    },
    "ai_profile": {
        "api_key": os.getenv("LOCAL_DIFY_WORKFLOW_PROFILE_KEY", ""),
    },
    "problem_generation": {
        "api_key": os.getenv("LOCAL_DIFY_WORKFLOW_PROBLEM_KEY", ""),
    },
}


def _get_api_key(workflow_key: str, track: str) -> str:
    if track == "local":
        local_wf = LOCAL_WORKFLOWS.get(workflow_key)
        if local_wf:
            return local_wf.get("api_key", "") or DIFY_API_KEY
        return DIFY_API_KEY
    # cloud
    wf = WORKFLOWS.get(workflow_key)
    if wf:
        return wf.get("api_key", "") or DIFY_API_KEY
    return DIFY_API_KEY


async def call_dify_or_llm(
    workflow_key: str,
    inputs: dict[str, Any],
    *,
    user_id: str = "system",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    response_format: dict[str, str] | None = None,
) -> dict[str, Any]:
    """尝试 Dify（local → cloud），失败后回退到 DeepSeek。"""
    # Track 1: Local Dify
    if dify_config.local.enabled:
        api_key = _get_api_key(workflow_key, "local")
        if api_key:
            try:
                result = await _call_dify_endpoint(
                    workflow_key, inputs, user_id,
                    track=dify_config.local, api_key=api_key, track_label="local",
                )
                return result
            except Exception as exc:
                logger.warning(
                    "Local Dify %s 失败，尝试 Cloud: %s", workflow_key, exc,
                )

    # Track 2: Cloud Dify
    if dify_config.cloud.enabled:
        api_key = _get_api_key(workflow_key, "cloud")
        if api_key:
            try:
                result = await _call_dify_endpoint(
                    workflow_key, inputs, user_id,
                    track=dify_config.cloud, api_key=api_key, track_label="cloud",
                )
                return result
            except Exception as exc:
                logger.warning(
                    "Cloud Dify %s 失败，回退到 DeepSeek: %s", workflow_key, exc,
                )

    # Track 3: DeepSeek 直连回退
    return await _call_deepseek_fallback(
        workflow_key, inputs, temperature, max_tokens, response_format,
    )


async def _call_dify_endpoint(
    workflow_key: str,
    inputs: dict[str, Any],
    user_id: str,
    *,
    track: _DifyTrack,
    api_key: str,
    track_label: str,
) -> dict[str, Any]:
    if workflow_key not in WORKFLOWS:
        raise ValueError(f"未知 workflow 键: {workflow_key}")

    is_chatflow = workflow_key in CHATFLOW_KEYS
    endpoint = "/chat-messages" if is_chatflow else "/workflows/run"
    url = f"{track.base_url}{endpoint}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if is_chatflow:
        query = WORKFLOWS[workflow_key]["prompt_user_template"]
        for key, value in inputs.items():
            str_value = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
            query = query.replace("{" + key + "}", str_value)
        query = re.sub(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", "", query)
        payload: dict[str, Any] = {"inputs": {}, "query": query, "response_mode": "blocking", "user": user_id}
    else:
        payload = {"inputs": inputs, "response_mode": "blocking", "user": user_id}

    t0 = time.monotonic()
    async with track.get_semaphore():
        client = await track.get_client()
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            elapsed = time.monotonic() - t0
            data = resp.json()
            logger.info("[%s] Dify %s %s ok (%.1fs)", track_label, "chatflow" if is_chatflow else "workflow", workflow_key, elapsed)
            if is_chatflow:
                answer = data.get("answer", "").strip()
                answer = answer.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                try:
                    return json.loads(answer)
                except json.JSONDecodeError:
                    return {"raw_content": answer, "parse_error": True}
            return data.get("data", {}).get("outputs", {})
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            elapsed = time.monotonic() - t0
            raise RuntimeError(f"[{track_label}] Dify 连接失败 ({elapsed:.1fs}): {exc}") from exc
        except httpx.HTTPStatusError as exc:
            elapsed = time.monotonic() - t0
            raise RuntimeError(
                f"[{track_label}] Dify HTTP {exc.response.status_code} ({elapsed:.1fs}): {exc.response.text[:300]}"
            ) from exc


async def _call_deepseek_fallback(
    workflow_key: str,
    inputs: dict[str, Any],
    temperature: float,
    max_tokens: int,
    response_format: dict[str, str] | None,
) -> dict[str, Any]:
    from app.services.llm_client import call_deepseek

    wf = WORKFLOWS.get(workflow_key)
    if wf is None:
        raise ValueError(f"未知 workflow 键: {workflow_key}")

    system_prompt = wf["prompt_system"]
    user_template = wf["prompt_user_template"]

    # 把 inputs 字典中的值填入模板
    user_content = user_template
    for key, value in inputs.items():
        placeholder = "{" + key + "}"
        str_value = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        user_content = user_content.replace(placeholder, str_value)

    # 清理未替换的模板变量
    user_content = re.sub(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", "", user_content)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    fmt = response_format or {"type": "json_object"}

    raw = await call_deepseek(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=fmt,
    )

    content = raw["choices"][0]["message"]["content"].strip()
    content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("DeepSeek 回退返回非 JSON，尝试提取: %s", content[:200])
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = content.find(start_char)
            end = content.rfind(end_char) + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    continue
        return {"raw_content": content, "parse_error": True}


async def generate_student_feedback(
    *,
    problem: str,
    student_answer: str,
    diagnosis: str | dict,
    student_id: str = "system",
    grade: int = 6,
) -> dict[str, Any]:
    diag_str = json.dumps(diagnosis, ensure_ascii=False) if isinstance(diagnosis, dict) else diagnosis
    return await call_dify_or_llm(
        "student_guidance",
        {
            "problem": problem,
            "student_answer": student_answer,
            "diagnosis": diag_str,
            "grade": str(grade),
        },
        user_id=student_id,
    )


async def generate_teacher_summary(
    *,
    diagnosis: str | dict,
    session_history: str | dict,
    student_id: str = "system",
) -> dict[str, Any]:
    diag_str = json.dumps(diagnosis, ensure_ascii=False) if isinstance(diagnosis, dict) else diagnosis
    hist_str = json.dumps(session_history, ensure_ascii=False) if isinstance(session_history, dict) else session_history
    return await call_dify_or_llm(
        "teacher_summary",
        {
            "diagnosis": diag_str,
            "session_history": hist_str,
        },
        user_id=student_id,
    )


async def ai_grade_answers(
    *,
    grading_results: str | dict,
    student_info: str | dict,
    student_id: str = "system",
) -> dict[str, Any]:
    grade_str = json.dumps(grading_results, ensure_ascii=False) if isinstance(grading_results, dict) else grading_results
    info_str = json.dumps(student_info, ensure_ascii=False) if isinstance(student_info, dict) else student_info
    return await call_dify_or_llm(
        "ai_grading",
        {
            "grading_results": grade_str,
            "student_info": info_str,
        },
        user_id=student_id,
    )


async def ai_analyze_profile(
    *,
    student_data: str | dict,
    error_stats: str | dict,
    accuracy_trend: str | dict,
    student_id: str = "system",
) -> dict[str, Any]:
    return await call_dify_or_llm(
        "ai_profile",
        {
            "student_data": json.dumps(student_data, ensure_ascii=False) if isinstance(student_data, dict) else student_data,
            "error_stats": json.dumps(error_stats, ensure_ascii=False) if isinstance(error_stats, dict) else error_stats,
            "accuracy_trend": json.dumps(accuracy_trend, ensure_ascii=False) if isinstance(accuracy_trend, dict) else accuracy_trend,
        },
        user_id=student_id,
    )


async def ai_generate_problems(
    *,
    error_codes: str | list[str],
    difficulty: str = "A",
    count: int = 5,
    grade: int = 6,
    student_id: str = "system",
) -> dict[str, Any]:
    codes_str = ", ".join(error_codes) if isinstance(error_codes, list) else error_codes
    return await call_dify_or_llm(
        "problem_generation",
        {
            "error_codes": codes_str,
            "difficulty": difficulty,
            "count": str(count),
            "grade": str(grade),
        },
        user_id=student_id,
    )


def get_dify_status() -> dict[str, Any]:
    return {
        "cloud": {
            "enabled": dify_config.cloud.enabled,
            "base_url": dify_config.cloud.base_url,
            "api_key_set": bool(DIFY_API_KEY),
        },
        "local": {
            "enabled": dify_config.local.enabled,
            "base_url": dify_config.local.base_url,
            "api_key_set": bool(
                any(
                    LOCAL_WORKFLOWS.get(k, {}).get("api_key", "")
                    for k in WORKFLOWS
                )
            ),
        },
        "workflows_configured": list(WORKFLOWS.keys()),
        "routing": "local → cloud → deepseek",
    }

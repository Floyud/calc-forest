"""Dify Workflow 客户端，自动回退到 DeepSeek 直连。

架构:
    FastAPI → dify_client.py → try Dify Workflow API
                              → fallback to direct DeepSeek (llm_client.py)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dify 配置
# ---------------------------------------------------------------------------
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_ENABLED = os.getenv("DIFY_ENABLED", "false").lower() in ("true", "1", "yes")

DEFAULT_TIMEOUT = 60
MAX_CONCURRENT_REQUESTS = int(os.getenv("DIFY_MAX_CONCURRENCY", "5"))
MAX_RETRIES = int(os.getenv("DIFY_MAX_RETRIES", "2"))
RETRY_DELAY = float(os.getenv("DIFY_RETRY_DELAY", "1.0"))


# ---------------------------------------------------------------------------
# DifyConfig — 镜像 llm_client._LLMConfig 模式
# ---------------------------------------------------------------------------
class DifyConfig:
    """Dify 连接池与并发控制。"""

    def __init__(self) -> None:
        self.base_url: str = DIFY_BASE_URL
        self.api_key: str = DIFY_API_KEY
        self.enabled: bool = DIFY_ENABLED
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


dify_config = DifyConfig()


# ---------------------------------------------------------------------------
# Workflow 定义 — 硬编码，后续可迁移到配置文件
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# 核心函数：先试 Dify，失败回退到 DeepSeek
# ---------------------------------------------------------------------------
async def call_dify_or_llm(
    workflow_key: str,
    inputs: dict[str, Any],
    *,
    user_id: str = "system",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    response_format: dict[str, str] | None = None,
) -> dict[str, Any]:
    """尝试 Dify workflow，失败后回退到 DeepSeek 直连。

    Args:
        workflow_key: WORKFLOWS 字典中的键。
        inputs: 传入 workflow 的参数。
        user_id: Dify 用户标识。
        temperature: DeepSeek 回退时的温度参数。
        max_tokens: DeepSeek 回退时的最大 token 数。
        response_format: DeepSeek 回退时的 response_format 参数。

    Returns:
        解析后的 JSON 字典。
    """
    if dify_config.enabled and dify_config.api_key:
        try:
            return await _call_dify_workflow(workflow_key, inputs, user_id)
        except Exception as exc:
            logger.warning(
                "Dify workflow %s 失败，回退到 DeepSeek: %s", workflow_key, exc,
            )
    return await _call_deepseek_fallback(
        workflow_key, inputs, temperature, max_tokens, response_format,
    )


# ---------------------------------------------------------------------------
# Dify Workflow 调用
# ---------------------------------------------------------------------------
async def _call_dify_workflow(
    workflow_key: str,
    inputs: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    """POST 到 Dify /workflows/run 接口。"""
    wf = WORKFLOWS.get(workflow_key)
    if wf is None:
        raise ValueError(f"未知 workflow 键: {workflow_key}")

    api_key = wf["api_key"] or dify_config.api_key
    url = f"{dify_config.base_url}/workflows/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": inputs,
        "response_mode": "blocking",
        "user": user_id,
    }

    t0 = time.monotonic()
    async with dify_config.get_semaphore():
        client = await dify_config.get_client()
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            elapsed = time.monotonic() - t0
            data = resp.json()
            outputs = data.get("data", {}).get("outputs", {})
            logger.info(
                "Dify workflow %s 成功 (%.1fs): task_id=%s",
                workflow_key, elapsed, data.get("task_id", "?"),
            )
            return outputs
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            elapsed = time.monotonic() - t0
            raise RuntimeError(
                f"Dify 连接失败 ({elapsed:.1fs}): {exc}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            elapsed = time.monotonic() - t0
            raise RuntimeError(
                f"Dify 返回 HTTP {exc.response.status_code} ({elapsed:.1fs}): "
                f"{exc.response.text[:300]}"
            ) from exc


# ---------------------------------------------------------------------------
# DeepSeek 直连回退
# ---------------------------------------------------------------------------
async def _call_deepseek_fallback(
    workflow_key: str,
    inputs: dict[str, Any],
    temperature: float,
    max_tokens: int,
    response_format: dict[str, str] | None,
) -> dict[str, Any]:
    """使用 llm_client.call_deepseek 进行直连 LLM 调用。"""
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
    # (保留 JSON 中的花括号，只清理 {variable_name} 形式的)
    import re
    user_content = re.sub(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', '', user_content)

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
        # 尝试提取 JSON 对象或数组
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = content.find(start_char)
            end = content.rfind(end_char) + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    continue
        # 无法解析，返回原始内容
        return {"raw_content": content, "parse_error": True}


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------
async def generate_student_feedback(
    *,
    problem: str,
    student_answer: str,
    diagnosis: str | dict,
    student_id: str = "system",
    grade: int = 6,
) -> dict[str, Any]:
    """生成学生反馈（引导式讲解）。"""
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
    """生成教师诊断摘要。"""
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
    """AI 辅助批改分析。"""
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
    """AI 学习画像分析。"""
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
    """AI 生成针对性练习题。"""
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


# ---------------------------------------------------------------------------
# 状态查询
# ---------------------------------------------------------------------------
def get_dify_status() -> dict[str, Any]:
    """返回 Dify 客户端当前状态（用于 /api/config/dify-status 等端点）。"""
    return {
        "enabled": dify_config.enabled,
        "base_url": dify_config.base_url,
        "api_key_set": bool(dify_config.api_key),
        "workflows_configured": list(WORKFLOWS.keys()),
    }

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class _CircuitBreaker:
    """Simple circuit breaker: skip a failing track after N consecutive failures."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0) -> None:
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0.0
        self.is_open = False

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            self.last_failure_time = time.time()

    def record_success(self) -> None:
        self.failure_count = 0
        self.is_open = False

    def should_skip(self) -> bool:
        if not self.is_open:
            return False
        if time.time() - self.last_failure_time > self.recovery_timeout:
            # Half-open: allow one probe
            self.is_open = False
            self.failure_count = 0
            return False
        return True


DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_ENABLED = os.getenv("DIFY_ENABLED", "false").lower() in ("true", "1", "yes")

LOCAL_DIFY_BASE_URL = os.getenv("LOCAL_DIFY_BASE_URL", "http://127.0.0.1:18080/v1")
LOCAL_DIFY_ENABLED = os.getenv("LOCAL_DIFY_ENABLED", "false").lower() in ("true", "1", "yes")

# GLM / 智谱 direct fallback (Track 3.5)
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4-flash")

DEFAULT_TIMEOUT = 45  # seconds — workflows need 20-30s with KB retrieval + LLM
MAX_CONCURRENT_REQUESTS = int(os.getenv("DIFY_MAX_CONCURRENCY", "5"))

# chatflow 类型标记 — student_guidance 用 /chat-messages，其余用 /workflows/run
CHATFLOW_KEYS: set[str] = {"student_guidance"}

WORKFLOW_TIMEOUTS: dict[str, int] = {
    "student_guidance": 45,
    "teacher_summary": 20,
    "ai_grading": 40,
    "ai_profile": 40,
    "problem_generation": 35,
}

_conversation_cache: dict[str, str] = {}

ERROR_TAXONOMY_CONTEXT = (
    "错因代码体系（E01-E11）：\n"
    "- E01 基础事实错误：口诀、口算、基础加减乘除事实错误\n"
    "- E02 进位错误：加法或乘法中满十进位遗漏或未加\n"
    "- E03 退位错误：减法本位不够减时退位处理错误\n"
    "- E04 数位对齐错误：竖式错位、小数位或部分积位置错误\n"
    "- E05 运算顺序错误：混合运算未按括号或先乘除后加减\n"
    "- E06 小数点/分数单位错误：小数点位置、分子分母或分数单位错误\n"
    "- E07 抄题/转写错误：数字、符号、条件从题目到步骤变化\n"
    "- E08 步骤遗漏：漏部分积、漏商位、跳过关键中间步骤\n"
    "- E11 习惯性未验算：结果明显不合理但未发现\n"
    "- E99 其他/未分类"
)


class _DifyTrack:

    def __init__(self, *, base_url: str, enabled: bool) -> None:
        self.base_url = base_url.rstrip("/")
        self.enabled = enabled
        self.breaker = _CircuitBreaker()
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
            "输出必须严格遵守 JSON 格式。\n\n"
            "【错因代码体系】\n"
            "E01 基础事实错误：口诀、口算、基础加减乘除事实错误\n"
            "E02 进位错误：加法或乘法中满十进位遗漏或未加\n"
            "E03 退位错误：减法本位不够减时退位处理错误\n"
            "E04 数位对齐错误：竖式错位、小数位或部分积位置错误\n"
            "E05 运算顺序错误：混合运算未按括号或先乘除后加减\n"
            "E06 小数点/分数单位错误：小数点位置、分子分母或分数单位错误\n"
            "E07 抄题/转写错误：数字、符号、条件从题目到步骤变化\n"
            "E08 步骤遗漏：漏部分积、漏商位、跳过关键中间步骤\n"
            "E11 习惯性未验算：结果明显不合理但未发现\n"
            "E99 其他/未分类\n\n"
            "【引导原则】\n"
            "1. 先肯定学生的努力和正确部分，再温和指出问题。\n"
            "2. 用提问引导学生自己发现错误（例如：你看看这一位上的数够不够减？），"
            "绝对不能直接给出最终答案。\n"
            "3. 每次只聚焦一个关键步骤，不要一次灌输太多。\n"
            "4. 用生活化的比喻帮助理解算理。"
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
            "输出必须严格遵守 JSON 格式。\n\n"
            "【错因分类标准】\n"
            "根据错误特征归类到以下代码：\n"
            "E01 基础事实错误（口诀/口算出错）\n"
            "E02 进位错误（满十未进位）\n"
            "E03 退位错误（不够减时退位处理错误）\n"
            "E04 数位对齐错误（竖式错位）\n"
            "E05 运算顺序错误（未遵循运算优先级）\n"
            "E06 小数点/分数单位错误\n"
            "E07 抄题/转写错误\n"
            "E08 步骤遗漏（跳过中间步骤）\n"
            "E11 习惯性未验算\n"
            "E99 其他\n\n"
            "【严重度评估】\n"
            "- high：基础概念错误（如运算顺序），影响后续学习\n"
            "- medium：计算习惯问题（如进退位），可通过专项训练改善\n"
            "- low：偶然性错误（如抄题），提醒即可"
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
            "输出必须严格遵守 JSON 格式。\n\n"
            "【批改标准】\n"
            "- pattern_summary：总结本次作业中反复出现的错误模式\n"
            "- error_type：归类为 'conceptual'（概念性错误）或 'procedural'（计算习惯问题）\n"
            "- suggestion：给出针对该学生的具体改进建议（1-2句话）\n"
            "- priority：根据错误频率和严重度评定 'high'/'medium'/'low'\n\n"
            "【错因代码参考】\n"
            "E01 基础事实错误 | E02 进位错误 | E03 退位错误 | E04 数位对齐错误\n"
            "E05 运算顺序错误 | E06 小数点/分数单位错误 | E07 抄题/转写错误\n"
            "E08 步骤遗漏 | E11 未验算 | E99 其他"
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


async def _retry_request(
    fn,
    *,
    max_retries: int = 2,
    base_delay: float = 1.0,
) -> Any:
    """Retry an async function with exponential backoff for transient errors."""
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(
                "Dify request failed (attempt %d/%d), retrying in %.1fs: %s",
                attempt + 1, max_retries + 1, delay, exc,
            )
            await asyncio.sleep(delay)


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
    # Fast-fail: if no LLM backend has valid credentials, skip immediately
    local_has_key = dify_config.local.enabled and bool(_get_api_key(workflow_key, "local"))
    cloud_has_key = dify_config.cloud.enabled and bool(_get_api_key(workflow_key, "cloud"))
    glm_has_key = bool(GLM_API_KEY)
    deepseek_has_key = bool(os.getenv("DEEPSEEK_API_KEY", ""))

    if not (local_has_key or cloud_has_key or glm_has_key or deepseek_has_key):
        raise RuntimeError(
            f"No LLM backend available for '{workflow_key}': "
            "local_dify disabled, cloud_dify no key, glm no key, deepseek no key"
        )

    # Track 1: Local Dify
    if dify_config.local.enabled:
        api_key = _get_api_key(workflow_key, "local")
        if api_key and not dify_config.local.breaker.should_skip():
            try:
                result = await _call_dify_endpoint(
                    workflow_key, inputs, user_id,
                    track=dify_config.local, api_key=api_key, track_label="local",
                )
                dify_config.local.breaker.record_success()
                return result
            except Exception as exc:
                dify_config.local.breaker.record_failure()
                logger.warning(
                    "Local Dify %s 失败，尝试 Cloud: %s", workflow_key, exc,
                )

    # Track 2: Cloud Dify
    if dify_config.cloud.enabled:
        api_key = _get_api_key(workflow_key, "cloud")
        if api_key and not dify_config.cloud.breaker.should_skip():
            try:
                result = await _call_dify_endpoint(
                    workflow_key, inputs, user_id,
                    track=dify_config.cloud, api_key=api_key, track_label="cloud",
                )
                dify_config.cloud.breaker.record_success()
                return result
            except Exception as exc:
                dify_config.cloud.breaker.record_failure()
                logger.warning(
                    "Cloud Dify %s 失败，回退到 DeepSeek: %s", workflow_key, exc,
                )

    # Track 3: GLM 直连回退 (智谱)
    if GLM_API_KEY:
        try:
            result = await _call_glm_direct(
                workflow_key, inputs, temperature, max_tokens, response_format,
            )
            logger.info("GLM 直连 %s 成功", workflow_key)
            return result
        except Exception as exc:
            logger.warning("GLM 直连 %s 失败，回退到 DeepSeek: %s", workflow_key, exc)

    # Track 4: DeepSeek 直连回退
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
    wf_timeout = WORKFLOW_TIMEOUTS.get(workflow_key, DEFAULT_TIMEOUT)
    req_timeout = httpx.Timeout(connect=10.0, read=float(wf_timeout), write=10.0, pool=5.0)

    if is_chatflow:
        query = WORKFLOWS[workflow_key]["prompt_user_template"]
        for key, value in inputs.items():
            str_value = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
            query = query.replace("{" + key + "}", str_value)
        query = re.sub(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", "", query)
        payload: dict[str, Any] = {"inputs": {}, "query": query, "response_mode": "blocking", "user": user_id}
        conversation_id = _conversation_cache.get(user_id)
        if conversation_id:
            payload["conversation_id"] = conversation_id
    else:
        payload = {"inputs": inputs, "response_mode": "blocking", "user": user_id}

    t0 = time.monotonic()
    async with track.get_semaphore():
        client = await track.get_client()

        async def _do_post() -> httpx.Response:
            resp = await client.post(url, headers=headers, json=payload, timeout=req_timeout)
            resp.raise_for_status()
            return resp

        try:
            if track_label == "local":
                resp = await _retry_request(_do_post)
            else:
                resp = await _do_post()
            elapsed = time.monotonic() - t0
            data = resp.json()
            logger.info("[%s] Dify %s %s ok (%.1fs)", track_label, "chatflow" if is_chatflow else "workflow", workflow_key, elapsed)
            if is_chatflow:
                if "conversation_id" in data:
                    _conversation_cache[user_id] = data["conversation_id"]
                answer = data.get("answer", "").strip()
                answer = answer.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                try:
                    return json.loads(answer)
                except json.JSONDecodeError:
                    return {"raw_content": answer, "parse_error": True}
            return data.get("data", {}).get("outputs", {})
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            elapsed = time.monotonic() - t0
            raise RuntimeError(f"[{track_label}] Dify 连接失败 ({elapsed:.1f}s): {exc}") from exc
        except httpx.HTTPStatusError as exc:
            elapsed = time.monotonic() - t0
            raise RuntimeError(
                f"[{track_label}] Dify HTTP {exc.response.status_code} ({elapsed:.1f}s): {exc.response.text[:300]}"
            ) from exc


async def _call_glm_direct(
    workflow_key: str,
    inputs: dict[str, Any],
    temperature: float,
    max_tokens: int,
    response_format: dict[str, str] | None,
) -> dict[str, Any]:
    """Call GLM (智谱) directly via OpenAI-compatible API as Track 3.5 fallback."""
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

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GLM_API_KEY}",
    }
    endpoint = f"{GLM_BASE_URL}/chat/completions"
    payload: dict[str, Any] = {
        "model": GLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    t0 = time.monotonic()
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=5.0)) as client:
        try:
            resp = await client.post(endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            elapsed = time.monotonic() - t0
            logger.info("GLM 直连 %s ok (%.1fs)", workflow_key, elapsed)
            raw = resp.json()

            content = raw["choices"][0]["message"]["content"].strip()
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                logger.warning("GLM 直连返回非 JSON，尝试提取: %s", content[:200])
                for start_char, end_char in [("{", "}"), ("[", "]")]:
                    start = content.find(start_char)
                    end = content.rfind(end_char) + 1
                    if start >= 0 and end > start:
                        try:
                            return json.loads(content[start:end])
                        except json.JSONDecodeError:
                            continue
                return {"raw_content": content, "parse_error": True}

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            elapsed = time.monotonic() - t0
            raise RuntimeError(f"GLM 直连失败 ({elapsed:.1f}s): {exc}") from exc
        except httpx.HTTPStatusError as exc:
            elapsed = time.monotonic() - t0
            raise RuntimeError(
                f"GLM 直连 HTTP {exc.response.status_code} ({elapsed:.1f}s): {exc.response.text[:300]}"
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

    try:
        raw = await call_deepseek(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=fmt,
        )
    except RuntimeError as exc:
        # DeepSeek failed — if it's a connection error and GLM is available, try GLM mode
        if GLM_API_KEY and ("连接" in str(exc) or "不可用" in str(exc) or "Server disconnected" in str(exc)):
            logger.warning("DeepSeek 连接失败，自动切换到 GLM 模式: %s", exc)
            from app.services.llm_client import llm_config
            saved_mode = llm_config.mode
            try:
                llm_config.mode = "glm"
                raw = await call_deepseek(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=fmt,
                )
                logger.info("GLM 模式回退成功")
            finally:
                llm_config.mode = saved_mode
        else:
            raise

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
    student_info: str | dict | None = None,
    student_id: str = "system",
) -> dict[str, Any]:
    diag_str = json.dumps(diagnosis, ensure_ascii=False) if isinstance(diagnosis, dict) else diagnosis
    hist_str = json.dumps(session_history, ensure_ascii=False) if isinstance(session_history, dict) else session_history
    info_str = json.dumps(student_info, ensure_ascii=False) if isinstance(student_info, dict) else (student_info or "{}")
    return await call_dify_or_llm(
        "teacher_summary",
        {
            "diagnosis": diag_str,
            "student_info": info_str,
            "session_history": hist_str,
        },
        user_id=student_id,
    )


async def ai_grade_answers(
    *,
    grading_results: str | dict,
    student_info: str | dict,
    error_stats: str | dict | None = None,
    accuracy_trend: str | dict | None = None,
    student_id: str = "system",
) -> dict[str, Any]:
    grade_str = json.dumps(grading_results, ensure_ascii=False) if isinstance(grading_results, dict) else grading_results
    info_str = json.dumps(student_info, ensure_ascii=False) if isinstance(student_info, dict) else student_info
    estats_str = json.dumps(error_stats, ensure_ascii=False) if isinstance(error_stats, dict) else (error_stats or "{}")
    trend_str = json.dumps(accuracy_trend, ensure_ascii=False) if isinstance(accuracy_trend, dict) else (accuracy_trend or "[]")
    return await call_dify_or_llm(
        "ai_grading",
        {
            "mode": "grading",
            "grading_results": grade_str,
            "student_info": info_str,
            "error_stats": estats_str,
            "accuracy_trend": trend_str,
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
    data_str = json.dumps(student_data, ensure_ascii=False) if isinstance(student_data, dict) else student_data
    estats_str = json.dumps(error_stats, ensure_ascii=False) if isinstance(error_stats, dict) else error_stats
    trend_str = json.dumps(accuracy_trend, ensure_ascii=False) if isinstance(accuracy_trend, dict) else accuracy_trend
    return await call_dify_or_llm(
        "ai_profile",
        {
            "mode": "profiling",
            "student_info": data_str,
            "grading_results": "{}",
            "error_stats": estats_str,
            "accuracy_trend": trend_str,
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


def clear_conversation(student_id: str) -> None:
    """Clear cached conversation_id for a student, starting a fresh session."""
    _conversation_cache.pop(student_id, None)


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
        "routing": "local → cloud → glm_direct → deepseek (auto-glm on connection error)",
    }

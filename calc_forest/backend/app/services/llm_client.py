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
# Provider: DeepSeek (primary)
# ---------------------------------------------------------------------------
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ---------------------------------------------------------------------------
# Provider: GLM / 智谱 (secondary fallback)
# ---------------------------------------------------------------------------
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4-flash")

# ---------------------------------------------------------------------------
# Provider: Xiaomi MiMo (树精灵引导对话)
# ---------------------------------------------------------------------------
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2.5-pro")

# ---------------------------------------------------------------------------
# Proxy (opencode reverse-proxy) config
# ---------------------------------------------------------------------------
DEEPSEEK_MODE = os.getenv("DEEPSEEK_MODE", "official")  # "official" | "proxy" | "glm"
DEEPSEEK_PROXY_URL = os.getenv("DEEPSEEK_PROXY_URL", "http://127.0.0.1:46223")
DEEPSEEK_PROXY_MODEL = os.getenv("DEEPSEEK_PROXY_MODEL", "opencode-go/deepseek-v4-flash")

DEFAULT_TIMEOUT = 60
PROXY_TIMEOUT = int(os.getenv("DEEPSEEK_PROXY_TIMEOUT", "90"))

# Concurrency tuning
MAX_CONCURRENT_REQUESTS = int(os.getenv("DEEPSEEK_MAX_CONCURRENCY", "5"))
MAX_RETRIES = int(os.getenv("DEEPSEEK_MAX_RETRIES", "2"))
RETRY_DELAY = float(os.getenv("DEEPSEEK_RETRY_DELAY", "1.0"))


# ---------------------------------------------------------------------------
# Runtime config helpers (used by /api/config/llm-mode endpoint)
# ---------------------------------------------------------------------------
class _LLMConfig:
    """Mutable runtime wrapper so the main.py endpoints can switch mode."""

    def __init__(self) -> None:
        self.mode: str = DEEPSEEK_MODE
        self.official_base_url: str = DEEPSEEK_BASE_URL
        self.official_model: str = DEEPSEEK_MODEL
        self.api_key: str = DEEPSEEK_API_KEY
        self.proxy_url: str = DEEPSEEK_PROXY_URL
        self.proxy_model: str = DEEPSEEK_PROXY_MODEL
        self.proxy_timeout: int = PROXY_TIMEOUT
        self.glm_base_url: str = GLM_BASE_URL
        self.glm_api_key: str = GLM_API_KEY
        self.glm_model: str = GLM_MODEL
        self.mimo_base_url: str = MIMO_BASE_URL
        self.mimo_api_key: str = MIMO_API_KEY
        self.mimo_model: str = MIMO_MODEL
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None

    @property
    def active_base_url(self) -> str:
        if self.mode == "proxy":
            return self.proxy_url
        if self.mode == "glm":
            return self.glm_base_url
        if self.mode == "mimo":
            return self.mimo_base_url
        return self.official_base_url

    @property
    def active_model(self) -> str:
        if self.mode == "proxy":
            return self.proxy_model
        if self.mode == "glm":
            return self.glm_model
        if self.mode == "mimo":
            return self.mimo_model
        return self.official_model

    @property
    def active_timeout(self) -> int:
        if self.mode == "proxy":
            return self.proxy_timeout
        return DEFAULT_TIMEOUT

    @property
    def active_endpoint(self) -> str:
        if self.mode == "proxy":
            return f"{self.proxy_url}/v1/chat/completions"
        if self.mode == "glm":
            return f"{self.glm_base_url}/chat/completions"
        if self.mode == "mimo":
            return f"{self.mimo_base_url}/chat/completions"
        return f"{self.official_base_url}/chat/completions"

    @property
    def active_api_key(self) -> str:
        if self.mode == "glm":
            return self.glm_api_key
        if self.mode == "mimo":
            return self.mimo_api_key
        return self.api_key

    def get_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        return self._semaphore

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=float(self.active_timeout),
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


llm_config = _LLMConfig()


def get_llm_status() -> dict[str, Any]:
    status = "ready"
    active_key = llm_config.active_api_key
    if not active_key:
        status = "no_api_key"
    return {
        "mode": llm_config.mode,
        "base_url": llm_config.active_base_url,
        "model": llm_config.active_model,
        "api_key_set": bool(active_key),
        "status": status,
        "providers": {
            "deepseek": {"key_set": bool(llm_config.api_key), "model": llm_config.official_model},
            "glm": {"key_set": bool(llm_config.glm_api_key), "model": llm_config.glm_model},
            "mimo": {"key_set": bool(llm_config.mimo_api_key), "model": llm_config.mimo_model},
        },
        "max_concurrency": MAX_CONCURRENT_REQUESTS,
        "max_retries": MAX_RETRIES,
    }


async def call_deepseek(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    response_format: dict[str, str] | None = None,
    _attempt: int = 0,
) -> dict[str, Any]:
    cfg = llm_config
    t0 = time.monotonic()

    headers: dict[str, str] = {"Content-Type": "application/json"}
    active_key = cfg.active_api_key
    if active_key:
        headers["Authorization"] = f"Bearer {active_key}"

    payload: dict[str, Any] = {
        "model": cfg.active_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    async with cfg.get_semaphore():
        client = await cfg.get_client()
        try:
            resp = await client.post(cfg.active_endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            elapsed = time.monotonic() - t0
            logger.info(
                "call_deepseek ok mode=%s model=%s attempt=%d elapsed=%.1fs",
                cfg.mode, cfg.active_model, _attempt + 1, elapsed,
            )
            return resp.json()

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            elapsed = time.monotonic() - t0
            if _attempt < MAX_RETRIES:
                wait = RETRY_DELAY * (_attempt + 1)
                logger.warning(
                    "LLM transient error (attempt=%d/%d, %.1fs), retrying in %.1fs: %s",
                    _attempt + 1, MAX_RETRIES + 1, elapsed, wait, exc,
                )
                await asyncio.sleep(wait)
                return await call_deepseek(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    _attempt=_attempt + 1,
                )
            logger.error("LLM failed after %d attempts (%.1fs): %s", _attempt + 1, elapsed, exc)
            raise RuntimeError(
                f"LLM 服务不可用 (mode={cfg.mode}, { _attempt + 1}次重试后仍失败): {exc}"
            ) from exc

        except httpx.HTTPStatusError as exc:
            elapsed = time.monotonic() - t0
            # Retry on 429 (rate limit) or 502/503 (gateway)
            if exc.response.status_code in (429, 502, 503) and _attempt < MAX_RETRIES:
                wait = RETRY_DELAY * (_attempt + 1) * 2
                logger.warning(
                    "LLM HTTP %d (attempt=%d/%d, %.1fs), retrying in %.1fs",
                    exc.response.status_code, _attempt + 1, MAX_RETRIES + 1, elapsed, wait,
                )
                await asyncio.sleep(wait)
                return await call_deepseek(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    _attempt=_attempt + 1,
                )
            logger.error("LLM returned HTTP %d (%.1fs): %s", exc.response.status_code, elapsed, exc.response.text[:300])
            raise RuntimeError(
                f"LLM 服务返回错误 HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc


def _build_rag_prompt_block(
    rag_context: dict | None,
    error_codes: list[str] | None,
    difficulty: str,
    week_number: int | None,
) -> str:
    if not rag_context:
        return ""

    lines = ["\n【教学参考】"]

    wc = rag_context.get("week_context")
    if wc:
        lines.append(f"当前教学进度：第{week_number}周，{wc['calc_type']}")

    kps = rag_context.get("knowledge_points", [])
    if kps:
        lines.append("知识点规则：")
        for kp in kps[:8]:
            lines.append(f"  - {kp['topic']}：{kp['description']}")

    related = rag_context.get("related_concepts", [])
    if related:
        names = [r["topic"] for r in related[:5]]
        lines.append(f"相关概念：{', '.join(names)}")

    examples = rag_context.get("example_problems", [])
    if examples:
        lines.append("典型例题：")
        for ex in examples[:4]:
            lines.append(f"  - {ex['problem_plain']}{ex['correct_answer']}（{ex['knowledge_point']}）")

    diff_std = {"A": "基础(分子分母≤6)", "B": "中等(≤12)", "C": "高档(≤20)"}
    lines.append(f"难度标准：{diff_std.get(difficulty, '综合')}")
    return "\n".join(lines)


async def _fetch_rag_context(
    error_codes: list[str] | None,
    difficulty: str,
    week_number: int | None,
) -> dict | None:
    if not error_codes:
        return None
    try:
        from app.services.knowledge_rag_service import build_rag_context
        return await build_rag_context(error_codes, difficulty, week_number)
    except Exception as exc:
        logger.warning("RAG context fetch failed, proceeding without: %s", exc)
        return None


async def generate_math_problems(
    *,
    grade: int = 6,
    semester: int = 1,
    error_codes: list[str] | None = None,
    difficulty: str = "A",
    count: int = 5,
    unit_title: str = "",
    week_number: int | None = None,
) -> list[dict[str, Any]]:
    diff_map = {"A": "基础巩固", "B": "能力提升", "C": "挑战冲刺"}
    diff_label = diff_map.get(difficulty, "综合")

    rag_context = await _fetch_rag_context(error_codes, difficulty, week_number)
    rag_block = _build_rag_prompt_block(rag_context, error_codes, difficulty, week_number)

    error_desc = ""
    if error_codes:
        error_desc = f"针对以下错因类型出题：{', '.join(error_codes)}。"

    unit_ctx = f"当前教学单元：{unit_title}。" if unit_title else ""

    system_prompt = (
        "你是一位小学数学教师，擅长根据学生错因生成针对性练习题。"
        "所有题目必须是纯计算题（不含应用题），覆盖人教版对应年级的计算内容。"
        "返回严格 JSON 数组，不要加 markdown 代码块标记。"
    )

    user_prompt = (
        f"年级：{grade}年级{semester and '上' or '下'}册\n"
        f"难度：{diff_label}\n"
        f"题量：{count}道\n"
        f"{unit_ctx}{error_desc}\n"
        f"{rag_block}\n"
        "每道题返回如下 JSON 格式：\n"
        '{"problem": "题目表达式（用 LaTeX 数学格式）", '
        '"problem_plain": "纯文本题目（如 2/3×3/4=）", '
        '"correct_answer": "标准答案（最简分数/小数）", '
        '"knowledge_point": "知识点", '
        '"target_error_code": "针对的错因代码", '
        '"difficulty": "' + difficulty + '"}\n'
        "返回纯 JSON 数组，不要任何额外文字。"
    )

    raw = await call_deepseek(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=max(1024, count * 256),
    )

    content = raw["choices"][0]["message"]["content"].strip()
    content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        problems = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("DeepSeek returned non-JSON, attempting extraction: %s", content[:200])
        start = content.find("[")
        end = content.rfind("]") + 1
        problems = json.loads(content[start:end])

    return problems


async def batch_generate_homework_sets(
    *,
    teacher_id: str,
    class_id: str,
    grade: int = 6,
    semester: int = 1,
    difficulty: str = "A",
    count: int = 5,
    unit_title: str = "",
    student_targets: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if not student_targets:
        result = await generate_math_problems(
            grade=grade, semester=semester, difficulty=difficulty,
            count=count, unit_title=unit_title,
        )
        return [{"student_id": None, "problems": result}]

    total = len(student_targets)
    logger.info("batch_generate_homework_sets: %d students, concurrency=%d", total, MAX_CONCURRENT_REQUESTS)

    async def _gen_one(idx: int, target: dict[str, Any]) -> dict[str, Any]:
        sid = target.get("student_id", f"?{idx}")
        try:
            problems = await generate_math_problems(
                grade=grade, semester=semester,
                error_codes=target.get("error_codes"),
                difficulty=target.get("difficulty", difficulty),
                count=count,
                unit_title=unit_title,
            )
            logger.info("batch_generate: [%d/%d] %s ok (%d problems)", idx + 1, total, sid, len(problems))
            return {"student_id": sid, "problems": problems}
        except Exception as exc:
            logger.error("batch_generate: [%d/%d] %s failed: %s", idx + 1, total, sid, exc)
            return {"student_id": sid, "problems": [], "error": str(exc)}

    tasks = [_gen_one(i, t) for i, t in enumerate(student_targets)]
    output = await asyncio.gather(*tasks)

    return list(output)

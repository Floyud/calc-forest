"""Baidu Education OCR — 智能作业批改 API integration.

API docs: https://ai.baidu.com/ai-doc/OCR/omimjkvlz
Two modes:
  1. Full correction (async): create_task(only_split=False) → get_result(task_id)
  2. Problem splitting only (sync): create_task(only_split=True) → immediate result

Auth: OAuth2 access_token from API_KEY + SECRET_KEY.

Endpoints:
  - POST create_task: submit base64 image for correction
  - POST get_result: poll for async task result

Response format (get_result):
  result.status: "pending" | "running" | "Success" | "Failed"
  result.isAllFinished: bool
  result.imageResults: [{imageId, imageUrl, paperSubject, resize_ratio, result: [...]}]
"""
from __future__ import annotations

import asyncio
import base64
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://aip.baidubce.com"
_TOKEN_URL = f"{_BASE}/oauth/2.0/token"
_CREATE_URL = f"{_BASE}/rest/2.0/ocr/v1/correct_edu/create_task"
_RESULT_URL = f"{_BASE}/rest/2.0/ocr/v1/correct_edu/get_result"

_api_key: str = ""
_secret_key: str = ""
_access_token: str = ""
_token_expires: float = 0

# ── Correct result constants ─────────────────────────────────────────
CORRECT_UNCHECKED = 0  # 未批
CORRECT_RIGHT = 1  # 正确
CORRECT_WRONG = 2  # 错误
CORRECT_UNANSWERED = 3  # 未作答

CORRECT_LABELS = {
    CORRECT_UNCHECKED: "未批",
    CORRECT_RIGHT: "正确",
    CORRECT_WRONG: "错误",
    CORRECT_UNANSWERED: "未作答",
}

# ── Question type constants ──────────────────────────────────────────
QTYPE_DEFAULT = 0
QTYPE_ORAL_CALC = 1  # 口算
QTYPE_CHOICE = 2  # 选择
QTYPE_JUDGE = 3  # 判断
QTYPE_FILL = 4  # 填空
QTYPE_APPLY = 5  # 应用
QTYPE_CALCULATE = 17  # 计算


# ── Configuration ────────────────────────────────────────────────────

def configure(api_key: str, secret_key: str) -> None:
    """Set Baidu API credentials. Call once at startup."""
    global _api_key, _secret_key
    _api_key = api_key
    _secret_key = secret_key
    logger.info("Baidu OCR configured with API key: %s...%s", api_key[:4], api_key[-4:])


# ── Token management ─────────────────────────────────────────────────

async def _ensure_token() -> str:
    """Get a valid OAuth2 access_token, refreshing if needed."""
    global _access_token, _token_expires
    if _access_token and time.time() < _token_expires - 60:
        return _access_token

    logger.debug("Refreshing Baidu OCR access_token...")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _TOKEN_URL,
            params={
                "grant_type": "client_credentials",
                "client_id": _api_key,
                "client_secret": _secret_key,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        raise RuntimeError(
            f"百度 OAuth2 令牌获取失败: {data.get('error_description', data['error'])}"
        )

    _access_token = data["access_token"]
    _token_expires = time.time() + data.get("expires_in", 2592000)
    logger.info("Baidu OCR access_token refreshed, expires in %.0f seconds",
                _token_expires - time.time())
    return _access_token


# ── Data classes ─────────────────────────────────────────────────────

@dataclass
class BaiduSlotResult:
    """A single answer slot within a question (e.g. blank in fill-in-the-blank)."""
    slot_id: str = ""
    sequence: int = 0
    correct_result: int = CORRECT_UNCHECKED  # 0=未批,1=正确,2=错误,3=未作答
    reason: str = ""  # 错因描述
    handwriting_area: dict = field(default_factory=dict)  # {left_x, left_y, right_x, right_y}

    @property
    def label(self) -> str:
        return CORRECT_LABELS.get(self.correct_result, "未知")

    @property
    def is_wrong(self) -> bool:
        return self.correct_result == CORRECT_WRONG


@dataclass
class BaiduQuestionResult:
    """A single question detected on the homework page."""
    question_id: str = ""
    sequence: int = 0  # 0-based sequence number
    question_type: int = QTYPE_DEFAULT  # 0=default,1=口算,2=选择,3=判断,4=填空,5=应用,17=计算
    correct_result: int = CORRECT_UNCHECKED  # 0=未批,1=正确,2=错误,3=未作答
    is_finished: bool = False
    question_area: list[dict] = field(default_factory=list)  # [{left_x,left_y,right_x,right_y}]
    crop_url: str = ""
    slots: list[BaiduSlotResult] = field(default_factory=list)

    @property
    def label(self) -> str:
        return CORRECT_LABELS.get(self.correct_result, "未知")

    @property
    def is_wrong(self) -> bool:
        return self.correct_result == CORRECT_WRONG

    @property
    def wrong_slots(self) -> list[BaiduSlotResult]:
        return [s for s in self.slots if s.is_wrong]


@dataclass
class BaiduImageResult:
    """Results for one submitted image (page)."""
    image_id: str = ""
    image_url: str = ""
    subject: str = ""  # "math", "chinese", "english" etc
    resize_ratio: float = 1.0
    questions: list[BaiduQuestionResult] = field(default_factory=list)

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    @property
    def wrong_questions(self) -> list[BaiduQuestionResult]:
        return [q for q in self.questions if q.is_wrong]


@dataclass
class BaiduCorrectionResult:
    """Top-level result from the Baidu 智能作业批改 API."""
    task_id: str = ""
    status: str = ""  # "pending" | "running" | "Success" | "Failed"
    is_all_finished: bool = False
    stat_result: dict = field(default_factory=dict)  # {all, corrected, correcting}
    images: list[BaiduImageResult] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == "Success"

    @property
    def total_questions(self) -> int:
        return sum(img.total_questions for img in self.images)

    @property
    def total_wrong(self) -> int:
        return sum(len(img.wrong_questions) for img in self.images)

    @property
    def all_wrong_questions(self) -> list[BaiduQuestionResult]:
        out: list[BaiduQuestionResult] = []
        for img in self.images:
            out.extend(img.wrong_questions)
        return out


# ── API helpers ───────────────────────────────────────────────────────

def _is_error_response(data: dict) -> bool:
    """Check if the API returned an error. error_code can be int or string."""
    if "error_code" not in data:
        return False
    code = data["error_code"]
    # Normal response may have error_code = 0 or "0" (no error)
    if code == 0 or code == "0":
        return False
    return True


# ── Main API ──────────────────────────────────────────────────────────

async def correct_homework(
    image_bytes: bytes,
    only_split: bool = False,
) -> BaiduCorrectionResult:
    """Submit a homework image for correction.

    Args:
        image_bytes: Raw image bytes (JPEG/PNG).
        only_split: If True, only do problem segmentation (sync, no grading).
                    If False (default), do full async correction with grading.

    Returns:
        BaiduCorrectionResult with structured correction data.

    Raises:
        RuntimeError: On API errors.
        TimeoutError: If polling exceeds max_wait.
    """
    token = await _ensure_token()
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")

    logger.info("Submitting Baidu OCR task (only_split=%s, image_size=%d bytes)",
                only_split, len(image_bytes))

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            _CREATE_URL,
            params={"access_token": token},
            json={"image": img_b64, "only_split": only_split},
            headers={"content-type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    logger.debug("create_task response: %s", _truncate_for_log(data))

    if _is_error_response(data):
        error_code = data.get("error_code", "unknown")
        error_msg = data.get("error_msg", "")
        raise RuntimeError(f"百度 OCR create_task 错误 {error_code}: {error_msg}")

    # Sync mode (only_split=True): immediate result with different structure
    if only_split:
        logger.info("Baidu OCR split-only task completed (sync)")
        return _parse_split_result(data)

    # Async mode: extract task_id and poll
    task_id = data.get("task_id", "")
    if not task_id:
        # Some responses nest task_id inside result
        task_id = data.get("result", {}).get("task_id", "")
    if not task_id:
        raise RuntimeError(f"百度 OCR create_task 未返回 task_id: {data}")

    logger.info("Baidu OCR task created: %s", task_id)
    result = await _poll_result(task_id)
    return result


async def correct_homework_from_path(image_path: str) -> BaiduCorrectionResult:
    """Convenience: submit an image file from a local path.

    Args:
        image_path: Path to image file (JPEG/PNG).

    Returns:
        BaiduCorrectionResult with structured correction data.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    image_bytes = path.read_bytes()
    logger.info("Loading image from %s (%d bytes)", image_path, len(image_bytes))
    return await correct_homework(image_bytes)


# ── Polling ───────────────────────────────────────────────────────────

async def _poll_result(task_id: str, max_wait: int = 60) -> BaiduCorrectionResult:
    """Poll get_result endpoint until task completes or times out.

    The API response format:
      {
        "result": {
          "task_id": "...",
          "status": "pending" | "running" | "Success" | "Failed",
          "isAllFinished": true/false,
          "stat_result": {"all": N, "corrected": N, "correcting": N},
          "imageResults": [...]
        }
      }
    """
    token = await _ensure_token()
    start = time.time()
    poll_count = 0

    async with httpx.AsyncClient(timeout=15) as client:
        while time.time() - start < max_wait:
            await asyncio.sleep(5)
            poll_count += 1
            elapsed = time.time() - start

            resp = await client.post(
                _RESULT_URL,
                params={"access_token": token},
                json={"task_id": task_id},
                headers={"content-type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

            logger.debug("get_result poll #%d (%.1fs): %s",
                         poll_count, elapsed, _truncate_for_log(data))

            # Check for API-level errors
            if _is_error_response(data):
                error_code = data.get("error_code", "unknown")
                error_msg = data.get("error_msg", "")
                raise RuntimeError(f"百度 OCR get_result 错误 {error_code}: {error_msg}")

            result = data.get("result", {})
            status = result.get("status", "")

            # Terminal failure
            if status == "Failed":
                raise RuntimeError(f"百度 OCR 任务 {task_id} 失败: {data}")

            # Success — parse and return
            if status == "Success" and result.get("isAllFinished", False):
                logger.info("Baidu OCR task %s completed after %d polls (%.1fs)",
                            task_id, poll_count, time.time() - start)
                return _parse_result(data)

            # Still pending/running — continue polling
            logger.debug("Task %s status=%s, isAllFinished=%s — polling...",
                         task_id, status, result.get("isAllFinished"))

    raise TimeoutError(f"百度 OCR 任务 {task_id} 超时（超过 {max_wait} 秒）")


# ── Result parsing ───────────────────────────────────────────────────

def _parse_slot(slot_data: dict) -> BaiduSlotResult:
    """Parse a single slot from the API response."""
    hw_area = slot_data.get("handwritingArea", {})
    return BaiduSlotResult(
        slot_id=str(slot_data.get("slotId", "")),
        sequence=int(slot_data.get("seqence", 0)),  # API typo "seqence"
        correct_result=int(slot_data.get("correctResult", CORRECT_UNCHECKED)),
        reason=str(slot_data.get("reason", "")),
        handwriting_area=hw_area,
    )


def _parse_question(q_data: dict) -> BaiduQuestionResult:
    """Parse a single question from the API response."""
    slots = [_parse_slot(s) for s in q_data.get("slot", [])]
    question_area = q_data.get("questionArea", [])

    return BaiduQuestionResult(
        question_id=str(q_data.get("questionId", "")),
        sequence=int(q_data.get("seqence", 0)),  # API typo "seqence"
        question_type=int(q_data.get("type", QTYPE_DEFAULT)),
        correct_result=int(q_data.get("correctResult", CORRECT_UNCHECKED)),
        is_finished=bool(q_data.get("isFinish", False)),
        question_area=question_area,
        crop_url=str(q_data.get("cropUrl", "")),
        slots=slots,
    )


def _parse_image(img_data: dict) -> BaiduImageResult:
    """Parse a single image result from the API response."""
    questions = [_parse_question(q) for q in img_data.get("result", [])]

    return BaiduImageResult(
        image_id=str(img_data.get("imageId", "")),
        image_url=str(img_data.get("imageUrl", "")),
        subject=str(img_data.get("paperSubject", "")),
        resize_ratio=float(img_data.get("resize_ratio", 1.0)),
        questions=questions,
    )


def _parse_result(data: dict) -> BaiduCorrectionResult:
    """Parse the full get_result response into structured dataclasses."""
    result = data.get("result", {})
    images = [_parse_image(img) for img in result.get("imageResults", [])]
    stat = result.get("stat_result", {})

    return BaiduCorrectionResult(
        task_id=str(result.get("task_id", "")),
        status=str(result.get("status", "")),
        is_all_finished=bool(result.get("isAllFinished", False)),
        stat_result=stat,
        images=images,
        raw=data,
    )


def _parse_split_result(data: dict) -> BaiduCorrectionResult:
    """Parse the sync split-only response (different structure from async)."""
    # Split-only mode returns questions directly, wrapped differently.
    # Build a minimal BaiduCorrectionResult from the available data.
    questions_raw = data.get("questions_result", [])

    questions = []
    for i, q in enumerate(questions_raw):
        questions.append(BaiduQuestionResult(
            question_id=str(q.get("questionId", f"split-{i}")),
            sequence=i,
            question_type=int(q.get("type", QTYPE_DEFAULT)),
            correct_result=CORRECT_UNCHECKED,  # No grading in split mode
            is_finished=True,
            question_area=q.get("questionArea", []),
            crop_url=str(q.get("cropUrl", "")),
            slots=[_parse_slot(s) for s in q.get("slot", [])],
        ))

    image = BaiduImageResult(
        image_id="split",
        image_url=str(data.get("imageUrl", "")),
        subject=str(data.get("paperSubject", "")),
        resize_ratio=float(data.get("resize_ratio", 1.0)),
        questions=questions,
    )

    return BaiduCorrectionResult(
        task_id=str(data.get("task_id", "")),
        status="Success",
        is_all_finished=True,
        stat_result={"all": len(questions), "corrected": 0, "correcting": 0},
        images=[image],
        raw=data,
    )


# ── Logging helpers ──────────────────────────────────────────────────

def _truncate_for_log(data: dict, max_len: int = 500) -> str:
    """Format a dict for logging, truncating if too long."""
    import json
    text = json.dumps(data, ensure_ascii=False)
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text

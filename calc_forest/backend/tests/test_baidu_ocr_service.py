"""Unit tests for baidu_ocr_service module.

Tests all public and key private functions with mocked HTTP calls.
No real network requests are made.
"""
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.services.baidu_ocr_service as svc
from app.services.baidu_ocr_service import (
    CORRECT_RIGHT,
    CORRECT_UNANSWERED,
    CORRECT_UNCHECKED,
    CORRECT_WRONG,
    QTYPE_CALCULATE,
    QTYPE_DEFAULT,
    BaiduCorrectionResult,
    BaiduImageResult,
    BaiduQuestionResult,
    BaiduSlotResult,
    _is_error_response,
    _parse_image,
    _parse_question,
    _parse_result,
    _parse_slot,
    _parse_split_result,
    configure,
)


# ── Helpers ────────────────────────────────────────────────────────────

def _reset_module_state():
    """Reset module-level globals to a clean state."""
    svc._api_key = "test_ak"
    svc._secret_key = "test_sk"
    svc._access_token = ""
    svc._token_expires = 0


def _make_async_client_mock(post_return_value=None):
    """Build an AsyncMock that behaves like httpx.AsyncClient context manager.

    Returns (mock_client_instance, mock_client_class) so you can:
      - mock_client_instance.post.return_value = ...
      - patch("...httpx.AsyncClient", return_value=mock_client_class)
    """
    mock_response = post_return_value or MagicMock()
    mock_response.raise_for_status = MagicMock()

    client = AsyncMock()
    client.post = AsyncMock(return_value=mock_response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    # The "class" that returns the client instance
    client_cls = MagicMock(return_value=client)
    return client, client_cls


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clean_state():
    """Reset module globals before each test."""
    _reset_module_state()
    yield
    _reset_module_state()


# ===================================================================
# A. Token Management
# ===================================================================

class TestConfigure:
    def test_configure_sets_globals(self):
        configure("my_api_key_12345678", "my_secret_key_87654321")
        assert svc._api_key == "my_api_key_12345678"
        assert svc._secret_key == "my_secret_key_87654321"


class TestEnsureToken:
    @pytest.mark.asyncio
    async def test_ensure_token_success(self):
        """Mocks httpx POST to token URL, returns access_token + expires_in."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "fake_token_abc",
            "expires_in": 2592000,
        }
        mock_response.raise_for_status = MagicMock()

        client, client_cls = _make_async_client_mock(mock_response)
        # Override because we need a specific response
        client.post = AsyncMock(return_value=mock_response)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client):
            token = await svc._ensure_token()

        assert token == "fake_token_abc"
        assert svc._access_token == "fake_token_abc"
        assert svc._token_expires > time.time()

    @pytest.mark.asyncio
    async def test_ensure_token_cached(self):
        """Second call within expiry returns cached token (no HTTP call)."""
        svc._access_token = "cached_tok"
        svc._token_expires = time.time() + 3600  # 1 hour from now

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient") as mock_cls:
            token = await svc._ensure_token()

        assert token == "cached_tok"
        mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_token_refresh(self):
        """Expired token triggers new HTTP call."""
        svc._access_token = "old_token"
        svc._token_expires = time.time() - 10  # expired

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_token_xyz",
            "expires_in": 2592000,
        }
        mock_response.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=mock_response)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client):
            token = await svc._ensure_token()

        assert token == "new_token_xyz"
        assert svc._access_token == "new_token_xyz"
        client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_token_failure(self):
        """OAuth error response raises RuntimeError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "invalid_client",
            "error_description": "Unknown client",
        }
        mock_response.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=mock_response)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client):
            with pytest.raises(RuntimeError, match="百度 OAuth2"):
                await svc._ensure_token()


# ===================================================================
# B. Error Detection
# ===================================================================

class TestIsErrorResponse:
    def test_no_code_returns_false(self):
        assert _is_error_response({}) is False

    def test_no_code_other_keys_returns_false(self):
        assert _is_error_response({"foo": "bar"}) is False

    def test_zero_int_returns_false(self):
        assert _is_error_response({"error_code": 0}) is False

    def test_zero_string_returns_false(self):
        assert _is_error_response({"error_code": "0"}) is False

    def test_nonzero_int_returns_true(self):
        assert _is_error_response({"error_code": 216201}) is True

    def test_nonzero_string_returns_true(self):
        assert _is_error_response({"error_code": "216201"}) is True

    def test_negative_int_returns_true(self):
        assert _is_error_response({"error_code": -1}) is True


# ===================================================================
# C. Result Parsing
# ===================================================================

class TestParseSlot:
    def test_parse_slot_full(self):
        data = {
            "slotId": "s1",
            "seqence": 3,  # API typo
            "correctResult": 2,
            "reason": "计算错误",
            "handwritingArea": {"left_x": 10, "left_y": 20, "right_x": 100, "right_y": 50},
        }
        slot = _parse_slot(data)
        assert slot.slot_id == "s1"
        assert slot.sequence == 3
        assert slot.correct_result == CORRECT_WRONG
        assert slot.reason == "计算错误"
        assert slot.handwriting_area == {"left_x": 10, "left_y": 20, "right_x": 100, "right_y": 50}

    def test_parse_slot_defaults(self):
        slot = _parse_slot({})
        assert slot.slot_id == ""
        assert slot.sequence == 0
        assert slot.correct_result == CORRECT_UNCHECKED
        assert slot.reason == ""
        assert slot.handwriting_area == {}

    def test_parse_slot_no_handwriting_area(self):
        slot = _parse_slot({"slotId": "s2", "correctResult": 1})
        assert slot.handwriting_area == {}
        assert slot.correct_result == CORRECT_RIGHT


class TestParseQuestion:
    def test_parse_question_with_slots(self):
        data = {
            "questionId": "q1",
            "seqence": 0,
            "type": 17,
            "correctResult": 2,
            "isFinish": True,
            "questionArea": [{"left_x": 0, "left_y": 0, "right_x": 200, "right_y": 40}],
            "cropUrl": "https://example.com/crop.png",
            "slot": [
                {"slotId": "s1", "seqence": 0, "correctResult": 1},
                {"slotId": "s2", "seqence": 1, "correctResult": 2, "reason": "进位错误"},
            ],
        }
        q = _parse_question(data)
        assert q.question_id == "q1"
        assert q.sequence == 0
        assert q.question_type == QTYPE_CALCULATE
        assert q.correct_result == CORRECT_WRONG
        assert q.is_finished is True
        assert len(q.question_area) == 1
        assert q.crop_url == "https://example.com/crop.png"
        assert len(q.slots) == 2
        assert q.slots[1].reason == "进位错误"

    def test_parse_question_defaults(self):
        q = _parse_question({})
        assert q.question_id == ""
        assert q.sequence == 0
        assert q.question_type == QTYPE_DEFAULT
        assert q.correct_result == CORRECT_UNCHECKED
        assert q.is_finished is False
        assert q.question_area == []
        assert q.crop_url == ""
        assert q.slots == []

    def test_parse_question_handles_seqence_typo(self):
        """Ensure 'seqence' (API typo) is read, not 'sequence'."""
        data = {"seqence": 5}
        q = _parse_question(data)
        assert q.sequence == 5


class TestParseImage:
    def test_parse_image_full(self):
        data = {
            "imageId": "img-001",
            "imageUrl": "https://example.com/img.png",
            "paperSubject": "math",
            "resize_ratio": 0.8,
            "result": [
                {"questionId": "q1", "seqence": 0, "correctResult": 1},
                {"questionId": "q2", "seqence": 1, "correctResult": 2},
            ],
        }
        img = _parse_image(data)
        assert img.image_id == "img-001"
        assert img.image_url == "https://example.com/img.png"
        assert img.subject == "math"
        assert img.resize_ratio == 0.8
        assert len(img.questions) == 2

    def test_parse_image_defaults(self):
        img = _parse_image({})
        assert img.image_id == ""
        assert img.image_url == ""
        assert img.subject == ""
        assert img.resize_ratio == 1.0
        assert img.questions == []

    def test_parse_image_empty_result(self):
        img = _parse_image({"imageId": "img-002", "result": []})
        assert img.questions == []


class TestParseResult:
    def test_parse_result_full(self):
        data = {
            "result": {
                "task_id": "task-123",
                "status": "Success",
                "isAllFinished": True,
                "stat_result": {"all": 5, "corrected": 5, "correcting": 0},
                "imageResults": [
                    {
                        "imageId": "img-1",
                        "paperSubject": "math",
                        "resize_ratio": 1.0,
                        "result": [
                            {"questionId": "q1", "correctResult": 1},
                        ],
                    }
                ],
            }
        }
        result = _parse_result(data)
        assert result.task_id == "task-123"
        assert result.status == "Success"
        assert result.is_all_finished is True
        assert result.stat_result == {"all": 5, "corrected": 5, "correcting": 0}
        assert len(result.images) == 1
        assert result.images[0].questions[0].correct_result == CORRECT_RIGHT
        assert result.raw == data

    def test_parse_result_empty_image_results(self):
        data = {"result": {"task_id": "t1", "status": "Success", "imageResults": []}}
        result = _parse_result(data)
        assert result.images == []

    def test_parse_result_missing_image_results(self):
        data = {"result": {"task_id": "t2", "status": "pending"}}
        result = _parse_result(data)
        assert result.images == []
        assert result.status == "pending"

    def test_parse_result_missing_result_key(self):
        data = {}
        result = _parse_result(data)
        assert result.task_id == ""
        assert result.images == []


class TestParseSplitResult:
    def test_parse_split_result(self):
        data = {
            "task_id": "split-task-1",
            "imageUrl": "https://example.com/split.png",
            "paperSubject": "math",
            "resize_ratio": 0.9,
            "questions_result": [
                {
                    "questionId": "sq1",
                    "type": 17,
                    "questionArea": [{"left_x": 0}],
                    "cropUrl": "https://example.com/c1.png",
                    "slot": [{"slotId": "ss1", "correctResult": 0}],
                },
                {
                    "questionId": "sq2",
                    "type": 4,
                },
            ],
        }
        result = _parse_split_result(data)
        assert result.task_id == "split-task-1"
        assert result.status == "Success"
        assert result.is_all_finished is True
        assert result.stat_result == {"all": 2, "corrected": 0, "correcting": 0}
        assert len(result.images) == 1
        assert result.images[0].image_id == "split"
        assert result.images[0].subject == "math"
        assert result.images[0].resize_ratio == 0.9
        assert len(result.images[0].questions) == 2
        # Split mode: correct_result always UNCHECKED
        assert result.images[0].questions[0].correct_result == CORRECT_UNCHECKED
        assert result.images[0].questions[0].slots[0].slot_id == "ss1"

    def test_parse_split_result_empty(self):
        data = {}
        result = _parse_split_result(data)
        assert result.images[0].questions == []
        assert result.stat_result["all"] == 0

    def test_parse_split_result_default_ids(self):
        """Missing questionId gets generated 'split-{i}'."""
        data = {"questions_result": [{}, {}]}
        result = _parse_split_result(data)
        assert result.images[0].questions[0].question_id == "split-0"
        assert result.images[0].questions[1].question_id == "split-1"


# ===================================================================
# D. Dataclass Properties
# ===================================================================

class TestBaiduSlotResultProperties:
    def test_is_wrong_true(self):
        s = BaiduSlotResult(correct_result=CORRECT_WRONG)
        assert s.is_wrong is True

    def test_is_wrong_false_right(self):
        s = BaiduSlotResult(correct_result=CORRECT_RIGHT)
        assert s.is_wrong is False

    def test_is_wrong_false_unchecked(self):
        s = BaiduSlotResult(correct_result=CORRECT_UNCHECKED)
        assert s.is_wrong is False

    def test_is_wrong_false_unanswered(self):
        s = BaiduSlotResult(correct_result=CORRECT_UNANSWERED)
        assert s.is_wrong is False

    def test_label(self):
        assert BaiduSlotResult(correct_result=CORRECT_RIGHT).label == "正确"
        assert BaiduSlotResult(correct_result=CORRECT_WRONG).label == "错误"
        assert BaiduSlotResult(correct_result=CORRECT_UNCHECKED).label == "未批"
        assert BaiduSlotResult(correct_result=CORRECT_UNANSWERED).label == "未作答"
        assert BaiduSlotResult(correct_result=99).label == "未知"


class TestBaiduQuestionResultProperties:
    def test_wrong_slots_filters(self):
        q = BaiduQuestionResult(slots=[
            BaiduSlotResult(slot_id="s1", correct_result=CORRECT_RIGHT),
            BaiduSlotResult(slot_id="s2", correct_result=CORRECT_WRONG),
            BaiduSlotResult(slot_id="s3", correct_result=CORRECT_WRONG),
        ])
        wrong = q.wrong_slots
        assert len(wrong) == 2
        assert wrong[0].slot_id == "s2"
        assert wrong[1].slot_id == "s3"

    def test_wrong_slots_empty(self):
        q = BaiduQuestionResult(slots=[
            BaiduSlotResult(correct_result=CORRECT_RIGHT),
        ])
        assert q.wrong_slots == []

    def test_is_wrong(self):
        assert BaiduQuestionResult(correct_result=CORRECT_WRONG).is_wrong is True
        assert BaiduQuestionResult(correct_result=CORRECT_RIGHT).is_wrong is False


class TestBaiduImageResultProperties:
    def test_total_questions(self):
        img = BaiduImageResult(questions=[
            BaiduQuestionResult(), BaiduQuestionResult(), BaiduQuestionResult(),
        ])
        assert img.total_questions == 3

    def test_total_questions_zero(self):
        img = BaiduImageResult()
        assert img.total_questions == 0

    def test_wrong_questions(self):
        img = BaiduImageResult(questions=[
            BaiduQuestionResult(question_id="q1", correct_result=CORRECT_RIGHT),
            BaiduQuestionResult(question_id="q2", correct_result=CORRECT_WRONG),
            BaiduQuestionResult(question_id="q3", correct_result=CORRECT_WRONG),
        ])
        wrong = img.wrong_questions
        assert len(wrong) == 2
        assert wrong[0].question_id == "q2"


class TestBaiduCorrectionResultProperties:
    def test_is_success_true(self):
        r = BaiduCorrectionResult(status="Success")
        assert r.is_success is True

    def test_is_success_false(self):
        for status in ["pending", "running", "Failed", ""]:
            r = BaiduCorrectionResult(status=status)
            assert r.is_success is False

    def test_total_questions(self):
        r = BaiduCorrectionResult(images=[
            BaiduImageResult(questions=[BaiduQuestionResult(), BaiduQuestionResult()]),
            BaiduImageResult(questions=[BaiduQuestionResult()]),
        ])
        assert r.total_questions == 3

    def test_total_wrong(self):
        r = BaiduCorrectionResult(images=[
            BaiduImageResult(questions=[
                BaiduQuestionResult(correct_result=CORRECT_RIGHT),
                BaiduQuestionResult(correct_result=CORRECT_WRONG),
            ]),
            BaiduImageResult(questions=[
                BaiduQuestionResult(correct_result=CORRECT_WRONG),
            ]),
        ])
        assert r.total_wrong == 2

    def test_all_wrong_questions(self):
        r = BaiduCorrectionResult(images=[
            BaiduImageResult(questions=[
                BaiduQuestionResult(question_id="q1", correct_result=CORRECT_WRONG),
            ]),
            BaiduImageResult(questions=[
                BaiduQuestionResult(question_id="q2", correct_result=CORRECT_WRONG),
                BaiduQuestionResult(question_id="q3", correct_result=CORRECT_RIGHT),
            ]),
        ])
        wrong = r.all_wrong_questions
        assert len(wrong) == 2
        assert wrong[0].question_id == "q1"
        assert wrong[1].question_id == "q2"


# ===================================================================
# E. correct_homework (main function)
# ===================================================================

def _mock_token():
    """Pre-set a valid cached token so _ensure_token is a no-op."""
    svc._access_token = "pre_cached_token"
    svc._token_expires = time.time() + 3600


class TestCorrectHomework:
    @pytest.mark.asyncio
    async def test_async_success(self):
        """Mocks create_task (returns task_id) + poll_result (returns Success)."""
        _mock_token()

        # First call: create_task → returns task_id
        create_resp = MagicMock()
        create_resp.json.return_value = {"task_id": "task-xyz"}
        create_resp.raise_for_status = MagicMock()

        # We'll mock _poll_result directly to avoid complex polling setup
        fake_result = BaiduCorrectionResult(
            task_id="task-xyz",
            status="Success",
            is_all_finished=True,
            images=[BaiduImageResult(
                image_id="img-1",
                questions=[BaiduQuestionResult(question_id="q1", correct_result=CORRECT_RIGHT)],
            )],
        )

        client = AsyncMock()
        client.post = AsyncMock(return_value=create_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client), \
             patch("app.services.baidu_ocr_service._poll_result", return_value=fake_result):
            result = await svc.correct_homework(b"fake_image_bytes")

        assert result.task_id == "task-xyz"
        assert result.is_success is True
        assert result.total_questions == 1

    @pytest.mark.asyncio
    async def test_async_timeout(self):
        """get_result never returns Success → TimeoutError."""
        _mock_token()

        create_resp = MagicMock()
        create_resp.json.return_value = {"task_id": "task-timeout"}
        create_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=create_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client), \
             patch("app.services.baidu_ocr_service._poll_result",
                   side_effect=TimeoutError("百度 OCR 任务 task-timeout 超时")):
            with pytest.raises(TimeoutError, match="超时"):
                await svc.correct_homework(b"fake_image_bytes")

    @pytest.mark.asyncio
    async def test_async_failed(self):
        """get_result returns status='Failed' → RuntimeError from poll."""
        _mock_token()

        create_resp = MagicMock()
        create_resp.json.return_value = {"task_id": "task-fail"}
        create_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=create_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client), \
             patch("app.services.baidu_ocr_service._poll_result",
                   side_effect=RuntimeError("百度 OCR 任务 task-fail 失败")):
            with pytest.raises(RuntimeError, match="失败"):
                await svc.correct_homework(b"fake_image_bytes")

    @pytest.mark.asyncio
    async def test_create_error(self):
        """create_task returns error_code=216201 → RuntimeError."""
        _mock_token()

        create_resp = MagicMock()
        create_resp.json.return_value = {
            "error_code": 216201,
            "error_msg": "image quality too low",
        }
        create_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=create_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client):
            with pytest.raises(RuntimeError, match="216201"):
                await svc.correct_homework(b"bad_image_bytes")

    @pytest.mark.asyncio
    async def test_split_mode(self):
        """only_split=True returns immediately without polling."""
        _mock_token()

        split_resp = MagicMock()
        split_resp.json.return_value = {
            "questions_result": [
                {"questionId": "sq1", "type": 17},
            ],
        }
        split_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=split_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client):
            result = await svc.correct_homework(b"image_bytes", only_split=True)

        assert result.status == "Success"
        assert len(result.images[0].questions) == 1

    @pytest.mark.asyncio
    async def test_task_id_nested_in_result(self):
        """task_id can be nested inside result dict."""
        _mock_token()

        create_resp = MagicMock()
        create_resp.json.return_value = {"result": {"task_id": "nested-task-1"}}
        create_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=create_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        fake_result = BaiduCorrectionResult(task_id="nested-task-1", status="Success")

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client), \
             patch("app.services.baidu_ocr_service._poll_result", return_value=fake_result) as mock_poll:
            result = await svc.correct_homework(b"img")

        mock_poll.assert_called_once_with("nested-task-1")

    @pytest.mark.asyncio
    async def test_no_task_id_raises(self):
        """If no task_id is found, raises RuntimeError."""
        _mock_token()

        create_resp = MagicMock()
        create_resp.json.return_value = {"foo": "bar"}  # no task_id
        create_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=create_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client):
            with pytest.raises(RuntimeError, match="未返回 task_id"):
                await svc.correct_homework(b"img")


class TestCorrectHomeworkFromPath:
    @pytest.mark.asyncio
    async def test_from_path_success(self):
        """Reads file and calls correct_homework."""
        fake_result = BaiduCorrectionResult(status="Success")

        with patch("app.services.baidu_ocr_service.correct_homework",
                   return_value=fake_result) as mock_ch, \
             patch("app.services.baidu_ocr_service.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.read_bytes.return_value = b"file_image_data"
            mock_path_cls.return_value = mock_path

            result = await svc.correct_homework_from_path("/fake/path/img.png")

        mock_ch.assert_called_once_with(b"file_image_data")
        assert result.status == "Success"

    @pytest.mark.asyncio
    async def test_from_path_missing(self):
        """FileNotFoundError for missing file."""
        with patch("app.services.baidu_ocr_service.Path") as mock_path_cls:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path_cls.return_value = mock_path

            with pytest.raises(FileNotFoundError, match="Image file not found"):
                await svc.correct_homework_from_path("/nonexistent/img.png")


# ===================================================================
# F. Polling
# ===================================================================

class TestPollResult:
    @pytest.mark.asyncio
    async def test_success_first_poll(self):
        """Immediate success on first poll."""
        _mock_token()

        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "result": {
                "task_id": "t1",
                "status": "Success",
                "isAllFinished": True,
                "stat_result": {"all": 1, "corrected": 1, "correcting": 0},
                "imageResults": [],
            }
        }
        poll_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=poll_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client), \
             patch("app.services.baidu_ocr_service.asyncio.sleep", new_callable=AsyncMock):
            result = await svc._poll_result("t1")

        assert result.is_success is True
        assert result.task_id == "t1"

    @pytest.mark.asyncio
    async def test_success_after_pending(self):
        """First returns pending, second returns Success."""
        _mock_token()

        pending_resp = MagicMock()
        pending_resp.json.return_value = {
            "result": {
                "task_id": "t2",
                "status": "pending",
                "isAllFinished": False,
            }
        }
        pending_resp.raise_for_status = MagicMock()

        success_resp = MagicMock()
        success_resp.json.return_value = {
            "result": {
                "task_id": "t2",
                "status": "Success",
                "isAllFinished": True,
                "stat_result": {},
                "imageResults": [],
            }
        }
        success_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(side_effect=[pending_resp, success_resp])
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        call_count = 0

        async def fake_sleep(_seconds):
            nonlocal call_count
            call_count += 1

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client), \
             patch("app.services.baidu_ocr_service.asyncio.sleep", side_effect=fake_sleep):
            result = await svc._poll_result("t2")

        assert result.is_success is True
        assert client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_poll_api_error_raises(self):
        """API error in poll response raises RuntimeError."""
        _mock_token()

        error_resp = MagicMock()
        error_resp.json.return_value = {
            "error_code": 18,
            "error_msg": "QPS limit reached",
        }
        error_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=error_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client), \
             patch("app.services.baidu_ocr_service.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="18"):
                await svc._poll_result("t3")

    @pytest.mark.asyncio
    async def test_poll_failed_status_raises(self):
        """Status='Failed' raises RuntimeError."""
        _mock_token()

        failed_resp = MagicMock()
        failed_resp.json.return_value = {
            "result": {
                "task_id": "t4",
                "status": "Failed",
            }
        }
        failed_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=failed_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client), \
             patch("app.services.baidu_ocr_service.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="失败"):
                await svc._poll_result("t4")

    @pytest.mark.asyncio
    async def test_poll_timeout(self):
        """Polling exceeds max_wait → TimeoutError."""
        _mock_token()

        pending_resp = MagicMock()
        pending_resp.json.return_value = {
            "result": {"task_id": "t5", "status": "running"},
        }
        pending_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.post = AsyncMock(return_value=pending_resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        # Mock time.time to simulate timeout: first call starts timer,
        # subsequent calls return values that exceed max_wait
        call_count = [0]
        original_time = time.time

        def fake_time():
            call_count[0] += 1
            if call_count[0] <= 1:
                return original_time()
            return original_time() + 100  # way past max_wait=1

        with patch("app.services.baidu_ocr_service.httpx.AsyncClient", return_value=client), \
             patch("app.services.baidu_ocr_service.asyncio.sleep", new_callable=AsyncMock), \
             patch("app.services.baidu_ocr_service.time.time", side_effect=fake_time):
            with pytest.raises(TimeoutError, match="超时"):
                await svc._poll_result("t5", max_wait=1)


# ===================================================================
# G. Logging helpers
# ===================================================================

class TestTruncateForLog:
    def test_short_dict(self):
        result = svc._truncate_for_log({"a": 1})
        assert '"a": 1' in result
        assert "..." not in result

    def test_long_dict_truncated(self):
        big = {"key": "x" * 1000}
        result = svc._truncate_for_log(big, max_len=50)
        assert result.endswith("...")
        assert len(result) <= 60  # 50 + "..."

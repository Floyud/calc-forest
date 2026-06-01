"""Deep multi-turn conversation tests for /api/dify/chat (树精灵引导).

Tests the full guidance chat flow including:
- Single message round-trip
- Multi-turn with context retention
- Student context injection
- Conversation ID handling
- Error recovery
- Guidance quality (no answer leakage)
"""

from __future__ import annotations

import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure .env is loaded for tests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@pytest.fixture
def app():
    from app.main import app
    return app


# ---------------------------------------------------------------------------
# Mock LLM responses for deterministic testing
# ---------------------------------------------------------------------------

def _mock_llm_response(text: str) -> dict:
    return {
        "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
    }


# ---------------------------------------------------------------------------
# Test 1: Single message round-trip via LLM track
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_single_message_llm_track(app):
    """Single message should return a valid answer via LLM track."""
    mock_response = _mock_llm_response(
        "你好呀！我是树精灵 🌳 很高兴认识你！有什么计算题想和我一起探索吗？"
    )

    with patch("app.services.llm_client.call_deepseek", new_callable=AsyncMock) as mock_llm:
        # Force Dify key to empty so we hit LLM track
        with patch.dict(os.environ, {"DIFY_WORKFLOW_GUIDANCE_KEY": "", "LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY": ""}):
            mock_llm.return_value = mock_response

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/api/dify/chat", json={
                    "query": "你好",
                    "user": "student-test-001",
                    "inputs": {},
                    "conversation_id": "",
                })

    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "conversation_id" in data
    mock_llm.assert_called_once()


# ---------------------------------------------------------------------------
# Test 2: Multi-turn WITHOUT history — exposes the bug
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multiturn_without_history_loses_context(app):
    """Without history, LLM track cannot recall previous turns.

    This test documents the CURRENT behavior: the LLM receives only
    the latest user message, so it has no memory of prior turns.
    The system prompt is included each time.
    """

    turn1_response = _mock_llm_response("2/3 + 1/6 呢，先想想分母怎么变成一样？")
    turn2_response = _mock_llm_response("好的，那我们来看看 2/3 怎么变成以 6 为分母的分数。")

    with patch("app.services.llm_client.call_deepseek", new_callable=AsyncMock) as mock_llm:
        with patch.dict(os.environ, {"DIFY_WORKFLOW_GUIDANCE_KEY": "", "LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY": ""}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Turn 1
                mock_llm.return_value = turn1_response
                resp1 = await client.post("/api/dify/chat", json={
                    "query": "2/3 + 1/6 等于多少？",
                    "user": "student-test-002",
                    "inputs": {},
                    "conversation_id": "",
                })
                assert resp1.status_code == 200
                data1 = resp1.json()
                conv_id = data1.get("conversation_id", "")

                # Turn 2 — reference previous turn context
                mock_llm.return_value = turn2_response
                resp2 = await client.post("/api/dify/chat", json={
                    "query": "通分之后呢？",
                    "user": "student-test-002",
                    "inputs": {},
                    "conversation_id": conv_id,
                })
                assert resp2.status_code == 200

    # The LLM was called twice — but with only 2 messages each time (system + user)
    assert mock_llm.call_count == 2

    # Inspect the messages sent to the LLM on turn 2
    turn2_call_args = mock_llm.call_args_list[1]
    messages_sent = turn2_call_args.kwargs.get("messages") or turn2_call_args[1].get("messages") or turn2_call_args[0][0]

    # BUG: Only system + current user message, NO history
    user_messages = [m for m in messages_sent if m["role"] == "user"]
    assert len(user_messages) == 1, "LLM track sends only 1 user message (no history)"
    assert user_messages[0]["content"] == "通分之后呢？"


# ---------------------------------------------------------------------------
# Test 3: Multi-turn WITH history — the fix target
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multiturn_with_history_carries_context(app):
    """When frontend sends history, LLM should receive full conversation.

    This tests the DESIRED behavior: the frontend sends chat history
    and the backend builds a complete messages array for the LLM.
    """

    turn2_response = _mock_llm_response(
        "你已经知道 2/3 = 4/6 了，那 4/6 + 1/6 等于多少呢？"
    )

    with patch("app.services.llm_client.call_deepseek", new_callable=AsyncMock) as mock_llm:
        with patch.dict(os.environ, {"DIFY_WORKFLOW_GUIDANCE_KEY": "", "LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY": ""}):
            mock_llm.return_value = turn2_response

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/api/dify/chat", json={
                    "query": "通分之后呢？",
                    "user": "student-test-003",
                    "inputs": {},
                    "conversation_id": "conv-abc-123",
                    "history": [
                        {"role": "user", "content": "2/3 + 1/6 等于多少？"},
                        {"role": "bot", "content": "2/3 + 1/6 呢，先想想分母怎么变成一样？"},
                    ],
                })

    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data

    # Verify the LLM received full history
    call_args = mock_llm.call_args
    messages_sent = call_args.kwargs.get("messages") or call_args[0][0]

    # Should have: system + history(2) + current user = 4 messages
    assert len(messages_sent) == 4, (
        f"Expected 4 messages (system + 2 history + 1 current), got {len(messages_sent)}"
    )
    assert messages_sent[0]["role"] == "system"
    assert messages_sent[1]["role"] == "user"
    assert messages_sent[1]["content"] == "2/3 + 1/6 等于多少？"
    assert messages_sent[2]["role"] == "assistant"
    assert messages_sent[2]["content"] == "2/3 + 1/6 呢，先想想分母怎么变成一样？"
    assert messages_sent[3]["role"] == "user"
    assert messages_sent[3]["content"] == "通分之后呢？"


# ---------------------------------------------------------------------------
# Test 4: Student context injection on first message
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_context_injected_on_first_message(app):
    """Student context should appear in system prompt on first turn."""

    mock_response = _mock_llm_response("我看到你最近在练习分数加法，加油！")

    with patch("app.services.llm_client.call_deepseek", new_callable=AsyncMock) as mock_llm:
        with patch.dict(os.environ, {"DIFY_WORKFLOW_GUIDANCE_KEY": "", "LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY": ""}):
            mock_llm.return_value = mock_response

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/api/dify/chat", json={
                    "query": "你好",
                    "user": "student-test-004",
                    "inputs": {
                        "student_context": "六年级，最近错因：E-K02（通分错误），正确率 60%",
                    },
                    "conversation_id": "",
                })

    assert resp.status_code == 200
    messages_sent = mock_llm.call_args.kwargs.get("messages") or mock_llm.call_args[0][0]
    system_msg = messages_sent[0]["content"]
    assert "E-K02" in system_msg
    assert "通分错误" in system_msg


# ---------------------------------------------------------------------------
# Test 5: Conversation ID generation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_conversation_id_generated_when_empty(app):
    """LLM track should generate a conversation_id if none provided."""

    mock_response = _mock_llm_response("好的，让我来帮你！")

    with patch("app.services.llm_client.call_deepseek", new_callable=AsyncMock) as mock_llm:
        with patch.dict(os.environ, {"DIFY_WORKFLOW_GUIDANCE_KEY": "", "LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY": ""}):
            mock_llm.return_value = mock_response

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/api/dify/chat", json={
                    "query": "3/4 × 2/5",
                    "user": "student-test-005",
                    "inputs": {},
                    "conversation_id": "",
                })

    data = resp.json()
    assert data["conversation_id"], "LLM track should return a conversation_id"


# ---------------------------------------------------------------------------
# Test 6: Empty query handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_query_handled_gracefully(app):
    """Empty query should not crash the endpoint."""

    with patch("app.services.llm_client.call_deepseek", new_callable=AsyncMock) as mock_llm:
        with patch.dict(os.environ, {"DIFY_WORKFLOW_GUIDANCE_KEY": "", "LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY": ""}):
            mock_llm.return_value = _mock_llm_response("你想问什么呢？")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/api/dify/chat", json={
                    "query": "",
                    "user": "student-test-006",
                    "inputs": {},
                    "conversation_id": "",
                })

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Test 7: LLM failure returns friendly error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_llm_failure_returns_friendly_error(app):
    """When LLM call fails, return friendly message, not stack trace."""

    with patch("app.services.llm_client.call_deepseek", new_callable=AsyncMock) as mock_llm:
        with patch.dict(os.environ, {"DIFY_WORKFLOW_GUIDANCE_KEY": "", "LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY": ""}):
            mock_llm.side_effect = RuntimeError("LLM 服务不可用")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/api/dify/chat", json={
                    "query": "你好",
                    "user": "student-test-007",
                    "inputs": {},
                    "conversation_id": "",
                })

    assert resp.status_code == 200
    data = resp.json()
    assert "离线" in data["answer"] or "稍后" in data["answer"]


# ---------------------------------------------------------------------------
# Test 8: Long conversation (5+ turns) with history
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_long_conversation_with_full_history(app):
    """5-turn conversation should carry full context through."""

    responses = [
        _mock_llm_response("先看看 1/2 + 1/3 的分母怎么统一？"),
        _mock_llm_response("对，最小公倍数是 6！那 1/2 变成什么？"),
        _mock_llm_response("很好！那 1/3 呢？"),
        _mock_llm_response("对了！那 3/6 + 2/6 等于？"),
        _mock_llm_response("太棒了！5/6 就是最简分数了 🎉"),
    ]

    history: list[dict] = []

    with patch("app.services.llm_client.call_deepseek", new_callable=AsyncMock) as mock_llm:
        with patch.dict(os.environ, {"DIFY_WORKFLOW_GUIDANCE_KEY": "", "LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY": ""}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                queries = [
                    "1/2 + 1/3",
                    "6?",
                    "1/2 = 3/6",
                    "1/3 = 2/6",
                    "3/6 + 2/6 = 5/6",
                ]

                for i, (query, resp_text) in enumerate(zip(queries, responses)):
                    mock_llm.return_value = resp_text
                    resp = await client.post("/api/dify/chat", json={
                        "query": query,
                        "user": "student-test-008",
                        "inputs": {},
                        "conversation_id": "conv-long-test",
                        "history": history.copy(),
                    })
                    assert resp.status_code == 200
                    data = resp.json()

                    # Verify message count: system + history + current
                    call_messages = mock_llm.call_args.kwargs.get("messages") or mock_llm.call_args[0][0]
                    expected_count = 1 + len(history) + 1  # system + history + current
                    assert len(call_messages) == expected_count, (
                        f"Turn {i+1}: expected {expected_count} messages, got {len(call_messages)}"
                    )

                    # Update history for next turn
                    history.append({"role": "user", "content": query})
                    history.append({"role": "bot", "content": data["answer"]})


# ---------------------------------------------------------------------------
# Test 9: History with bot role maps to assistant role for LLM
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_history_role_mapping_bot_to_assistant(app):
    """Frontend 'bot' role should be mapped to 'assistant' for LLM API."""

    with patch("app.services.llm_client.call_deepseek", new_callable=AsyncMock) as mock_llm:
        with patch.dict(os.environ, {"DIFY_WORKFLOW_GUIDANCE_KEY": "", "LOCAL_DIFY_WORKFLOW_GUIDANCE_KEY": ""}):
            mock_llm.return_value = _mock_llm_response("继续加油！")

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post("/api/dify/chat", json={
                    "query": "然后呢？",
                    "user": "student-test-009",
                    "inputs": {},
                    "conversation_id": "conv-role-test",
                    "history": [
                        {"role": "user", "content": "1+1=?"},
                        {"role": "bot", "content": "你觉得呢？"},
                    ],
                })

    messages_sent = mock_llm.call_args.kwargs.get("messages") or mock_llm.call_args[0][0]
    roles = [m["role"] for m in messages_sent]
    assert "bot" not in roles, "'bot' role should be mapped to 'assistant'"
    assert roles == ["system", "user", "assistant", "user"]

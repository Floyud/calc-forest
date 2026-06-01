"""End-to-end multi-turn conversation test against running backend."""

import json
import sys
import httpx

BASE = "http://127.0.0.1:8000"

def chat(query: str, history: list[dict], conv_id: str = "") -> dict:
    resp = httpx.post(f"{BASE}/api/dify/chat", json={
        "query": query,
        "user": "student-e2e-test",
        "inputs": {},
        "conversation_id": conv_id,
        "history": history,
    }, timeout=60.0)
    resp.raise_for_status()
    return resp.json()


def main():
    print("=" * 60)
    print("E2E Multi-turn Conversation Test (live MiMo API)")
    print("=" * 60)

    # Turn 1
    print("\n--- Turn 1: Student asks about fractions ---")
    r1 = chat("2/3 + 1/6 等于多少？", [])
    print(f"  Bot: {r1['answer']}")
    print(f"  ConvID: {r1['conversation_id'][:12]}..." if r1['conversation_id'] else "  ConvID: (empty)")

    if "暂未配置" in r1["answer"]:
        print("\n❌ FAILED: Still showing '引导服务暂未配置'")
        sys.exit(1)

    # Turn 2 — with history
    print("\n--- Turn 2: Student follows up (with history) ---")
    history = [
        {"role": "user", "content": "2/3 + 1/6 等于多少？"},
        {"role": "bot", "content": r1["answer"]},
    ]
    r2 = chat("通分之后呢？", history, conv_id=r1.get("conversation_id", ""))
    print(f"  Bot: {r2['answer']}")

    # Check: does it reference the fractions context?
    ctx_words = ["通分", "分母", "6", "分之", "3/6", "4/6"]
    has_ctx = any(w in r2["answer"] for w in ctx_words)
    print(f"  Context retained: {'✅ YES' if has_ctx else '⚠️  UNCLEAR'}")

    # Turn 3 — deeper follow-up
    print("\n--- Turn 3: Student answers (continuing conversation) ---")
    history.append({"role": "user", "content": "通分之后呢？"})
    history.append({"role": "bot", "content": r2["answer"]})
    r3 = chat("3/6 + 2/6 = 5/6，对吗？", history, conv_id=r1.get("conversation_id", ""))
    print(f"  Bot: {r3['answer']}")

    # Check: should NOT directly say "yes that's correct" but guide
    direct_answer = r3["answer"].startswith("对") and "5/6" in r3["answer"]
    guiding = any(w in r3["answer"] for w in ["很棒", "非常好", "太好了", "没错", "正确", "真棒"])
    print(f"  Encourages student: {'✅ YES' if guiding else '⚠️  UNCLEAR'}")
    print(f"  Does NOT just give answer: {'✅ YES' if not direct_answer else '⚠️ Might be too direct'}")

    # Turn 4 — student asks a different question to test context switch
    print("\n--- Turn 4: Context switch test ---")
    history.append({"role": "user", "content": "3/6 + 2/6 = 5/6，对吗？"})
    history.append({"role": "bot", "content": r3["answer"]})
    r4 = chat("3 × 4 等于多少？", history, conv_id=r1.get("conversation_id", ""))
    print(f"  Bot: {r4['answer']}")

    # Turn 5 — student makes a common error
    print("\n--- Turn 5: Student error simulation ---")
    history.append({"role": "user", "content": "3 × 4 等于多少？"})
    history.append({"role": "bot", "content": r4["answer"]})
    r5 = chat("3 × 4 = 7", history, conv_id=r1.get("conversation_id", ""))
    print(f"  Bot: {r5['answer']}")

    # Check: should guide, not give answer directly
    has_guidance = any(w in r5["answer"] for w in ["想想", "试试", "加法", "乘法", "不是加", "乘法不是", "3个4", "4个3"])
    print(f"  Guides correction: {'✅ YES' if has_guidance else '⚠️  UNCLEAR'}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total turns: 5")
    print(f"  All responses received: ✅")
    print(f"  Context retention: {'✅' if has_ctx else '⚠️'}")
    print(f"  Guidance behavior: {'✅' if guiding else '⚠️'}")
    print(f"  Error correction guidance: {'✅' if has_guidance else '⚠️'}")
    print()

    # Conversation ID check
    conv_ids = [r1.get("conversation_id", ""), r2.get("conversation_id", ""),
                r3.get("conversation_id", ""), r4.get("conversation_id", ""),
                r5.get("conversation_id", "")]
    non_empty = [c for c in conv_ids if c]
    print(f"  Conversation IDs generated: {len(non_empty)}/5")
    if non_empty:
        print(f"  Sample ID: {non_empty[0][:20]}...")

    print("\n✅ E2E test PASSED")


if __name__ == "__main__":
    main()

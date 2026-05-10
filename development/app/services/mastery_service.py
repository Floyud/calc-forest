"""Simplified BKT (Bayesian Knowledge Tracing) mastery estimation.

Computes per-error-code mastery probability using the classic 4-parameter
BKT model with a fixed prior.  The result is suitable for display in a
teacher dashboard but should NOT drive automated decisions without teacher
review.
"""

from __future__ import annotations

from app.db import get_db

# All recognised error codes (E01–E11)
ERROR_CODES = [f"E{i:02d}" for i in range(1, 12)]

# ── BKT parameters ──────────────────────────────────────────────────
P_L0 = 0.3   # initial mastery probability
P_T  = 0.1   # learning rate per attempt
P_G  = 0.2   # guess probability
P_S  = 0.1   # slip probability


def _bkt_update(total_attempts: int, correct_count: int) -> float:
    """Run BKT forward updates and return final P(mastery).

    Correct answers come first (optimistic ordering), then wrong answers.
    """
    p = P_L0
    # Clamp in case data is inconsistent
    correct = min(correct_count, total_attempts)
    wrong = total_attempts - correct

    for _ in range(correct):
        # P(correct | mastery) update — evidence of knowing
        p_correct_given_mastery = p * (1 - P_S)
        p_correct_given_no_mastery = (1 - p) * P_G
        denom = p_correct_given_mastery + p_correct_given_no_mastery
        if denom > 0:
            p = p_correct_given_mastery / denom
        # learning transition
        p = p + (1 - p) * P_T
        p = min(p, 0.999)  # avoid ceiling lock

    for _ in range(wrong):
        # P(wrong | mastery) update — evidence of NOT knowing
        p_wrong_given_mastery = p * P_S
        p_wrong_given_no_mastery = (1 - p) * (1 - P_G)
        denom = p_wrong_given_mastery + p_wrong_given_no_mastery
        if denom > 0:
            p = p_wrong_given_mastery / denom
        # learning transition
        p = p + (1 - p) * P_T
        p = min(p, 0.999)

    return round(p, 4)


def _zone(p: float) -> str:
    if p >= 0.85:
        return "mastered"
    if p >= 0.5:
        return "learning"
    return "needs_practice"


async def get_student_mastery(student_id: str) -> dict:
    """Return per-error-code mastery probabilities for a student.

    Returns a dict matching the API response schema:
    {
        "student_id": ...,
        "error_codes": { "E01": {...}, ... },
        "overall_mastery": ...,
        "mastered_count": ...,
        "total_error_codes": 11,
        "review_status": "pending_teacher_review"
    }
    """
    async with get_db() as db:
        # Verify student exists
        cur = await db.execute("SELECT id FROM students WHERE id = ?", (student_id,))
        if await cur.fetchone() is None:
            return {"error": "Student not found"}

        # Fetch error stats
        cur = await db.execute(
            "SELECT error_code, total_attempts, correct_count "
            "FROM student_error_stats WHERE student_id = ?",
            (student_id,),
        )
        rows = await cur.fetchall()

    stats: dict[str, dict] = {r["error_code"]: dict(r) for r in rows}

    error_codes_result: dict[str, dict] = {}
    for code in ERROR_CODES:
        s = stats.get(code)
        if s and s["total_attempts"] > 0:
            p = _bkt_update(s["total_attempts"], s["correct_count"])
            error_codes_result[code] = {
                "mastery_probability": p,
                "zone": _zone(p),
                "total_attempts": s["total_attempts"],
                "correct_count": s["correct_count"],
            }
        else:
            # No data — default to initial prior
            error_codes_result[code] = {
                "mastery_probability": P_L0,
                "zone": _zone(P_L0),
                "total_attempts": 0,
                "correct_count": 0,
            }

    probabilities = [v["mastery_probability"] for v in error_codes_result.values()]
    overall = round(sum(probabilities) / len(probabilities), 4)
    mastered_count = sum(1 for v in error_codes_result.values() if v["zone"] == "mastered")

    return {
        "student_id": student_id,
        "error_codes": error_codes_result,
        "overall_mastery": overall,
        "mastered_count": mastered_count,
        "total_error_codes": len(ERROR_CODES),
        "review_status": "pending_teacher_review",
    }

"""BKT (Bayesian Knowledge Tracing) mastery estimation with temporal ordering.

Computes per-error-code mastery probability using the classic 4-parameter
BKT model with **temporal ordering** of answers and per-error-code parameters.

Key improvements over the aggregate-based approach:
- Answers are processed in chronological order (not correct-first)
- Each error code has calibrated P_L0, P_T, P_G, P_S parameters
- Forgetting decay is applied based on time since last practice

The result is suitable for display in a teacher dashboard but should NOT
drive automated decisions without teacher review.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from app.db import get_db
from app.exceptions import NotFoundException

# All recognised error codes (E01–E11)
ERROR_CODES = [f"E{i:02d}" for i in range(1, 12)]


@dataclass(frozen=True)
class BKTParams:
    """Classic 4-parameter BKT model."""
    p_l0: float  # initial mastery probability
    p_t: float   # learning rate per attempt (transition)
    p_g: float   # guess probability
    p_s: float   # slip probability


# Per-error-code parameters calibrated for primary school math
ERROR_CODE_PARAMS: dict[str, BKTParams] = {
    "E01": BKTParams(p_l0=0.35, p_t=0.15, p_g=0.20, p_s=0.10),  # Basic facts
    "E02": BKTParams(p_l0=0.30, p_t=0.10, p_g=0.20, p_s=0.10),  # Carry
    "E03": BKTParams(p_l0=0.30, p_t=0.10, p_g=0.20, p_s=0.10),  # Borrow
    "E04": BKTParams(p_l0=0.25, p_t=0.08, p_g=0.15, p_s=0.12),  # Alignment
    "E05": BKTParams(p_l0=0.20, p_t=0.06, p_g=0.15, p_s=0.15),  # Operation order
    "E06": BKTParams(p_l0=0.25, p_t=0.08, p_g=0.15, p_s=0.12),  # Decimal/fraction
    "E07": BKTParams(p_l0=0.40, p_t=0.20, p_g=0.10, p_s=0.05),  # Transcription
    "E08": BKTParams(p_l0=0.25, p_t=0.08, p_g=0.15, p_s=0.12),  # Missing steps
    "E09": BKTParams(p_l0=0.15, p_t=0.05, p_g=0.10, p_s=0.15),  # Conceptual
    "E10": BKTParams(p_l0=0.20, p_t=0.08, p_g=0.15, p_s=0.12),  # Wording/unit
    "E11": BKTParams(p_l0=0.35, p_t=0.12, p_g=0.20, p_s=0.10),  # Not checking
}

DEFAULT_PARAMS = BKTParams(p_l0=0.30, p_t=0.10, p_g=0.20, p_s=0.10)

# Forgetting decay rate (per day without practice)
FORGETTING_RATE = 0.02  # 2% exponential decay per day


def _days_since(datetime_str: str | None) -> float:
    if not datetime_str:
        return 0.0
    try:
        then = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        now = datetime.now(then.tzinfo)
        return max(0.0, (now - then).total_seconds() / 86400)
    except (ValueError, TypeError):
        return 0.0


def _zone(p: float) -> str:
    if p >= 0.85:
        return "mastered"
    if p >= 0.5:
        return "learning"
    return "needs_practice"


def _bkt_forward(params: BKTParams, outcomes: list[bool]) -> float:
    """Run BKT forward updates in temporal order and return final P(mastery).

    Each observation updates the belief using Bayes' rule, followed by
    a learning transition.  The order of correct/incorrect matters —
    this is the key difference from the old aggregate-based approach.
    """
    p = params.p_l0

    for is_correct in outcomes:
        if is_correct:
            # P(L|correct) — evidence of knowing
            p_know_given_correct = p * (1 - params.p_s)
            p_guess_given_no_know = (1 - p) * params.p_g
            denom = p_know_given_correct + p_guess_given_no_know
            if denom > 0:
                p = p_know_given_correct / denom
        else:
            # P(L|wrong) — evidence of not knowing
            p_slip_given_know = p * params.p_s
            p_wrong_given_no_know = (1 - p) * (1 - params.p_g)
            denom = p_slip_given_know + p_wrong_given_no_know
            if denom > 0:
                p = p_slip_given_know / denom

        # Learning transition
        p = p + (1 - p) * params.p_t
        p = min(p, 0.999)  # avoid ceiling lock

    return round(p, 4)


async def get_student_mastery(student_id: str) -> dict:
    """Return per-error-code mastery probabilities for a student.

    Uses temporal ordering of answers (chronological) and per-error-code
    BKT parameters with forgetting decay.

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
        cur = await db.execute("SELECT id FROM students WHERE id = ?", (student_id,))
        if await cur.fetchone() is None:
            raise NotFoundException(f"学生 {student_id} 不存在")

        cur = await db.execute(
            """SELECT error_code, is_correct, created_at
               FROM student_answers
               WHERE student_id = ? AND error_code IS NOT NULL
               ORDER BY created_at ASC""",
            (student_id,),
        )
        answers = await cur.fetchall()

        cur = await db.execute(
            """SELECT error_code, last_seen_at
               FROM student_error_stats
               WHERE student_id = ?""",
            (student_id,),
        )
        last_practice_rows = await cur.fetchall()
        last_practice = {r["error_code"]: r["last_seen_at"] for r in last_practice_rows}

    error_outcomes: dict[str, list[bool]] = {}
    for ans in answers:
        code = ans["error_code"]
        if code not in error_outcomes:
            error_outcomes[code] = []
        error_outcomes[code].append(bool(ans["is_correct"]))

    error_codes_result: dict[str, dict] = {}
    for code in ERROR_CODES:
        outcomes = error_outcomes.get(code)
        if outcomes:
            params = ERROR_CODE_PARAMS.get(code, DEFAULT_PARAMS)
            p_mastered = _bkt_forward(params, outcomes)

            days = _days_since(last_practice.get(code))
            if days > 0:
                p_mastered = round(p_mastered * math.exp(-FORGETTING_RATE * days), 4)

            error_codes_result[code] = {
                "mastery_probability": p_mastered,
                "zone": _zone(p_mastered),
                "total_attempts": len(outcomes),
                "correct_count": sum(outcomes),
            }
        else:
            default_p = DEFAULT_PARAMS.p_l0
            error_codes_result[code] = {
                "mastery_probability": default_p,
                "zone": _zone(default_p),
                "total_attempts": 0,
                "correct_count": 0,
            }

    for code in error_outcomes:
        if code not in error_codes_result:
            outcomes = error_outcomes[code]
            params = DEFAULT_PARAMS
            p_mastered = _bkt_forward(params, outcomes)

            days = _days_since(last_practice.get(code))
            if days > 0:
                p_mastered = round(p_mastered * math.exp(-FORGETTING_RATE * days), 4)

            zone = _zone(p_mastered)
            error_codes_result[code] = {
                "mastery_probability": p_mastered,
                "zone": zone,
                "total_attempts": len(outcomes),
                "correct_count": sum(outcomes),
            }

    probabilities = [v["mastery_probability"] for v in error_codes_result.values()]
    overall = round(sum(probabilities) / len(probabilities), 4) if probabilities else 0.0
    mastered_count = sum(1 for v in error_codes_result.values() if v["zone"] == "mastered")

    return {
        "student_id": student_id,
        "error_codes": error_codes_result,
        "overall_mastery": overall,
        "mastered_count": mastered_count,
        "total_error_codes": len(ERROR_CODES),
        "review_status": "pending_teacher_review",
    }

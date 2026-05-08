from __future__ import annotations

from app.schemas import (
    ErrorCode,
    GuidanceMode,
    PracticeItem,
    PracticeRecommendationResponse,
)


def recommend_practice(
    error_code: ErrorCode,
    grade: int,
    guidance_mode: GuidanceMode = GuidanceMode.STANDARD,
) -> PracticeRecommendationResponse:
    """Return a deterministic practice-plan stub for the MVP."""
    templates = {
        ErrorCode.BASIC_FACT: ["7×8=", "9×6=", "14-8="],
        ErrorCode.CARRY: ["236+178=", "457+286=", "68+57="],
        ErrorCode.BORROW: ["\\frac{5}{6}-\\frac{1}{3}=", "\\frac{7}{8}-\\frac{3}{8}=", "5\\frac{1}{4}-2\\frac{3}{4}="],
        ErrorCode.OPERATION_ORDER: ["18+6×3=", "40-12÷3=", "(15+9)÷3="],
    }
    items = templates.get(error_code, ["\\frac{2}{3}×\\frac{3}{4}=", "\\frac{5}{6}÷\\frac{2}{3}=", "240×35%="])
    level = {
        GuidanceMode.STANDARD: "A",
        GuidanceMode.EXPLORATION: "B",
        GuidanceMode.CHALLENGE: "C",
    }[guidance_mode]
    if error_code == ErrorCode.CORRECT:
        level = "B"

    mode_reason = {
        GuidanceMode.STANDARD: "先巩固教材方法",
        GuidanceMode.EXPLORATION: "在教材方法后加入一点变式探索",
        GuidanceMode.CHALLENGE: "保持短时练习，同时给学有余力的孩子一点挑战",
    }[guidance_mode]

    return PracticeRecommendationResponse(
        grade=grade,
        guidance_mode=guidance_mode,
        level=level,
        target_error=error_code.value,
        items=[PracticeItem(problem=item, reason=mode_reason) for item in items],
        estimated_minutes=5,
    )

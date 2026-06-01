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
        ErrorCode.BORROW: ["5/6-1/3=", "7/8-3/8=", "5又1/4-2又3/4="],
        ErrorCode.PLACE_VALUE_ALIGNMENT: [
            "402-178=", "5006-3287=", "3.14+2.5=",
        ],
        ErrorCode.OPERATION_ORDER: ["18+6×3=", "40-12÷3=", "(15+9)÷3="],
        ErrorCode.DECIMAL_FRACTION_UNIT: [
            "3.6×2.5=", "3/4+5/8=", "7.2÷0.12=",
        ],
        ErrorCode.TRANSCRIPTION: [
            "68×35=", "85×36=", "396+507=",
        ],
        ErrorCode.MISSING_STEP: [
            "3.6×2.5+4.8÷1.2=", "12.5×8-3.6÷0.9=", "(1/2+1/3)×6=",
        ],
        ErrorCode.CONCEPTUAL_UNDERSTANDING: [
            "一根圆柱形木料底面半径2cm、高5cm，体积是多少？",
            "用125粒种子做发芽实验，有100粒发芽，发芽率是多少？",
            "把3:5的后项加上10，前项应加多少才能保持比值不变？",
        ],
        ErrorCode.WORDING_UNIT: [
            "用递等式计算：125×32=",
            "用简便方法计算：99×37+37=",
            "列式计算：25的4倍与36的差是多少？",
        ],
        ErrorCode.NO_CHECKING: [
            "402-178=234", "6.8×3.5=23.6", "5/8+3/8=8/16",
        ],
    }
    items = templates.get(error_code, ["2/3×3/4=", "5/6÷2/3=", "240×35%="])
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

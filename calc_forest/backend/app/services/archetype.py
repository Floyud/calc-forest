"""Student archetype auto-classification.

Four archetypes from the pedagogy spec:
- 扎实稳健型 (Solid & Steady): accuracy ≥ 80%, stable or improving trend
- 稳步进步型 (Steady Progress): improving trend, any accuracy level
- 努力攀登型 (Climbing Hard): accuracy < 60%, or long wrong streak, high effort
- 成长潜力型 (Growth Potential): everything else — may be inconsistent
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ArchetypeResult:
    archetype: str
    archetype_id: str
    description: str
    confidence: float
    evidence: list[str]


def classify_student(
    accuracy: float | None,
    accuracy_trend: str,
    total_attempts: int = 0,
    current_streak_correct: int = 0,
    current_streak_wrong: int = 0,
    mastery_count: int = 0,
    total_error_codes: int = 11,
) -> ArchetypeResult:
    if total_attempts < 5:
        return ArchetypeResult(
            archetype="成长潜力型",
            archetype_id="growth_potential",
            description="数据不足，持续观察中",
            confidence=0.3,
            evidence=[f"仅 {total_attempts} 次作答记录"],
        )

    evidence: list[str] = []
    confidence = 0.7

    if accuracy is not None:
        evidence.append(f"整体准确率 {accuracy * 100:.0f}%")

    if accuracy_trend == "improving":
        evidence.append("准确率呈上升趋势")
    elif accuracy_trend == "declining":
        evidence.append("准确率呈下降趋势")

    if current_streak_correct >= 3:
        evidence.append(f"连续 {current_streak_correct} 次正确")
    if current_streak_wrong >= 3:
        evidence.append(f"连续 {current_streak_wrong} 次错误")

    if mastery_count > 0:
        evidence.append(f"已掌握 {mastery_count}/{total_error_codes} 个错因类型")

    # order matters: most specific checks first
    if accuracy is not None and accuracy >= 0.80:
        if accuracy_trend in ("stable", "improving"):
            return ArchetypeResult(
                archetype="扎实稳健型",
                archetype_id="solid_steady",
                description="基础扎实，表现稳定，可以尝试更高难度的挑战",
                confidence=min(0.95, confidence + 0.1 * min(mastery_count, 3)),
                evidence=evidence,
            )

    if accuracy_trend == "improving":
        return ArchetypeResult(
            archetype="稳步进步型",
            archetype_id="steady_progress",
            description="正在稳步提升，继续保持当前学习节奏",
            confidence=confidence,
            evidence=evidence,
        )

    if (accuracy is not None and accuracy < 0.60) or current_streak_wrong >= 3:
        return ArchetypeResult(
            archetype="努力攀登型",
            archetype_id="climbing_hard",
            description="正在攻克难点，需要更多鼓励和针对性练习",
            confidence=confidence,
            evidence=evidence,
        )

    return ArchetypeResult(
        archetype="成长潜力型",
        archetype_id="growth_potential",
        description="有成长空间，需要找到适合的学习方式",
        confidence=0.6,
        evidence=evidence,
    )

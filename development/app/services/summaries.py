from __future__ import annotations

from collections import Counter

from app.schemas import DiagnosisResponse


def summarize_class(diagnoses: list[DiagnosisResponse]) -> dict:
    counts = Counter(item.primary_error.code.value for item in diagnoses if not item.is_correct)
    return {
        "attempt_count": len(diagnoses),
        "top_error_tags": [{"code": code, "count": count} for code, count in counts.most_common(5)],
        "teacher_brief": "优先讲评出现次数最高的错因，所有建议需教师审核后使用。",
    }

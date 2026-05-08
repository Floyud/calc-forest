from __future__ import annotations

from collections import Counter

from app.schemas import DiagnosisResponse


def summarize_profile(student_id: str, diagnoses: list[DiagnosisResponse]) -> dict:
    """Return a small in-memory profile summary for MVP demos."""
    student_diagnoses = [item for item in diagnoses if item.student_id == student_id]
    counts = Counter(item.primary_error.code.value for item in student_diagnoses)
    total = len(student_diagnoses)
    correct = sum(1 for item in student_diagnoses if item.is_correct)
    return {
        "student_id": student_id,
        "attempt_count": total,
        "accuracy": correct / total if total else None,
        "dominant_error_tags": [code for code, _ in counts.most_common(3) if code != "OK"],
        "review_status": "pending_teacher_review",
    }

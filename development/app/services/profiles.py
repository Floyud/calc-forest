from __future__ import annotations

from collections import Counter
from typing import Any

from app.db import get_db
from app.schemas import DiagnosisResponse


async def get_student_profile_summary(student_id: str) -> dict[str, Any] | None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM student_error_stats WHERE student_id = ?",
            (student_id,),
        )
        rows = await cursor.fetchall()
        if not rows:
            return None

        total_attempts = sum(r["total_attempts"] for r in rows)
        total_correct = sum(r["correct_count"] for r in rows)

        error_breakdown = []
        for r in sorted(rows, key=lambda x: x["total_attempts"], reverse=True):
            if r["total_attempts"] > 0:
                error_breakdown.append({
                    "error_code": r["error_code"],
                    "total_attempts": r["total_attempts"],
                    "correct_count": r["correct_count"],
                    "accuracy": round(r["correct_count"] / r["total_attempts"], 2),
                })

        return {
            "student_id": student_id,
            "total_attempts": total_attempts,
            "total_correct": total_correct,
            "overall_accuracy": round(total_correct / total_attempts, 2) if total_attempts else None,
            "error_breakdown": error_breakdown[:5],
            "review_status": "pending_teacher_review",
        }


async def get_class_profile_summary(class_id: str) -> dict[str, Any]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id FROM students WHERE class_id = ?",
            (class_id,),
        )
        students = await cursor.fetchall()

        if not students:
            return {"class_id": class_id, "students": [], "review_status": "pending_teacher_review"}

        student_ids = [s["id"] for s in students]
        placeholders = ",".join("?" * len(student_ids))

        cursor = await db.execute(
            f"SELECT * FROM student_error_stats WHERE student_id IN ({placeholders})",
            student_ids,
        )
        all_stats = await cursor.fetchall()

        error_counts = Counter(r["error_code"] for r in all_stats)

        return {
            "class_id": class_id,
            "student_count": len(student_ids),
            "top_class_errors": [
                {"error_code": code, "count": count}
                for code, count in error_counts.most_common(5)
            ],
            "review_status": "pending_teacher_review",
        }


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

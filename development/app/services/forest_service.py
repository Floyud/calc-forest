from __future__ import annotations

import json
from collections import Counter
from typing import Any

from app.db import get_db
from app.schemas import ClassForestResponse, StudentTree, WeeklyAccuracy
from app.services.cycle_service import get_current_cycle


TREE_SPECIES_MAP: dict[str, dict[str, str]] = {
    "apple": {"emoji": "\U0001f34e", "name": "苹果树"},
    "orange": {"emoji": "\U0001f34a", "name": "橘子树"},
    "cherry": {"emoji": "\U0001f338", "name": "樱花树"},
    "maple": {"emoji": "\U0001f341", "name": "枫树"},
    "pine": {"emoji": "\U0001f332", "name": "松树"},
    "oak": {"emoji": "\U0001f333", "name": "橡树"},
    "wintersweet": {"emoji": "\U0001f33c", "name": "腊梅"},
    "sunflower": {"emoji": "\U0001f33b", "name": "向日葵"},
}

STAGE_THRESHOLDS = [1, 3, 7, 14, 21, 30, 45, 60, 90]
STAGE_KEYS = [
    "seed", "sprout", "first_leaf", "taller", "branching",
    "sturdy", "bud", "flowering", "mature",
]


def _stage_from_days(days: int) -> str:
    for i in range(len(STAGE_THRESHOLDS) - 1, -1, -1):
        if days >= STAGE_THRESHOLDS[i]:
            return STAGE_KEYS[i]
    return "seed"


def compute_emotional_state(
    weekly_accuracy: list[dict],
    overall_accuracy: float = 0.0,
) -> dict[str, Any]:
    if not weekly_accuracy or len(weekly_accuracy) < 2:
        if overall_accuracy >= 0.9:
            return {"state": "thriving", "intensity": 0.8}
        if overall_accuracy >= 0.4:
            return {"state": "stable", "intensity": 0.0}
        return {"state": "wilting", "intensity": 0.5}

    recent = weekly_accuracy[-3:] if len(weekly_accuracy) >= 3 else weekly_accuracy
    accs = [w["accuracy"] if isinstance(w, dict) else w.accuracy for w in recent]

    if len(accs) < 2:
        return {"state": "stable", "intensity": 0.0}

    trend = accs[-1] - accs[0]
    latest = accs[-1]

    if overall_accuracy > 0.95 or (trend >= 0.10 and latest >= 0.70):
        intensity = min(1.0, trend / 0.20) if trend >= 0.10 else 0.6
        return {"state": "thriving", "intensity": round(intensity, 2)}

    if trend > 0.05 and latest >= 0.70:
        return {"state": "happy", "intensity": round(min(1.0, trend / 0.15), 2)}

    if trend >= -0.05:
        return {"state": "stable", "intensity": round(abs(trend) / 0.10, 2)}

    if trend >= -0.15:
        intensity = round(min(1.0, abs(trend) / 0.15), 2)
        return {"state": "wilting", "intensity": intensity}

    intensity = round(min(1.0, abs(trend) / 0.30), 2)
    return {"state": "struggling", "intensity": intensity}


def _build_in_placeholders(ids: list[str]) -> str:
    return ",".join("?" for _ in ids)


async def get_class_forest(class_id: str) -> ClassForestResponse | None:
    async with get_db() as db:
        cls_cursor = await db.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        cls_row = await cls_cursor.fetchone()
        if not cls_row:
            return None

        class_name = cls_row["name"]
        grade = cls_row["grade"]
        academic_year = cls_row["academic_year"]
        semester = cls_row["semester"]
        student_ids = json.loads(cls_row["student_ids"])

        if not student_ids:
            return ClassForestResponse(
                class_id=class_id,
                class_name=class_name,
                grade=grade,
                semester=semester,
                academic_year=academic_year,
                cycle_id=None,
                week_number=None,
                trees=[],
                class_accuracy=0.0,
                class_top_errors=[],
                class_emotional_state="stable",
            )

        cycle = await get_current_cycle(grade)
        cycle_id = cycle.id if cycle else None

        ph = _build_in_placeholders(student_ids)

        diag_cursor = await db.execute(
            f"SELECT student_id, is_correct, error_code FROM diagnosis_history WHERE student_id IN ({ph})",
            student_ids,
        )
        diag_by_student: dict[str, list[dict]] = {sid: [] for sid in student_ids}
        for row in await diag_cursor.fetchall():
            diag_by_student[row["student_id"]].append(dict(row))

        sa_cursor = await db.execute(
            f"SELECT student_id, is_correct, error_code FROM student_answers WHERE student_id IN ({ph})",
            student_ids,
        )
        sa_by_student: dict[str, list[dict]] = {sid: [] for sid in student_ids}
        for row in await sa_cursor.fetchall():
            sa_by_student[row["student_id"]].append(dict(row))

        progress_cursor = await db.execute(
            f"SELECT * FROM student_cycle_progress WHERE student_id IN ({ph}) AND cycle_id = ?",
            student_ids + [cycle_id],
        )
        progress_by_student: dict[str, dict | None] = {sid: None for sid in student_ids}
        for row in await progress_cursor.fetchall():
            progress_by_student[row["student_id"]] = dict(row)

        student_cursor = await db.execute(
            f"SELECT id, name FROM students WHERE id IN ({ph})",
            student_ids,
        )
        name_by_student: dict[str, str] = {}
        for row in await student_cursor.fetchall():
            name_by_student[row["id"]] = row["name"]

        hw_cursor = await db.execute(
            f"""SELECT sa.student_id, h.id as hw_id, h.created_at,
                   COUNT(sa.id) as total,
                   SUM(CASE WHEN sa.is_correct = 1 THEN 1 ELSE 0 END) as correct
                 FROM homework h
                 JOIN student_answers sa ON sa.homework_id = h.id
                 WHERE sa.student_id IN ({ph})
                 GROUP BY sa.student_id, h.id
                 ORDER BY h.created_at""",
            student_ids,
        )
        hw_by_student: dict[str, list[dict]] = {sid: [] for sid in student_ids}
        for row in await hw_cursor.fetchall():
            hw_by_student[row["student_id"]].append(dict(row))

        all_class_errors: list[str] = []
        trees: list[StudentTree] = []

        for sid in student_ids:
            all_rows = diag_by_student[sid] + sa_by_student[sid]
            total_attempts = len(all_rows)
            correct_count = sum(1 for r in all_rows if r["is_correct"])
            overall_accuracy = round(correct_count / total_attempts, 4) if total_attempts > 0 else 0.0

            error_codes = [
                r["error_code"]
                for r in all_rows
                if r["error_code"] and r["error_code"] != "OK" and r["is_correct"] == 0
            ]
            all_class_errors.extend(error_codes)
            error_counter = Counter(error_codes)
            dominant_errors = [code for code, _ in error_counter.most_common(3)]

            progress_row = progress_by_student[sid]
            tree_species_id = None
            days_completed = 0
            current_stage = "seed"
            if progress_row:
                tree_species_id = progress_row["tree_species_id"]
                days_completed = progress_row["days_completed"]
                current_stage = progress_row["current_stage"]

            if not tree_species_id:
                species_list = ["cherry", "apple", "orange", "maple", "pine", "oak"]
                tree_species_id = species_list[hash(sid) % len(species_list)]

            species_info = TREE_SPECIES_MAP.get(tree_species_id, {"emoji": "\U0001f331", "name": ""})

            weekly_acc: list[WeeklyAccuracy] = []
            for i, hw in enumerate(hw_by_student[sid]):
                weekly_acc.append(WeeklyAccuracy(
                    week_number=i + 1,
                    accuracy=round(hw["correct"] / hw["total"], 4) if hw["total"] > 0 else 0.0,
                    total_attempts=hw["total"],
                    correct_count=hw["correct"],
                ))

            student_name = name_by_student.get(sid, sid)

            emotion = compute_emotional_state(
                [
                    {"accuracy": w.accuracy, "total_attempts": w.total_attempts, "correct_count": w.correct_count}
                    for w in weekly_acc
                ],
                overall_accuracy,
            )

            trees.append(StudentTree(
                student_id=sid,
                student_name=student_name,
                tree_species_id=tree_species_id,
                tree_species_emoji=species_info["emoji"],
                tree_species_name=species_info["name"],
                current_stage=current_stage,
                days_completed=days_completed,
                total_days=90,
                overall_accuracy=overall_accuracy,
                weekly_accuracy=weekly_acc,
                dominant_errors=dominant_errors,
                total_attempts=total_attempts,
                correct_count=correct_count,
                emotional_state=emotion["state"],
                emotional_intensity=emotion["intensity"],
                encouragement_needed=emotion["state"] == "struggling",
            ))

    class_error_counter = Counter(all_class_errors)
    class_top_errors = [code for code, _ in class_error_counter.most_common(3)]
    class_accuracy = (
        round(sum(t.overall_accuracy for t in trees) / len(trees), 4)
        if trees else 0.0
    )

    emotion_counts = Counter(t.emotional_state for t in trees)
    class_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "stable"

    return ClassForestResponse(
        class_id=class_id,
        class_name=class_name,
        grade=grade,
        semester=semester,
        academic_year=academic_year,
        cycle_id=cycle_id,
        week_number=None,
        trees=trees,
        class_accuracy=class_accuracy,
        class_top_errors=class_top_errors,
        class_emotional_state=class_emotion,
    )

import asyncio
import json
import random
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import _SCHEMA_SQL

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "calc_forest.db"

STUDENT_IDS = [f"S{i:03d}" for i in range(1, 11)]

STUDENT_PROFILES = {
    "S001": {"base_accuracy": 0.60, "weak_codes": ["E03"], "improve_rate": 0.05},
    "S002": {"base_accuracy": 0.80, "weak_codes": ["E02"], "improve_rate": 0.02},
    "S003": {"base_accuracy": 0.45, "weak_codes": ["E03", "E05"], "improve_rate": 0.07},
    "S004": {"base_accuracy": 0.90, "weak_codes": [], "improve_rate": 0.01},
    "S005": {"base_accuracy": 0.55, "weak_codes": ["E01", "E03"], "improve_rate": 0.06},
    "S006": {"base_accuracy": 0.70, "weak_codes": ["E05"], "improve_rate": 0.04},
    "S007": {"base_accuracy": 0.75, "weak_codes": ["E02", "E04"], "improve_rate": 0.03},
    "S008": {"base_accuracy": 0.50, "weak_codes": ["E01"], "improve_rate": 0.06},
    "S009": {"base_accuracy": 0.85, "weak_codes": ["E07"], "improve_rate": 0.02},
    "S010": {"base_accuracy": 0.65, "weak_codes": ["E03", "E08"], "improve_rate": 0.04},
}

ERROR_CODES = ["E01", "E02", "E03", "E04", "E05", "E07", "E08", "E11"]


def make_wrong_answer(correct: str, error_type: str = "random") -> str:
    try:
        num = int(correct)
        if error_type == "E03":
            return str(num + random.choice([100, 110, -100, -110]))
        elif error_type == "E02":
            return str(num - random.choice([1, 10, 100]))
        elif error_type == "E01":
            return str(num + random.choice([-1, 1, 2, -2]))
        elif error_type == "E04":
            return str(num + random.choice([10, -10, 100, -100]))
        elif error_type == "E05":
            return str(num + random.choice([-5, 5, -10, 10, 20, -20]))
        else:
            offset = random.choice([-1, 1, 10, -10, 100, -100])
            return str(max(0, num + offset))
    except ValueError:
        return correct + "x"


def get_student_accuracy(profile: dict, week: int, error_code: str | None = None) -> float:
    base = profile["base_accuracy"]
    improve = profile["improve_rate"]
    weak_codes = profile["weak_codes"]

    acc = base + improve * week

    if error_code and error_code in weak_codes:
        acc -= random.uniform(0.15, 0.30)
    else:
        acc += random.uniform(0.05, 0.10)

    acc += random.uniform(-0.05, 0.05)

    return max(0.1, min(0.98, acc))


async def run_week(
    week_num: int,
    target_codes: list[str],
    difficulty: str = "A",
) -> dict[str, dict]:
    from app.services.homework_service import generate_homework, assign_homework
    from app.services.grading_service import submit_homework, grade_homework

    result = await generate_homework(
        class_id="G6A1",
        grade=6,
        error_codes_target=target_codes,
        problem_count=5,
        difficulty=difficulty,
    )
    hw_id = result["homework_id"]

    due_date = f"2026-0{3 + week_num // 4}-{10 + week_num * 7 % 28}"
    await assign_homework(hw_id, due_date=due_date)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    problems = conn.execute(
        "SELECT * FROM homework_problems WHERE homework_id = ? ORDER BY sequence",
        (hw_id,),
    ).fetchall()
    conn.close()

    week_results: dict[str, dict] = {}

    for sid in STUDENT_IDS:
        profile = STUDENT_PROFILES[sid]
        answers = []

        for p in problems:
            correct = p["correct_answer"]
            target_code = p["target_error_code"]
            acc = get_student_accuracy(profile, week_num, target_code)

            if random.random() < acc:
                student_ans = correct
            else:
                error_type = target_code if target_code else "random"
                student_ans = make_wrong_answer(correct, error_type)

            answers.append({
                "problem_sequence": p["sequence"],
                "student_answer": student_ans,
            })

        await submit_homework(hw_id, sid, answers)
        grade_result = await grade_homework(hw_id, sid)

        week_results[sid] = {
            "week": week_num,
            "accuracy": grade_result.get("accuracy", 0),
            "correct": grade_result.get("correct_count", 0),
            "total": grade_result.get("total_problems", 0),
            "errors": grade_result.get("primary_errors", []),
            "growth_updated": grade_result.get("growth_updated", False),
        }

    return week_results


async def simulate(
    weeks: int = 8,
    target_codes: list[str] | None = None,
    difficulty: str = "A",
):
    if not target_codes:
        target_codes = ["E03", "E02", "E05"]

    print(f"=== Multi-Round Simulation: {weeks} weeks ===")
    print(f"Target error codes: {target_codes}")
    print(f"Difficulty: {difficulty}")
    print()

    difficulty_progression = ["A", "A", "A", "B", "B", "B", "C", "C"]

    all_results: list[dict[str, dict]] = []

    for week in range(1, weeks + 1):
        diff = difficulty_progression[min(week - 1, len(difficulty_progression) - 1)]
        print(f"--- Week {week}/{weeks} (difficulty: {diff}) ---")

        week_codes = list(target_codes)
        if week > 3:
            all_errors = []
            for wr in all_results:
                for sid_data in wr.values():
                    all_errors.extend(sid_data.get("errors", []))
            if all_errors:
                from collections import Counter
                common = [c for c, _ in Counter(all_errors).most_common(3) if c not in week_codes]
                if common:
                    week_codes.append(common[0])

        week_results = await run_week(week, week_codes[:3], diff)
        all_results.append(week_results)

        for sid in STUDENT_IDS:
            r = week_results[sid]
            print(
                f"  {sid}: {r['correct']}/{r['total']} "
                f"({r['accuracy']:.0%}) errors={r['errors']} "
                f"growth={'+' if r['growth_updated'] else '-'}"
            )
        print()

    print("=== Summary ===")
    for sid in STUDENT_IDS:
        student_weeks = [wr[sid] for wr in all_results if sid in wr]
        if student_weeks:
            first_acc = student_weeks[0]["accuracy"]
            last_acc = student_weeks[-1]["accuracy"]
            total_correct = sum(w["correct"] for w in student_weeks)
            total_problems = sum(w["total"] for w in student_weeks)
            all_errors = []
            for w in student_weeks:
                all_errors.extend(w["errors"])
            from collections import Counter
            error_summary = dict(Counter(all_errors))
            trend = "improving" if last_acc > first_acc + 0.05 else "stable" if abs(last_acc - first_acc) <= 0.05 else "declining"
            print(
                f"  {sid}: {total_correct}/{total_problems} "
                f"({total_correct/total_problems:.0%}) "
                f"w1={first_acc:.0%} -> w{weeks}={last_acc:.0%} "
                f"trend={trend} errors={error_summary}"
            )

    print(f"\nSimulation complete. {weeks} weeks x {len(STUDENT_IDS)} students.")


if __name__ == "__main__":
    asyncio.run(simulate())

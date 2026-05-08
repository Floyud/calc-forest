import asyncio
import random
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.homework_service import generate_homework, assign_homework
from app.services.grading_service import submit_homework, grade_homework
from app.db import _SCHEMA_SQL

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "calc_forest.db"


def make_wrong_answer(correct: str, error_type: str = "random") -> str:
    try:
        num = int(correct)
        if error_type == "off_by_one":
            return str(num + random.choice([-1, 1, 10, -10]))
        elif error_type == "no_borrow":
            return str(num + random.choice([100, 110, -100, -110]))
        elif error_type == "no_carry":
            return str(num - random.choice([1, 10]))
        else:
            offset = random.choice([-1, 1, 10, -10, 100, -100])
            return str(max(0, num + offset))
    except ValueError:
        return correct + "x"


STUDENT_IDS = [f"S{i:03d}" for i in range(1, 11)]


async def simulate():
    print("=== Homework Simulation ===")

    result = await generate_homework(class_id="G6A1", grade=6, problem_count=5)
    hw_id = result["homework_id"]
    print(f"Generated homework: {hw_id}, {result['problem_count']} problems, targets: {result['error_codes_target']}")

    await assign_homework(hw_id, due_date="2026-05-10")
    print(f"Assigned homework: {hw_id}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    problems = conn.execute(
        "SELECT * FROM homework_problems WHERE homework_id = ? ORDER BY sequence",
        (hw_id,),
    ).fetchall()
    conn.close()

    for sid in STUDENT_IDS:
        answers = []
        for p in problems:
            correct = p["correct_answer"]
            if random.random() < 0.6:
                student_ans = correct
            else:
                student_ans = make_wrong_answer(
                    correct, random.choice(["random", "no_borrow", "no_carry", "off_by_one"])
                )
            answers.append({"problem_sequence": p["sequence"], "student_answer": student_ans})

        sub = await submit_homework(hw_id, sid, answers)
        print(f"  {sid} submitted {sub['answer_count']} answers")

    print("\n--- Grading Results ---")
    for sid in STUDENT_IDS:
        result = await grade_homework(hw_id, sid)
        acc = result.get("accuracy", 0)
        errors = result.get("primary_errors", [])
        print(
            f"  {sid}: {result.get('correct_count', '?')}/{result.get('total_problems', '?')} "
            f"correct ({acc:.0%}) errors={errors} growth={result.get('growth_updated')} "
            f"next={result.get('next_suggestion')}"
        )

    print(f"\nSimulation complete. Homework ID: {hw_id}")


if __name__ == "__main__":
    asyncio.run(simulate())

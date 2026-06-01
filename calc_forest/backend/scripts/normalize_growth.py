#!/usr/bin/env python3
"""Normalize student growth data to mid-semester levels.

Sets all students' days_completed to tier-based values so trees are
at similar sizes (sturdy stage, close to bud). Recomputes current_stage
from thresholds and sets last_practice_date to mid-May 2026.

Usage:
    cd calc_forest/backend
    python scripts/normalize_growth.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "calc_forest.db"

STAGE_THRESHOLDS = [1, 3, 7, 14, 21, 30, 45, 60, 90]
STAGE_NAMES = [
    "seed", "sprout", "first_leaf", "taller", "branching",
    "sturdy", "bud", "flowering", "mature",
]

LAST_PRACTICE_DATE = "2026-05-20"


def compute_stage(days: int) -> str:
    """Return growth stage name for a given days_completed value."""
    stage_idx = 0
    for i, threshold in enumerate(STAGE_THRESHOLDS):
        if days >= threshold:
            stage_idx = i
    return STAGE_NAMES[stage_idx]


def main() -> None:
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Find the spring semester cycle
    cur.execute("SELECT id FROM academic_cycles WHERE id LIKE '%spring%'")
    cycles = [row["id"] for row in cur.fetchall()]
    if not cycles:
        print("No spring cycle found. Nothing to update.")
        conn.close()
        return
    print(f"Found {len(cycles)} spring cycle(s): {cycles}")

    # 2. Compute per-student accuracy from student_error_stats
    cur.execute(
        "SELECT student_id, "
        "SUM(total_attempts) AS total, "
        "SUM(correct_count) AS correct "
        "FROM student_error_stats "
        "GROUP BY student_id"
    )
    accuracy_map: dict[str, float] = {}
    for row in cur.fetchall():
        total = row["total"] or 0
        correct = row["correct"] or 0
        accuracy_map[row["student_id"]] = correct / total if total > 0 else 0.0

    # 3. Fetch progress rows for spring cycles
    placeholders = ",".join("?" for _ in cycles)
    cur.execute(
        f"SELECT id, student_id FROM student_cycle_progress "
        f"WHERE cycle_id IN ({placeholders})",
        cycles,
    )
    rows = cur.fetchall()
    if not rows:
        print("No student_cycle_progress rows for spring cycles.")
        conn.close()
        return

    # 4. Assign days by accuracy tier
    updated = {"excellent": 0, "average": 0, "needs_attention": 0, "no_stats": 0}

    for row in rows:
        sid = row["student_id"]
        acc = accuracy_map.get(sid)

        if acc is None:
            days = 38  # default mid-semester
            tier = "no_stats"
        elif acc >= 0.80:
            days = 42
            tier = "excellent"
        elif acc >= 0.50:
            days = 38
            tier = "average"
        else:
            days = 35
            tier = "needs_attention"

        stage = compute_stage(days)
        cur.execute(
            "UPDATE student_cycle_progress "
            "SET days_completed = ?, current_stage = ?, last_practice_date = ? "
            "WHERE id = ?",
            (days, stage, LAST_PRACTICE_DATE, row["id"]),
        )
        updated[tier] += 1

    conn.commit()
    conn.close()

    total = sum(updated.values())
    print(f"\nUpdated {total} student_cycle_progress rows:")
    print(f"  Excellent     (accuracy ≥0.80, 42 days, sturdy):  {updated['excellent']}")
    print(f"  Average       (accuracy ≥0.50, 38 days, sturdy): {updated['average']}")
    print(f"  Needs attn    (accuracy <0.50, 35 days, sturdy): {updated['needs_attention']}")
    print(f"  No stats      (default 38 days, sturdy):         {updated['no_stats']}")
    print(f"\nAll last_practice_date set to {LAST_PRACTICE_DATE}")
    print("Done.")


if __name__ == "__main__":
    main()

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import _SCHEMA_SQL

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "calc_forest.db"
DATA_PATH = Path(__file__).resolve().parent.parent / "data"

ERROR_LABELS = {
    "OK": "答案正确",
    "E01": "基础事实错误",
    "E02": "进位错误",
    "E03": "退位错误",
    "E04": "数位对齐错误",
    "E05": "运算顺序错误",
    "E06": "小数点/分数单位错误",
    "E07": "抄题/转写错误",
    "E08": "步骤遗漏",
    "E09": "算理理解不足",
    "E10": "审题与单位理解错误",
    "E11": "习惯性未验算",
    "E99": "暂未识别错因",
}


def create_tables(conn):
    conn.executescript(_SCHEMA_SQL)
    print("  tables ensured.")


def seed_classes(conn):
    class_id = "G6A1"
    if conn.execute("SELECT 1 FROM classes WHERE id=?", (class_id,)).fetchone():
        print("  classes already seeded, skipping.")
        return

    conn.execute(
        """INSERT INTO classes (id, name, grade, academic_year, semester, student_ids)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            class_id,
            "六年级1班",
            6,
            "2025-2026",
            "fall",
            json.dumps([f"S{i:03d}" for i in range(1, 11)]),
        ),
    )
    print("  seeded 1 class.")


def seed_students(conn):
    students = [
        ("S001", "小明", 6, "G6A1", "standard", 5, "2024-09-01"),
        ("S002", "小红", 6, "G6A1", "standard", 5, "2024-09-01"),
        ("S003", "小刚", 6, "G6A1", "exploration", 6, "2025-09-01"),
        ("S004", "小美", 6, "G6A1", "standard", 5, "2024-09-01"),
        ("S005", "小强", 6, "G6A1", "challenge", 5, "2024-09-01"),
        ("S006", "小丽", 6, "G6A1", "standard", 6, "2025-09-01"),
        ("S007", "小伟", 6, "G6A1", "standard", 5, "2024-09-01"),
        ("S008", "小芳", 6, "G6A1", "exploration", 6, "2025-09-01"),
        ("S009", "小军", 6, "G6A1", "standard", 5, "2024-09-01"),
        ("S010", "小静", 6, "G6A1", "standard", 6, "2025-09-01"),
    ]

    inserted = 0
    for sid, name, grade, cid, mode, start_g, enrolled in students:
        if conn.execute("SELECT 1 FROM students WHERE id=?", (sid,)).fetchone():
            continue
        conn.execute(
            """INSERT INTO students (id, name, grade, class_id, guidance_mode,
               textbook_version, start_grade, enrolled_at)
               VALUES (?, ?, ?, ?, ?, 'PEP', ?, ?)""",
            (sid, name, grade, cid, mode, start_g, enrolled),
        )
        inserted += 1

    print(f"  seeded {inserted} students ({10 - inserted} already existed).")


def seed_cycles(conn):
    cycles = [
        (
            "2025-fall-semester",
            "fall_semester",
            "2025-2026",
            6,
            "2025-09-01",
            "2026-01-16",
            138,
            70,
            json.dumps(["apple", "orange", "cherry", "maple", "pine", "oak"]),
        ),
        (
            "2026-winter-break",
            "winter_break",
            "2025-2026",
            6,
            "2026-01-17",
            "2026-02-15",
            30,
            15,
            json.dumps(["wintersweet"]),
        ),
        (
            "2026-spring-semester",
            "spring_semester",
            "2025-2026",
            6,
            "2026-02-16",
            "2026-07-03",
            138,
            70,
            json.dumps(["apple", "orange", "cherry", "maple", "pine", "oak"]),
        ),
        (
            "2026-summer-break",
            "summer_break",
            "2025-2026",
            6,
            "2026-07-04",
            "2026-08-31",
            59,
            30,
            json.dumps(["sunflower"]),
        ),
    ]

    inserted = 0
    for row in cycles:
        if conn.execute("SELECT 1 FROM academic_cycles WHERE id=?", (row[0],)).fetchone():
            continue
        conn.execute(
            """INSERT INTO academic_cycles
               (id, cycle_type, academic_year, grade, start_date, end_date,
                total_days, practice_goal_days, available_tree_species)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            row,
        )
        inserted += 1

    print(f"  seeded {inserted} cycles ({len(cycles) - inserted} already existed).")


def migrate_demo_records(conn):
    demo_path = DATA_PATH / "demo_answer_records.json"
    if not demo_path.exists():
        print("  demo_answer_records.json not found, skipping.")
        return

    records = json.loads(demo_path.read_text(encoding="utf-8"))
    inserted = 0
    for rec in records:
        rid = rec["record_id"]
        if conn.execute("SELECT 1 FROM diagnosis_history WHERE id=?", (rid,)).fetchone():
            continue

        error_code = rec.get("expected_error_tags", ["E99"])[0]
        error_label = ERROR_LABELS.get(error_code, "暂未识别错因")
        is_correct = 1 if rec["student_answer"].strip() == rec["correct_answer"].strip() else 0

        conn.execute(
            """INSERT INTO diagnosis_history
               (id, student_id, class_id, grade, problem, correct_answer,
                student_answer, student_steps, is_correct, error_code,
                error_label, confidence, evidence, teacher_action,
                student_feedback, teacher_summary, guidance_mode, review_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rid,
                rec["student_id"],
                "G6A1",
                rec["grade"],
                rec["problem"],
                rec["correct_answer"],
                rec["student_answer"],
                json.dumps(rec.get("student_steps", []), ensure_ascii=False),
                is_correct,
                error_code,
                error_label,
                0.90,
                "",
                "",
                "",
                "",
                "standard",
                "pending_teacher_review",
            ),
        )
        inserted += 1

    print(f"  migrated {inserted} records ({len(records) - inserted} already existed).")


def main():
    print(f"Seeding database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    create_tables(conn)
    seed_classes(conn)
    seed_students(conn)
    seed_cycles(conn)
    migrate_demo_records(conn)
    conn.commit()
    conn.close()
    print("Seed complete.")


if __name__ == "__main__":
    main()

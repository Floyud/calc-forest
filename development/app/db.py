from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "calc_forest.db"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    grade INTEGER NOT NULL CHECK(grade BETWEEN 1 AND 6),
    class_id TEXT NOT NULL,
    guidance_mode TEXT NOT NULL DEFAULT 'standard',
    textbook_version TEXT NOT NULL DEFAULT 'PEP',
    start_grade INTEGER NOT NULL,
    enrolled_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    grade INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    semester TEXT NOT NULL,
    student_ids TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS academic_cycles (
    id TEXT PRIMARY KEY,
    cycle_type TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    grade INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    total_days INTEGER NOT NULL,
    practice_goal_days INTEGER NOT NULL,
    available_tree_species TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS diagnosis_history (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    class_id TEXT,
    grade INTEGER NOT NULL,
    problem TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    student_answer TEXT NOT NULL,
    student_steps TEXT NOT NULL DEFAULT '[]',
    is_correct INTEGER NOT NULL DEFAULT 0,
    error_code TEXT NOT NULL,
    error_label TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence TEXT NOT NULL DEFAULT '',
    teacher_action TEXT NOT NULL DEFAULT '',
    student_feedback TEXT NOT NULL DEFAULT '',
    teacher_summary TEXT NOT NULL DEFAULT '',
    guidance_mode TEXT NOT NULL DEFAULT 'standard',
    review_status TEXT NOT NULL DEFAULT 'pending_teacher_review',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS student_cycle_progress (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    cycle_id TEXT NOT NULL,
    tree_species_id TEXT,
    days_completed INTEGER NOT NULL DEFAULT 0,
    current_stage TEXT NOT NULL DEFAULT 'seed',
    last_practice_date TEXT,
    UNIQUE(student_id, cycle_id)
);

CREATE TABLE IF NOT EXISTS homework (
    id TEXT PRIMARY KEY,
    class_id TEXT NOT NULL,
    student_id TEXT,
    cycle_id TEXT,
    grade INTEGER NOT NULL,
    knowledge_points TEXT NOT NULL DEFAULT '[]',
    error_codes_target TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    assigned_date TEXT,
    due_date TEXT,
    generated_by TEXT NOT NULL DEFAULT 'system',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS homework_problems (
    id TEXT PRIMARY KEY,
    homework_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    problem TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    knowledge_point TEXT NOT NULL DEFAULT '',
    target_error_code TEXT,
    difficulty TEXT NOT NULL DEFAULT 'A'
);

CREATE TABLE IF NOT EXISTS homework_submissions (
    id TEXT PRIMARY KEY,
    homework_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'submitted'
);

CREATE TABLE IF NOT EXISTS student_answers (
    id TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL,
    homework_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    problem_sequence INTEGER NOT NULL,
    problem TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    student_answer TEXT NOT NULL,
    student_steps TEXT NOT NULL DEFAULT '[]',
    is_correct INTEGER NOT NULL DEFAULT 0,
    error_code TEXT,
    error_label TEXT,
    confidence REAL,
    evidence TEXT,
    teacher_action TEXT,
    student_feedback TEXT
);

CREATE TABLE IF NOT EXISTS practice_weeks (
    id TEXT PRIMARY KEY,
    cycle_id TEXT NOT NULL,
    week_number INTEGER NOT NULL CHECK(week_number BETWEEN 1 AND 20),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    UNIQUE(cycle_id, week_number)
);

CREATE TABLE IF NOT EXISTS student_error_stats (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    error_code TEXT NOT NULL,
    total_attempts INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    last_seen_at TEXT,
    UNIQUE(student_id, error_code)
);

CREATE TABLE IF NOT EXISTS quiz_sessions (
    id TEXT PRIMARY KEY,
    class_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    target_error_codes TEXT NOT NULL DEFAULT '[]',
    problem_count INTEGER NOT NULL DEFAULT 5,
    difficulty TEXT NOT NULL DEFAULT 'B',
    grade INTEGER NOT NULL DEFAULT 6,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS quiz_problems (
    id TEXT PRIMARY KEY,
    quiz_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    problem TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    target_error_code TEXT,
    difficulty TEXT NOT NULL DEFAULT 'B',
    knowledge_point TEXT NOT NULL DEFAULT '',
    hint TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (quiz_id) REFERENCES quiz_sessions(id)
);

CREATE TABLE IF NOT EXISTS quiz_responses (
    id TEXT PRIMARY KEY,
    quiz_id TEXT NOT NULL,
    problem_sequence INTEGER NOT NULL,
    class_response TEXT NOT NULL DEFAULT 'mixed',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (quiz_id) REFERENCES quiz_sessions(id)
);

CREATE TABLE IF NOT EXISTS teaching_units (
    id TEXT PRIMARY KEY,
    grade INTEGER NOT NULL CHECK(grade BETWEEN 1 AND 6),
    semester INTEGER NOT NULL DEFAULT 2 CHECK(semester IN (1, 2)),
    unit_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    domain TEXT NOT NULL DEFAULT '',
    hours_planned INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    parent_id TEXT,
    textbook_version TEXT NOT NULL DEFAULT 'PEP'
);

CREATE TABLE IF NOT EXISTS teaching_schedule (
    id TEXT PRIMARY KEY,
    class_id TEXT NOT NULL,
    week_number INTEGER NOT NULL,
    unit_id TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    notes TEXT NOT NULL DEFAULT '',
    is_custom INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (unit_id) REFERENCES teaching_units(id),
    UNIQUE(class_id, week_number)
);

CREATE TABLE IF NOT EXISTS calendar_weeks (
    id TEXT PRIMARY KEY,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL DEFAULT 2,
    week_number INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    is_holiday INTEGER NOT NULL DEFAULT 0,
    label TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS student_error_trajectory (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    unit_id TEXT,
    week_number INTEGER,
    error_code TEXT NOT NULL,
    error_count INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    accuracy REAL NOT NULL DEFAULT 0.0,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (unit_id) REFERENCES teaching_units(id)
);

CREATE TABLE IF NOT EXISTS scanned_submissions (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    homework_id TEXT,
    pdf_path TEXT NOT NULL,
    ocr_status TEXT NOT NULL DEFAULT 'pending',
    ocr_result_json TEXT,
    graded_status TEXT NOT NULL DEFAULT 'pending',
    uploaded_at TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS homework_pdfs (
    id TEXT PRIMARY KEY,
    homework_id TEXT NOT NULL,
    class_id TEXT NOT NULL,
    student_id TEXT,
    pdf_path TEXT NOT NULL,
    pdf_type TEXT NOT NULL DEFAULT 'individual',
    generated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS teachers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    password_hash TEXT NOT NULL,
    avatar TEXT NOT NULL DEFAULT '',
    class_ids TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Structured knowledge points from textbook
CREATE TABLE IF NOT EXISTS knowledge_points (
    id TEXT PRIMARY KEY,
    error_code TEXT NOT NULL,
    topic TEXT NOT NULL,
    description TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT '',
    example TEXT NOT NULL DEFAULT '',
    prerequisite_ids TEXT NOT NULL DEFAULT '[]',
    difficulty_level TEXT NOT NULL DEFAULT 'B',
    unit_number INTEGER,
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- Concept relations (knowledge graph edges)
CREATE TABLE IF NOT EXISTS concept_relations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    FOREIGN KEY (source_id) REFERENCES knowledge_points(id),
    FOREIGN KEY (target_id) REFERENCES knowledge_points(id)
);

-- Verified problem bank (for reuse and RAG context)
CREATE TABLE IF NOT EXISTS problem_bank (
    id TEXT PRIMARY KEY,
    problem_text TEXT NOT NULL,
    problem_plain TEXT NOT NULL DEFAULT '',
    correct_answer TEXT NOT NULL,
    error_code TEXT NOT NULL,
    knowledge_point TEXT NOT NULL,
    difficulty TEXT NOT NULL DEFAULT 'B',
    method TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'system',
    use_count INTEGER NOT NULL DEFAULT 0,
    verified INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Week → calculation type mapping (from teacher's doc)
CREATE TABLE IF NOT EXISTS week_calc_mapping (
    id TEXT PRIMARY KEY,
    week_start INTEGER NOT NULL,
    week_end INTEGER NOT NULL,
    calc_type TEXT NOT NULL,
    calc_subtypes TEXT NOT NULL DEFAULT '[]',
    error_codes TEXT NOT NULL DEFAULT '[]',
    is_review INTEGER NOT NULL DEFAULT 0,
    review_types TEXT NOT NULL DEFAULT '[]',
    semester INTEGER NOT NULL DEFAULT 1,
    grade INTEGER NOT NULL DEFAULT 6
);

-- FTS5 for knowledge point search
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_points_fts USING fts5(
    id, topic, description, method, example,
    tokenize='trigram'
);

-- AI grading comments (per-question feedback from LLM)
CREATE TABLE IF NOT EXISTS grading_comments (
    id TEXT PRIMARY KEY,
    homework_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    problem_sequence INTEGER NOT NULL,
    ai_comment TEXT,
    error_code TEXT,
    confidence REAL,
    created_at TEXT,
    FOREIGN KEY (homework_id, student_id, problem_sequence)
        REFERENCES student_answers(homework_id, student_id, problem_sequence)
);

-- AI student profile snapshots
CREATE TABLE IF NOT EXISTS profile_snapshots (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    snapshot_type TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    portrait_summary TEXT,
    personality_tags TEXT,
    growth_narrative TEXT,
    created_at TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- Exercise type catalog (题型类别库)
CREATE TABLE IF NOT EXISTS exercise_types (
    id TEXT PRIMARY KEY,
    parent_id TEXT,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    difficulty_range TEXT NOT NULL DEFAULT '["A","B","C"]',
    related_error_codes TEXT NOT NULL DEFAULT '[]',
    knowledge_points TEXT NOT NULL DEFAULT '[]',
    description TEXT NOT NULL DEFAULT '',
    example_problem TEXT NOT NULL DEFAULT '',
    example_answer TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    grade_range TEXT NOT NULL DEFAULT '[5,6]',
    textbook_unit TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (parent_id) REFERENCES exercise_types(id)
);
"""

_MIGRATE_SQL = [
    "ALTER TABLE students ADD COLUMN personality_tags TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE students ADD COLUMN learning_style TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE students ADD COLUMN notes TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE classes ADD COLUMN teacher_id TEXT NOT NULL DEFAULT ''",
    # Hot-path indexes for diagnosis_history and student_answers
    "CREATE INDEX IF NOT EXISTS idx_diag_student ON diagnosis_history(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_diag_class ON diagnosis_history(class_id)",
    "CREATE INDEX IF NOT EXISTS idx_diag_student_class ON diagnosis_history(student_id, class_id)",
    "CREATE INDEX IF NOT EXISTS idx_answers_student ON student_answers(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_answers_hw_student ON student_answers(homework_id, student_id)",
    "CREATE INDEX IF NOT EXISTS idx_answers_hw_student_err ON student_answers(homework_id, student_id, error_code)",
    "CREATE INDEX IF NOT EXISTS idx_progress_student_cycle ON student_cycle_progress(student_id, cycle_id)",
    "CREATE INDEX IF NOT EXISTS idx_schedule_class ON teaching_schedule(class_id)",
    "CREATE INDEX IF NOT EXISTS idx_trajectory_student ON student_error_trajectory(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_teachers_phone ON teachers(phone)",
    # Knowledge graph indexes
    "CREATE INDEX IF NOT EXISTS idx_kp_error_code ON knowledge_points(error_code)",
    "CREATE INDEX IF NOT EXISTS idx_kp_unit ON knowledge_points(unit_number)",
    "CREATE INDEX IF NOT EXISTS idx_cr_source ON concept_relations(source_id)",
    "CREATE INDEX IF NOT EXISTS idx_cr_target ON concept_relations(target_id)",
    "CREATE INDEX IF NOT EXISTS idx_cr_type ON concept_relations(relation_type)",
    "CREATE INDEX IF NOT EXISTS idx_pb_error_code ON problem_bank(error_code)",
    "CREATE INDEX IF NOT EXISTS idx_pb_difficulty ON problem_bank(difficulty)",
    "CREATE INDEX IF NOT EXISTS idx_pb_kp ON problem_bank(knowledge_point)",
    "CREATE INDEX IF NOT EXISTS idx_wcm_week ON week_calc_mapping(week_start, week_end)",
    "CREATE INDEX IF NOT EXISTS idx_wcm_grade_sem ON week_calc_mapping(grade, semester)",
    "CREATE INDEX IF NOT EXISTS idx_gc_hw_student ON grading_comments(homework_id, student_id)",
    "CREATE INDEX IF NOT EXISTS idx_ps_student ON profile_snapshots(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_ps_type ON profile_snapshots(snapshot_type)",
    "CREATE INDEX IF NOT EXISTS idx_et_parent ON exercise_types(parent_id)",
    "CREATE INDEX IF NOT EXISTS idx_et_category ON exercise_types(category)",
    "CREATE INDEX IF NOT EXISTS idx_et_code ON exercise_types(code)",
]

_DEFAULT_TEACHER_SQL = """
INSERT OR IGNORE INTO teachers (id, name, phone, password_hash, class_ids)
VALUES ('T001', '王老师', '13800000001', 'dev', '["G6A1"]');
"""


async def seed_default_teacher() -> None:
    async with get_db() as db:
        cur = await db.execute("SELECT COUNT(*) FROM teachers")
        count = (await cur.fetchone())[0]
        if count == 0:
            await db.execute(_DEFAULT_TEACHER_SQL)
            # also backfill teacher_id on existing classes
            await db.execute("UPDATE classes SET teacher_id = 'T001' WHERE teacher_id = ''")
            await db.commit()

_pragmas_done: bool = False


@asynccontextmanager
async def get_db():
    global _pragmas_done
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    if not _pragmas_done:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        _pragmas_done = True
    try:
        yield db
    finally:
        await db.close()


async def close_db() -> None:
    pass


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with get_db() as db:
        await db.executescript(_SCHEMA_SQL)
        for sql in _MIGRATE_SQL:
            try:
                await db.execute(sql)
            except Exception:
                pass
        await db.commit()
    await seed_default_teacher()

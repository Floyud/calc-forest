"""Timetable (课程表) service — full weekly schedule + auto-assign homework."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Any

from app.db import get_db


DAYS = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}

# Period time labels for display
PERIOD_TIMES: dict[int, str] = {
    1: "8:30-9:10",
    2: "9:20-10:00",
    3: "10:30-11:10",
    4: "11:20-11:50",
    5: "14:30-15:10",
    6: "15:20-16:00",
}

# Break between period 2 and 3
BREAK_AFTER_PERIOD = 2
BREAK_LABEL = "花样跳绳"

# Realistic curriculum schedule: (period, day_of_week) -> (subject, teacher)
# day_of_week: 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri
REALISTIC_SCHEDULE: dict[tuple[int, int], tuple[str, str]] = {
    # Period 1
    (1, 1): ("语文", "小田老师"),
    (1, 2): ("语文", "小田老师"),
    (1, 3): ("英语", "小王老师"),
    (1, 4): ("语文", "小田老师"),
    (1, 5): ("语文", "小田老师"),
    # Period 2
    (2, 1): ("数学", "小常老师"),
    (2, 2): ("英语", "小王老师"),
    (2, 3): ("语文", "小田老师"),
    (2, 4): ("数学", "小常老师"),
    (2, 5): ("数学", "小常老师"),
    # Period 3
    (3, 1): ("体育", "小郑老师"),
    (3, 2): ("数学", "小常老师"),
    (3, 3): ("数学", "小常老师"),
    (3, 4): ("体育", "小郑老师"),
    (3, 5): ("语文", "小田老师"),
    # Period 4
    (4, 1): ("劳动", "小田老师"),
    (4, 2): ("美术", "小田老师"),
    (4, 3): ("体育", "小郑老师"),
    (4, 4): ("道法", "小朱老师"),
    (4, 5): ("体育", "小郑老师"),
    # Period 5
    (5, 1): ("英语", "小王老师"),
    (5, 2): ("体育", "小郑老师"),
    (5, 3): ("科学", "小常老师"),
    (5, 4): ("音乐", "小常老师"),
    (5, 5): ("英语", "小王老师"),
    # Period 6
    (6, 1): ("音乐", "小常老师"),
    (6, 2): ("科学", "小常老师"),
    (6, 3): ("道法", "小朱老师"),
    (6, 4): ("信息科技", "小王老师"),
    (6, 5): ("班会", "小王老师"),
}

# Subject color mapping for frontend theming
SUBJECT_COLORS: dict[str, str] = {
    "数学": "emerald",
    "语文": "blue",
    "英语": "violet",
    "体育": "orange",
    "音乐": "pink",
    "美术": "fuchsia",
    "科学": "cyan",
    "道法": "amber",
    "劳动": "lime",
    "信息科技": "indigo",
    "班会": "slate",
}


async def ensure_timetable_table() -> None:
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS weekly_timetable (
                id TEXT PRIMARY KEY,
                class_id TEXT NOT NULL,
                day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 1 AND 7),
                period_number INTEGER NOT NULL DEFAULT 1,
                subject TEXT NOT NULL DEFAULT 'math',
                teacher TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                UNIQUE(class_id, day_of_week, period_number)
            )
        """)
        # Migration: add teacher column if missing (existing DBs)
        try:
            await db.execute("ALTER TABLE weekly_timetable ADD COLUMN teacher TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass  # Column already exists
        await db.commit()


async def get_timetable(class_id: str) -> list[dict[str, Any]]:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT * FROM weekly_timetable WHERE class_id = ? ORDER BY day_of_week, period_number",
            (class_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_weekly_math_schedule(class_id: str) -> dict[str, Any]:
    """Return math-only schedule grouped by day (backward compatible)."""
    rows = await get_timetable(class_id)
    schedule: dict[int, list[dict]] = {}
    for r in rows:
        subj = r["subject"]
        # Handle both new "数学" and legacy "math" subject names
        if subj not in ("数学", "math") or not r["is_active"]:
            continue
        day = r["day_of_week"]
        schedule.setdefault(day, []).append({
            "period": r["period_number"],
            "subject": "数学",
            "teacher": r.get("teacher", ""),
            "id": r["id"],
        })

    assignments = await _get_recent_assignments(class_id)
    return {
        "timetable": rows,  # full list for backward compat
        "math_schedule": schedule,
        "assignments": assignments,
    }


async def get_full_weekly_schedule(class_id: str) -> dict[str, Any]:
    """Return full schedule with all subjects, period times, and break info."""
    rows = await get_timetable(class_id)

    timetable_entries = []
    for r in rows:
        entry = {
            "day_of_week": r["day_of_week"],
            "period_number": r["period_number"],
            "subject": r["subject"],
            "teacher": r.get("teacher", ""),
            "is_active": bool(r["is_active"]),
            "time_label": PERIOD_TIMES.get(r["period_number"], ""),
        }
        timetable_entries.append(entry)

    assignments = await _get_recent_assignments(class_id)

    return {
        "timetable": timetable_entries,
        "period_times": PERIOD_TIMES,
        "break_after_period": BREAK_AFTER_PERIOD,
        "break_label": BREAK_LABEL,
        "subject_colors": SUBJECT_COLORS,
        "assignments": assignments,
        "total_periods": 6,
    }


async def _get_recent_assignments(class_id: str) -> list[dict]:
    """Get recent homework assignments for this week."""
    today = date.today()
    monday = today - timedelta(days=today.isoweekday() - 1)
    friday = monday + timedelta(days=4)
    async with get_db() as db:
        cur = await db.execute(
            """SELECT h.id as homework_id, h.assigned_date,
                      (SELECT COUNT(*) FROM homework_problems hp WHERE hp.homework_id = h.id) as problem_count
               FROM homework h
               WHERE h.class_id = ? AND h.assigned_date >= ? AND h.assigned_date <= ?
               ORDER BY h.assigned_date""",
            (class_id, monday.isoformat(), friday.isoformat()),
        )
        results = []
        for r in await cur.fetchall():
            row = dict(r)
            assigned = row.get("assigned_date", "")
            if assigned:
                try:
                    dow = date.fromisoformat(assigned).isoweekday()
                    row["day_of_week"] = dow
                except (ValueError, TypeError):
                    row["day_of_week"] = 0
            results.append(row)
        return results


async def get_today_math_classes(class_id: str) -> list[dict]:
    dow = date.today().isoweekday()  # 1=Mon ... 7=Sun
    rows = await get_timetable(class_id)
    classes = []
    for r in rows:
        if r["subject"] in ("数学", "math") and r["is_active"] and r["day_of_week"] == dow:
            classes.append({
                "period": r["period_number"],
                "subject": r["subject"],
                "teacher": r.get("teacher", ""),
                "id": r["id"],
            })
    return classes


async def update_timetable(class_id: str, entries: list[dict[str, Any]]) -> int:
    count = 0
    async with get_db() as db:
        for e in entries:
            row_id = f"TT_{class_id}_D{e['day_of_week']}_P{e.get('period_number', 1)}"
            await db.execute(
                """INSERT OR REPLACE INTO weekly_timetable
                   (id, class_id, day_of_week, period_number, subject, teacher, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (row_id, class_id, e["day_of_week"], e.get("period_number", 1),
                 e.get("subject", "math"), e.get("teacher", ""),
                 1 if e.get("is_active", True) else 0),
            )
            count += 1
        await db.commit()
    return count


async def seed_default_timetable(class_id: str) -> int:
    """Seed math-only default (5 rows, Mon-Fri period 1). Legacy."""
    rows = await get_timetable(class_id)
    if rows:
        return 0
    entries = [{"day_of_week": d, "period_number": 1, "subject": "数学", "teacher": "小常老师"} for d in range(1, 6)]
    return await update_timetable(class_id, entries)


async def seed_realistic_timetable(class_id: str) -> int:
    """Seed the full realistic curriculum schedule (30 entries = 6 periods × 5 days)."""
    existing = await get_timetable(class_id)
    if existing:
        # Check if we already have multi-subject data
        subjects = {r["subject"] for r in existing}
        if len(subjects) > 1:
            return 0  # Already seeded with realistic data

        # Remove old math-only data and re-seed
        async with get_db() as db:
            await db.execute("DELETE FROM weekly_timetable WHERE class_id = ?", (class_id,))
            await db.commit()

    entries = []
    for (period, dow), (subject, teacher) in REALISTIC_SCHEDULE.items():
        entries.append({
            "day_of_week": dow,
            "period_number": period,
            "subject": subject,
            "teacher": teacher,
            "is_active": True,
        })
    return await update_timetable(class_id, entries)


async def seed_all_classes() -> int:
    async with get_db() as db:
        cur = await db.execute("SELECT id FROM classes")
        class_ids = [r["id"] for r in await cur.fetchall()]
    total = 0
    for cid in class_ids:
        total += await seed_realistic_timetable(cid)
    return total


async def auto_assign_homework(class_id: str) -> dict[str, Any] | None:
    today_classes = await get_today_math_classes(class_id)
    if not today_classes:
        return {"status": "no_math_today", "message": "今天没有数学课"}

    today_str = date.today().isoformat()
    async with get_db() as db:
        cur = await db.execute(
            "SELECT id FROM homework WHERE class_id = ? AND assigned_date = ? LIMIT 1",
            (class_id, today_str),
        )
        if await cur.fetchone():
            return {"status": "already_assigned", "message": "今日已布置过作业"}

        cur2 = await db.execute("SELECT grade FROM classes WHERE id = ?", (class_id,))
        row = await cur2.fetchone()
        grade = row["grade"] if row else 6

    from app.services.homework_service import generate_homework, assign_homework

    hw = await generate_homework(
        class_id=class_id,
        grade=grade,
        error_codes_target=None,
        problem_count=5,
        difficulty="auto",
    )
    await assign_homework(hw["homework_id"])

    async with get_db() as db:
        await db.execute(
            "UPDATE homework SET assigned_date = ? WHERE id = ?",
            (today_str, hw["homework_id"]),
        )
        await db.commit()

    return {
        "status": "assigned",
        "homework_id": hw["homework_id"],
        "problem_count": hw.get("problem_count", 5),
        "message": "作业已自动布置",
    }


async def manual_assign_homework(
    class_id: str,
    *,
    grade: int = 6,
    problem_count: int = 5,
    error_codes: list[str] | None = None,
    difficulty: str = "B",
    unit_title: str = "",
) -> dict[str, Any]:
    from app.services.homework_service import generate_homework, assign_homework

    hw = await generate_homework(
        class_id=class_id,
        grade=grade,
        error_codes_target=error_codes,
        problem_count=problem_count,
        difficulty=difficulty,
    )
    await assign_homework(hw["homework_id"])

    today_str = date.today().isoformat()
    async with get_db() as db:
        await db.execute(
            "UPDATE homework SET assigned_date = ? WHERE id = ?",
            (today_str, hw["homework_id"]),
        )
        await db.commit()

    return {
        "status": "assigned",
        "homework_id": hw["homework_id"],
        "problem_count": hw.get("problem_count", problem_count),
    }

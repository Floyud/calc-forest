from __future__ import annotations

import asyncio
import json
import uuid
from app.db import init_db, get_db

UNITS = [
    {"num": 1, "title": "负数", "domain": "数与代数", "hours": 3},
    {"num": 2, "title": "百分数（二）", "domain": "数与代数", "hours": 5, "children": [
        {"num": 21, "title": "折扣", "hours": 1},
        {"num": 22, "title": "成数", "hours": 1},
        {"num": 23, "title": "税率", "hours": 1},
        {"num": 24, "title": "利率", "hours": 1},
        {"num": 25, "title": "解决问题", "hours": 1},
    ]},
    {"num": 3, "title": "圆柱与圆锥", "domain": "图形与几何", "hours": 9, "children": [
        {"num": 31, "title": "圆柱的认识", "hours": 2},
        {"num": 32, "title": "圆柱的表面积", "hours": 3},
        {"num": 33, "title": "圆柱的体积", "hours": 2},
        {"num": 34, "title": "圆锥的认识", "hours": 1},
        {"num": 35, "title": "圆锥的体积", "hours": 1},
    ]},
    {"num": 4, "title": "比例", "domain": "数与代数", "hours": 14, "children": [
        {"num": 41, "title": "比例的意义和基本性质", "hours": 4},
        {"num": 42, "title": "正比例和反比例", "hours": 4},
        {"num": 43, "title": "比例的应用", "hours": 5},
    ]},
    {"num": 5, "title": "数学广角——鸽巢问题", "domain": "综合与实践", "hours": 3},
    {"num": 6, "title": "整理和复习", "domain": "综合", "hours": 27, "children": [
        {"num": 61, "title": "数与代数", "hours": 10},
        {"num": 62, "title": "图形与几何", "hours": 9},
        {"num": 63, "title": "统计与概率", "hours": 4},
        {"num": 64, "title": "综合应用", "hours": 4},
    ]},
]

WEEKLY_SCHEDULE = [
    (1, 1, "2026-02-23", "2026-02-27"),
    (2, 2, "2026-03-02", "2026-03-06"),
    (3, 2, "2026-03-09", "2026-03-13"),
    (4, 3, "2026-03-16", "2026-03-20"),
    (5, 3, "2026-03-23", "2026-03-27"),
    (6, 3, "2026-03-30", "2026-04-03"),
    (7, 4, "2026-04-06", "2026-04-10"),
    (8, 4, "2026-04-13", "2026-04-17"),
    (9, 4, "2026-04-20", "2026-04-24"),
    (10, 4, "2026-04-27", "2026-05-01"),
    (11, 5, "2026-05-04", "2026-05-08"),
    (12, 5, "2026-05-11", "2026-05-15"),
    (13, 6, "2026-05-18", "2026-05-22"),
    (14, 6, "2026-05-25", "2026-05-29"),
    (15, 6, "2026-06-01", "2026-06-05"),
    (16, 6, "2026-06-08", "2026-06-12"),
    (17, 6, "2026-06-15", "2026-06-19"),
    (18, 6, "2026-06-22", "2026-06-26"),
]

HOLIDAY_WEEKS = {
    6: ("清明节", "2026-04-04"),
    10: ("劳动节", "2026-05-01"),
    15: ("端午节", "2026-06-05"),
}

CLASS_ID = "G6A1"
CLASS_NAME = "六年级1班"
ACADEMIC_YEAR = "2025-2026"

STUDENT_NAMES = [
    "王子涵", "李思琪", "张浩然", "刘雨萱", "陈梓轩",
    "杨诗涵", "黄俊杰", "赵梦琪", "周思远", "吴佳怡",
]


async def seed():
    await init_db()
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) FROM teaching_units")
        count = (await cursor.fetchone())[0]
        if count > 0:
            print(f"Curriculum already seeded ({count} units). Skipping.")
            return

        parent_map: dict[int, str] = {}
        for unit in UNITS:
            uid = f"U{unit['num']:02d}"
            await db.execute(
                """INSERT INTO teaching_units (id, grade, semester, unit_number, title, domain, hours_planned, sort_order)
                   VALUES (?, 6, 2, ?, ?, ?, ?, ?)""",
                (uid, unit["num"], unit["title"], unit["domain"], unit["hours"], unit["num"]),
            )
            parent_map[unit["num"]] = uid
            for i, child in enumerate(unit.get("children", [])):
                cid = f"U{child['num']:02d}"
                await db.execute(
                    """INSERT INTO teaching_units (id, grade, semester, unit_number, title, domain, hours_planned, sort_order, parent_id)
                       VALUES (?, 6, 2, ?, ?, ?, ?, ?, ?)""",
                    (cid, child["num"], child["title"], unit["domain"], child["hours"], i + 1, uid),
                )
        print(f"Seeded {len(UNITS)} top-level units + sub-units.")

        await db.execute(
            """INSERT OR REPLACE INTO classes (id, name, grade, academic_year, semester, student_ids)
               VALUES (?, ?, 6, ?, 'spring', ?)""",
            (CLASS_ID, CLASS_NAME, ACADEMIC_YEAR, json.dumps([f"S{i+1:03d}" for i in range(10)])),
        )

        for week_num, unit_num, start, end in WEEKLY_SCHEDULE:
            sid = f"SCH_{CLASS_ID}_W{week_num:02d}"
            unit_id = parent_map.get(unit_num, f"U{unit_num:02d}")
            holiday = HOLIDAY_WEEKS.get(week_num)
            notes = ""
            if holiday:
                notes = f"含{holiday[0]}假期"
            await db.execute(
                """INSERT OR REPLACE INTO teaching_schedule (id, class_id, week_number, unit_id, start_date, end_date, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sid, CLASS_ID, week_num, unit_id, start, end, notes),
            )
        print(f"Seeded {len(WEEKLY_SCHEDULE)} weeks of schedule for {CLASS_ID}.")

        for week_num, unit_num, start, end in WEEKLY_SCHEDULE:
            cw_id = f"CW_{ACADEMIC_YEAR}_S2_W{week_num:02d}"
            holiday = HOLIDAY_WEEKS.get(week_num)
            is_holiday = 1 if holiday else 0
            label = holiday[0] if holiday else ""
            await db.execute(
                """INSERT OR REPLACE INTO calendar_weeks (id, academic_year, semester, week_number, start_date, end_date, is_holiday, label)
                   VALUES (?, ?, 2, ?, ?, ?, ?, ?)""",
                (cw_id, ACADEMIC_YEAR, week_num, start, end, is_holiday, label),
            )
        print(f"Seeded 18 calendar weeks.")

        for i, name in enumerate(STUDENT_NAMES):
            sid = f"S{i+1:03d}"
            await db.execute(
                """INSERT OR REPLACE INTO students (id, name, grade, class_id, start_grade, enrolled_at, personality_tags)
                   VALUES (?, ?, 6, ?, 1, '2020-09-01', '[]')""",
                (sid, name, CLASS_ID),
            )
        print(f"Seeded {len(STUDENT_NAMES)} students.")

        await db.commit()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(seed())

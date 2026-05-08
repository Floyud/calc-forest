"""Seed 人教版六年级上册 (Grade 6, Semester 1, 2025 Autumn) curriculum data.

Units focus on calculation-related content per teacher feedback:
- 分数乘法, 位置与方向, 分数除法, 比, 圆, 百分数, 扇形统计图

Simulation time point: Week 8 (~mid-October 2025), during 分数除法 unit.
"""
from __future__ import annotations

import asyncio
import json
from app.db import init_db, get_db

# 人教版六年级上册单元（含计算单元标记）
UNITS = [
    {"num": 1, "title": "分数乘法", "domain": "数与代数", "hours": 8, "calc": True, "children": [
        {"num": 11, "title": "分数乘整数", "hours": 2},
        {"num": 12, "title": "分数乘分数", "hours": 2},
        {"num": 13, "title": "分数乘法的简便运算", "hours": 2},
        {"num": 14, "title": "解决问题（分数乘法）", "hours": 2},
    ]},
    {"num": 2, "title": "位置与方向（二）", "domain": "图形与几何", "hours": 4, "calc": False},
    {"num": 3, "title": "分数除法", "domain": "数与代数", "hours": 10, "calc": True, "children": [
        {"num": 31, "title": "倒数", "hours": 1},
        {"num": 32, "title": "分数除以整数", "hours": 2},
        {"num": 33, "title": "整数除以分数", "hours": 2},
        {"num": 34, "title": "分数除以分数", "hours": 2},
        {"num": 35, "title": "解决问题（分数除法）", "hours": 3},
    ]},
    {"num": 4, "title": "比", "domain": "数与代数", "hours": 6, "calc": True, "children": [
        {"num": 41, "title": "比的意义", "hours": 2},
        {"num": 42, "title": "比的基本性质", "hours": 2},
        {"num": 43, "title": "比的应用", "hours": 2},
    ]},
    {"num": 5, "title": "圆", "domain": "图形与几何", "hours": 8, "calc": True, "children": [
        {"num": 51, "title": "圆的认识", "hours": 2},
        {"num": 52, "title": "圆的周长", "hours": 2},
        {"num": 53, "title": "圆的面积", "hours": 3},
        {"num": 54, "title": "扇形", "hours": 1},
    ]},
    {"num": 6, "title": "百分数（一）", "domain": "数与代数", "hours": 8, "calc": True, "children": [
        {"num": 61, "title": "百分数的意义和写法", "hours": 1},
        {"num": 62, "title": "百分数与小数的互化", "hours": 2},
        {"num": 63, "title": "百分数与分数的互化", "hours": 2},
        {"num": 64, "title": "用百分数解决问题", "hours": 3},
    ]},
    {"num": 7, "title": "扇形统计图", "domain": "统计与概率", "hours": 3, "calc": False},
    {"num": 8, "title": "数学广角——数与形", "domain": "综合与实践", "hours": 3, "calc": False},
]

# 2025秋学期校历（约18周，9月1日开学）
WEEKLY_SCHEDULE = [
    # (week_num, unit_num, start_date, end_date)
    (1,  1, "2025-09-01", "2025-09-05"),   # 第1周：开学 + 分数乘法起步
    (2,  1, "2025-09-08", "2025-09-12"),   # 第2周：分数乘法
    (3,  1, "2025-09-15", "2025-09-19"),   # 第3周：分数乘法（续）
    (4,  2, "2025-09-22", "2025-09-26"),   # 第4周：位置与方向
    (5,  3, "2025-10-06", "2025-10-10"),   # 第5周：分数除法起步（国庆后）
    (6,  3, "2025-10-13", "2025-10-17"),   # 第6周：分数除法
    (7,  3, "2025-10-20", "2025-10-24"),   # 第7周：分数除法（续）
    (8,  3, "2025-10-27", "2025-10-31"),   # 第8周：分数除法解决问题 ← 模拟时间点
    (9,  4, "2025-11-03", "2025-11-07"),   # 第9周：比
    (10, 4, "2025-11-10", "2025-11-14"),   # 第10周：比（续）
    (11, 5, "2025-11-17", "2025-11-21"),   # 第11周：圆
    (12, 5, "2025-11-24", "2025-11-28"),   # 第12周：圆（续）
    (13, 5, "2025-12-01", "2025-12-05"),   # 第13周：圆（续）
    (14, 6, "2025-12-08", "2025-12-12"),   # 第14周：百分数
    (15, 6, "2025-12-15", "2025-12-19"),   # 第15周：百分数（续）
    (16, 7, "2025-12-22", "2025-12-26"),   # 第16周：扇形统计图
    (17, 8, "2026-01-05", "2026-01-09"),   # 第17周：数学广角
    (18, 8, "2026-01-12", "2026-01-16"),   # 第18周：期末复习（归入数学广角周）
]

HOLIDAY_WEEKS = {
    5: ("国庆节", "2025-10-01"),   # 第5周实际从10月6日开始（国庆调休）
}

CLASS_ID = "G6A1"
CLASS_NAME = "六年级1班"
ACADEMIC_YEAR = "2025-2026"
SEMESTER = 1  # 秋学期 = 上册 = semester 1

STUDENT_NAMES = [
    "王子涵", "李思琪", "张浩然", "刘雨萱", "陈梓轩",
    "杨诗涵", "黄俊杰", "赵梦琪", "周思远", "吴佳怡",
]

# 模拟时间点：2025年10月30日（第8周周四），分数除法单元解决问题阶段
SIMULATION_DATE = "2025-10-30"


async def seed():
    await init_db()
    async with get_db() as db:
        # Check if autumn units already exist
        cursor = await db.execute(
            "SELECT COUNT(*) FROM teaching_units WHERE grade=6 AND semester=1"
        )
        count = (await cursor.fetchone())[0]
        if count > 0:
            print(f"Grade 6 autumn units already seeded ({count} units). Skipping.")
            return

        parent_map: dict[int, str] = {}
        for unit in UNITS:
            uid = f"U6A{unit['num']:02d}"  # U6A01, U6A02, ... (6=A上册)
            await db.execute(
                """INSERT INTO teaching_units
                   (id, grade, semester, unit_number, title, domain, hours_planned, sort_order)
                   VALUES (?, 6, 1, ?, ?, ?, ?, ?)""",
                (uid, unit["num"], unit["title"], unit["domain"], unit["hours"], unit["num"]),
            )
            parent_map[unit["num"]] = uid
            for i, child in enumerate(unit.get("children", [])):
                cid = f"U6A{child['num']:02d}"
                await db.execute(
                    """INSERT INTO teaching_units
                       (id, grade, semester, unit_number, title, domain, hours_planned, sort_order, parent_id)
                       VALUES (?, 6, 1, ?, ?, ?, ?, ?, ?)""",
                    (cid, child["num"], child["title"], unit["domain"], child["hours"], i + 1, uid),
                )
        print(f"Seeded {len(UNITS)} autumn units + sub-units.")

        # Create class
        await db.execute(
            """INSERT OR REPLACE INTO classes (id, name, grade, academic_year, semester, student_ids)
               VALUES (?, ?, 6, ?, 'autumn', ?)""",
            (CLASS_ID, CLASS_NAME, ACADEMIC_YEAR,
             json.dumps([f"G6A{i+1:03d}" for i in range(10)])),
        )
        print(f"Seeded class {CLASS_ID} ({CLASS_NAME}).")

        # Seed schedule
        for week_num, unit_num, start, end in WEEKLY_SCHEDULE:
            sid = f"SCH_{CLASS_ID}_W{week_num:02d}"
            unit_id = parent_map.get(unit_num, f"U6A{unit_num:02d}")
            notes = ""
            holiday = HOLIDAY_WEEKS.get(week_num)
            if holiday:
                notes = f"含{holiday[0]}假期"
            await db.execute(
                """INSERT INTO teaching_schedule (id, class_id, week_number, unit_id, start_date, end_date, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sid, CLASS_ID, week_num, unit_id, start, end, notes),
            )
        print(f"Seeded {len(WEEKLY_SCHEDULE)} weeks of schedule.")

        # Seed calendar weeks
        for week_num, unit_num, start, end in WEEKLY_SCHEDULE:
            cw_id = f"CW_{ACADEMIC_YEAR}_S1_W{week_num:02d}"
            holiday = HOLIDAY_WEEKS.get(week_num)
            is_holiday = 1 if holiday else 0
            label = holiday[0] if holiday else ""
            await db.execute(
                """INSERT OR REPLACE INTO calendar_weeks
                   (id, academic_year, semester, week_number, start_date, end_date, is_holiday, label)
                   VALUES (?, ?, 1, ?, ?, ?, ?, ?)""",
                (cw_id, ACADEMIC_YEAR, week_num, start, end, is_holiday, label),
            )
        print("Seeded 18 calendar weeks (2025 autumn).")

        # Seed students (with G6A prefix to distinguish from spring semester)
        for i, name in enumerate(STUDENT_NAMES):
            sid = f"G6A{i+1:03d}"
            await db.execute(
                """INSERT OR REPLACE INTO students (id, name, grade, class_id, start_grade, enrolled_at, personality_tags)
                   VALUES (?, ?, 6, ?, 1, '2020-09-01', '[]')""",
                (sid, name, CLASS_ID),
            )
        print(f"Seeded {len(STUDENT_NAMES)} students.")

        # Create academic cycle for simulation
        cycle_id = "CYC_2025_2026_S1"
        await db.execute(
            """INSERT OR REPLACE INTO academic_cycles
               (id, academic_year, grade, cycle_type, start_date, end_date, total_days, practice_goal_days)
               VALUES (?, ?, 6, '学期', '2025-09-01', '2026-01-16', 100, 60)""",
            (cycle_id, ACADEMIC_YEAR),
        )
        print(f"Seeded academic cycle {cycle_id}.")

        await db.commit()
        print(f"\nDone! Simulation time point: {SIMULATION_DATE} (Week 8, 分数除法单元)")
        print(f"Class: {CLASS_ID} ({CLASS_NAME}), {len(STUDENT_NAMES)} students")


if __name__ == "__main__":
    asyncio.run(seed())

#!/usr/bin/env python3
"""
Fill empty database tables to simulate a deeply-used mid-semester system (week 14, mid-May 2026).

Uses ONLY sqlite3 — no asyncio, no FastAPI imports.
Idempotent: safe to run multiple times (INSERT OR IGNORE).
"""

import sqlite3
import uuid
import random
import json
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "calc_forest.db"
CYCLE_ID = "2026-spring-semester"
STUDENT_IDS = [f"S{i:03d}" for i in range(1, 11)]
CLASS_ID = "G6C1"

random.seed(42)


def uid(prefix: str = "") -> str:
    return prefix + uuid.uuid4().hex[:8].upper()


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def ts(offset_days: int = 0, hour: int = 10, minute: int = 0) -> str:
    """Generate ISO timestamp with day offset from 2026-05-28 (mid-semester)."""
    base = datetime(2026, 5, 28, hour, minute, 0)
    t = base + timedelta(days=offset_days)
    return t.strftime("%Y-%m-%d %H:%M:%S")


def random_date_in_range(start: str, end: str) -> str:
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    delta = (e - s).days
    d = s + timedelta(days=random.randint(0, max(delta, 0)))
    return d.strftime("%Y-%m-%d")


# ─── Section 1: knowledge_points ───────────────────────────────────────────────

def fill_knowledge_points(cur: sqlite3.Cursor) -> int:
    """Generate knowledge point entries for error codes E01-E11."""
    points = [
        {
            "id": "KP-E01",
            "error_code": "E01",
            "topic": "基础事实错误",
            "description": "学生在基本计算事实上出错，如乘法口诀记错、加减法基本结果错误。这是最底层的计算错误类型。",
            "method": "通过反复练习乘法口诀表和基本加减法来巩固基础事实记忆。建议使用卡片练习、口算竞赛等方式强化记忆。",
            "example": "题目：7×8=?  学生答案：54（应为56）",
            "prerequisite_ids": "[]",
            "difficulty_level": "A",
            "unit_number": 1,
            "sort_order": 1,
        },
        {
            "id": "KP-E02",
            "error_code": "E02",
            "topic": "进位错误",
            "description": "在进行加法或乘法运算时，忘记向高位进位或进位数值计算错误。常见于多位数加法和乘法。",
            "method": "强调竖式计算中进位的标注习惯，用颜色标记进位数字，建立进位检查机制。练习时要求学生写出每步进位。",
            "example": "题目：47+38=?  学生答案：75（忘记进位，应为85）",
            "prerequisite_ids": '["KP-E01"]',
            "difficulty_level": "B",
            "unit_number": 2,
            "sort_order": 2,
        },
        {
            "id": "KP-E03",
            "error_code": "E03",
            "topic": "退位错误",
            "description": "在进行减法运算时，忘记从高位借位（退位），或退位后高位数字忘记减1。常见于多位数减法。",
            "method": "使用实物教具（如小棒、计数器）演示退位过程，建立退位标注习惯。引导学生说出退位过程，强化理解。",
            "example": "题目：52-27=?  学生答案：35（忘记退位，应为25）",
            "prerequisite_ids": '["KP-E01"]',
            "difficulty_level": "B",
            "unit_number": 2,
            "sort_order": 3,
        },
        {
            "id": "KP-E04",
            "error_code": "E04",
            "topic": "数位对齐错误",
            "description": "竖式计算时数位未正确对齐，导致个位与十位相加等错误。常见于小数加减法和多位数运算。",
            "method": "使用方格纸辅助竖式书写，强调小数点对齐和个位对齐原则。练习时先画竖线分隔数位再计算。",
            "example": "题目：3.5+2.14=?  学生答案：23.9（小数点未对齐，应为5.64）",
            "prerequisite_ids": '["KP-E02", "KP-E03"]',
            "difficulty_level": "B",
            "unit_number": 3,
            "sort_order": 4,
        },
        {
            "id": "KP-E05",
            "error_code": "E05",
            "topic": "运算顺序错误",
            "description": "在混合运算中未按正确顺序计算，忽略括号或运算优先级。如先加减后乘除，或忽略括号内的优先计算。",
            "method": "使用运算顺序口诀：先乘除后加减，有括号先算括号。通过分步标注法让学生逐步标出计算顺序后再执行。",
            "example": "题目：3+4×2=?  学生答案：14（先算3+4，应为11）",
            "prerequisite_ids": '["KP-E01", "KP-E02"]',
            "difficulty_level": "C",
            "unit_number": 4,
            "sort_order": 5,
        },
        {
            "id": "KP-E06",
            "error_code": "E06",
            "topic": "小数与分数转换错误",
            "description": "小数与分数之间的转换出错，或小数点位置错误。包括分数化简、通分、小数四则运算等。",
            "method": "使用数轴可视化小数和分数的关系，建立小数-分数对照表。重点练习常见的分数-小数对应关系（如1/4=0.25）。",
            "example": "题目：0.75=?/?  学生答案：7/5（应为3/4）",
            "prerequisite_ids": '["KP-E01"]',
            "difficulty_level": "C",
            "unit_number": 3,
            "sort_order": 6,
        },
        {
            "id": "KP-E08",
            "error_code": "E08",
            "topic": "步骤遗漏错误",
            "description": "多步运算中遗漏中间步骤，导致最终结果错误。常见于需要先乘除后加减、或有多层运算的情况。",
            "method": "教学生分步写出中间结果，每步完成后检查。使用流程图标注法，将多步运算分解为独立的子步骤。",
            "example": "题目：(12+3)×2=?  学生答案：15（只算了括号内，遗漏×2）",
            "prerequisite_ids": '["KP-E05"]',
            "difficulty_level": "C",
            "unit_number": 4,
            "sort_order": 7,
        },
        {
            "id": "KP-E09",
            "error_code": "E09",
            "topic": "算理理解错误",
            "description": "对运算的数学原理理解不深，机械记忆算法而不理解为什么这样做。导致遇到变式题时无法灵活应对。",
            "method": "通过直观教具和情境帮助学生理解运算背后的原理，不仅教'怎么做'更要教'为什么这样做'。鼓励学生用自己的语言解释算理。",
            "example": "学生知道0.3×0.2的竖式写法，但不理解为什么结果是0.06而不是0.6",
            "prerequisite_ids": '["KP-E05", "KP-E06"]',
            "difficulty_level": "C",
            "unit_number": 4,
            "sort_order": 8,
        },
        {
            "id": "KP-E10",
            "error_code": "E10",
            "topic": "审题错误",
            "description": "未认真阅读题目要求或条件，看错数字、符号或单位。不是计算能力问题，而是审题习惯问题。",
            "method": "培养学生'圈画法'审题习惯：圈出关键词、画线标注数字和条件。做之前先复述题目意思，确认理解无误再动笔。",
            "example": "题目要求'从大到小排列'，学生按'从小到大'排列",
            "prerequisite_ids": "[]",
            "difficulty_level": "A",
            "unit_number": 1,
            "sort_order": 9,
        },
        {
            "id": "KP-E11",
            "error_code": "E11",
            "topic": "未验算错误",
            "description": "计算完成后不进行验算检查，导致已犯的错误未能及时发现和纠正。属于学习习惯问题。",
            "method": "建立验算意识，教给多种验算方法：逆运算检验、估算法、代入法。要求每题必验算，逐步养成检查习惯。",
            "example": "题目：234+567=?  学生答案：701（应为801，未验算发现错误）",
            "prerequisite_ids": "[]",
            "difficulty_level": "A",
            "unit_number": 1,
            "sort_order": 10,
        },
    ]

    count = 0
    for p in points:
        try:
            cur.execute(
                """INSERT OR IGNORE INTO knowledge_points
                   (id, error_code, topic, description, method, example,
                    prerequisite_ids, difficulty_level, unit_number, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p["id"], p["error_code"], p["topic"], p["description"],
                    p["method"], p["example"], p["prerequisite_ids"],
                    p["difficulty_level"], p["unit_number"], p["sort_order"],
                ),
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ knowledge_points {p['id']}: {e}")
    return count


# ─── Section 2: knowledge_points_fts ───────────────────────────────────────────

def fill_knowledge_points_fts(cur: sqlite3.Cursor) -> int:
    # Guard: skip if already populated
    cur.execute("SELECT COUNT(*) FROM knowledge_points_fts")
    if cur.fetchone()[0] > 0:
        return 0

    cur.execute("SELECT id, topic, description, method, example FROM knowledge_points")
    rows = cur.fetchall()
    count = 0
    for row in rows:
        kp_id, topic, description, method, example = row
        # Use numeric rowid derived from the KP id hash for stability
        rowid = hash(kp_id) & 0x7FFFFFFF
        try:
            cur.execute(
                "INSERT OR IGNORE INTO knowledge_points_fts(rowid, id, topic, description, method) VALUES (?, ?, ?, ?, ?)",
                (rowid, kp_id, topic, description, method),
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ FTS {kp_id}: {e}")
    return count


# ─── Section 3: concept_relations ──────────────────────────────────────────────

def fill_concept_relations(cur: sqlite3.Cursor) -> int:
    relations = [
        ("CR01", "KP-E01", "KP-E02", "prerequisite", 0.95),
        ("CR02", "KP-E01", "KP-E03", "prerequisite", 0.95),
        ("CR03", "KP-E02", "KP-E04", "prerequisite", 0.85),
        ("CR04", "KP-E03", "KP-E04", "prerequisite", 0.85),
        ("CR05", "KP-E01", "KP-E05", "prerequisite", 0.80),
        ("CR06", "KP-E05", "KP-E08", "prerequisite", 0.90),
        ("CR07", "KP-E01", "KP-E06", "prerequisite", 0.75),
        ("CR08", "KP-E05", "KP-E09", "prerequisite", 0.88),
        ("CR09", "KP-E06", "KP-E09", "related", 0.70),
        ("CR10", "KP-E02", "KP-E03", "related", 0.85),
        ("CR11", "KP-E01", "KP-E10", "related", 0.60),
        ("CR12", "KP-E01", "KP-E11", "related", 0.65),
        ("CR13", "KP-E08", "KP-E09", "related", 0.72),
        ("CR14", "KP-E04", "KP-E06", "related", 0.78),
        ("CR15", "KP-E05", "KP-E06", "related", 0.68),
    ]
    count = 0
    for r in relations:
        try:
            cur.execute(
                "INSERT OR IGNORE INTO concept_relations (id, source_id, target_id, relation_type, weight) VALUES (?, ?, ?, ?, ?)",
                r,
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ concept_relations {r[0]}: {e}")
    return count


# ─── Section 4: error_code_knowledge_map ────────────────────────────────────────

def fill_error_code_knowledge_map(cur: sqlite3.Cursor) -> int:
    mappings = [
        ("EKM01", "E01", "U01", "负数", "基本运算事实", "乘法口诀记忆错误，加减法基础结果出错", 1),
        ("EKM02", "E01", "U02", "百分数（二）", "百分数基础计算", "百分数与小数互化时基本计算错误", 2),
        ("EKM03", "E02", "U02", "百分数（二）", "进位运算", "百分数加法中进位遗漏", 3),
        ("EKM04", "E02", "U21", "折扣", "折扣计算进位", "折扣金额计算时忘记进位", 4),
        ("EKM05", "E03", "U02", "百分数（二）", "退位运算", "百分数减法中退位遗漏", 5),
        ("EKM06", "E03", "U23", "税率", "退位计算", "计算税额时退位出错", 6),
        ("EKM07", "E04", "U03", "圆柱与圆锥", "数位对齐", "圆柱表面积计算中数位对齐错误", 7),
        ("EKM08", "E04", "U32", "圆柱的表面积", "小数对齐", "小数加减法中小数点未对齐", 8),
        ("EKM09", "E05", "U04", "比例", "运算顺序", "比例计算中运算顺序错误", 9),
        ("EKM10", "E05", "U41", "比例的意义和基本性质", "混合运算顺序", "含比例的混合运算中先加减后乘除", 10),
        ("EKM11", "E06", "U04", "比例", "小数分数转换", "比例计算中小数分数转换错误", 11),
        ("EKM12", "E08", "U04", "比例", "多步运算", "比例应用题中步骤遗漏", 12),
        ("EKM13", "E08", "U43", "比例的应用", "解题步骤", "比例应用题中间步骤遗漏", 13),
        ("EKM14", "E09", "U04", "比例", "算理理解", "不理解比例运算的数学原理", 14),
        ("EKM15", "E09", "U06", "整理和复习", "综合算理", "综合复习中对算理理解不深", 15),
        ("EKM16", "E10", "U05", "数学广角——鸽巢问题", "审题习惯", "未仔细阅读题目条件和要求", 16),
        ("EKM17", "E10", "U25", "解决问题", "审题错误", "应用题审题不仔细", 17),
        ("EKM18", "E11", "U06", "整理和复习", "验算习惯", "计算后不验算检查", 18),
        ("EKM19", "E11", "U61", "数与代数", "检查习惯", "数与代数综合练习中未验算", 19),
        ("EKM20", "E01", "U24", "利率", "基础运算", "利率计算中基础加减乘除错误", 20),
    ]
    count = 0
    for m in mappings:
        try:
            cur.execute(
                """INSERT OR IGNORE INTO error_code_knowledge_map
                   (id, error_code, unit_id, unit_title, knowledge_point, typical_error, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                m,
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ error_code_knowledge_map {m[0]}: {e}")
    return count


# ─── Section 5: exercise_types ──────────────────────────────────────────────────

def fill_exercise_types(cur: sqlite3.Cursor) -> int:
    types = [
        {
            "id": "ET01", "parent_id": None, "category": "计算", "name": "口算速算",
            "code": "oral_calc", "difficulty_range": '["A","B"]',
            "related_error_codes": '["E01","E02","E03"]',
            "knowledge_points": '["基本加减乘除"]',
            "description": "限时口算练习，训练基本计算速度和准确度",
            "example_problem": "25+38=?", "example_answer": "63",
            "sort_order": 1, "is_active": 1, "grade_range": "[1,2,3,4,5,6]",
            "textbook_unit": "通用",
        },
        {
            "id": "ET02", "parent_id": None, "category": "计算", "name": "竖式计算",
            "code": "vertical_calc", "difficulty_range": '["A","B","C"]',
            "related_error_codes": '["E02","E03","E04"]',
            "knowledge_points": '["进位退位运算","数位对齐"]',
            "description": "竖式计算练习，重点训练进位、退位和数位对齐",
            "example_problem": "456+278=?", "example_answer": "734",
            "sort_order": 2, "is_active": 1, "grade_range": "[2,3,4,5,6]",
            "textbook_unit": "通用",
        },
        {
            "id": "ET03", "parent_id": None, "category": "计算", "name": "混合运算",
            "code": "mixed_calc", "difficulty_range": '["B","C"]',
            "related_error_codes": '["E05","E08","E09"]',
            "knowledge_points": '["运算顺序","括号运算"]',
            "description": "含加减乘除和括号的混合运算，训练运算顺序",
            "example_problem": "3+4×2-6÷3=?", "example_answer": "9",
            "sort_order": 3, "is_active": 1, "grade_range": "[3,4,5,6]",
            "textbook_unit": "U04",
        },
        {
            "id": "ET04", "parent_id": None, "category": "应用", "name": "应用题",
            "code": "word_problem", "difficulty_range": '["B","C"]',
            "related_error_codes": '["E10","E08","E09"]',
            "knowledge_points": '["审题理解","多步推理"]',
            "description": "文字应用题，训练审题能力和多步推理",
            "example_problem": "小明有45元，买了3本书每本12元，还剩多少元？",
            "example_answer": "9",
            "sort_order": 4, "is_active": 1, "grade_range": "[2,3,4,5,6]",
            "textbook_unit": "通用",
        },
        {
            "id": "ET05", "parent_id": None, "category": "计算", "name": "计算填空",
            "code": "fill_blank", "difficulty_range": '["A","B"]',
            "related_error_codes": '["E01","E11"]',
            "knowledge_points": '["基础运算","验算"]',
            "description": "填空形式的基础计算，训练逆向思考能力",
            "example_problem": "□+27=63", "example_answer": "36",
            "sort_order": 5, "is_active": 1, "grade_range": "[1,2,3,4,5,6]",
            "textbook_unit": "通用",
        },
        {
            "id": "ET06", "parent_id": None, "category": "判断", "name": "判断对错",
            "code": "true_false", "difficulty_range": '["A","B"]',
            "related_error_codes": '["E01","E09","E11"]',
            "knowledge_points": '["验算判断","算理理解"]',
            "description": "判断计算过程或结果是否正确，训练验算意识",
            "example_problem": "判断：3.5+2.15=5.20（ ）",
            "example_answer": "√",
            "sort_order": 6, "is_active": 1, "grade_range": "[3,4,5,6]",
            "textbook_unit": "通用",
        },
        {
            "id": "ET07", "parent_id": None, "category": "选择", "name": "选择题",
            "code": "multiple_choice", "difficulty_range": '["A","B","C"]',
            "related_error_codes": '["E01","E05","E10"]',
            "knowledge_points": '["综合判断","概念辨析"]',
            "description": "选择题形式，训练概念辨析和综合判断能力",
            "example_problem": "下列哪个计算是正确的？A.3+4×2=14  B.3+4×2=11  C.3+4×2=20",
            "example_answer": "B",
            "sort_order": 7, "is_active": 1, "grade_range": "[2,3,4,5,6]",
            "textbook_unit": "通用",
        },
        {
            "id": "ET08", "parent_id": None, "category": "计算", "name": "估算",
            "code": "estimation", "difficulty_range": '["B","C"]',
            "related_error_codes": '["E09","E11"]',
            "knowledge_points": '["数感","估算策略"]',
            "description": "估算练习，培养数感和估算能力",
            "example_problem": "估算：398×21≈?", "example_answer": "8000",
            "sort_order": 8, "is_active": 1, "grade_range": "[4,5,6]",
            "textbook_unit": "通用",
        },
        {
            "id": "ET09", "parent_id": None, "category": "计算", "name": "分数计算",
            "code": "fraction_calc", "difficulty_range": '["B","C"]',
            "related_error_codes": '["E06","E09"]',
            "knowledge_points": '["分数运算","通分化简"]',
            "description": "分数加减乘除运算，训练分数四则运算能力",
            "example_problem": "1/3+1/4=?", "example_answer": "7/12",
            "sort_order": 9, "is_active": 1, "grade_range": "[5,6]",
            "textbook_unit": "U04",
        },
        {
            "id": "ET10", "parent_id": None, "category": "计算", "name": "比例计算",
            "code": "ratio_calc", "difficulty_range": '["B","C"]',
            "related_error_codes": '["E05","E06","E08"]',
            "knowledge_points": '["比例运算","正反比例"]',
            "description": "比例相关计算，包括正比例、反比例应用",
            "example_problem": "如果3:5=x:20，求x=?", "example_answer": "12",
            "sort_order": 10, "is_active": 1, "grade_range": "[6]",
            "textbook_unit": "U04",
        },
    ]
    count = 0
    for t in types:
        try:
            cur.execute(
                """INSERT OR IGNORE INTO exercise_types
                   (id, parent_id, category, name, code, difficulty_range,
                    related_error_codes, knowledge_points, description,
                    example_problem, example_answer, sort_order, is_active,
                    grade_range, textbook_unit)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    t["id"], t["parent_id"], t["category"], t["name"], t["code"],
                    t["difficulty_range"], t["related_error_codes"],
                    t["knowledge_points"], t["description"], t["example_problem"],
                    t["example_answer"], t["sort_order"], t["is_active"],
                    t["grade_range"], t["textbook_unit"],
                ),
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ exercise_types {t['id']}: {e}")
    return count


# ─── Section 6: problem_bank ────────────────────────────────────────────────────

def fill_problem_bank(cur: sqlite3.Cursor) -> int:
    problems = [
        # E01 - 基础事实错误 (A)
        ("PB-E01-01", "8×7=?", "56", "E01", "乘法口诀", "A", "基础", 42, 1),
        ("PB-E01-02", "9×6=?", "54", "E01", "乘法口诀", "A", "基础", 38, 1),
        ("PB-E01-03", "13+28=?", "41", "E01", "加法基础", "A", "基础", 35, 1),
        ("PB-E01-04", "45-17=?", "28", "E01", "减法基础", "A", "基础", 33, 1),
        ("PB-E01-05", "72÷8=?", "9", "E01", "除法基础", "A", "基础", 30, 1),
        # E02 - 进位错误 (B)
        ("PB-E02-01", "47+38=?", "85", "E02", "进位加法", "B", "竖式", 28, 1),
        ("PB-E02-02", "56+67=?", "123", "E02", "进位加法", "B", "竖式", 25, 1),
        ("PB-E02-03", "28×4=?", "112", "E02", "进位乘法", "B", "竖式", 22, 1),
        ("PB-E02-04", "39+47+15=?", "101", "E02", "连续进位", "B", "竖式", 20, 1),
        ("PB-E02-05", "186+247=?", "433", "E02", "三位数进位", "B", "竖式", 18, 1),
        # E03 - 退位错误 (B)
        ("PB-E03-01", "52-27=?", "25", "E03", "退位减法", "B", "竖式", 26, 1),
        ("PB-E03-02", "103-47=?", "56", "E03", "退位减法", "B", "竖式", 23, 1),
        ("PB-E03-03", "312-158=?", "154", "E03", "连续退位", "B", "竖式", 19, 1),
        ("PB-E03-04", "500-237=?", "263", "E03", "中间有零退位", "B", "竖式", 17, 1),
        ("PB-E03-05", "1000-456=?", "544", "E03", "多次退位", "B", "竖式", 15, 1),
        # E04 - 数位对齐错误 (B)
        ("PB-E04-01", "3.5+2.14=?", "5.64", "E04", "小数对齐", "B", "竖式", 24, 1),
        ("PB-E04-02", "12.5-3.28=?", "9.22", "E04", "小数对齐", "B", "竖式", 21, 1),
        ("PB-E04-03", "456+23=?", "479", "E04", "位数不同对齐", "B", "竖式", 18, 1),
        ("PB-E04-04", "23.7+1.45+0.8=?", "25.95", "E04", "多小数对齐", "B", "竖式", 16, 1),
        ("PB-E04-05", "100.3-45.67=?", "54.63", "E04", "小数退位对齐", "C", "竖式", 14, 1),
        # E05 - 运算顺序错误 (C)
        ("PB-E05-01", "3+4×2=?", "11", "E05", "先乘后加", "C", "分步", 27, 1),
        ("PB-E05-02", "(3+4)×2=?", "14", "E05", "括号优先", "C", "分步", 25, 1),
        ("PB-E05-03", "18-6÷3+2=?", "18", "E05", "混合运算顺序", "C", "分步", 22, 1),
        ("PB-E05-04", "24÷(6-2)×3=?", "18", "E05", "括号与乘除", "C", "分步", 19, 1),
        ("PB-E05-05", "15+3×(7-2)÷5=?", "18", "E05", "综合运算顺序", "C", "分步", 16, 1),
        # E06 - 小数与分数转换 (C)
        ("PB-E06-01", "0.75=?/?（化为最简分数）", "3/4", "E06", "小数化分数", "B", "转换", 20, 1),
        ("PB-E06-02", "3/8=?（化为小数）", "0.375", "E06", "分数化小数", "B", "转换", 18, 1),
        ("PB-E06-03", "0.125+1/4=?", "0.375", "E06", "小数分数混合", "C", "混合", 15, 1),
        ("PB-E06-04", "2/5×0.3=?", "0.12", "E06", "分数小数乘法", "C", "混合", 12, 1),
        ("PB-E06-05", "1.5-3/4=?", "0.75", "E06", "分数小数减法", "C", "混合", 11, 1),
        # E08 - 步骤遗漏 (C)
        ("PB-E08-01", "(12+3)×2+5=?", "35", "E08", "多步运算", "C", "分步", 23, 1),
        ("PB-E08-02", "4×5+3×6-20=?", "28", "E08", "三步运算", "C", "分步", 20, 1),
        ("PB-E08-03", "(8+2)×(9-4)÷5=?", "10", "E08", "四步运算", "C", "分步", 17, 1),
        ("PB-E08-04", "36÷6+4×(7-3)=?", "22", "E08", "混合多步", "C", "分步", 14, 1),
        ("PB-E08-05", "2×(3+4)-10÷2+6=?", "15", "E08", "综合多步", "C", "分步", 12, 1),
        # E09 - 算理理解 (C)
        ("PB-E09-01", "为什么0.3×0.2=0.06而不是0.6？请计算并说明。", "0.06", "E09", "小数乘法算理", "C", "理解", 13, 1),
        ("PB-E09-02", "解释为什么除以一个分数等于乘以它的倒数，并计算2÷1/3=?", "6", "E09", "分数除法算理", "C", "理解", 11, 1),
        ("PB-E09-03", "比较3/4和5/6的大小，用通分说明。", "5/6>3/4", "E09", "通分比较算理", "C", "理解", 9, 1),
        ("PB-E09-04", "计算0.1÷0.01=? 为什么结果变大了？", "10", "E09", "小数除法算理", "C", "理解", 8, 1),
        ("PB-E09-05", "验证：25×4×8=(25×8)×4=? 用运算律说明。", "800", "E09", "运算律理解", "C", "理解", 7, 1),
        # E10 - 审题错误 (A)
        ("PB-E10-01", "计算并从大到小排列：3.5, 3/2, 1.8, 7/3", "7/3>3.5>1.8>3/2", "E10", "审题-排列", "B", "审题", 16, 1),
        ("PB-E10-02", "求36的1/4与18的2/3的差", "0", "E10", "审题-多条件", "B", "审题", 14, 1),
        ("PB-E10-03", "一个数的3倍比15多6，这个数是多少？", "7", "E10", "审题-逆向", "C", "审题", 12, 1),
        ("PB-E10-04", "甲数是24，乙数比甲数多1/3，乙数是多少？", "32", "E10", "审题-条件", "C", "审题", 10, 1),
        ("PB-E10-05", "把3/5、0.6、2/3从小到大排列", "0.6=3/5<2/3", "E10", "审题-排列", "B", "审题", 9, 1),
        # E11 - 未验算 (A)
        ("PB-E11-01", "计算并验算：456+289=?", "745", "E11", "加法验算", "B", "验算", 21, 1),
        ("PB-E11-02", "计算并验算：803-567=?", "236", "E11", "减法验算", "B", "验算", 19, 1),
        ("PB-E11-03", "计算并验算：34×26=?", "884", "E11", "乘法验算", "B", "验算", 16, 1),
        ("PB-E11-04", "计算并验算：918÷27=?", "34", "E11", "除法验算", "B", "验算", 14, 1),
        ("PB-E11-05", "计算并用两种方法验算：12.5×0.8=?", "10", "E11", "小数验算", "C", "验算", 11, 1),
    ]

    count = 0
    for p in problems:
        pid, text, answer, ec, kp, diff, method, use_count, verified = p
        created = ts(random.randint(-90, -10))
        try:
            cur.execute(
                """INSERT OR IGNORE INTO problem_bank
                   (id, problem_text, problem_plain, correct_answer, error_code,
                    knowledge_point, difficulty, method, source, use_count, verified, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pid, text, text, answer, ec, kp, diff, method, "system", use_count, verified, created),
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ problem_bank {pid}: {e}")
    return count


# ─── Section 7: practice_weeks ──────────────────────────────────────────────────

def fill_practice_weeks(cur: sqlite3.Cursor) -> int:
    # Read calendar weeks for date info
    cur.execute("SELECT week_number, start_date, end_date, label FROM calendar_weeks ORDER BY week_number")
    weeks = cur.fetchall()
    week_labels = {
        1: "负数入门", 2: "百分数基础", 3: "百分数应用",
        4: "圆柱认识", 5: "圆柱表面积", 6: "圆柱体积",
        7: "圆锥与比例", 8: "比例性质", 9: "比例应用",
        10: "数学广角", 11: "数与代数复习", 12: "图形几何复习",
        13: "统计概率复习", 14: "综合应用复习", 15: "期末复习一",
        16: "期末复习二", 17: "期末复习三", 18: "期末综合",
    }
    count = 0
    for w in weeks:
        wn, sd, ed, orig_label = w
        label = week_labels.get(wn, orig_label or f"第{wn}周")
        pw_id = f"PW-{CYCLE_ID}-W{wn:02d}"
        try:
            cur.execute(
                """INSERT OR IGNORE INTO practice_weeks
                   (id, cycle_id, week_number, start_date, end_date, label)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (pw_id, CYCLE_ID, wn, sd, ed, label),
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ practice_weeks {pw_id}: {e}")
    return count


# ─── Section 8: student_practice_sessions ────────────────────────────────────────

def fill_student_practice_sessions(cur: sqlite3.Cursor) -> int:
    """Generate 3-5 practice sessions per student (30-50 total). Idempotent via guard check."""
    # Guard: skip if sessions already exist
    cur.execute("SELECT COUNT(*) FROM student_practice_sessions")
    if cur.fetchone()[0] > 0:
        return 0

    error_code_combos = [
        '["E01","E02"]', '["E02","E03"]', '["E04","E05"]', '["E05","E08"]',
        '["E06","E09"]', '["E10","E11"]', '["E01","E03"]', '["E05","E06"]',
        '["E08","E09"]', '["E02","E04"]',
    ]
    difficulties = ["A", "B", "C"]

    count = 0
    for si, student_id in enumerate(STUDENT_IDS):
        num_sessions = random.randint(3, 5)
        for j in range(num_sessions):
            session_id = f"SP-{si:02d}-{j:02d}"
            error_codes = random.choice(error_code_combos)
            difficulty = random.choice(difficulties)
            problems_done = random.randint(5, 10)
            correct_count = int(problems_done * random.uniform(0.55, 0.85))
            # Dates spread across Apr-May 2026
            day_offset = random.randint(-60, -5)
            started = ts(day_offset, random.randint(14, 18), random.randint(0, 59))
            ended = ts(day_offset, random.randint(18, 21), random.randint(0, 59))
            status = "completed"
            try:
                cur.execute(
                    """INSERT OR IGNORE INTO student_practice_sessions
                       (id, student_id, error_codes, difficulty, started_at, ended_at,
                        problems_done, correct_count, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (session_id, student_id, error_codes, difficulty, started, ended,
                     problems_done, correct_count, status),
                )
                if cur.rowcount > 0:
                    count += 1
            except Exception as e:
                print(f"  ⚠ practice_session {session_id}: {e}")
    return count


# ─── Section 9: student_practice_problems ────────────────────────────────────────

def fill_student_practice_problems(cur: sqlite3.Cursor) -> int:
    """Generate 5-10 problems per practice session. ~65% correct rate."""
    # Guard: skip if problems already exist
    cur.execute("SELECT COUNT(*) FROM student_practice_problems")
    if cur.fetchone()[0] > 0:
        return 0

    problem_pool = {
        "E01": [("8×7", "56"), ("9×6", "54"), ("13+28", "41"), ("45-17", "28"), ("72÷8", "9"), ("6×8", "48"), ("15+27", "42")],
        "E02": [("47+38", "85"), ("56+67", "123"), ("28×4", "112"), ("186+247", "433"), ("39+47+15", "101")],
        "E03": [("52-27", "25"), ("103-47", "56"), ("312-158", "154"), ("500-237", "263"), ("1000-456", "544")],
        "E04": [("3.5+2.14", "5.64"), ("12.5-3.28", "9.22"), ("456+23", "479"), ("23.7+1.45", "25.15")],
        "E05": [("3+4×2", "11"), ["(3+4)×2", "14"], ("18-6÷3+2", "18"), ("24÷(6-2)×3", "18")],
        "E06": [("0.75化为分数", "3/4"), ("3/8化为小数", "0.375"), ("1.5-3/4", "0.75"), ("2/5×0.3", "0.12")],
        "E08": [("(12+3)×2+5", "35"), ("4×5+3×6-20", "28"), ("36÷6+4×(7-3)", "22"), ("2×(3+4)-10÷2+6", "15")],
        "E09": [("0.3×0.2", "0.06"), ("2÷1/3", "6"), ("比较3/4和5/6", "5/6>3/4"), ("0.1÷0.01", "10")],
        "E10": [("36的1/4与18的2/3的差", "0"), ("甲数24乙数比甲数多1/3乙数", "32")],
        "E11": [("456+289", "745"), ("803-567", "236"), ("34×26", "884"), ("918÷27", "34")],
    }

    # Error patterns for generating wrong answers
    def make_wrong_answer(correct: str) -> str:
        try:
            val = float(correct)
            # Common error patterns
            err_type = random.choice(["off_by_one", "digit_swap", "sign_err", "off_by_ten"])
            if err_type == "off_by_one":
                return str(val + random.choice([-1, 1]))
            elif err_type == "digit_swap":
                s = correct.replace(".", "")
                if len(s) >= 2:
                    idx = random.randint(0, len(s) - 2)
                    s = s[:idx] + s[idx + 1] + s[idx] + s[idx + 2:]
                    if "." in correct:
                        pos = correct.index(".")
                        s = s[:pos] + "." + s[pos:]
                    return s
                return str(val + random.randint(-10, 10))
            elif err_type == "sign_err":
                return str(abs(val) + random.randint(1, 5))
            else:
                return str(val + random.choice([10, -10, 100, -100]))
        except (ValueError, IndexError):
            return correct + "（有误）"

    # Get all sessions
    cur.execute("SELECT id, student_id, error_codes, difficulty, problems_done, started_at FROM student_practice_sessions")
    sessions = cur.fetchall()
    count = 0

    for session in sessions:
        session_id, student_id, error_codes_json, difficulty, problems_done, started_at = session
        try:
            target_codes = json.loads(error_codes_json)
        except (json.JSONDecodeError, TypeError):
            target_codes = ["E01"]

        for seq in range(1, problems_done + 1):
            prob_id = f"PP-{session_id}-S{seq:02d}"
            target_ec = random.choice(target_codes)
            pool = problem_pool.get(target_ec, problem_pool["E01"])
            prob = random.choice(pool)
            problem_text, correct_answer = prob[0], prob[1]

            is_correct = random.random() < 0.65  # 65% correct rate
            if is_correct:
                student_answer = correct_answer
                error_code = None
            else:
                student_answer = make_wrong_answer(correct_answer)
                error_code = target_ec

            answered_at = started_at  # Rough approximation

            try:
                cur.execute(
                    """INSERT OR IGNORE INTO student_practice_problems
                       (id, session_id, sequence, problem, correct_answer,
                        target_error_code, difficulty, student_answer, is_correct,
                        error_code, answered_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (prob_id, session_id, seq, problem_text, correct_answer,
                     target_ec, difficulty, student_answer, int(is_correct),
                     error_code, answered_at),
                )
                if cur.rowcount > 0:
                    count += 1
            except Exception as e:
                print(f"  ⚠ practice_problem {prob_id}: {e}")
    return count


# ─── Section 10: scanned_submissions ────────────────────────────────────────────

def fill_scanned_submissions(cur: sqlite3.Cursor) -> int:
    """Generate ~20 scanned submission entries using existing G6C1 graded homework."""
    # Guard: skip if already populated
    cur.execute("SELECT COUNT(*) FROM scanned_submissions")
    if cur.fetchone()[0] > 0:
        return 0

    cur.execute("SELECT id FROM homework WHERE class_id='G6C1' AND status='graded' ORDER BY id")
    hw_ids = [r[0] for r in cur.fetchall()]

    count = 0
    used_pairs = set()
    for idx in range(20):
        hw_id = random.choice(hw_ids)
        student_id = random.choice(STUDENT_IDS)
        pair = (hw_id, student_id)
        if pair in used_pairs:
            continue
        used_pairs.add(pair)

        scan_id = f"SC-{idx:02d}"
        day_offset = random.randint(-60, -5)
        uploaded = ts(day_offset, random.randint(8, 17), random.randint(0, 59))
        reviewed = ts(day_offset, random.randint(18, 22), random.randint(0, 59))
        pdf_path = f"/uploads/scanned/{student_id}/{hw_id}.pdf"
        ocr_result = json.dumps({
            "pages": random.randint(1, 3),
            "confidence": round(random.uniform(0.88, 0.98), 2),
            "problems_detected": random.randint(4, 8),
        }, ensure_ascii=False)

        try:
            cur.execute(
                """INSERT OR IGNORE INTO scanned_submissions
                   (id, student_id, homework_id, pdf_path, ocr_status,
                    ocr_result_json, graded_status, uploaded_at, reviewed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (scan_id, student_id, hw_id, pdf_path, "completed",
                 ocr_result, "graded", uploaded, reviewed),
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ scanned_submission {scan_id}: {e}")
    return count


# ─── Section 11: grading_comments ───────────────────────────────────────────────

def fill_grading_comments(cur: sqlite3.Cursor) -> int:
    """Generate ~40 AI grading comments for graded homework."""
    # Guard: skip if already populated
    cur.execute("SELECT COUNT(*) FROM grading_comments")
    if cur.fetchone()[0] > 0:
        return 0

    cur.execute("SELECT id FROM homework WHERE class_id='G6C1' AND status='graded' ORDER BY id")
    hw_ids = [r[0] for r in cur.fetchall()]

    comment_templates = [
        ("退位时忘记向高位借1，导致十位计算错误", "E03"),
        ("运算顺序正确，但最后一步计算有误", "E01"),
        ("进位加法中忘记向百位进1", "E02"),
        ("小数点未对齐，导致加法结果错误", "E04"),
        ("混合运算中应先算乘除，运算顺序有误", "E05"),
        ("中间步骤遗漏，注意检查每一步", "E08"),
        ("分数化简不彻底，2/4应化简为1/2", "E06"),
        ("审题不仔细，注意看清题目要求", "E10"),
        ("计算正确但未进行验算检查", "E11"),
        ("乘法口诀记忆有误，8×7=56而非54", "E01"),
        ("退位后高位未减1，注意退位标注", "E03"),
        ("括号内的运算应优先计算", "E05"),
        ("小数乘法中积的小数位数计算有误", "E09"),
        ("连续退位时中间位出错", "E03"),
        ("这道题计算完全正确，继续保持！", None),
        ("步骤完整，过程规范，答案正确", None),
        ("注意除法验算用乘法验证", "E11"),
        ("百分数转小数时小数点移动方向有误", "E06"),
        ("多步运算需要写出中间过程", "E08"),
        ("数位对齐正确，计算过程无误", None),
    ]

    count = 0
    for idx in range(40):
        hw_id = random.choice(hw_ids)
        student_id = random.choice(STUDENT_IDS)
        seq = random.randint(1, 5)
        template = random.choice(comment_templates)
        ai_comment, ec = template
        confidence = round(random.uniform(0.75, 0.98), 2)
        day_offset = random.randint(-60, -3)
        created = ts(day_offset, random.randint(16, 22), random.randint(0, 59))
        comment_id = f"GC-{idx:02d}"

        try:
            cur.execute(
                """INSERT OR IGNORE INTO grading_comments
                   (id, homework_id, student_id, problem_sequence, ai_comment,
                    error_code, confidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (comment_id, hw_id, student_id, seq, ai_comment, ec, confidence, created),
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ grading_comment {comment_id}: {e}")
    return count


# ─── Section 12: quiz_student_answers ───────────────────────────────────────────

def fill_quiz_student_answers(cur: sqlite3.Cursor) -> int:
    """Generate student answers for existing quiz_responses."""
    # Guard: skip if already populated
    cur.execute("SELECT COUNT(*) FROM quiz_student_answers")
    if cur.fetchone()[0] > 0:
        return 0

    # Get G6C1 quiz sessions with problem info
    cur.execute("SELECT id FROM quiz_sessions WHERE class_id='G6C1'")
    quiz_ids = [r[0] for r in cur.fetchall()]

    if not quiz_ids:
        return 0

    # Get quiz problems for each quiz
    quiz_problems = {}
    for qid in quiz_ids:
        cur.execute("SELECT sequence, correct_answer, target_error_code FROM quiz_problems WHERE quiz_id=?", (qid,))
        quiz_problems[qid] = cur.fetchall()

    # Get quiz responses
    placeholders = ",".join(["?"] * len(quiz_ids))
    cur.execute(f"SELECT id, quiz_id, problem_sequence FROM quiz_responses WHERE quiz_id IN ({placeholders})", quiz_ids)
    responses = cur.fetchall()

    # Correct answers map: quiz_id -> {sequence: correct_answer}
    correct_map = {}
    for qid, probs in quiz_problems.items():
        correct_map[qid] = {p[0]: p[1] for p in probs}

    count = 0
    answer_idx = 0
    for resp in responses:
        resp_id, quiz_id, problem_seq = resp
        # Generate 2-3 student answers per response (class aggregate)
        for j in range(random.randint(2, 3)):
            answer_id = f"QA-{answer_idx:04d}"
            answer_idx += 1
            student_id = random.choice(STUDENT_IDS)
            ca_map = correct_map.get(quiz_id, {})
            correct = ca_map.get(problem_seq, "?")

            is_correct = random.random() < 0.68
            if is_correct:
                student_answer = correct
            else:
                # Generate a plausible wrong answer
                try:
                    val = float(correct)
                    student_answer = str(val + random.choice([-1, 1, 10, -10, 0.1, -0.1]))
                except (ValueError, IndexError):
                    student_answer = correct + "（错）"

            day_offset = random.randint(-70, -5)
            answered = ts(day_offset, random.randint(8, 16), random.randint(0, 59))

            try:
                cur.execute(
                    """INSERT OR IGNORE INTO quiz_student_answers
                       (id, quiz_id, student_id, problem_sequence, student_answer,
                        is_correct, answered_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (answer_id, quiz_id, student_id, problem_seq, student_answer,
                     int(is_correct), answered),
                )
                if cur.rowcount > 0:
                    count += 1
            except Exception as e:
                print(f"  ⚠ quiz_answer {answer_id}: {e}")
    return count


# ─── Section 13: week_calc_mapping ──────────────────────────────────────────────

def fill_week_calc_mapping(cur: sqlite3.Cursor) -> int:
    mappings = [
        ("WCM01", 1, 3, "加减法运算", '["口算加法","口算减法","竖式加减"]', '["E01","E02","E03"]', 0, "[]", 1, 6),
        ("WCM02", 4, 6, "乘除法运算", '["乘法竖式","除法竖式","余数处理"]', '["E04","E05"]', 0, "[]", 1, 6),
        ("WCM03", 7, 9, "小数与分数", '["小数加减","小数乘除","分数基础"]', '["E06"]', 0, "[]", 1, 6),
        ("WCM04", 10, 12, "混合运算", '["四则混合","括号运算","简便计算"]', '["E05","E08"]', 0, "[]", 1, 6),
        ("WCM05", 13, 15, "综合复习", '["综合计算","应用题","易错题集"]', '["E09","E10","E11"]', 1, '["加减法","乘除法"]', 1, 6),
        ("WCM06", 16, 18, "期末复习", '["全册复习","模拟测试","查漏补缺"]', '["E01","E02","E03","E04","E05","E06","E08","E09","E10","E11"]', 1, '["全部单元"]', 1, 6),
        # More granular mappings
        ("WCM07", 1, 1, "口算加法", '["一位数加法","两位数加法"]', '["E01","E02"]', 0, "[]", 1, 6),
        ("WCM08", 2, 2, "口算减法与退位", '["退位减法","连续退位"]', '["E01","E03"]', 0, "[]", 1, 6),
        ("WCM09", 3, 3, "竖式计算基础", '["竖式加法","竖式减法","数位对齐"]', '["E02","E03","E04"]', 0, "[]", 1, 6),
        ("WCM10", 4, 4, "乘法竖式", '["一位数乘法","两位数乘法","进位乘法"]', '["E02","E04"]', 0, "[]", 1, 6),
        ("WCM11", 5, 5, "除法竖式", '["一位数除法","有余数除法","试商"]', '["E01","E04"]', 0, "[]", 1, 6),
        ("WCM12", 6, 6, "余数与验算", '["余数概念","验算方法"]', '["E01","E11"]', 0, "[]", 1, 6),
        ("WCM13", 7, 7, "小数认识与加减", '["小数意义","小数加减法"]', '["E04","E06"]', 0, "[]", 1, 6),
        ("WCM14", 8, 8, "小数乘除法", '["小数乘法","小数除法"]', '["E06","E09"]', 0, "[]", 1, 6),
        ("WCM15", 9, 9, "分数基础", '["分数意义","分数加减","约分通分"]', '["E06"]', 0, "[]", 1, 6),
        ("WCM16", 10, 10, "四则混合运算", '["无括号混合","有括号混合"]', '["E05","E08"]', 0, "[]", 1, 6),
        ("WCM17", 11, 11, "简便计算", '["运算律应用","凑整策略"]', '["E05","E09"]', 0, "[]", 1, 6),
        ("WCM18", 12, 12, "应用题综合", '["审题训练","多步推理"]', '["E10","E08"]', 0, "[]", 1, 6),
    ]
    count = 0
    for m in mappings:
        try:
            cur.execute(
                """INSERT OR IGNORE INTO week_calc_mapping
                   (id, week_start, week_end, calc_type, calc_subtypes,
                    error_codes, is_review, review_types, semester, grade)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                m,
            )
            if cur.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  ⚠ week_calc_mapping {m[0]}: {e}")
    return count


# ─── Section 14: Fix class summary total_attempts ──────────────────────────────

def fix_class_summary(cur: sqlite3.Cursor) -> int:
    """Update total_attempts in student_error_stats to realistic numbers."""
    cur.execute("SELECT COUNT(*) FROM student_error_stats WHERE total_attempts=0")
    zero_count = cur.fetchone()[0]
    if zero_count == 0:
        return 0

    # Update existing stats with realistic attempt counts
    cur.execute("SELECT id, student_id, error_code FROM student_error_stats")
    stats = cur.fetchall()
    updated = 0
    for stat_id, student_id, error_code in stats:
        # Different error codes have different frequencies
        freq_map = {
            "E01": (15, 35), "E02": (10, 25), "E03": (10, 25),
            "E04": (8, 20), "E05": (12, 28), "E06": (6, 18),
            "E08": (8, 22), "E09": (5, 15), "E10": (8, 18), "E11": (6, 16),
        }
        lo, hi = freq_map.get(error_code, (8, 20))
        total = random.randint(lo, hi)
        correct = int(total * random.uniform(0.55, 0.80))
        last_seen = ts(random.randint(-30, -1), random.randint(8, 18), 0)

        cur.execute(
            "UPDATE student_error_stats SET total_attempts=?, correct_count=?, last_seen_at=? WHERE id=? AND total_attempts=0",
            (total, correct, last_seen, stat_id),
        )
        if cur.rowcount > 0:
            updated += 1
    return updated


# ─── Section 15: Fix homework completion_rate ───────────────────────────────────

def fix_completion_rate(cur: sqlite3.Cursor) -> int:
    """
    Fix homework submissions to have better completion coverage.
    Only adds missing submissions; skips homework already at target.
    """
    # Guard: check if we already boosted (if avg submissions > 7, skip)
    cur.execute("""SELECT AVG(sub_count) FROM (
        SELECT COUNT(s.id) as sub_count 
        FROM homework h 
        LEFT JOIN homework_submissions s ON h.id = s.homework_id 
        WHERE h.class_id='G6C1' 
        GROUP BY h.id
    )""")
    avg = cur.fetchone()[0]
    if avg and avg >= 7.0:
        return 0

    cur.execute("SELECT id, status FROM homework WHERE class_id='G6C1'")
    homework_list = cur.fetchall()

    updated_hw = 0

    for hw_id, hw_status in homework_list:
        # Check how many submissions exist for this homework
        cur.execute("SELECT COUNT(*) FROM homework_submissions WHERE homework_id=?", (hw_id,))
        sub_count = cur.fetchone()[0]

        # Get existing student IDs who already submitted
        cur.execute("SELECT student_id FROM homework_submissions WHERE homework_id=?", (hw_id,))
        existing_students = {r[0] for r in cur.fetchall()}

        # Add missing submissions to reach ~85% of 10 students = 8-9 per homework
        target_count = random.randint(8, 10)
        missing_count = target_count - sub_count

        if missing_count <= 0:
            continue

        available = [s for s in STUDENT_IDS if s not in existing_students]
        to_add = random.sample(available, min(missing_count, len(available)))

        for student_id in to_add:
            sub_id = uid("HS-")
            # Submission dates near homework dates
            cur.execute("SELECT assigned_date, due_date FROM homework WHERE id=?", (hw_id,))
            row = cur.fetchone()
            if row and row[0]:
                submitted = random_date_in_range(row[0], row[1] or row[0])
            else:
                submitted = ts(random.randint(-80, -5), random.randint(8, 17), 0)

            try:
                cur.execute(
                    """INSERT OR IGNORE INTO homework_submissions
                       (id, homework_id, student_id, submitted_at, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (sub_id, hw_id, student_id, submitted, "graded"),
                )
            except Exception:
                pass

        updated_hw += 1

    return updated_hw


# ─── Main ────────────────────────────────────────────────────────────────────────

def main():
    print(f"📂 DB: {DB_PATH}")
    if not DB_PATH.exists():
        print(f"❌ 数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Verify existing data
    cur.execute("SELECT COUNT(*) FROM students")
    print(f"✅ 学生数: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM homework WHERE class_id='G6C1'")
    print(f"✅ G6C1作业数: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM homework WHERE class_id='G6C1' AND status='graded'")
    print(f"✅ 已批改作业: {cur.fetchone()[0]}")

    print("\n" + "=" * 60)
    print("开始填充空表数据")
    print("=" * 60)

    # Section 1: knowledge_points
    print("\n📌 [1/15] knowledge_points — 错因知识点")
    n = fill_knowledge_points(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 2: knowledge_points_fts
    print("\n📌 [2/15] knowledge_points_fts — 全文搜索索引")
    n = fill_knowledge_points_fts(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 3: concept_relations
    print("\n📌 [3/15] concept_relations — 知识图谱关系")
    n = fill_concept_relations(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 4: error_code_knowledge_map
    print("\n📌 [4/15] error_code_knowledge_map — 错因代码映射")
    n = fill_error_code_knowledge_map(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 5: exercise_types
    print("\n📌 [5/15] exercise_types — 题型定义")
    n = fill_exercise_types(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 6: problem_bank
    print("\n📌 [6/15] problem_bank — 题库")
    n = fill_problem_bank(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 7: practice_weeks
    print("\n📌 [7/15] practice_weeks — 练习周记录")
    n = fill_practice_weeks(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 8: student_practice_sessions
    print("\n📌 [8/15] student_practice_sessions — 学生练习会话")
    n = fill_student_practice_sessions(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 9: student_practice_problems
    print("\n📌 [9/15] student_practice_problems — 练习题目")
    n = fill_student_practice_problems(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 10: scanned_submissions
    print("\n📌 [10/15] scanned_submissions — 扫描提交记录")
    n = fill_scanned_submissions(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 11: grading_comments
    print("\n📌 [11/15] grading_comments — AI批改评语")
    n = fill_grading_comments(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 12: quiz_student_answers
    print("\n📌 [12/15] quiz_student_answers — 测验学生答案")
    n = fill_quiz_student_answers(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 13: week_calc_mapping
    print("\n📌 [13/15] week_calc_mapping — 周次计算类型映射")
    n = fill_week_calc_mapping(cur)
    conn.commit()
    print(f"   ✅ 新增 {n} 条")

    # Section 14: Fix class summary total_attempts
    print("\n📌 [14/15] student_error_stats — 修复 total_attempts")
    n = fix_class_summary(cur)
    conn.commit()
    print(f"   ✅ 更新 {n} 条")

    # Section 15: Fix homework completion_rate
    print("\n📌 [15/15] homework_submissions — 修复提交率")
    n = fix_completion_rate(cur)
    conn.commit()
    print(f"   ✅ 更新 {n} 个作业")

    # Final summary
    print("\n" + "=" * 60)
    print("📊 最终数据统计")
    print("=" * 60)

    tables = [
        "knowledge_points", "knowledge_points_fts", "concept_relations",
        "error_code_knowledge_map", "exercise_types", "problem_bank",
        "practice_weeks", "student_practice_sessions", "student_practice_problems",
        "scanned_submissions", "grading_comments", "quiz_student_answers",
        "week_calc_mapping", "student_error_stats",
    ]
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"   {t}: {cur.fetchone()[0]} 条")

    cur.execute("SELECT COUNT(*) FROM homework_submissions")
    print(f"   homework_submissions: {cur.fetchone()[0]} 条")

    conn.close()
    print("\n✅ 填充完成！")


if __name__ == "__main__":
    main()

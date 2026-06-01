#!/usr/bin/env python3
"""
Realistic Homework Lifecycle Simulation — Diagnosis-Aligned
============================================================
Generates problems and wrong answers that are COMPATIBLE with the diagnosis
engine in app/services/diagnosis.py.

Core fix: the problem_generator maps E01→fraction multiply, E02→fraction divide,
but the diagnosis engine maps E01→basic facts, E02→carry, E03→borrow, etc.
This simulation generates problems that the diagnosis engine can actually detect,
and wrong answers computed via the SAME cognitive-error math the detectors check.

Usage:
    cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend
    PYTHONPATH=. /home/lyzhang/miniconda3/envs/pyt0/bin/python scripts/simulate_realistic.py
"""

from __future__ import annotations

import asyncio
import json
import operator as _op_mod
import random
import re
import sqlite3
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "calc_forest.db"
CLASS_ID = "G6A1"

# ──────────────────────────────────────────────────────────────────────────────
# Curriculum week → error-code map (人教版六年级下册 alignment)
# ──────────────────────────────────────────────────────────────────────────────

WEEK_ERROR_MAP: dict[int, list[str]] = {
    1:  ["E01", "E02"],                     # 负数 + 基础运算
    2:  ["E01", "E06"],                     # 百分数转换
    3:  ["E02", "E06"],                     # 百分数应用
    4:  ["E02", "E03"],                     # 圆柱表面积（多步计算）
    5:  ["E03", "E04", "E08"],              # 圆柱体积（退位+对齐+遗漏步骤）
    6:  ["E03", "E08"],                     # 圆锥体积
    7:  ["E05", "E06"],                     # 比例计算（运算顺序+分数）
    8:  ["E04", "E05"],                     # 比例尺（小数+运算顺序）
    9:  ["E05", "E09"],                     # 正反比例（概念理解）
    10: ["E09", "E10"],                     # 比例应用（概念+单位）
    11: ["E01", "E11"],                     # 鸽巢问题 + 综合
    12: ["E10", "E11"],                     # 综合练习（审题+验算）
    # 13-20 mixed review
    13: ["E01", "E03", "E05", "E09"],
    14: ["E02", "E04", "E06", "E10"],
    15: ["E01", "E02", "E03", "E11"],
    16: ["E04", "E05", "E06", "E08"],
    17: ["E01", "E06", "E09", "E10"],
    18: ["E02", "E03", "E08", "E11"],
    19: ["E04", "E05", "E09", "E10"],
    20: ["E01", "E02", "E03", "E04", "E05", "E06", "E08", "E09", "E10", "E11"],
}

ALL_DIAG_CODES = ["E01", "E02", "E03", "E04", "E05", "E06", "E08", "E09", "E10", "E11"]

ERROR_LABELS = {
    "OK": "正确", "E01": "基础事实", "E02": "进位错误", "E03": "退位错误",
    "E04": "数位对齐", "E05": "运算顺序", "E06": "小数/分数", "E07": "抄写错误",
    "E08": "步骤遗漏", "E09": "算理理解", "E10": "审题错误", "E11": "未验算", "E99": "未识别",
}

TIER_EMOJI = {"优秀": "🌟", "中等": "📊", "需关注": "⚠️"}

# ──────────────────────────────────────────────────────────────────────────────
# Student profiles — 3 tiers, rich data, non-monotonic trajectories
# ──────────────────────────────────────────────────────────────────────────────

STUDENT_PROFILES = {
    # ── 优秀组 (3) — accuracy 80-95% ──
    "S002": dict(
        tier="优秀", name="李思琪", base_accuracy=0.88,
        code_accuracy={"E02": 0.72, "E08": 0.68}, improve_rate=0.015,
        personality_tags=["坚持不懈", "勇于尝试"], learning_style="逻辑型",
        notes="计算能力扎实，偶尔粗心导致进位错误",
        trajectory_type="linear",
    ),
    "S004": dict(
        tier="优秀", name="刘雨萱", base_accuracy=0.92,
        code_accuracy={"E05": 0.76}, improve_rate=0.010,
        personality_tags=["细心谨慎", "独立思考"], learning_style="视觉型",
        notes="几乎全对，运算顺序偶尔搞混",
        trajectory_type="linear",
    ),
    "S009": dict(
        tier="优秀", name="周思远", base_accuracy=0.85,
        code_accuracy={"E08": 0.70}, improve_rate=0.015,
        personality_tags=["条理清晰", "追求完美"], learning_style="逻辑型",
        notes="偶尔跳步导致遗漏",
        trajectory_type="plateau",        # plateaus weeks 4-5
    ),
    # ── 中等组 (4) — accuracy 55-80% ──
    "S003": dict(
        tier="中等", name="张浩然", base_accuracy=0.65,
        code_accuracy={"E03": 0.42, "E09": 0.48}, improve_rate=0.030,
        personality_tags=["勤奋努力", "需要引导"], learning_style="听觉型",
        notes="退位减法弱，算理理解需加强",
        trajectory_type="breakthrough",   # breakthrough week 5-6
    ),
    "S005": dict(
        tier="中等", name="陈梓轩", base_accuracy=0.60,
        code_accuracy={"E02": 0.48, "E04": 0.45, "E06": 0.42}, improve_rate=0.035,
        personality_tags=["活跃积极", "容易分心"], learning_style="动手型",
        notes="进位错误多，数位对齐和小数点问题",
        trajectory_type="linear",
    ),
    "S007": dict(
        tier="中等", name="黄俊杰", base_accuracy=0.62,
        code_accuracy={"E06": 0.40, "E09": 0.45}, improve_rate=0.030,
        personality_tags=["安静内敛", "认真踏实"], learning_style="视觉型",
        notes="概念模糊，小数分数互化和算理理解薄弱",
        trajectory_type="regression",     # regression week 4 then recovery
    ),
    "S010": dict(
        tier="中等", name="吴佳怡", base_accuracy=0.58,
        code_accuracy={"E01": 0.42, "E05": 0.40, "E06": 0.38}, improve_rate=0.035,
        personality_tags=["活泼开朗", "需要鼓励"], learning_style="听觉型",
        notes="口算弱，运算顺序和小数点概念薄弱",
        trajectory_type="linear",
    ),
    # ── 需关注组 (3) — accuracy 25-55% ──
    "S001": dict(
        tier="需关注", name="王子涵", base_accuracy=0.42,
        code_accuracy={"E03": 0.25, "E06": 0.20, "E08": 0.30}, improve_rate=0.040,
        personality_tags=["坚持不懈", "需要鼓励"], learning_style="动手型",
        notes="多方面薄弱，需要系统帮扶",
        trajectory_type="linear",
    ),
    "S006": dict(
        tier="需关注", name="杨诗涵", base_accuracy=0.35,
        code_accuracy={"E01": 0.28, "E03": 0.22, "E10": 0.25}, improve_rate=0.045,
        personality_tags=["腼腆安静", "细心但慢"], learning_style="视觉型",
        notes="基础差，退位减法和审题问题严重",
        trajectory_type="regression",     # regression week 3-4
    ),
    "S008": dict(
        tier="需关注", name="赵梦琪", base_accuracy=0.38,
        code_accuracy={"E02": 0.25, "E03": 0.22, "E09": 0.28}, improve_rate=0.040,
        personality_tags=["勇于提问", "需要系统辅导"], learning_style="听觉型",
        notes="进位、退位和算理理解均有困难",
        trajectory_type="breakthrough",   # breakthrough week 6-7
    ),
}

STUDENT_IDS = list(STUDENT_PROFILES.keys())
TIER_ORDER = ["需关注", "中等", "优秀"]


# ──────────────────────────────────────────────────────────────────────────────
# Diagnosis-engine helpers (mirrors diagnosis.py exactly)
# ──────────────────────────────────────────────────────────────────────────────

def _needs_carry(a: int, b: int) -> bool:
    while a or b:
        if a % 10 + b % 10 >= 10:
            return True
        a //= 10
        b //= 10
    return False


def _needs_borrow(a: int, b: int) -> bool:
    while a or b:
        if a % 10 < b % 10:
            return True
        a //= 10
        b //= 10
    return False


def _add_without_carry(a: int, b: int) -> int:
    place, result = 1, 0
    while a or b:
        result += ((a % 10 + b % 10) % 10) * place
        a //= 10
        b //= 10
        place *= 10
    return result


def _subtract_without_borrow(a: int, b: int) -> int:
    place, result = 1, 0
    while a or b:
        result += abs((a % 10) - (b % 10)) * place
        a //= 10
        b //= 10
        place *= 10
    return result


def _eval_left_to_right(expr: str):
    """Evaluate expression strictly left-to-right (no precedence)."""
    from fractions import Fraction
    tokens = re.findall(r"\d+(?:\.\d+)?|[+\-*/]", expr)
    if not tokens:
        return None
    try:
        val = Fraction(tokens[0])
        ops = {"+": _op_mod.add, "-": _op_mod.sub, "*": _op_mod.mul, "/": _op_mod.truediv}
        i = 1
        while i < len(tokens) - 1:
            val = ops[tokens[i]](val, Fraction(tokens[i + 1]))
            i += 2
        return val
    except (KeyError, ValueError, ZeroDivisionError):
        return None


def _normalize(problem: str) -> str:
    return problem.replace("×", "*").replace("÷", "/").replace("＝", "=").split("=")[0]


# ──────────────────────────────────────────────────────────────────────────────
# Diagnosis-compatible problem generators
# ──────────────────────────────────────────────────────────────────────────────
# Each returns (problem_text, correct_answer).
# Problem text format: "EXPR=" so _extract_expression can parse it.

def _gen_basic_fact(rng: random.Random) -> tuple[str, str]:
    """E01: a+b= / a-b= / a×b= with a,b ≤ 20 (diagnosis: simple_problem check)."""
    op = rng.choice(["+", "-", "×"])
    if op == "+":
        a, b = rng.randint(2, 12), rng.randint(2, 12)
        return f"{a}+{b}=", str(a + b)
    if op == "-":
        a = rng.randint(5, 18)
        b = rng.randint(2, max(2, a - 1))
        return f"{a}-{b}=", str(a - b)
    a, b = rng.randint(2, 9), rng.randint(2, 9)
    return f"{a}×{b}=", str(a * b)


def _gen_carry(rng: random.Random) -> tuple[str, str]:
    """E02: a+b= where at least one digit pair sums ≥ 10."""
    for _ in range(200):
        a = rng.randint(11, 99)
        b = rng.randint(11, 99)
        if _needs_carry(a, b):
            return f"{a}+{b}=", str(a + b)
    return "37+46=", "83"


def _gen_borrow(rng: random.Random) -> tuple[str, str]:
    """E03: a-b= where at least one digit of a < corresponding digit of b."""
    for _ in range(200):
        a = rng.randint(100, 999)
        b = rng.randint(10, a - 10)
        if _needs_borrow(a, b):
            return f"{a}-{b}=", str(a - b)
    return "402-178=", "224"


def _gen_place_value(rng: random.Random) -> tuple[str, str]:
    """E04: a+b= result ≥ 100, no carry needed (avoids E02 false match)."""
    pool_a = [100, 110, 120, 130, 200, 210, 220, 300, 310, 320, 400, 410]
    pool_b = [100, 200, 300, 110, 210, 120, 220, 130, 230]
    for _ in range(200):
        a = rng.choice(pool_a)
        b = rng.choice(pool_b)
        if not _needs_carry(a, b) and a + b >= 100:
            return f"{a}+{b}=", str(a + b)
    return "200+300=", "500"


def _gen_operation_order(rng: random.Random) -> tuple[str, str]:
    """E05: a+b×c= where left-to-right ≠ correct (precedence matters)."""
    for _ in range(200):
        a = rng.randint(2, 10)
        b = rng.randint(2, 8)
        c = rng.randint(2, 8)
        op = rng.choice(["+", "-"])
        expr = f"{a}{op}{b}×{c}="
        if op == "+":
            correct = a + b * c
        else:
            correct = a - b * c
        ltr = _eval_left_to_right(_normalize(expr))
        if ltr is not None and ltr != correct and correct > 0 and ltr > 0:
            return expr, str(correct)
    return "3+4×5=", "23"


def _gen_decimal(rng: random.Random) -> tuple[str, str]:
    """E06: decimal arithmetic — problem contains '.', so _detect_decimal_error fires."""
    kind = rng.choice(["add", "sub", "mul"])
    if kind == "add":
        a = rng.choice([1.2, 2.5, 3.4, 4.6, 5.8, 6.3, 7.1, 8.4])
        b = rng.choice([1.3, 2.4, 3.5, 4.2, 5.6, 6.7, 1.8, 2.1])
        correct = round(a + b, 2)
        return f"{a}+{b}=", str(correct)
    if kind == "sub":
        a = rng.choice([5.8, 7.4, 8.2, 9.5, 6.3, 4.9])
        b = rng.choice([1.2, 2.5, 3.4, 1.8, 2.3, 3.1])
        hi, lo = max(a, b), min(a, b)
        return f"{hi}-{lo}=", str(round(hi - lo, 2))
    a = rng.choice([1.5, 2.4, 3.6, 2.5, 4.8])
    b = rng.choice([2, 3, 4, 5])
    return f"{a}×{b}=", str(round(a * b, 2))


def _gen_missing_step(rng: random.Random) -> tuple[str, str]:
    """E08: a×b= with a,b ≥ 10 — partial-product detection fires."""
    for _ in range(200):
        a = rng.randint(11, 35)
        b = rng.randint(11, 35)
        if a >= 10 and b >= 10 and a != b:
            return f"{a}×{b}=", str(a * b)
    return "23×15=", "345"


def _gen_conceptual(rng: random.Random) -> tuple[str, str]:
    """E09: a×a= (square) — student may compute 2a instead of a²."""
    a = rng.randint(3, 12)
    return f"{a}×{a}=", str(a * a)


def _gen_wording(rng: random.Random) -> tuple[str, str]:
    """E10: a×b= where a≠b — student may add instead of multiply."""
    for _ in range(200):
        a = rng.randint(2, 12)
        b = rng.randint(2, 12)
        if a != b and a + b != a * b:
            return f"{a}×{b}=", str(a * b)
    return "7×8=", "56"


def _gen_no_checking(rng: random.Random) -> tuple[str, str]:
    """E11: any arithmetic, wrong answer will be 2-3× correct (ratio > 2.0)."""
    kind = rng.choice(["add", "sub", "mul"])
    if kind == "add":
        a, b = rng.randint(15, 50), rng.randint(15, 50)
        return f"{a}+{b}=", str(a + b)
    if kind == "sub":
        a = rng.randint(50, 100)
        b = rng.randint(10, a - 10)
        return f"{a}-{b}=", str(a - b)
    a, b = rng.randint(3, 12), rng.randint(3, 12)
    return f"{a}×{b}=", str(a * b)


_PROBLEM_GENS: dict[str, callable] = {
    "E01": _gen_basic_fact,
    "E02": _gen_carry,
    "E03": _gen_borrow,
    "E04": _gen_place_value,
    "E05": _gen_operation_order,
    "E06": _gen_decimal,
    "E08": _gen_missing_step,
    "E09": _gen_conceptual,
    "E10": _gen_wording,
    "E11": _gen_no_checking,
}


# ──────────────────────────────────────────────────────────────────────────────
# Wrong-answer generators — produce the EXACT value each diagnosis detector checks
# ──────────────────────────────────────────────────────────────────────────────

def _wrong_basic_fact(problem: str, correct: str, rng: random.Random) -> str:
    """E01: off by ±1 or ±2 (simple arithmetic slip on small numbers)."""
    n = int(correct)
    return str(max(0, n + rng.choice([-2, -1, 1, 2])))


def _wrong_carry(problem: str, correct: str, rng: random.Random) -> str:
    """E02: add digit-by-digit WITHOUT carrying → matches _add_without_carry."""
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    return str(_add_without_carry(nums[0], nums[1]))


def _wrong_borrow(problem: str, correct: str, rng: random.Random) -> str:
    """E03: subtract digit-by-digit WITHOUT borrowing → matches _subtract_without_borrow."""
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    return str(_subtract_without_borrow(nums[0], nums[1]))


def _wrong_place_value(problem: str, correct: str, rng: random.Random) -> str:
    """E04: answer is expected+90 or expected*10 → matches place-value-alignment set."""
    n = int(correct)
    options = [x for x in [n * 10, n + 90, n - 90] if x > 0 and x != n]
    return str(rng.choice(options) if options else n + 90)


def _wrong_operation_order(problem: str, correct: str, rng: random.Random) -> str:
    """E05: left-to-right evaluation → matches _detect_operation_order."""
    from fractions import Fraction
    ltr = _eval_left_to_right(_normalize(problem))
    if ltr is not None:
        return str(ltr.numerator) if ltr.denominator == 1 else str(float(ltr))
    return str(int(correct) + 10)


def _wrong_decimal(problem: str, correct: str, rng: random.Random) -> str:
    """E06: decimal-point shift ×10 or ÷10 → ratio in {10, 0.1}."""
    try:
        n = float(correct)
    except ValueError:
        n = float(int(correct))
    wrong = rng.choice([n * 10, n / 10])
    if wrong == int(wrong):
        return str(int(wrong))
    return f"{wrong:.4f}".rstrip("0").rstrip(".")


def _wrong_missing_step(problem: str, correct: str, rng: random.Random) -> str:
    """E08: only one partial product → matches _detect_missing_step partials set."""
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    a, b = nums[0], nums[1]
    partials = [a * (b % 10), a * (b // 10)]
    partials = [p for p in partials if p > 0 and p != a * b]
    return str(rng.choice(partials) if partials else int(correct) // 2)


def _wrong_conceptual(problem: str, correct: str, rng: random.Random) -> str:
    """E09: a²→2a (confuse square with double) → matches _detect_conceptual_error."""
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    return str(2 * nums[0])


def _wrong_wording(problem: str, correct: str, rng: random.Random) -> str:
    """E10: × seen as + → matches _detect_wording_unit_error (has_mult, student=a+b)."""
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    return str(nums[0] + nums[1])


def _wrong_no_checking(problem: str, correct: str, rng: random.Random) -> str:
    """E11: answer ×2 or ×3 (student/expected > 2.0) → matches _detect_no_checking."""
    n = int(correct)
    return str(n * rng.choice([2, 3]))


_WRONG_GENS: dict[str, callable] = {
    "E01": _wrong_basic_fact,
    "E02": _wrong_carry,
    "E03": _wrong_borrow,
    "E04": _wrong_place_value,
    "E05": _wrong_operation_order,
    "E06": _wrong_decimal,
    "E08": _wrong_missing_step,
    "E09": _wrong_conceptual,
    "E10": _wrong_wording,
    "E11": _wrong_no_checking,
}


# ──────────────────────────────────────────────────────────────────────────────
# Accuracy model with trajectory overrides
# ──────────────────────────────────────────────────────────────────────────────

def _student_accuracy(profile: dict, error_code: str, week: int) -> float:
    base = profile["base_accuracy"]
    code_base = profile["code_accuracy"].get(error_code, base + 0.10)
    acc = code_base + profile["improve_rate"] * week

    tt = profile.get("trajectory_type", "linear")
    if tt == "plateau" and 4 <= week <= 5:
        acc = code_base + profile["improve_rate"] * 3      # stuck at week-3 level
    elif tt == "regression" and 3 <= week <= 4:
        acc -= 0.10                                          # temporary drop
    elif tt == "breakthrough" and week >= 6:
        acc += 0.12                                          # sudden jump

    acc += random.uniform(-0.03, 0.03)
    return max(0.10, min(0.98, acc))


def _tier_config(tier: str, week: int) -> dict:
    if tier == "优秀":
        return {"difficulty": "C" if week >= 5 else "B", "count": 5}
    if tier == "中等":
        return {"difficulty": "B" if week >= 4 else "A", "count": 5}
    return {"difficulty": "B" if week >= 6 else "A", "count": 5}


# ──────────────────────────────────────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _ensure_students():
    """Insert / update class + students with rich profile data."""
    from app.db import get_db

    async with get_db() as db:
        # Ensure class exists (FK dependency)
        cur = await db.execute("SELECT id FROM classes WHERE id = ?", (CLASS_ID,))
        if not await cur.fetchone():
            await db.execute(
                """INSERT INTO classes (id, name, grade, academic_year, semester)
                   VALUES (?, '六年级一班', 6, '2025-2026', 'spring')""",
                (CLASS_ID,),
            )
            await db.commit()

        for sid, p in STUDENT_PROFILES.items():
            cur = await db.execute("SELECT id FROM students WHERE id = ?", (sid,))
            exists = await cur.fetchone()
            tags_json = json.dumps(p["personality_tags"], ensure_ascii=False)
            if not exists:
                await db.execute(
                    """INSERT INTO students
                       (id, name, grade, class_id, guidance_mode, textbook_version,
                        start_grade, enrolled_at, personality_tags, learning_style,
                        notes, student_number)
                       VALUES (?, ?, 6, ?, 'standard', 'PEP', 6, '2026-02-17', ?, ?, ?, ?)""",
                    (sid, p["name"], CLASS_ID, tags_json, p["learning_style"], p["notes"], sid),
                )
            else:
                await db.execute(
                    "UPDATE students SET personality_tags=?, learning_style=?, notes=? WHERE id=?",
                    (tags_json, p["learning_style"], p["notes"], sid),
                )
        await db.commit()


async def _create_homework(week: int, codes: list[str], difficulty: str) -> tuple[str, list[dict]]:
    """Create homework with diagnosis-compatible problems.  Returns (hw_id, problems)."""
    from app.db import get_db

    hw_id = f"HW{uuid.uuid4().hex[:8].upper()}"
    rng = random.Random(week * 1000 + hash(tuple(codes)))
    problems: list[dict] = []
    for i in range(5):
        code = codes[i % len(codes)]
        gen = _PROBLEM_GENS.get(code, _gen_basic_fact)
        text, answer = gen(rng)
        problems.append(dict(
            sequence=i + 1, problem=text, correct_answer=answer,
            target_error_code=code, difficulty=difficulty,
            knowledge_point=f"第{week}周练习",
        ))

    async with get_db() as db:
        await db.execute(
            """INSERT INTO homework
               (id, class_id, grade, knowledge_points, error_codes_target,
                status, generated_by, created_at)
               VALUES (?, ?, 6, ?, ?, 'assigned', 'simulation', ?)""",
            (hw_id, CLASS_ID,
             json.dumps(list({p["knowledge_point"] for p in problems})),
             json.dumps(codes),
             f"2026-0{3 + week // 4}-{10 + week * 7 % 28:02d}"),
        )
        for p in problems:
            await db.execute(
                """INSERT INTO homework_problems
                   (id, homework_id, sequence, problem, correct_answer,
                    knowledge_point, target_error_code, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"HP{uuid.uuid4().hex[:8].upper()}", hw_id,
                 p["sequence"], p["problem"], p["correct_answer"],
                 p["knowledge_point"], p["target_error_code"], p["difficulty"]),
            )
        await db.commit()
    return hw_id, problems


async def _generate_quiz_sessions() -> int:
    """Create 5 quiz sessions across the 8 weeks."""
    from app.db import get_db

    configs = [
        dict(week=2, title="第2周课堂小测 — 基础运算与百分数",
             codes=["E01", "E06"],
             responses=["mostly_correct", "mixed", "mostly_correct", "mixed", "mostly_correct"]),
        dict(week=4, title="第4周课堂小测 — 进位与退位",
             codes=["E02", "E03"],
             responses=["mixed", "mostly_wrong", "mostly_correct", "mixed", "mostly_correct"]),
        dict(week=5, title="第5周课堂小测 — 退位对齐与步骤",
             codes=["E03", "E04", "E08"],
             responses=["mostly_wrong", "mixed", "mostly_wrong", "mixed", "mostly_correct"]),
        dict(week=7, title="第7周课堂小测 — 运算顺序与小数",
             codes=["E05", "E06"],
             responses=["mixed", "mostly_correct", "mixed", "mostly_wrong", "mostly_correct"]),
        dict(week=8, title="第8周综合测验 — 数位与运算顺序",
             codes=["E04", "E05"],
             responses=["mostly_correct", "mixed", "mostly_correct", "mixed", "mostly_correct"]),
    ]
    rng = random.Random(42)

    async with get_db() as db:
        for cfg in configs:
            qid = f"QS{uuid.uuid4().hex[:8].upper()}"
            dt = f"2026-03-{10 + cfg['week'] * 7 % 20:02d}"
            await db.execute(
                """INSERT INTO quiz_sessions
                   (id, class_id, title, status, target_error_codes,
                    problem_count, difficulty, grade, created_at, completed_at)
                   VALUES (?, ?, ?, 'completed', ?, 5, 'B', 6, ?, ?)""",
                (qid, CLASS_ID, cfg["title"], json.dumps(cfg["codes"]), dt, dt),
            )
            for i in range(5):
                code = cfg["codes"][i % len(cfg["codes"])]
                gen = _PROBLEM_GENS.get(code, _gen_basic_fact)
                text, answer = gen(rng)
                await db.execute(
                    """INSERT INTO quiz_problems
                       (id, quiz_id, sequence, problem, correct_answer,
                        target_error_code, difficulty, knowledge_point, hint)
                       VALUES (?, ?, ?, ?, ?, ?, 'B', ?, '')""",
                    (f"QP{uuid.uuid4().hex[:8].upper()}", qid, i + 1,
                     text, answer, code, f"第{cfg['week']}周测验"),
                )
            for i, resp in enumerate(cfg["responses"]):
                await db.execute(
                    """INSERT INTO quiz_responses
                       (id, quiz_id, problem_sequence, class_response, notes, created_at)
                       VALUES (?, ?, ?, ?, '', ?)""",
                    (f"QR{uuid.uuid4().hex[:8].upper()}", qid, i + 1, resp, dt),
                )
        await db.commit()
    return len(configs)


async def _populate_trajectories() -> int:
    """Fill student_error_trajectory from diagnosis_history."""
    from app.db import get_db

    async with get_db() as db:
        await db.execute("DELETE FROM student_error_trajectory")

        # Build week→unit_id mapping from teaching_schedule
        cur = await db.execute(
            "SELECT week_number, unit_id FROM teaching_schedule WHERE class_id = ?",
            (CLASS_ID,),
        )
        week_unit_map: dict[int, str | None] = {}
        for row in await cur.fetchall():
            week_unit_map[row["week_number"]] = row["unit_id"]

        # Fallback: first teaching unit
        cur = await db.execute("SELECT id FROM teaching_units LIMIT 1")
        unit_row = await cur.fetchone()
        fallback_unit = unit_row["id"] if unit_row else None

        cur = await db.execute(
            """SELECT student_id, error_code, is_correct, created_at
               FROM diagnosis_history
               WHERE student_id IN (SELECT id FROM students WHERE class_id = ?)
               ORDER BY created_at""",
            (CLASS_ID,),
        )
        rows = await cur.fetchall()

        grouped: dict[tuple, dict] = defaultdict(lambda: {"err": 0, "ok": 0})
        for r in rows:
            try:
                day = int(r["created_at"][:10].split("-")[2])
                week = max(1, min(18, (day - 10) // 7 + 1))
            except (ValueError, IndexError):
                week = 1
            key = (r["student_id"], week, r["error_code"])
            if r["is_correct"]:
                grouped[key]["ok"] += 1
            else:
                grouped[key]["err"] += 1

        for (sid, wk, code), c in grouped.items():
            total = c["err"] + c["ok"]
            acc = c["ok"] / total if total else 0.0
            unit_id = week_unit_map.get(wk) or fallback_unit
            await db.execute(
                """INSERT INTO student_error_trajectory
                   (id, student_id, unit_id, week_number, error_code,
                    error_count, correct_count, accuracy, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', datetime('now'))""",
                (f"SET{uuid.uuid4().hex[:8].upper()}", sid, unit_id,
                 wk, code, c["err"], c["ok"], round(acc, 3)),
            )
        await db.commit()

        cnt = await db.execute("SELECT COUNT(*) FROM student_error_trajectory")
        return (await cnt.fetchone())[0]


# ──────────────────────────────────────────────────────────────────────────────
# Alignment verification
# ──────────────────────────────────────────────────────────────────────────────

def _verify_alignment() -> dict:
    """Check intended vs diagnosed error codes in the DB."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Overall error-code distribution
    cur = conn.execute(
        "SELECT error_code, COUNT(*) as cnt FROM diagnosis_history "
        "GROUP BY error_code ORDER BY cnt DESC"
    )
    code_dist = {r["error_code"]: r["cnt"] for r in cur.fetchall()}

    # Per-answer alignment: intended (from homework_problems) vs diagnosed (from student_answers)
    cur = conn.execute("""
        SELECT sa.error_code AS diagnosed, hp.target_error_code AS intended
        FROM student_answers sa
        JOIN homework_problems hp ON sa.homework_id = hp.homework_id
             AND sa.problem_sequence = hp.sequence
        WHERE sa.is_correct = 0
          AND hp.target_error_code IS NOT NULL
          AND sa.error_code IS NOT NULL
    """)
    rows = cur.fetchall()
    total_wrong = len(rows)
    matched = sum(1 for r in rows if r["diagnosed"] == r["intended"])
    match_rate = matched / total_wrong if total_wrong else 0

    conn.close()
    return dict(code_dist=code_dist, total_wrong=total_wrong,
                matched=matched, match_rate=match_rate)


# ──────────────────────────────────────────────────────────────────────────────
# Main simulation
# ──────────────────────────────────────────────────────────────────────────────

async def run_simulation():
    import os
    os.environ["DIFY_ENABLED"] = "false"
    os.environ["LOCAL_DIFY_ENABLED"] = "false"

    from app.db import init_db
    from app.services.grading_service import submit_homework, grade_homework
    import app.services.dify_client as _dify

    async def _skip_dify(*_a, **_kw):
        return {"skipped": True}
    _dify.call_dify_or_llm = _skip_dify
    try:
        _dify.ai_grade_answers = _skip_dify
    except AttributeError:
        pass

    await init_db()
    await _ensure_students()

    print("=" * 72)
    print("🌲 我的计算森林 — 8周诊断对齐仿真模拟 🌲")
    print("=" * 72)
    print()
    print("📋 学生名单:")
    for tier in TIER_ORDER:
        students = [(s, STUDENT_PROFILES[s]) for s in STUDENT_IDS if STUDENT_PROFILES[s]["tier"] == tier]
        names = ", ".join(f"{p['name']}({s})" for s, p in students)
        print(f"  {TIER_EMOJI[tier]} {tier}组: {names}")
    print()

    all_results: list[dict] = []

    for week in range(1, 9):
        target_codes = WEEK_ERROR_MAP.get(week, ALL_DIAG_CODES[:3])
        print("=" * 72)
        print(f"📅 第{week}周 — 目标错因: {', '.join(target_codes)}")
        print("=" * 72)

        for tier in TIER_ORDER:
            tier_students = [
                (s, STUDENT_PROFILES[s])
                for s in STUDENT_IDS if STUDENT_PROFILES[s]["tier"] == tier
            ]
            if not tier_students:
                continue

            cfg = _tier_config(tier, week)
            emoji = TIER_EMOJI[tier]
            print(f"\n  {emoji} {tier}组 (难度: {cfg['difficulty']})")

            hw_id, problems = await _create_homework(week, target_codes, cfg["difficulty"])
            print(f"     📝 作业 {hw_id}: {len(problems)}题")

            for sid, profile in tier_students:
                name = profile["name"]
                answers = []
                correct_count = 0
                details = []

                for p in problems:
                    code = p["target_error_code"]
                    acc = _student_accuracy(profile, code, week)

                    if random.random() < acc:
                        stu_ans = p["correct_answer"]
                        is_correct = True
                        correct_count += 1
                    else:
                        wrong_fn = _WRONG_GENS.get(code)
                        if wrong_fn:
                            stu_ans = wrong_fn(p["problem"], p["correct_answer"], random.Random())
                        else:
                            try:
                                stu_ans = str(int(p["correct_answer"]) + random.choice([-5, 3, 5]))
                            except ValueError:
                                stu_ans = p["correct_answer"] + "?"
                        is_correct = False

                    answers.append({"problem_sequence": p["sequence"], "student_answer": stu_ans})
                    details.append(dict(
                        problem=p["problem"], correct=p["correct_answer"],
                        student=stu_ans, intended=code, is_correct=is_correct,
                    ))

                try:
                    await submit_homework(hw_id, sid, answers)
                    grade_result = await grade_homework(hw_id, sid)
                except Exception as e:
                    print(f"     ❌ {name} 批改失败: {e}")
                    continue

                total = len(problems)
                accuracy = correct_count / total
                diag_errors = grade_result.get("primary_errors", [])

                perf = ("✅" if accuracy >= 0.8 else "👍" if accuracy >= 0.6
                        else "📈" if accuracy >= 0.4 else "❌")
                print(f"     {name} — {correct_count}/{total} ({accuracy:.0%}) {perf}")

                for d in details:
                    mark = "✅" if d["is_correct"] else "❌"
                    print(f"       {mark} {d['problem']}{d['student']}  "
                          f"(目标:{d['intended']})")

                if diag_errors:
                    elabels = [ERROR_LABELS.get(e, e) for e in diag_errors[:3]]
                    print(f"       💡 反馈: {', '.join(elabels)}")

                all_results.append(dict(
                    student_id=sid, name=name, tier=tier, week=week,
                    accuracy=accuracy, correct_count=correct_count,
                    total=total, diag_errors=diag_errors,
                ))

    # ── Quiz sessions ──
    print(f"\n{'=' * 72}")
    print("📋 生成课堂测验数据...")
    n_quizzes = await _generate_quiz_sessions()
    print(f"   ✅ 已生成 {n_quizzes} 个课堂测验")

    # ── Trajectory ──
    print("📊 生成学习轨迹数据...")
    n_traj = await _populate_trajectories()
    print(f"   ✅ 已生成 {n_traj} 条轨迹记录")

    # ── Alignment verification ──
    print(f"\n{'=' * 72}")
    print("🔍 诊断对齐验证")
    print(f"{'=' * 72}")

    alignment = _verify_alignment()
    dist = alignment["code_dist"]
    total_diag = sum(dist.values())
    e99_cnt = dist.get("E99", 0)
    e99_pct = e99_cnt / total_diag * 100 if total_diag else 0

    print(f"\n  错因分布 (共 {total_diag} 条诊断记录):")
    for code, cnt in dist.items():
        bar = "█" * min(30, cnt // 2)
        print(f"    {code} ({ERROR_LABELS.get(code, code)}): {cnt:>4d}  {bar}")

    print(f"\n  意图-诊断匹配率: {alignment['matched']}/{alignment['total_wrong']} "
          f"= {alignment['match_rate']:.0%}")
    print(f"  E99 比例: {e99_pct:.1f}% {'✅ 良好' if e99_pct < 20 else '⚠️ 偏高'}")

    if alignment["match_rate"] >= 0.70:
        print("  ✅ 诊断对齐率 ≥ 70%! 数据可靠。")
    elif alignment["match_rate"] >= 0.50:
        print("  👍 诊断对齐率 ≥ 50%，尚可接受。")
    else:
        print("  ⚠️ 对齐率偏低，部分错因可能被其他检测器捕获。")

    # ── Student trajectory overview ──
    print(f"\n{'=' * 72}")
    print("📊 8周学习轨迹总览")
    print(f"{'=' * 72}\n")

    for tier in TIER_ORDER:
        emoji = TIER_EMOJI[tier]
        print(f"  {emoji} {tier}组")
        print(f"  {'─' * 65}")

        for sid, profile in STUDENT_PROFILES.items():
            if profile["tier"] != tier:
                continue
            name = profile["name"]
            weeks = [r for r in all_results if r["student_id"] == sid]
            if not weeks:
                continue

            tot_ok = sum(r["correct_count"] for r in weeks)
            tot_all = sum(r["total"] for r in weeks)
            overall = tot_ok / tot_all if tot_all else 0
            first, last = weeks[0]["accuracy"], weeks[-1]["accuracy"]
            wstr = " → ".join(f"W{r['week']}:{r['accuracy']:.0%}" for r in weeks)
            imp = last - first
            imp_s = f"+{imp:.0%}" if imp >= 0 else f"{imp:.0%}"
            trend = "📈" if imp > 0.05 else "📉" if imp < -0.05 else "➡️"

            errs = []
            for r in weeks:
                errs.extend(r["diag_errors"])
            esum = dict(Counter(errs).most_common(5))
            estr = ", ".join(f"{ERROR_LABELS.get(e, e)}×{c}" for e, c in esum.items())

            print(f"  {name} ({sid}) [{profile['trajectory_type']}]")
            print(f"    轨迹: {wstr}")
            print(f"    总体: {tot_ok}/{tot_all} ({overall:.0%}) | "
                  f"首→末: {first:.0%}→{last:.0%} ({imp_s}) {trend}")
            print(f"    高频错因: {estr or '无'}")
            print(f"    个性: {', '.join(profile['personality_tags'])} | "
                  f"风格: {profile['learning_style']}")
            print()

    # ── Improvement ranking ──
    print(f"  {'─' * 65}")
    print("📊 进步排行榜")
    print(f"  {'─' * 65}")
    print(f"  {'排名':<4} {'姓名':<8} {'组别':<6} {'首周':<6} {'末周':<6} {'进步':<8}")
    print(f"  {'─' * 65}")

    imps = []
    for sid, p in STUDENT_PROFILES.items():
        ws = [r for r in all_results if r["student_id"] == sid]
        if len(ws) >= 2:
            imps.append((sid, p["name"], p["tier"], ws[0]["accuracy"], ws[-1]["accuracy"]))
    imps.sort(key=lambda x: x[4] - x[3], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    for i, (sid, name, t, f, l) in enumerate(imps):
        rank = medals[i] if i < 3 else f" {i + 1}"
        d = l - f
        ds = f"+{d:.0%}" if d >= 0 else f"{d:.0%}"
        print(f"  {rank:<4} {name:<8} {t:<6} {f:.0%}    {l:.0%}    {ds:<8}")
    print(f"  {'─' * 65}")
    print()

    # Final count
    conn = sqlite3.connect(str(DB_PATH))
    hw_cnt = conn.execute("SELECT COUNT(*) FROM homework").fetchone()[0]
    dh_cnt = conn.execute("SELECT COUNT(*) FROM diagnosis_history").fetchone()[0]
    conn.close()
    print(f"✅ 模拟完成! {hw_cnt} 条作业, {dh_cnt} 条诊断记录")


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(run_simulation())

#!/usr/bin/env python3
"""
Phase-2 Simulation — extend from 8 weeks to 20 weeks.
Direct SQL for speed. Uses same diagnosis-aligned generators as simulate_realistic.py.
Adds: homework, submissions, answers, diagnosis history, quizzes, trajectories, error stats, growth.

Usage:
    cd /mnt/d/Ubuntu_WSL/Teaching_agent/calc_forest/backend
    PYTHONPATH=. /home/lyzhang/miniconda3/envs/pyt0/bin/python scripts/simulate_phase2.py
"""

from __future__ import annotations

import operator as _op_mod
import random
import re
import sqlite3
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "calc_forest.db"
CLASS_ID = "G6C1"

WEEK_ERROR_MAP: dict[int, list[str]] = {
    9:  ["E05", "E06"],                     # 比例计算
    10: ["E09", "E10"],                     # 概念+审题
    11: ["E01", "E11"],                     # 鸽巢+验算
    12: ["E10", "E11"],                     # 综合练习
    13: ["E01", "E03", "E05", "E09"],       # 混合复习
    14: ["E02", "E04", "E06", "E10"],       # 混合复习
    15: ["E01", "E02", "E03", "E11"],       # 混合复习
    16: ["E04", "E05", "E06", "E08"],       # 混合复习
    17: ["E01", "E06", "E09", "E10"],       # 期末复习
    18: ["E02", "E03", "E08", "E11"],       # 期末复习
    19: ["E04", "E05", "E09", "E10"],       # 期末冲刺
    20: ["E01", "E02", "E03", "E04", "E05", "E06", "E08", "E09", "E10", "E11"],  # 综合测验
}

ALL_DIAG_CODES = ["E01", "E02", "E03", "E04", "E05", "E06", "E08", "E09", "E10", "E11"]

ERROR_LABELS = {
    "OK": "正确", "E01": "基础事实", "E02": "进位错误", "E03": "退位错误",
    "E04": "数位对齐", "E05": "运算顺序", "E06": "小数/分数", "E07": "抄写错误",
    "E08": "步骤遗漏", "E09": "算理理解", "E10": "审题错误", "E11": "未验算", "E99": "未识别",
}

TIER_EMOJI = {"优秀": "🌟", "中等": "📊", "需关注": "⚠️"}

STUDENT_PROFILES = {
    "S002": dict(tier="优秀", name="李思琪", base_accuracy=0.88,
                 code_accuracy={"E02": 0.72, "E08": 0.68}, improve_rate=0.015, trajectory_type="linear",
                 personality_tags=["坚持不懈", "勇于尝试"], learning_style="逻辑型"),
    "S004": dict(tier="优秀", name="刘雨萱", base_accuracy=0.92,
                 code_accuracy={"E05": 0.76}, improve_rate=0.010, trajectory_type="linear",
                 personality_tags=["细心谨慎", "独立思考"], learning_style="视觉型"),
    "S009": dict(tier="优秀", name="周思远", base_accuracy=0.85,
                 code_accuracy={"E08": 0.70}, improve_rate=0.015, trajectory_type="plateau",
                 personality_tags=["条理清晰", "追求完美"], learning_style="逻辑型"),
    "S003": dict(tier="中等", name="张浩然", base_accuracy=0.65,
                 code_accuracy={"E03": 0.42, "E09": 0.48}, improve_rate=0.030, trajectory_type="breakthrough",
                 personality_tags=["勤奋努力", "需要引导"], learning_style="听觉型"),
    "S005": dict(tier="中等", name="陈梓轩", base_accuracy=0.60,
                 code_accuracy={"E02": 0.48, "E04": 0.45, "E06": 0.42}, improve_rate=0.035, trajectory_type="linear",
                 personality_tags=["活跃积极", "容易分心"], learning_style="动手型"),
    "S007": dict(tier="中等", name="黄俊杰", base_accuracy=0.62,
                 code_accuracy={"E06": 0.40, "E09": 0.45}, improve_rate=0.030, trajectory_type="regression",
                 personality_tags=["安静内敛", "认真踏实"], learning_style="视觉型"),
    "S010": dict(tier="中等", name="吴佳怡", base_accuracy=0.58,
                 code_accuracy={"E01": 0.42, "E05": 0.40, "E06": 0.38}, improve_rate=0.035, trajectory_type="linear",
                 personality_tags=["活泼开朗", "需要鼓励"], learning_style="听觉型"),
    "S001": dict(tier="需关注", name="王子涵", base_accuracy=0.42,
                 code_accuracy={"E03": 0.25, "E06": 0.20, "E08": 0.30}, improve_rate=0.040, trajectory_type="linear",
                 personality_tags=["坚持不懈", "需要鼓励"], learning_style="动手型"),
    "S006": dict(tier="需关注", name="杨诗涵", base_accuracy=0.35,
                 code_accuracy={"E01": 0.28, "E03": 0.22, "E10": 0.25}, improve_rate=0.045, trajectory_type="regression",
                 personality_tags=["腼腆安静", "细心但慢"], learning_style="视觉型"),
    "S008": dict(tier="需关注", name="赵梦琪", base_accuracy=0.38,
                 code_accuracy={"E02": 0.25, "E03": 0.22, "E09": 0.28}, improve_rate=0.040, trajectory_type="breakthrough",
                 personality_tags=["勇于提问", "需要系统辅导"], learning_style="听觉型"),
}

STUDENT_IDS = list(STUDENT_PROFILES.keys())
TIER_ORDER = ["需关注", "中等", "优秀"]


# ──────────────────────────────────────────────────────────────────────────────
# Diagnosis-aligned problem generators (same as simulate_realistic.py)
# ──────────────────────────────────────────────────────────────────────────────

def _needs_carry(a, b):
    while a or b:
        if a % 10 + b % 10 >= 10:
            return True
        a //= 10
        b //= 10
    return False

def _needs_borrow(a, b):
    while a or b:
        if a % 10 < b % 10:
            return True
        a //= 10
        b //= 10
    return False

def _add_without_carry(a, b):
    place, result = 1, 0
    while a or b:
        result += ((a % 10 + b % 10) % 10) * place
        a //= 10
        b //= 10
        place *= 10
    return result

def _subtract_without_borrow(a, b):
    place, result = 1, 0
    while a or b:
        result += abs((a % 10) - (b % 10)) * place
        a //= 10
        b //= 10
        place *= 10
    return result

def _eval_left_to_right(expr):
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

def _normalize(problem):
    return problem.replace("×", "*").replace("÷", "/").replace("＝", "=").split("=")[0]


def _gen_basic_fact(rng):
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

def _gen_carry(rng):
    for _ in range(200):
        a, b = rng.randint(11, 99), rng.randint(11, 99)
        if _needs_carry(a, b):
            return f"{a}+{b}=", str(a + b)
    return "37+46=", "83"

def _gen_borrow(rng):
    for _ in range(200):
        a = rng.randint(100, 999)
        b = rng.randint(10, a - 10)
        if _needs_borrow(a, b):
            return f"{a}-{b}=", str(a - b)
    return "402-178=", "224"

def _gen_place_value(rng):
    pool_a = [100, 110, 120, 130, 200, 210, 220, 300, 310, 320, 400, 410]
    pool_b = [100, 200, 300, 110, 210, 120, 220, 130, 230]
    for _ in range(200):
        a, b = rng.choice(pool_a), rng.choice(pool_b)
        if not _needs_carry(a, b) and a + b >= 100:
            return f"{a}+{b}=", str(a + b)
    return "200+300=", "500"

def _gen_operation_order(rng):
    for _ in range(200):
        a, b, c = rng.randint(2, 10), rng.randint(2, 8), rng.randint(2, 8)
        op = rng.choice(["+", "-"])
        expr = f"{a}{op}{b}×{c}="
        correct = a + b * c if op == "+" else a - b * c
        ltr = _eval_left_to_right(_normalize(expr))
        if ltr is not None and ltr != correct and correct > 0 and ltr > 0:
            return expr, str(correct)
    return "3+4×5=", "23"

def _gen_decimal(rng):
    kind = rng.choice(["add", "sub", "mul"])
    if kind == "add":
        a = rng.choice([1.2, 2.5, 3.4, 4.6, 5.8, 6.3, 7.1, 8.4])
        b = rng.choice([1.3, 2.4, 3.5, 4.2, 5.6, 6.7, 1.8, 2.1])
        return f"{a}+{b}=", str(round(a + b, 2))
    if kind == "sub":
        a = rng.choice([5.8, 7.4, 8.2, 9.5, 6.3, 4.9])
        b = rng.choice([1.2, 2.5, 3.4, 1.8, 2.3, 3.1])
        hi, lo = max(a, b), min(a, b)
        return f"{hi}-{lo}=", str(round(hi - lo, 2))
    a = rng.choice([1.5, 2.4, 3.6, 2.5, 4.8])
    b = rng.choice([2, 3, 4, 5])
    return f"{a}×{b}=", str(round(a * b, 2))

def _gen_missing_step(rng):
    for _ in range(200):
        a, b = rng.randint(11, 35), rng.randint(11, 35)
        if a >= 10 and b >= 10 and a != b:
            return f"{a}×{b}=", str(a * b)
    return "23×15=", "345"

def _gen_conceptual(rng):
    a = rng.randint(3, 12)
    return f"{a}×{a}=", str(a * a)

def _gen_wording(rng):
    for _ in range(200):
        a, b = rng.randint(2, 12), rng.randint(2, 12)
        if a != b and a + b != a * b:
            return f"{a}×{b}=", str(a * b)
    return "7×8=", "56"

def _gen_no_checking(rng):
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

_PROBLEM_GENS = {
    "E01": _gen_basic_fact, "E02": _gen_carry, "E03": _gen_borrow,
    "E04": _gen_place_value, "E05": _gen_operation_order, "E06": _gen_decimal,
    "E08": _gen_missing_step, "E09": _gen_conceptual, "E10": _gen_wording,
    "E11": _gen_no_checking,
}


# ──────────────────────────────────────────────────────────────────────────────
# Wrong-answer generators
# ──────────────────────────────────────────────────────────────────────────────

def _wrong_basic_fact(problem, correct, rng):
    return str(max(0, int(correct) + rng.choice([-2, -1, 1, 2])))

def _wrong_carry(problem, correct, rng):
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    return str(_add_without_carry(nums[0], nums[1]))

def _wrong_borrow(problem, correct, rng):
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    return str(_subtract_without_borrow(nums[0], nums[1]))

def _wrong_place_value(problem, correct, rng):
    n = int(correct)
    opts = [x for x in [n * 10, n + 90, n - 90] if x > 0 and x != n]
    return str(rng.choice(opts) if opts else n + 90)

def _wrong_operation_order(problem, correct, rng):
    from fractions import Fraction
    ltr = _eval_left_to_right(_normalize(problem))
    if ltr is not None:
        return str(ltr.numerator) if ltr.denominator == 1 else str(float(ltr))
    return str(int(correct) + 10)

def _wrong_decimal(problem, correct, rng):
    try:
        n = float(correct)
    except ValueError:
        n = float(int(correct))
    wrong = rng.choice([n * 10, n / 10])
    return str(int(wrong)) if wrong == int(wrong) else f"{wrong:.4f}".rstrip("0").rstrip(".")

def _wrong_missing_step(problem, correct, rng):
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    a, b = nums[0], nums[1]
    partials = [p for p in [a * (b % 10), a * (b // 10)] if p > 0 and p != a * b]
    return str(rng.choice(partials) if partials else int(correct) // 2)

def _wrong_conceptual(problem, correct, rng):
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    return str(2 * nums[0])

def _wrong_wording(problem, correct, rng):
    nums = [int(x) for x in re.findall(r"\d+", _normalize(problem))]
    return str(nums[0] + nums[1])

def _wrong_no_checking(problem, correct, rng):
    return str(int(correct) * rng.choice([2, 3]))

_WRONG_GENS = {
    "E01": _wrong_basic_fact, "E02": _wrong_carry, "E03": _wrong_borrow,
    "E04": _wrong_place_value, "E05": _wrong_operation_order, "E06": _wrong_decimal,
    "E08": _wrong_missing_step, "E09": _wrong_conceptual, "E10": _wrong_wording,
    "E11": _wrong_no_checking,
}


# ──────────────────────────────────────────────────────────────────────────────
# Accuracy model
# ──────────────────────────────────────────────────────────────────────────────

def _student_accuracy(profile, error_code, week):
    base = profile["base_accuracy"]
    code_base = profile["code_accuracy"].get(error_code, base + 0.10)
    acc = code_base + profile["improve_rate"] * week
    tt = profile.get("trajectory_type", "linear")
    if tt == "plateau" and 12 <= week <= 13:
        acc = code_base + profile["improve_rate"] * 11
    elif tt == "regression" and 11 <= week <= 12:
        acc -= 0.10
    elif tt == "breakthrough" and week >= 14:
        acc += 0.12
    acc += random.uniform(-0.03, 0.03)
    return max(0.10, min(0.98, acc))


def _tier_difficulty(tier, week):
    if tier == "优秀":
        return "C" if week >= 13 else "B"
    if tier == "中等":
        return "B" if week >= 12 else "A"
    return "B" if week >= 14 else "A"


# ──────────────────────────────────────────────────────────────────────────────
# Main simulation
# ──────────────────────────────────────────────────────────────────────────────

def run():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row

    rng = random.Random(2026)

    print("=" * 72)
    print("🌲 我的计算森林 — Phase-2 仿真 (第9-20周) 🌲")
    print("=" * 72)

    # Get existing data for context
    existing_hw = conn.execute("SELECT COUNT(*) FROM homework").fetchone()[0]
    existing_diag = conn.execute("SELECT COUNT(*) FROM diagnosis_history").fetchone()[0]
    print(f"  现有: {existing_hw} 作业, {existing_diag} 诊断")
    print()

    # Baseline date: week 9 starts from April 14, 2026
    base_date = datetime(2026, 4, 14)

    hw_count = 0
    submission_count = 0
    answer_count = 0
    diag_count = 0
    all_results = []

    for week in range(9, 21):
        target_codes = WEEK_ERROR_MAP.get(week, ALL_DIAG_CODES[:3])
        week_date = base_date + timedelta(weeks=(week - 9))
        date_str = week_date.strftime("%Y-%m-%d")

        print(f"📅 第{week}周 ({date_str}) — 目标: {', '.join(target_codes)}")

        for tier in TIER_ORDER:
            tier_students = [(s, p) for s, p in STUDENT_PROFILES.items() if p["tier"] == tier]
            if not tier_students:
                continue

            difficulty = _tier_difficulty(tier, week)
            hw_id = f"HW{uuid.uuid4().hex[:8].upper()}"
            problem_count = 5

            # Generate homework + problems
            hw_rng = random.Random(week * 1000 + hash(tuple(target_codes)) + hash(tier))
            problems = []
            for i in range(problem_count):
                code = target_codes[i % len(target_codes)]
                gen = _PROBLEM_GENS.get(code, _gen_basic_fact)
                text, answer = gen(hw_rng)
                problems.append(dict(
                    sequence=i + 1, problem=text, correct_answer=answer,
                    target_error_code=code, difficulty=difficulty,
                    knowledge_point=f"第{week}周练习",
                ))

            conn.execute(
                "INSERT INTO homework (id, class_id, grade, knowledge_points, error_codes_target, status, generated_by, created_at) "
                "VALUES (?, ?, 6, ?, ?, 'assigned', 'simulation', ?)",
                (hw_id, CLASS_ID,
                 f'["第{week}周练习"]', str(target_codes).replace("'", '"'),
                 date_str),
            )
            for p in problems:
                conn.execute(
                    "INSERT INTO homework_problems (id, homework_id, sequence, problem, correct_answer, knowledge_point, target_error_code, difficulty) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (f"HP{uuid.uuid4().hex[:8].upper()}", hw_id,
                     p["sequence"], p["problem"], p["correct_answer"],
                     p["knowledge_point"], p["target_error_code"], p["difficulty"]),
                )
            hw_count += 1

            for sid, profile in tier_students:
                name = profile["name"]
                sub_id = f"SB{uuid.uuid4().hex[:8].upper()}"
                submit_date = (week_date + timedelta(days=rng.randint(1, 5))).strftime("%Y-%m-%d %H:%M:%S")

                conn.execute(
                    "INSERT INTO homework_submissions (id, homework_id, student_id, submitted_at, status) "
                    "VALUES (?, ?, ?, ?, 'graded')",
                    (sub_id, hw_id, sid, submit_date),
                )
                submission_count += 1

                correct_count = 0
                for p in problems:
                    code = p["target_error_code"]
                    acc = _student_accuracy(profile, code, week)

                    if rng.random() < acc:
                        stu_ans = p["correct_answer"]
                        is_correct = True
                        error_code = "OK"
                        correct_count += 1
                    else:
                        wrong_fn = _WRONG_GENS.get(code)
                        if wrong_fn:
                            stu_ans = wrong_fn(p["problem"], p["correct_answer"], rng)
                        else:
                            stu_ans = str(int(p["correct_answer"]) + rng.choice([-5, 3, 5]))
                        is_correct = False
                        error_code = code

                    ans_id = f"SA{uuid.uuid4().hex[:8].upper()}"
                    conn.execute(
                        "INSERT INTO student_answers (id, submission_id, homework_id, student_id, problem_sequence, problem, correct_answer, student_answer, is_correct, error_code, error_label, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (ans_id, sub_id, hw_id, sid, p["sequence"],
                         p["problem"], p["correct_answer"], stu_ans,
                         is_correct, error_code if not is_correct else None,
                         ERROR_LABELS.get(error_code, "") if not is_correct else None,
                         submit_date),
                    )
                    answer_count += 1

                    # Diagnosis history
                    diag_id = f"DH{uuid.uuid4().hex[:8].upper()}"
                    conn.execute(
                        "INSERT INTO diagnosis_history (id, student_id, class_id, grade, problem, correct_answer, student_answer, student_steps, is_correct, error_code, error_label, confidence, teacher_action, guidance_mode, review_status, created_at) "
                        "VALUES (?, ?, ?, 6, ?, ?, ?, '[]', ?, ?, ?, 0.9, 'review', 'standard', 'pending_teacher_review', ?)",
                        (diag_id, sid, CLASS_ID, p["problem"], p["correct_answer"],
                         stu_ans, is_correct,
                         error_code if not is_correct else "OK",
                         ERROR_LABELS.get(error_code if not is_correct else "OK", ""),
                         submit_date),
                    )
                    diag_count += 1

                total = len(problems)
                accuracy = correct_count / total
                all_results.append(dict(
                    student_id=sid, name=name, tier=tier, week=week,
                    accuracy=accuracy, correct_count=correct_count, total=total,
                ))
                perf = "✅" if accuracy >= 0.8 else "👍" if accuracy >= 0.6 else "📈" if accuracy >= 0.4 else "❌"
                print(f"  {name} — {correct_count}/{total} ({accuracy:.0%}) {perf}")

        print()

    conn.commit()

    # ── Quiz sessions (weeks 9-20) ──
    print("📋 生成第9-20周课堂测验...")
    quiz_configs = [
        dict(week=9,  title="第9周课堂小测 — 运算顺序与小数", codes=["E05", "E06"],
             responses=["mostly_correct", "mixed", "mostly_correct", "mixed", "mostly_correct",
                        "mostly_wrong", "mixed", "mostly_correct", "mostly_correct", "mixed"]),
        dict(week=11, title="第11周课堂小测 — 基础运算与验算", codes=["E01", "E11"],
             responses=["mixed", "mostly_correct", "mixed", "mostly_wrong", "mostly_correct",
                        "mostly_correct", "mixed", "mostly_correct", "mixed", "mostly_correct"]),
        dict(week=13, title="第13周混合复习测验", codes=["E01", "E03", "E05", "E09"],
             responses=["mixed", "mostly_wrong", "mostly_correct", "mixed", "mostly_correct",
                        "mostly_correct", "mostly_correct", "mixed", "mostly_wrong", "mixed"]),
        dict(week=15, title="第15周综合测验 — 基础与进位", codes=["E01", "E02", "E03"],
             responses=["mostly_correct", "mostly_correct", "mixed", "mostly_correct", "mixed",
                        "mixed", "mostly_correct", "mostly_correct", "mixed", "mostly_correct"]),
        dict(week=17, title="第17周期末复习测验", codes=["E01", "E06", "E09", "E10"],
             responses=["mostly_correct", "mixed", "mostly_correct", "mostly_correct", "mixed",
                        "mostly_wrong", "mixed", "mostly_correct", "mostly_correct", "mostly_correct"]),
        dict(week=19, title="第19周期末冲刺测验", codes=["E04", "E05", "E09", "E10"],
             responses=["mostly_correct", "mostly_correct", "mixed", "mostly_correct", "mostly_correct",
                        "mostly_correct", "mixed", "mostly_correct", "mixed", "mostly_correct"]),
        dict(week=20, title="期末综合模拟测验", codes=ALL_DIAG_CODES[:5],
             responses=["mixed", "mostly_correct", "mixed", "mostly_correct", "mostly_correct",
                        "mostly_correct", "mixed", "mostly_correct", "mostly_correct", "mostly_correct",
                        "mixed", "mostly_correct"]),
    ]

    quiz_rng = random.Random(99)
    quiz_count = 0
    for cfg in quiz_configs:
        qid = f"QZ{uuid.uuid4().hex[:8].upper()}"
        dt = (base_date + timedelta(weeks=(cfg["week"] - 9))).strftime("%Y-%m-%d")
        n_problems = len(cfg["responses"])

        conn.execute(
            "INSERT INTO quiz_sessions (id, class_id, title, status, target_error_codes, problem_count, difficulty, grade, created_at, completed_at) "
            "VALUES (?, ?, ?, 'completed', ?, ?, 'B', 6, ?, ?)",
            (qid, CLASS_ID, cfg["title"], str(cfg["codes"]).replace("'", '"'),
             n_problems, dt, dt),
        )

        for i in range(n_problems):
            code = cfg["codes"][i % len(cfg["codes"])]
            gen = _PROBLEM_GENS.get(code, _gen_basic_fact)
            text, answer = gen(quiz_rng)
            conn.execute(
                "INSERT INTO quiz_problems (id, quiz_id, sequence, problem, correct_answer, target_error_code, difficulty, knowledge_point, hint) "
                "VALUES (?, ?, ?, ?, ?, ?, 'B', ?, '')",
                (f"QP{uuid.uuid4().hex[:8].upper()}", qid, i + 1,
                 text, answer, code, f"第{cfg['week']}周测验"),
            )
            conn.execute(
                "INSERT INTO quiz_responses (id, quiz_id, problem_sequence, class_response, notes, created_at) "
                "VALUES (?, ?, ?, ?, '', ?)",
                (f"QR{uuid.uuid4().hex[:8].upper()}", qid, i + 1,
                 cfg["responses"][i], dt),
            )

        quiz_count += 1

    conn.commit()
    print(f"  ✅ 已生成 {quiz_count} 个课堂测验\n")

    # ── Rebuild trajectory from ALL diagnosis history ──
    print("📊 重建学习轨迹 (全部20周)...")
    conn.execute("DELETE FROM student_error_trajectory")

    unit_row = conn.execute("SELECT id FROM teaching_units LIMIT 1").fetchone()
    default_unit = unit_row["id"] if unit_row else "U01"

    diag_rows = conn.execute(
        "SELECT student_id, error_code, is_correct, created_at FROM diagnosis_history "
        "WHERE student_id IN (SELECT id FROM students WHERE class_id = ?) ORDER BY created_at",
        (CLASS_ID,),
    ).fetchall()

    grouped = defaultdict(lambda: {"err": 0, "ok": 0})
    for r in diag_rows:
        try:
            day = int(r["created_at"][:10].split("-")[2])
            month = int(r["created_at"][5:7])
            # Week 1-8: March (month 3), Week 9-20: April+ (month 4+)
            if month <= 3:
                week = max(1, min(8, (day - 10) // 7 + 1))
            else:
                days_from_apr14 = (datetime.strptime(r["created_at"][:10], "%Y-%m-%d") - datetime(2026, 4, 14)).days
                week = 9 + max(0, days_from_apr14 // 7)
                week = max(9, min(20, week))
        except (ValueError, IndexError):
            week = 1

        key = (r["student_id"], week, r["error_code"] or "OK")
        if r["is_correct"]:
            grouped[key]["ok"] += 1
        else:
            grouped[key]["err"] += 1

    traj_count = 0
    for (sid, wk, code), c in grouped.items():
        total = c["err"] + c["ok"]
        acc = c["ok"] / total if total else 0.0
        conn.execute(
            "INSERT INTO student_error_trajectory (id, student_id, unit_id, week_number, error_code, error_count, correct_count, accuracy, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', datetime('now'))",
            (f"SET{uuid.uuid4().hex[:8].upper()}", sid, default_unit,
             wk, code, c["err"], c["ok"], round(acc, 3)),
        )
        traj_count += 1

    conn.commit()
    print(f"  ✅ 已生成 {traj_count} 条轨迹记录\n")

    # ── Rebuild student_error_stats from ALL answers ──
    print("📊 重建学生错误统计...")
    conn.execute("DELETE FROM student_error_stats")

    ans_rows = conn.execute(
        "SELECT student_id, error_code, is_correct, created_at FROM student_answers "
        "WHERE student_id IN (SELECT id FROM students WHERE class_id = ?)",
        (CLASS_ID,),
    ).fetchall()

    stats = defaultdict(lambda: {"total": 0, "correct": 0, "last_seen": ""})
    for r in ans_rows:
        code = r["error_code"] if r["error_code"] else "OK"
        key = (r["student_id"], code)
        stats[key]["total"] += 1
        if r["is_correct"]:
            stats[key]["correct"] += 1
        if r["created_at"] and r["created_at"] > stats[key]["last_seen"]:
            stats[key]["last_seen"] = r["created_at"]

    stat_count = 0
    for (sid, code), c in stats.items():
        conn.execute(
            "INSERT INTO student_error_stats (id, student_id, error_code, total_attempts, correct_count, last_seen_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (f"SES{uuid.uuid4().hex[:8].upper()}", sid, code,
             c["total"], c["correct"], c["last_seen"]),
        )
        stat_count += 1

    conn.commit()
    print(f"  ✅ 已生成 {stat_count} 条统计记录\n")

    # ── Advance growth stages ──
    print("🌳 更新成长阶段...")
    STAGE_THRESHOLDS = [1, 3, 7, 14, 21, 30, 45, 60, 90]
    STAGE_NAMES = ["seed", "sprout", "first_leaf", "taller", "branching", "sturdy", "bud", "flowering", "mature"]

    for sid in STUDENT_IDS:
        days_row = conn.execute(
            "SELECT COUNT(DISTINCT date(created_at)) as days FROM diagnosis_history WHERE student_id = ?",
            (sid,),
        ).fetchone()
        days = days_row["days"] if days_row else 0

        acc_row = conn.execute(
            "SELECT SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as acc FROM diagnosis_history WHERE student_id = ?",
            (sid,),
        ).fetchone()
        accuracy = acc_row["acc"] if acc_row and acc_row["acc"] else 0.0

        # Mastery count: error codes with >= 80% accuracy
        mastery_row = conn.execute(
            "SELECT COUNT(*) FROM (SELECT error_code, SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as acc FROM diagnosis_history WHERE student_id = ? AND error_code != 'OK' GROUP BY error_code HAVING acc >= 0.8)",
            (sid,),
        ).fetchone()
        mastery_count = mastery_row[0] if mastery_row else 0

        # Find stage
        stage_idx = 0
        for i, threshold in enumerate(STAGE_THRESHOLDS):
            if days >= threshold:
                stage_idx = i

        # Accelerate/decelerate
        if accuracy >= 0.80 and mastery_count >= 3:
            stage_idx = min(stage_idx + 1, len(STAGE_NAMES) - 1)
        if accuracy < 0.50 and days > 7:
            stage_idx = max(stage_idx - 1, 0)

        stage = STAGE_NAMES[stage_idx]

        conn.execute(
            "UPDATE student_cycle_progress SET current_stage = ?, days_completed = ? WHERE student_id = ?",
            (stage, days, sid),
        )
        name = STUDENT_PROFILES[sid]["name"]
        print(f"  {name} ({sid}): {stage} ({days}天, {accuracy:.0%}准确率, {mastery_count}掌握)")

    conn.commit()
    print()

    # ── Generate scanned_submissions ──
    print("📄 生成扫描提交记录...")
    scan_count = 0
    for sid in STUDENT_IDS:
        for w in range(9, 21, 2):
            scan_date = (base_date + timedelta(weeks=(w - 9), days=rng.randint(0, 4))).strftime("%Y-%m-%d")
            conn.execute(
                "INSERT OR IGNORE INTO scanned_submissions (id, student_id, homework_id, pdf_path, ocr_status, ocr_result_json, graded_status, uploaded_at) "
                "VALUES (?, ?, ?, ?, 'pending', NULL, 'pending', ?)",
                (f"SC{uuid.uuid4().hex[:8].upper()}", sid, f"HW{uuid.uuid4().hex[:8].upper()}",
                 f"/uploads/{sid}/scan_w{w}.pdf", scan_date),
            )
            scan_count += 1
    conn.commit()
    print(f"  ✅ 已生成 {scan_count} 条扫描记录\n")

    # ── Profile snapshots ──
    print("📸 生成画像快照...")
    snap_count = 0
    for sid in STUDENT_IDS:
        profile = STUDENT_PROFILES[sid]
        for snap_week in [10, 14, 18]:
            snap_date = (base_date + timedelta(weeks=(snap_week - 9))).strftime("%Y-%m-%d")
            week_results = [r for r in all_results if r["student_id"] == sid and r["week"] <= snap_week]
            if not week_results:
                continue
            tot_ok = sum(r["correct_count"] for r in week_results)
            tot_all = sum(r["total"] for r in week_results)
            overall_acc = tot_ok / tot_all if tot_all else 0

            analysis = {
                "week": snap_week,
                "accuracy": round(overall_acc, 3),
                "total_problems": tot_all,
                "tier": profile["tier"],
                "trajectory_type": profile["trajectory_type"],
            }
            conn.execute(
                "INSERT INTO profile_snapshots (id, student_id, snapshot_type, analysis_json, portrait_summary, personality_tags, growth_narrative, created_at) "
                "VALUES (?, ?, 'weekly', ?, ?, ?, ?, ?)",
                (f"PS{uuid.uuid4().hex[:8].upper()}", sid,
                 str(analysis).replace("'", '"'),
                 f"{profile['name']}在第{snap_week}周的整体正确率为{overall_acc:.0%}",
                 str(profile["personality_tags"]).replace("'", '"'),
                 f"持续进步中", snap_date),
            )
            snap_count += 1
    conn.commit()
    print(f"  ✅ 已生成 {snap_count} 条画像快照\n")

    # ── Final summary ──
    print("=" * 72)
    print("📊 Phase-2 仿真完成 — 数据汇总")
    print("=" * 72)

    final_hw = conn.execute("SELECT COUNT(*) FROM homework").fetchone()[0]
    final_sub = conn.execute("SELECT COUNT(*) FROM homework_submissions").fetchone()[0]
    final_ans = conn.execute("SELECT COUNT(*) FROM student_answers").fetchone()[0]
    final_diag = conn.execute("SELECT COUNT(*) FROM diagnosis_history").fetchone()[0]
    final_quiz = conn.execute("SELECT COUNT(*) FROM quiz_sessions").fetchone()[0]
    final_resp = conn.execute("SELECT COUNT(*) FROM quiz_responses").fetchone()[0]
    final_traj = conn.execute("SELECT COUNT(*) FROM student_error_trajectory").fetchone()[0]
    final_stat = conn.execute("SELECT COUNT(*) FROM student_error_stats").fetchone()[0]
    final_scan = conn.execute("SELECT COUNT(*) FROM scanned_submissions").fetchone()[0]
    final_snap = conn.execute("SELECT COUNT(*) FROM profile_snapshots").fetchone()[0]

    # Total row count
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'fts%' AND name NOT LIKE '%_seg%' AND name NOT LIKE '%_doc%' AND name NOT LIKE '%_content%' AND name NOT LIKE '%_data%'"
    ).fetchall()]
    total = sum(conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0] for t in tables)

    print(f"""
  作业:          {final_hw} (+{hw_count})
  提交:          {final_sub} (+{submission_count})
  答题:          {final_ans} (+{answer_count})
  诊断:          {final_diag} (+{diag_count})
  测验:          {final_quiz} (+{quiz_count})
  测验回答:      {final_resp}
  轨迹:          {final_traj}
  错误统计:      {final_stat}
  扫描:          {final_scan}
  画像快照:      {final_snap}
  ─────────────────────────────
  总记录数:      {total}
    """)

    # Error code distribution
    dist = conn.execute(
        "SELECT error_code, COUNT(*) as cnt FROM diagnosis_history GROUP BY error_code ORDER BY cnt DESC"
    ).fetchall()
    print("  错因分布:")
    for r in dist:
        bar = "█" * min(30, r["cnt"] // 10)
        label = ERROR_LABELS.get(r["error_code"], r["error_code"])
        print(f"    {r['error_code']} ({label}): {r['cnt']:>5d}  {bar}")
    print()

    # Student trajectory overview
    print("📊 20周学习轨迹总览")
    print("─" * 72)
    for tier in TIER_ORDER:
        emoji = TIER_EMOJI[tier]
        print(f"\n  {emoji} {tier}组")
        for sid, profile in STUDENT_PROFILES.items():
            if profile["tier"] != tier:
                continue
            name = profile["name"]
            ws = [r for r in all_results if r["student_id"] == sid]
            if not ws:
                continue
            tot_ok = sum(r["correct_count"] for r in ws)
            tot_all = sum(r["total"] for r in ws)
            overall = tot_ok / tot_all if tot_all else 0
            first, last = ws[0]["accuracy"], ws[-1]["accuracy"]
            wstr = " → ".join(f"W{r['week']}:{r['accuracy']:.0%}" for r in ws[:4]) + " → ... → " + f"W{ws[-1]['week']}:{ws[-1]['accuracy']:.0%}"
            imp = last - first
            imp_s = f"+{imp:.0%}" if imp >= 0 else f"{imp:.0%}"
            trend = "📈" if imp > 0.05 else "📉" if imp < -0.05 else "➡️"
            print(f"  {name}: {tot_ok}/{tot_all} ({overall:.0%}) | W9:{first:.0%}→W20:{last:.0%} ({imp_s}) {trend}")
            print(f"    {wstr}")

    conn.close()
    print(f"\n✅ Phase-2 仿真完成!")


if __name__ == "__main__":
    run()

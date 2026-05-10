#!/usr/bin/env python3
"""
Realistic Homework Lifecycle Simulation
========================================
8-week simulation with 10 students across 3 tiers, each with distinct error patterns.

Pipeline: generate → assign → students write (with realistic errors) → auto-grade → update profile → adaptive next round.

Usage:
    cd /mnt/d/Ubuntu_WSL/Teaching_agent/development
    PYTHONPATH=. /home/lyzhang/miniconda3/envs/pyt0/bin/python scripts/simulate_realistic.py
"""

from __future__ import annotations

import asyncio
import random
import sqlite3
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "calc_forest.db"
CLASS_ID = "G6C1"
PYTHON = "/home/lyzhang/miniconda3/envs/pyt0/bin/python"

# ──────────────────────────────────────────────────────────────────────────────
# Student profiles — 3 tiers with realistic Chinese primary school characters
# ──────────────────────────────────────────────────────────────────────────────

STUDENT_PROFILES = {
    # ── 优秀组 (3 students) — accuracy 80-95% ──
    "S002": {
        "tier": "优秀",
        "name": "李思琪",
        "base_accuracy": 0.88,
        # Per-error-code base accuracy (only weak codes listed; others default to base_accuracy)
        "code_accuracy": {"E02": 0.72, "E08": 0.68},
        "improve_rate": 0.015,
        "description": "细心但偶尔粗心 — 擅长计算但偶尔进位错误和步骤遗漏",
    },
    "S004": {
        "tier": "优秀",
        "name": "刘雨萱",
        "base_accuracy": 0.92,
        "code_accuracy": {"E05": 0.76},
        "improve_rate": 0.010,
        "description": "几乎全对 — 运算顺序偶尔搞混",
    },
    "S009": {
        "tier": "优秀",
        "name": "周思远",
        "base_accuracy": 0.85,
        "code_accuracy": {"E08": 0.70},
        "improve_rate": 0.015,
        "description": "条理清晰但偶尔跳步 — 步骤遗漏",
    },
    # ── 中等组 (4 students) — accuracy 55-80% ──
    "S003": {
        "tier": "中等",
        "name": "张浩然",
        "base_accuracy": 0.65,
        "code_accuracy": {"E03": 0.42, "E09": 0.48},
        "improve_rate": 0.030,
        "description": "努力但理解有偏差 — 退位减法弱, 算理理解不足",
    },
    "S005": {
        "tier": "中等",
        "name": "陈梓轩",
        "base_accuracy": 0.60,
        "code_accuracy": {"E02": 0.48, "E04": 0.45, "E06": 0.42},
        "improve_rate": 0.035,
        "description": "计算基础不牢 — 进位错误, 数位对齐, 小数点",
    },
    "S007": {
        "tier": "中等",
        "name": "黄俊杰",
        "base_accuracy": 0.62,
        "code_accuracy": {"E06": 0.40, "E09": 0.45},
        "improve_rate": 0.030,
        "description": "概念模糊 — 小数分数互化, 算理理解",
    },
    "S010": {
        "tier": "中等",
        "name": "吴佳怡",
        "base_accuracy": 0.58,
        "code_accuracy": {"E01": 0.42, "E05": 0.40, "E06": 0.38},
        "improve_rate": 0.035,
        "description": "口算弱, 概念也弱 — 基础事实, 运算顺序, 小数点",
    },
    # ── 需关注组 (3 students) — accuracy 25-55% ──
    "S001": {
        "tier": "需关注",
        "name": "王子涵",
        "base_accuracy": 0.42,
        "code_accuracy": {"E03": 0.25, "E06": 0.20, "E08": 0.30},
        "improve_rate": 0.040,
        "description": "多方面薄弱, 需要系统帮扶 — 退位, 小数点严重, 步骤遗漏",
    },
    "S006": {
        "tier": "需关注",
        "name": "杨诗涵",
        "base_accuracy": 0.35,
        "code_accuracy": {"E01": 0.28, "E03": 0.22, "E07": 0.30, "E10": 0.25},
        "improve_rate": 0.045,
        "description": "基础差+习惯差 — 基础事实, 退位, 抄题, 审题",
    },
    "S008": {
        "tier": "需关注",
        "name": "赵梦琪",
        "base_accuracy": 0.38,
        "code_accuracy": {"E02": 0.25, "E03": 0.22, "E09": 0.28},
        "improve_rate": 0.040,
        "description": "理解困难, 需要更多引导 — 进位, 退位, 算理",
    },
}

STUDENT_IDS = list(STUDENT_PROFILES.keys())
TIER_ORDER = ["需关注", "中等", "优秀"]

# Error codes used by the problem generator
ALL_ERROR_CODES = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11"]

# Error code Chinese labels
ERROR_LABELS = {
    "OK": "正确", "E01": "基础事实", "E02": "进位错误", "E03": "退位错误",
    "E04": "数位对齐", "E05": "运算顺序", "E06": "小数/分数", "E07": "抄写错误",
    "E08": "步骤遗漏", "E09": "算理理解", "E10": "审题错误", "E11": "未验算", "E99": "未识别",
}

# Tier emojis
TIER_EMOJI = {"优秀": "🌟", "中等": "📊", "需关注": "⚠️"}


# ──────────────────────────────────────────────────────────────────────────────
# Tier-based homework configuration
# ──────────────────────────────────────────────────────────────────────────────

def get_tier_config(tier: str, week: int) -> dict:
    """Return homework config for a tier at a given week."""
    if tier == "优秀":
        difficulty = "C" if week >= 5 else "B"
        return {
            "difficulty": difficulty,
            "problem_count": 5,
            "focus_description": "B/C难度, 重点强化1-2个薄弱项",
        }
    elif tier == "中等":
        difficulty = "B" if week >= 4 else "A"
        return {
            "difficulty": difficulty,
            "problem_count": 5,
            "focus_description": "A/B难度, 聚焦2-3个薄弱项",
        }
    else:
        difficulty = "B" if week >= 6 else "A"
        return {
            "difficulty": difficulty,
            "problem_count": 5,
            "focus_description": "A难度(后期渐进B), 系统攻克3+个薄弱项",
        }


def get_tier_target_codes(profiles: list[dict]) -> list[str]:
    """Get target error codes for a tier based on students' weak codes."""
    code_counts = Counter()
    for p in profiles:
        code_counts.update(p["code_accuracy"].keys())
    # Return top 3 most common weak codes across the tier
    return [code for code, _ in code_counts.most_common(3)]


# ──────────────────────────────────────────────────────────────────────────────
# Wrong answer generation — error-code-specific plausible wrong answers
# ──────────────────────────────────────────────────────────────────────────────

def _parse_fraction_or_number(s: str) -> tuple[Fraction | None, str]:
    """Parse a string like '3/4', '15', '2π cm²', '50%', '0.5' into (Fraction, suffix)."""
    s = s.strip()
    # Extract suffix (units like 'π cm²', '元', '%')
    suffix = ""
    body = s
    for marker in ["π cm²", "π cm", "元", "%"]:
        if marker in s:
            idx = s.index(marker)
            body = s[:idx].strip()
            suffix = marker
            break

    # Handle "X和Y/Z" format
    if "和" in body:
        parts = body.split("和")
        try:
            dec_part = Fraction(parts[0].strip()) if parts[0].strip() else Fraction(0)
            frac_match = __import__("re").search(r"(\d+)\s*/\s*(\d+)", parts[1])
            if frac_match:
                frac_part = Fraction(int(frac_match.group(1)), int(frac_match.group(2)))
                return dec_part + frac_part, suffix
        except (ValueError, ZeroDivisionError):
            pass
        return None, suffix

    # Handle pure fraction
    frac_match = __import__("re").search(r"(\d+)\s*/\s*(\d+)", body)
    if frac_match:
        try:
            return Fraction(int(frac_match.group(1)), int(frac_match.group(2))), suffix
        except (ValueError, ZeroDivisionError):
            return None, suffix

    # Handle mixed number "a又b/c"
    mixed_match = __import__("re").search(r"(\d+)又(\d+)/(\d+)", body)
    if mixed_match:
        try:
            whole = int(mixed_match.group(1))
            num = int(mixed_match.group(2))
            den = int(mixed_match.group(3))
            return Fraction(whole * den + num, den), suffix
        except (ValueError, ZeroDivisionError):
            return None, suffix

    # Handle integer or decimal
    num_match = __import__("re").search(r"[\-]?\d+\.?\d*", body)
    if num_match:
        try:
            return Fraction(num_match.group(0)), suffix
        except ValueError:
            pass

    return None, suffix


def _frac_to_answer_str(f: Fraction, suffix: str = "") -> str:
    """Convert Fraction back to answer string matching expected formats."""
    if suffix == "%":
        val = float(f) * 100
        if val == int(val):
            return f"{int(val)}%"
        return f"{val:.1f}%"

    if suffix in ("π cm²", "π cm"):
        if f.denominator == 1:
            coeff = f.numerator
        else:
            coeff = f.numerator if f.denominator == 1 else f.numerator
        if coeff == 1:
            return f"π {suffix[2:]}" if suffix.startswith("π ") else f"π{suffix}"
        return f"{coeff}π {suffix[2:]}" if suffix.startswith("π ") else f"{coeff}π{suffix}"

    if suffix == "元":
        val = float(f)
        if val == int(val):
            return f"{int(val)}元"
        return f"{val}元"

    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def generate_wrong_answer(correct: str, target_error_code: str) -> tuple[str, str]:
    """Generate a plausible wrong answer for a given error code.

    Returns (wrong_answer, error_description).
    """
    value, suffix = _parse_fraction_or_number(correct)

    if value is None:
        # Fallback: just modify the string slightly
        return _wrong_answer_fallback(correct, target_error_code)

    rng = random.Random()  # Use default randomness

    if target_error_code == "E01":
        # 基础事实错误: off by ±1, ±2, or swap digits
        if value.denominator == 1:
            n = value.numerator
            offset = rng.choice([-2, -1, 1, 2])
            wrong = n + offset
            return _frac_to_answer_str(Fraction(wrong), suffix), f"基础事实错误, {n}→{wrong} (偏差{offset:+d})"
        else:
            # Fraction: flip numerator or denominator
            n, d = value.numerator, value.denominator
            choice = rng.choice(["num+1", "num-1", "flip"])
            if choice == "num+1":
                wrong = Fraction(n + 1, d)
            elif choice == "num-1":
                wrong = Fraction(max(1, n - 1), d)
            else:
                wrong = Fraction(d, n) if n > 0 else value
            return _frac_to_answer_str(wrong, suffix), f"基础事实错误, {value}→{wrong}"

    elif target_error_code == "E02":
        # 进位错误: forget carry
        if value.denominator == 1:
            n = value.numerator
            wrong = n - rng.choice([1, 10, 100])
            if wrong < 0:
                wrong = n + rng.choice([1, 10])
            return _frac_to_answer_str(Fraction(wrong), suffix), f"进位错误, 忘记进位 {n}→{wrong}"
        else:
            # Fraction: add 1 to whole number part
            wrong = value + 1
            return _frac_to_answer_str(wrong, suffix), f"进位错误, {value}→{wrong}"

    elif target_error_code == "E03":
        # 退位错误: forget borrow
        if value.denominator == 1:
            n = value.numerator
            wrong = n + rng.choice([10, 100, 110])
            return _frac_to_answer_str(Fraction(wrong), suffix), f"退位错误, 忘记借位 {n}→{wrong}"
        else:
            wrong = value + Fraction(1, 1)
            return _frac_to_answer_str(wrong, suffix), f"退位错误, {value}→{wrong}"

    elif target_error_code == "E04":
        # 数位对齐: shift digits (×10 or ÷10)
        if value.denominator == 1:
            n = value.numerator
            if suffix in ("π cm²", "π cm"):
                # For area/circumference, shift the coefficient
                wrong = value * 10
                return _frac_to_answer_str(wrong, suffix), f"数位对齐错误, 系数多一位 {value}→{wrong}"
            wrong = rng.choice([n * 10, n * 100])
            return _frac_to_answer_str(Fraction(wrong), suffix), f"数位对齐错误, 数位偏移 {n}→{wrong}"
        else:
            wrong = value * 10
            return _frac_to_answer_str(wrong, suffix), f"数位对齐错误, {value}→{wrong}"

    elif target_error_code == "E05":
        # 运算顺序: compute left-to-right instead of proper precedence
        if value.denominator == 1:
            n = value.numerator
            # Common pattern: answer = (a+b)*c instead of a+b*c
            wrong = rng.choice([n + rng.choice([5, 10, 20]), n - rng.choice([5, 10])])
            if wrong < 0:
                wrong = abs(wrong)
            return _frac_to_answer_str(Fraction(wrong), suffix), f"运算顺序错误, 先加减后乘除 {n}→{wrong}"
        else:
            wrong = value * 2
            return _frac_to_answer_str(wrong, suffix), f"运算顺序错误, {value}→{wrong}"

    elif target_error_code == "E06":
        # 小数点/分数单位: shift decimal or invert fraction
        if suffix == "%":
            # Common: 50% → 5% or 500%
            val_pct = float(value) * 100
            if val_pct >= 10:
                wrong_pct = val_pct / 10
            else:
                wrong_pct = val_pct * 10
            if wrong_pct == int(wrong_pct):
                wrong_pct = int(wrong_pct)
            return f"{wrong_pct}%", f"小数点错误, {float(value)*100}%→{wrong_pct}%"
        elif value.denominator == 1:
            n = value.numerator
            wrong = rng.choice([n * 10, n // 10 if n >= 10 else n])
            return _frac_to_answer_str(Fraction(wrong), suffix), f"小数点移位, {n}→{wrong}"
        else:
            # Fraction unit error: swap numerator/denominator or use wrong denominator
            n, d = value.numerator, value.denominator
            wrong = Fraction(d, n) if n > 0 else value
            return _frac_to_answer_str(wrong, suffix), f"分数单位错误, {value}→{wrong}"

    elif target_error_code == "E07":
        # 抄写错误: copy a number wrong (digit substitution)
        if value.denominator == 1:
            n = value.numerator
            digits = list(str(abs(n)))
            if len(digits) >= 1:
                idx = rng.randint(0, len(digits) - 1)
                old_digit = digits[idx]
                new_digit = str((int(old_digit) + rng.choice([1, 2, 3])) % 10)
                digits[idx] = new_digit
                wrong = int("".join(digits))
                if n < 0:
                    wrong = -wrong
                return _frac_to_answer_str(Fraction(wrong), suffix), f"抄写错误, {n}中{old_digit}→{new_digit}"
        # Fraction: change one digit in numerator or denominator
        n, d = value.numerator, value.denominator
        wrong = Fraction(n + 1, d)
        return _frac_to_answer_str(wrong, suffix), f"抄写错误, {value}→{wrong}"

    elif target_error_code == "E08":
        # 步骤遗漏: skip a step (e.g., forget ÷3 for cone, forget ×2 for surface area)
        if suffix in ("π cm²", "π cm"):
            # Common: surface area without bases, circumference without ×2, volume without ÷3
            if value > 0:
                wrong = value * 2  # or value / 3 for cone
                if rng.random() < 0.5:
                    wrong = value * Fraction(2, 3)  # Forget ÷3 → have 3× too much, but let's do this
                return _frac_to_answer_str(wrong, suffix), f"步骤遗漏, 忘记除以某因子 {value}→{wrong}"
        if value.denominator == 1:
            n = value.numerator
            # Skip last step: forget to multiply or divide
            wrong = rng.choice([n * 2, n * 3, n // 2 if n >= 2 else n, n // 3 if n >= 3 else n])
            return _frac_to_answer_str(Fraction(wrong), suffix), f"步骤遗漏, 跳过最后一步 {n}→{wrong}"
        else:
            wrong = value * 2
            return _frac_to_answer_str(wrong, suffix), f"步骤遗漏, {value}→{wrong}"

    elif target_error_code == "E09":
        # 算理理解: conceptual error (r² = r×2, area = π×d instead of π×r²)
        if suffix in ("π cm²", "π cm"):
            # r² → r×2 type error: if coeff is a perfect square, use 2*sqrt instead
            n, d = value.numerator, value.denominator
            import math
            if d == 1:
                sqrt_n = math.isqrt(abs(n))
                if sqrt_n * sqrt_n == abs(n):
                    # r² = n → r = sqrt_n, wrong: r×2 = 2*sqrt_n → wrong coeff
                    wrong = Fraction(2 * sqrt_n)
                    return _frac_to_answer_str(wrong, suffix), f"算理错误, r²=r×2 {n}→{2*sqrt_n}"
            wrong = value * 2
            return _frac_to_answer_str(wrong, suffix), f"算理理解错误, {value}→{wrong}"
        if value.denominator == 1:
            n = value.numerator
            wrong = rng.choice([n * 2, n + n // 2 if n > 0 else n])
            return _frac_to_answer_str(Fraction(wrong), suffix), f"算理理解错误, {n}→{wrong}"
        else:
            wrong = value * 2
            return _frac_to_answer_str(wrong, suffix), f"算理理解错误, {value}→{wrong}"

    elif target_error_code == "E10":
        # 审题错误: misunderstood the question
        if suffix == "元":
            val = float(value)
            wrong = val * 2
            if wrong == int(wrong):
                wrong = int(wrong)
            return f"{wrong}元", f"审题错误, 求的是另一部分 {val}→{wrong}"
        if value.denominator == 1:
            n = value.numerator
            # Answer the wrong question
            wrong = rng.choice([n * 2, max(0, n * 3 - n)])
            return _frac_to_answer_str(Fraction(wrong), suffix), f"审题错误, 理解偏差 {n}→{wrong}"
        else:
            wrong = 1 - value if 0 < value < 1 else value * 2
            return _frac_to_answer_str(wrong, suffix), f"审题错误, {value}→{wrong}"

    elif target_error_code == "E11":
        # 未验算: plausible but wrong answer, student didn't check
        if value.denominator == 1:
            n = value.numerator
            wrong = n + rng.choice([-5, -3, 3, 5, 10])
            if wrong < 0:
                wrong = n + rng.choice([3, 5, 10])
            return _frac_to_answer_str(Fraction(wrong), suffix), f"未验算, {n}→{wrong} (合理但错误)"
        else:
            # Slightly off fraction
            wrong = value + Fraction(1, value.denominator)
            return _frac_to_answer_str(wrong, suffix), f"未验算, {value}→{wrong}"

    else:
        return _wrong_answer_fallback(correct, target_error_code)


def _wrong_answer_fallback(correct: str, target_error_code: str) -> tuple[str, str]:
    """Fallback wrong answer when specific generation fails."""
    value, suffix = _parse_fraction_or_number(correct)
    if value is not None:
        if value.denominator == 1:
            n = value.numerator
            wrong = n + random.choice([-10, -5, -1, 1, 5, 10])
            if wrong < 0:
                wrong = abs(wrong)
            return _frac_to_answer_str(Fraction(wrong), suffix), f"计算错误 {n}→{wrong}"
        else:
            wrong = value + Fraction(1, value.denominator * 2)
            return _frac_to_answer_str(wrong, suffix), f"计算错误 {value}→{wrong}"
    return correct + "?", "答案异常"


# ──────────────────────────────────────────────────────────────────────────────
# Streak tracking per student per error code
# ──────────────────────────────────────────────────────────────────────────────

class StreakTracker:
    """Track consecutive correct/incorrect answers per student per error code."""

    def __init__(self):
        self._streaks: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))

    def record(self, student_id: str, error_code: str, is_correct: bool):
        self._streaks[student_id][error_code].append(is_correct)
        # Keep last 10 results
        if len(self._streaks[student_id][error_code]) > 10:
            self._streaks[student_id][error_code] = self._streaks[student_id][error_code][-10:]

    def get_streak_bonus(self, student_id: str, error_code: str) -> float:
        """Return accuracy adjustment based on recent streak."""
        history = self._streaks[student_id][error_code]
        if len(history) < 3:
            return 0.0
        recent = history[-3:]
        if all(recent):
            return 0.08  # 3+ correct in a row → +8%
        if not any(recent):
            return -0.05  # 3+ wrong in a row → -5%
        return 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Accuracy model
# ──────────────────────────────────────────────────────────────────────────────

def get_student_accuracy_for_code(
    profile: dict,
    error_code: str,
    week: int,
    streak_bonus: float = 0.0,
) -> float:
    """Compute probability of correct answer for a specific error code at a given week."""
    base = profile["base_accuracy"]
    code_base = profile["code_accuracy"].get(error_code, base + 0.10)
    improve = profile["improve_rate"]

    # Natural improvement over weeks
    acc = code_base + improve * week

    # Streak bonus
    acc += streak_bonus

    # Small random noise
    acc += random.uniform(-0.03, 0.03)

    return max(0.10, min(0.98, acc))


# ──────────────────────────────────────────────────────────────────────────────
# Simulation engine
# ──────────────────────────────────────────────────────────────────────────────

async def run_simulation():
    import os
    os.environ["DIFY_ENABLED"] = "false"
    os.environ["LOCAL_DIFY_ENABLED"] = "false"

    from app.services.homework_service import generate_homework, assign_homework
    from app.services.grading_service import submit_homework, grade_homework
    import app.services.dify_client as _dify

    _original_call = _dify.call_dify_or_llm

    async def _skip_dify(*args, **kwargs):
        return {"skipped": True, "reason": "simulation_mode"}

    _dify.call_dify_or_llm = _skip_dify

    streak_tracker = StreakTracker()
    all_week_results: list[dict] = []

    print("=" * 72)
    print("🌲 我的计算森林 — 8周仿真模拟 🌲")
    print("=" * 72)
    print()
    print("📋 学生名单:")
    for tier in TIER_ORDER:
        students = [(sid, p) for sid, p in STUDENT_PROFILES.items() if p["tier"] == tier]
        emoji = TIER_EMOJI[tier]
        names_str = ", ".join(f"{p['name']}({sid})" for sid, p in students)
        print(f"  {emoji} {tier}组: {names_str}")
    print()

    for week in range(1, 9):
        tier_config = get_tier_config("优秀", week)  # Just for display
        print("=" * 72)
        print(f"📅 第{week}周")
        print("=" * 72)

        week_results: list[dict] = []

        # Process each tier separately
        for tier in TIER_ORDER:
            tier_students = [(sid, STUDENT_PROFILES[sid]) for sid in STUDENT_IDS if STUDENT_PROFILES[sid]["tier"] == tier]
            if not tier_students:
                continue

            config = get_tier_config(tier, week)
            target_codes = get_tier_target_codes([p for _, p in tier_students])

            emoji = TIER_EMOJI[tier]
            print(f"\n  {emoji} {tier}组 (难度: {config['difficulty']}, 目标错因: {', '.join(target_codes)})")
            print(f"     {config['focus_description']}")
            print()

            # Generate one homework per tier
            try:
                hw_result = await generate_homework(
                    class_id=CLASS_ID,
                    grade=6,
                    error_codes_target=target_codes,
                    problem_count=config["problem_count"],
                    difficulty=config["difficulty"],
                )
                hw_id = hw_result["homework_id"]
            except Exception as e:
                print(f"     ❌ 生成作业失败: {e}")
                continue

            due_date = f"2026-0{3 + week // 4}-{10 + week * 7 % 28}"
            try:
                await assign_homework(hw_id, due_date=due_date)
            except Exception as e:
                print(f"     ⚠️ 分配失败: {e}")

            # Get problems
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            problems = conn.execute(
                "SELECT * FROM homework_problems WHERE homework_id = ? ORDER BY sequence",
                (hw_id,),
            ).fetchall()
            conn.close()

            target_desc = ", ".join(target_codes)
            print(f"     📝 作业 {hw_id}: {len(problems)}题, 目标: {target_desc}")
            print()

            # Each student "writes" the homework
            for sid, profile in tier_students:
                name = profile["name"]
                answers = []
                problem_results = []
                correct_count = 0

                for p in problems:
                    correct_answer = p["correct_answer"]
                    target_code = p["target_error_code"]

                    # Get accuracy with streak bonus
                    streak_bonus = streak_tracker.get_streak_bonus(sid, target_code)
                    acc = get_student_accuracy_for_code(profile, target_code, week, streak_bonus)

                    if random.random() < acc:
                        student_ans = correct_answer
                        is_correct = True
                        correct_count += 1
                        error_desc = ""
                    else:
                        student_ans, error_desc = generate_wrong_answer(correct_answer, target_code)
                        is_correct = False

                    # Record streak
                    streak_tracker.record(sid, target_code, is_correct)

                    answers.append({
                        "problem_sequence": p["sequence"],
                        "student_answer": student_ans,
                    })

                    problem_results.append({
                        "problem": p["problem"],
                        "correct_answer": correct_answer,
                        "student_answer": student_ans,
                        "target_code": target_code,
                        "is_correct": is_correct,
                        "error_desc": error_desc,
                    })

                # Submit and grade
                try:
                    await submit_homework(hw_id, sid, answers)
                    grade_result = await grade_homework(hw_id, sid)
                except Exception as e:
                    print(f"     ❌ {name} 批改失败: {e}")
                    continue

                total = len(problems)
                accuracy = correct_count / total if total > 0 else 0
                diagnosed_errors = grade_result.get("primary_errors", [])

                # Performance indicator
                if accuracy >= 0.8:
                    perf = "✅"
                    perf_desc = "优秀"
                elif accuracy >= 0.6:
                    perf = "👍"
                    perf_desc = "良好"
                elif accuracy >= 0.4:
                    perf = "📈"
                    perf_desc = "进步中"
                else:
                    perf = "❌"
                    perf_desc = "需努力"

                # Week-over-week trend
                prev_results = [wr for wr in all_week_results if wr["student_id"] == sid]
                trend = ""
                if prev_results:
                    prev_acc = prev_results[-1]["accuracy"]
                    if accuracy > prev_acc + 0.05:
                        trend = " 📈进步"
                    elif accuracy < prev_acc - 0.05:
                        trend = " 📉退步"

                print(f"     {name} ({tier}) — {correct_count}/{total} ({accuracy:.0%}) {perf} {perf_desc}{trend}")

                # Print per-problem details
                for pr in problem_results:
                    if pr["is_correct"]:
                        print(f"       ✅ {pr['problem']}={pr['student_answer']}  ({pr['target_code']})")
                    else:
                        print(f"       ❌ {pr['problem']}={pr['student_answer']}  ({pr['target_code']} {pr['error_desc']})")

                # Brief feedback
                if diagnosed_errors:
                    error_names = [ERROR_LABELS.get(e, e) for e in diagnosed_errors[:3]]
                    print(f"       💡 反馈: 主要问题 — {', '.join(error_names)}")
                elif accuracy == 1.0:
                    print(f"       🎉 全部正确!")
                print()

                week_results.append({
                    "student_id": sid,
                    "name": name,
                    "tier": tier,
                    "week": week,
                    "accuracy": accuracy,
                    "correct_count": correct_count,
                    "total": total,
                    "diagnosed_errors": diagnosed_errors,
                    "growth_updated": grade_result.get("growth_updated", False),
                })

        all_week_results.extend(week_results)

    # ──────────────────────────────────────────────────────────────────────────
    # Final Summary
    # ──────────────────────────────────────────────────────────────────────────
    print()
    print("=" * 72)
    print("📊 8周学习轨迹总览")
    print("=" * 72)
    print()

    for tier in TIER_ORDER:
        emoji = TIER_EMOJI[tier]
        tier_students = [(sid, p) for sid, p in STUDENT_PROFILES.items() if p["tier"] == tier]
        print(f"  {emoji} {tier}组")
        print(f"  {'─' * 65}")

        for sid, profile in tier_students:
            name = profile["name"]
            student_weeks = [wr for wr in all_week_results if wr["student_id"] == sid]
            if not student_weeks:
                continue

            total_correct = sum(wr["correct_count"] for wr in student_weeks)
            total_problems = sum(wr["total"] for wr in student_weeks)
            overall_acc = total_correct / total_problems if total_problems > 0 else 0

            first_acc = student_weeks[0]["accuracy"]
            last_acc = student_weeks[-1]["accuracy"]

            # Per-week accuracy string
            weekly_acc_str = " → ".join(f"W{wr['week']}:{wr['accuracy']:.0%}" for wr in student_weeks)

            # Most common errors
            all_errors = []
            for wr in student_weeks:
                all_errors.extend(wr["diagnosed_errors"])
            error_summary = dict(Counter(all_errors).most_common(5))
            error_str = ", ".join(f"{ERROR_LABELS.get(e, e)}×{c}" for e, c in error_summary.items())

            # Trend
            if last_acc > first_acc + 0.05:
                trend = "📈 进步中"
            elif last_acc < first_acc - 0.05:
                trend = "📉 需关注"
            else:
                trend = "➡️ 稳定"

            improvement = last_acc - first_acc
            improvement_str = f"+{improvement:.0%}" if improvement >= 0 else f"{improvement:.0%}"

            print(f"  {name} ({sid})")
            print(f"    轨迹: {weekly_acc_str}")
            print(f"    总体: {total_correct}/{total_problems} ({overall_acc:.0%}) | "
                  f"首→末: {first_acc:.0%}→{last_acc:.0%} ({improvement_str}) | {trend}")
            print(f"    高频错因: {error_str if error_str else '无'}")
            print()

    # ──────────────────────────────────────────────────────────────────────────
    # Improvement summary table
    # ──────────────────────────────────────────────────────────────────────────
    print()
    print("📊 进步排行榜")
    print(f"  {'─' * 65}")
    print(f"  {'排名':<4} {'姓名':<8} {'组别':<6} {'首周':<6} {'末周':<6} {'进步':<8} {'趋势'}")
    print(f"  {'─' * 65}")

    improvements = []
    for sid, profile in STUDENT_PROFILES.items():
        student_weeks = [wr for wr in all_week_results if wr["student_id"] == sid]
        if len(student_weeks) >= 2:
            first_acc = student_weeks[0]["accuracy"]
            last_acc = student_weeks[-1]["accuracy"]
            improvements.append((sid, profile["name"], profile["tier"], first_acc, last_acc, last_acc - first_acc))

    improvements.sort(key=lambda x: x[5], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    for i, (sid, name, tier, first, last, imp) in enumerate(improvements):
        rank = medals[i] if i < 3 else f" {i + 1}"
        imp_str = f"+{imp:.0%}" if imp >= 0 else f"{imp:.0%}"
        trend = "📈" if imp > 0.05 else "📉" if imp < -0.05 else "➡️"
        print(f"  {rank:<4} {name:<8} {tier:<6} {first:.0%}    {last:.0%}    {imp_str:<8} {trend}")

    print(f"  {'─' * 65}")
    print()
    print(f"✅ 模拟完成! 8周 × {len(STUDENT_IDS)}名学生 = {len(all_week_results)}条记录")

    # Count total homework generated
    conn = sqlite3.connect(str(DB_PATH))
    hw_count = conn.execute("SELECT COUNT(*) FROM homework").fetchone()[0]
    conn.close()
    print(f"📝 数据库中共 {hw_count} 条作业记录")


if __name__ == "__main__":
    asyncio.run(run_simulation())

"""真实感学生答题模拟器。

根据学生原型（学霸/中等/薄弱/偏科）生成符合特定错因的错误答案，
确保模拟答案能被规则引擎诊断出对应的错因代码。
"""
from __future__ import annotations

import ast
import logging
import operator
import random
import re
from fractions import Fraction
from typing import Any

from app.db import get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 学生原型定义
# ---------------------------------------------------------------------------
STUDENT_ARCHETYPES: dict[str, dict[str, Any]] = {
    "high_achiever": {
        "name": "学霸型",
        "accuracy": 0.85,
        "error_distribution": {
            "E01": 0.3,
            "E07": 0.3,
            "E11": 0.4,
        },
    },
    "average": {
        "name": "中等生",
        "accuracy": 0.6,
        "error_distribution": {
            "E02": 0.2,
            "E03": 0.25,
            "E05": 0.2,
            "E06": 0.15,
            "E07": 0.2,
        },
    },
    "struggling": {
        "name": "薄弱生",
        "accuracy": 0.35,
        "error_distribution": {
            "E01": 0.15,
            "E02": 0.2,
            "E03": 0.25,
            "E04": 0.15,
            "E05": 0.15,
            "E06": 0.1,
        },
    },
    "partial": {
        "name": "偏科型",
        "accuracy": 0.55,
        "error_distribution": {
            "E09": 0.5,
            "E10": 0.3,
            "E06": 0.2,
        },
    },
}

_WRONG_TIMES_TABLE: dict[tuple[int, int], list[int]] = {
    (3, 4): [11, 13],
    (4, 6): [22, 26],
    (6, 7): [48, 42],
    (7, 8): [54, 58],
    (8, 8): [68, 56],
    (7, 9): [56, 72],
    (6, 8): [44, 52],
    (6, 9): [48, 63],
    (8, 9): [70, 76],
    (9, 9): [78, 84],
    (3, 7): [24, 18],
    (4, 7): [26, 32],
    (4, 8): [30, 36],
    (4, 9): [34, 38],
    (3, 8): [20, 28],
    (3, 9): [24, 30],
    (5, 7): [30, 40],
    (5, 8): [35, 45],
    (5, 9): [40, 50],
}

TRANSCRIPTION_CONFUSIONS: dict[str, list[str]] = {
    "3": ["8", "5"],
    "8": ["3", "5"],
    "6": ["9", "0"],
    "9": ["6", "0"],
    "0": ["6", "9", "8"],
    "5": ["3", "8"],
    "7": ["1", "9"],
    "1": ["7"],
    "2": ["7"],
    "4": ["9"],
}


def generate_wrong_answer(correct_answer: str, error_code: str, problem: str) -> str:
    generators = {
        "E01": _wrong_basic_fact,
        "E02": _wrong_carry,
        "E03": _wrong_borrow,
        "E04": _wrong_place_value,
        "E05": _wrong_operation_order,
        "E06": _wrong_decimal_fraction,
        "E07": _wrong_transcription,
        "E08": _wrong_missing_step,
        "E09": _wrong_conceptual,
        "E10": _wrong_wording_unit,
        "E11": _wrong_no_checking,
    }
    gen = generators.get(error_code)
    if gen is None:
        return _wrong_generic(correct_answer)
    result = gen(correct_answer, problem)
    return result if result is not None else _wrong_generic(correct_answer)


def _wrong_basic_fact(correct_answer: str, problem: str) -> str | None:
    nums = _extract_two_integers(problem)
    if nums:
        a, b = nums
        if 2 <= a <= 9 and 2 <= b <= 9:
            key = (min(a, b), max(a, b))
            if key in _WRONG_TIMES_TABLE:
                return str(random.choice(_WRONG_TIMES_TABLE[key]))
            correct = a * b
            return str(max(1, correct + random.choice([-2, -1, 1, 2, 3])))

    correct = _parse_answer_as_int(correct_answer)
    if correct is not None:
        return str(max(0, correct + random.choice([-2, -1, 1, 2])))
    return None


def _wrong_carry(correct_answer: str, problem: str) -> str | None:
    nums = _extract_two_integers(problem)
    if not nums:
        return None
    a, b = nums

    if "+" not in problem:
        if "*" in problem or "×" in problem:
            correct = a * b
            no_carry = _add_without_carry(a, b)
            if no_carry != correct and no_carry > 0:
                return str(no_carry)
        return None

    no_carry = _add_without_carry(a, b)
    if no_carry != a + b:
        return str(no_carry)
    return None


def _wrong_borrow(correct_answer: str, problem: str) -> str | None:
    nums = _extract_two_integers(problem)
    if not nums or "-" not in problem:
        return None
    a, b = nums
    if a < b:
        a, b = b, a

    no_borrow = _subtract_without_borrow(a, b)
    if no_borrow != a - b:
        return str(no_borrow)
    return None


def _wrong_place_value(correct_answer: str, problem: str) -> str | None:
    correct = _parse_answer_as_int(correct_answer)
    if correct is None:
        return None
    shifts = [correct * 10, correct + 9, correct - 9, correct + 90, correct - 90]
    random.shuffle(shifts)
    for s in shifts:
        if s != correct and s > 0:
            return str(s)
    return None


def _wrong_operation_order(correct_answer: str, problem: str) -> str | None:
    expr = _extract_expression(problem)
    if expr is None:
        return None
    has_add = "+" in expr or "-" in expr
    has_mul = "*" in expr or "×" in expr
    if not (has_add and has_mul):
        return None
    result = _eval_left_to_right(expr)
    if result is not None:
        return _fraction_to_str(result)
    return None


def _wrong_decimal_fraction(correct_answer: str, problem: str) -> str | None:
    if "/" in problem or "/" in correct_answer:
        return _wrong_fraction_answer(correct_answer, problem)
    if "." in problem or "." in correct_answer:
        return _wrong_decimal_answer(correct_answer)
    return None


def _wrong_fraction_answer(correct_answer: str, problem: str) -> str | None:
    frac = _parse_fraction(correct_answer)
    if frac is None:
        return None
    errors = [
        f"{frac.denominator}/{frac.numerator}",
        f"{frac.numerator + 1}/{frac.denominator}",
        f"{max(1, frac.numerator - 1)}/{frac.denominator}",
        f"{frac.numerator}/{frac.denominator + 1}",
        f"{frac.numerator}/{max(2, frac.denominator - 1)}",
        f"{frac.numerator * 2}/{frac.denominator * 2}",
    ]
    random.shuffle(errors)
    return errors[0]


def _wrong_decimal_answer(correct_answer: str) -> str | None:
    try:
        val = float(correct_answer)
        if val == 0:
            return None
        shifts = [val * 10, val / 10, val * 100, val / 100]
        random.shuffle(shifts)
        for s in shifts:
            if 0 < abs(s) < 1e6:
                return f"{s:g}"
    except ValueError:
        pass
    return None


def _wrong_transcription(correct_answer: str, problem: str) -> str | None:
    digits_in_problem = re.findall(r"\d+", problem)
    if not digits_in_problem:
        return None

    target_num = random.choice(digits_in_problem)
    if len(target_num) == 1:
        d = target_num
        if d in TRANSCRIPTION_CONFUSIONS:
            new_d = random.choice(TRANSCRIPTION_CONFUSIONS[d])
            new_problem = problem.replace(target_num, new_d, 1)
            new_result = _eval_problem(new_problem)
            if new_result is not None:
                return _fraction_to_str(new_result)
    else:
        pos = random.randint(0, len(target_num) - 1)
        d = target_num[pos]
        if d in TRANSCRIPTION_CONFUSIONS:
            new_d = random.choice(TRANSCRIPTION_CONFUSIONS[d])
            new_num = target_num[:pos] + new_d + target_num[pos + 1:]
            new_problem = problem.replace(target_num, new_num, 1)
            new_result = _eval_problem(new_problem)
            if new_result is not None:
                return _fraction_to_str(new_result)

    ans_digits = list(correct_answer)
    digit_positions = [i for i, c in enumerate(ans_digits) if c.isdigit()]
    if digit_positions:
        pos = random.choice(digit_positions)
        d = ans_digits[pos]
        if d in TRANSCRIPTION_CONFUSIONS:
            ans_digits[pos] = random.choice(TRANSCRIPTION_CONFUSIONS[d])
            return "".join(ans_digits)
    return None


def _wrong_missing_step(correct_answer: str, problem: str) -> str | None:
    nums = _extract_two_integers(problem)
    if not nums:
        return None
    a, b = nums

    if "*" in problem or "×" in problem:
        if b >= 10:
            partials = [a * (b % 10), a * (b // 10)]
            correct = a * b
            random.shuffle(partials)
            for p in partials:
                if p != correct:
                    return str(p)
        elif a >= 10:
            partials = [(a % 10) * b, (a // 10) * b]
            correct = a * b
            random.shuffle(partials)
            for p in partials:
                if p != correct:
                    return str(p)

    if "+" in problem and ("*" in problem or "×" in problem):
        expr = _extract_expression(problem)
        if expr:
            parts = re.split(r"[+-]", expr)
            for part in parts:
                if "*" in part or "×" in part:
                    mul_result = _eval_problem(part.strip())
                    if mul_result is not None:
                        return _fraction_to_str(mul_result)
    return None


def _wrong_conceptual(correct_answer: str, problem: str) -> str | None:
    if "/" in problem or "/" in correct_answer:
        frac = _parse_fraction(correct_answer)
        if frac is not None and frac.denominator > 1:
            return f"{frac.numerator}/{frac.denominator + frac.numerator}"

    correct = _parse_answer_as_int(correct_answer)
    if correct is not None:
        nums = _extract_two_integers(problem)
        if nums and len(nums) == 2:
            a, b = nums
            if "+" in problem:
                return str(abs(a - b))
            if "-" in problem:
                return str(a + b)
    return None


def _wrong_wording_unit(correct_answer: str, problem: str) -> str | None:
    correct = _parse_answer_as_int(correct_answer)
    if correct is not None and correct > 0:
        if correct % 2 == 0:
            return str(correct // 2)
        if correct % 3 == 0:
            return str(correct // 3)
        return str(correct * 2)

    frac = _parse_fraction(correct_answer)
    if frac is not None:
        return f"{frac.numerator}/{frac.denominator * 2}"
    return None


def _wrong_no_checking(correct_answer: str, problem: str) -> str | None:
    correct = _parse_answer_as_int(correct_answer)
    if correct is not None:
        large_offsets = [
            correct * 2,
            correct * 3,
            max(1, correct // 2),
            correct + random.randint(10, 50),
            max(1, correct - random.randint(10, 50)),
        ]
        random.shuffle(large_offsets)
        for val in large_offsets:
            if val > 0 and val != correct:
                return str(val)

    frac = _parse_fraction(correct_answer)
    if frac is not None:
        return f"{frac.numerator + frac.denominator}/{frac.denominator}"
    return None


def _wrong_generic(correct_answer: str) -> str:
    correct = _parse_answer_as_int(correct_answer)
    if correct is not None:
        offset = random.choice([-10, -5, -3, -2, -1, 1, 2, 3, 5, 10])
        return str(max(0, correct + offset))
    frac = _parse_fraction(correct_answer)
    if frac is not None:
        return f"{frac.numerator + 1}/{frac.denominator}"
    return correct_answer + "0"


def _add_without_carry(a: int, b: int) -> int:
    place = 1
    result = 0
    while a or b:
        result += ((a % 10 + b % 10) % 10) * place
        a //= 10
        b //= 10
        place *= 10
    return result


def _subtract_without_borrow(a: int, b: int) -> int:
    place = 1
    result = 0
    while a or b:
        result += abs((a % 10) - (b % 10)) * place
        a //= 10
        b //= 10
        place *= 10
    return result


# ---------------------------------------------------------------------------
# 模拟函数
# ---------------------------------------------------------------------------
def simulate_student_answers(
    student_id: str,
    problems: list[dict[str, Any]],
    archetype: str | None = None,
    accuracy_override: float | None = None,
) -> list[dict[str, Any]]:
    if archetype is None:
        archetype = random.choice(list(STUDENT_ARCHETYPES.keys()))
    arch = STUDENT_ARCHETYPES.get(archetype, STUDENT_ARCHETYPES["average"])
    accuracy = accuracy_override if accuracy_override is not None else arch["accuracy"]
    dist = arch["error_distribution"]

    error_codes = list(dist.keys())
    weights = list(dist.values())

    answers: list[dict[str, Any]] = []
    for p in problems:
        seq = p.get("sequence", p.get("problem_sequence", 0))
        problem_text = p.get("problem_plain", p.get("problem", ""))
        correct_answer = str(p.get("correct_answer", ""))

        if random.random() < accuracy:
            student_answer = correct_answer
            simulated_error_code = None
        else:
            chosen_error = random.choices(error_codes, weights=weights, k=1)[0]
            student_answer = generate_wrong_answer(correct_answer, chosen_error, problem_text)
            simulated_error_code = chosen_error

        answers.append({
            "problem_sequence": seq,
            "student_answer": student_answer,
            "simulated_error_code": simulated_error_code,
        })
    return answers


async def simulate_class_answers(
    homework_id: str,
    class_id: str = "G6A1",
    *,
    seed: int | None = None,
) -> dict[str, Any]:
    if seed is not None:
        random.seed(seed)

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM homework_problems WHERE homework_id = ? ORDER BY sequence",
            (homework_id,),
        )
        problem_rows = await cursor.fetchall()
        problems = [dict(r) for r in problem_rows]

        cursor = await db.execute(
            "SELECT * FROM students WHERE class_id = ?",
            (class_id,),
        )
        student_rows = await cursor.fetchall()

    if not problems or not student_rows:
        return {
            "student_answers": {},
            "summary": {
                "total_students": 0,
                "avg_accuracy": 0.0,
                "error_distribution": {},
                "error": "没有找到题目或学生",
            },
        }

    student_answers: dict[str, list[dict[str, Any]]] = {}
    total_correct = 0
    total_problems = 0
    error_counter: dict[str, int] = {}

    for s_row in student_rows:
        sid = s_row["id"]
        archetype = await _determine_archetype(sid)

        answers = simulate_student_answers(
            student_id=sid,
            problems=problems,
            archetype=archetype,
        )
        student_answers[sid] = answers
        total_problems += len(answers)

        for a in answers:
            if a["simulated_error_code"] is None:
                total_correct += 1
            else:
                code = a["simulated_error_code"]
                error_counter[code] = error_counter.get(code, 0) + 1

    avg_accuracy = total_correct / total_problems if total_problems > 0 else 0.0

    return {
        "student_answers": student_answers,
        "summary": {
            "total_students": len(student_rows),
            "total_problems_per_student": len(problems),
            "avg_accuracy": round(avg_accuracy, 4),
            "error_distribution": error_counter,
        },
    }


async def _determine_archetype(student_id: str) -> str:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT error_code, total_attempts, correct_count "
            "FROM student_error_stats WHERE student_id = ?",
            (student_id,),
        )
        rows = await cursor.fetchall()

    if not rows:
        return random.choice(list(STUDENT_ARCHETYPES.keys()))

    total = sum(r["total_attempts"] for r in rows)
    correct = sum(r["correct_count"] for r in rows)
    accuracy = correct / total if total > 0 else 0.5

    error_freq: dict[str, int] = {}
    for r in rows:
        errors = r["total_attempts"] - r["correct_count"]
        if errors > 0:
            error_freq[r["error_code"]] = errors

    if accuracy >= 0.75:
        return "high_achiever"
    if not error_freq:
        return "average"

    dominant = max(error_freq, key=error_freq.get)
    if dominant in ("E09", "E10"):
        return "partial"
    if accuracy < 0.45:
        return "struggling"
    return "average"


# ---------------------------------------------------------------------------
# 内部辅助函数
# ---------------------------------------------------------------------------
def _extract_two_integers(text: str) -> tuple[int, int] | None:
    nums = re.findall(r"\d+", _normalize_math_text(text))
    int_nums = [int(n) for n in nums if len(n) <= 6]
    if len(int_nums) >= 2:
        return int_nums[0], int_nums[1]
    return None


def _extract_expression(text: str) -> str | None:
    normalized = _normalize_math_text(text)
    before_equal = normalized.split("=")[0] if "=" in normalized else normalized
    match = re.search(r"[\d\s+\-*/().]+", before_equal)
    if match:
        expr = match.group(0).strip()
        if any(op in expr for op in ["+", "-", "*", "/"]):
            return expr
    return None


def _eval_problem(problem: str) -> Fraction | None:
    expr = _extract_expression(problem)
    if expr is None:
        return None
    return _eval_expression(expr)


def _eval_expression(expression: str) -> Fraction | None:
    try:
        node = ast.parse(expression, mode="eval")
    except SyntaxError:
        return None

    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def _eval(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return Fraction(str(n.value))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -_eval(n.operand)
        if isinstance(n, ast.BinOp):
            left = _eval(n.left)
            right = _eval(n.right)
            op_fn = ops.get(type(n.op))
            if op_fn:
                return op_fn(left, right)
        raise ValueError("不支持的表达式")

    try:
        return _eval(node.body)
    except (ValueError, ZeroDivisionError, KeyError):
        return None


def _eval_left_to_right(expression: str) -> Fraction | None:
    tokens = re.findall(r"\d+(?:\.\d+)?|[+\-*/]", expression)
    if not tokens:
        return None
    try:
        value = Fraction(tokens[0])
        ops_map = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
        }
        idx = 1
        while idx < len(tokens) - 1:
            fn = ops_map.get(tokens[idx])
            if fn is None:
                return None
            value = fn(value, Fraction(tokens[idx + 1]))
            idx += 2
        return value
    except (KeyError, ValueError, ZeroDivisionError):
        return None


def _parse_answer_as_int(answer: str) -> int | None:
    try:
        return int(float(answer))
    except (ValueError, TypeError):
        return None


def _parse_fraction(text: str) -> Fraction | None:
    match = re.search(r"(\d+)\s*/\s*(\d+)", str(text))
    if match:
        try:
            return Fraction(int(match.group(1)), int(match.group(2)))
        except (ValueError, ZeroDivisionError):
            return None
    return None


def _fraction_to_str(frac: Fraction) -> str:
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def _normalize_math_text(text: str) -> str:
    return (
        text.replace("×", "*")
        .replace("÷", "/")
        .replace(" x ", " * ")
        .replace(" X ", " * ")
        .replace("＝", "=")
        .replace("—", "-")
    )

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class GeneratedProblem:
    problem: str
    correct_answer: str
    error_code: str
    knowledge_point: str
    difficulty: str
    hint: str
    exercise_type: str = ""


# ---------------------------------------------------------------------------
# Constants — difficulty-aware denominator and integer ranges
# ---------------------------------------------------------------------------

# Per-difficulty nice denominator pools
_NICE_DENOMS_A = [2, 3, 4, 5, 6]
_NICE_DENOMS_B = [2, 3, 4, 5, 6, 8, 10, 12]
_NICE_DENOMS_C = [2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20]

# Per-difficulty max integer value
_MAX_INT_A = 6
_MAX_INT_B = 12
_MAX_INT_C = 20

# Decimals usable in fraction×decimal problems, stored as (display_str, Fraction)
_DECIMAL_POOL: list[tuple[str, Fraction]] = [
    ("0.5", Fraction(1, 2)),
    ("0.25", Fraction(1, 4)),
    ("0.75", Fraction(3, 4)),
    ("0.2", Fraction(1, 5)),
    ("0.4", Fraction(2, 5)),
    ("0.6", Fraction(3, 5)),
    ("0.8", Fraction(4, 5)),
    ("1.2", Fraction(6, 5)),
    ("1.5", Fraction(3, 2)),
    ("2.4", Fraction(12, 5)),
    ("2.5", Fraction(5, 2)),
    ("1.25", Fraction(5, 4)),
    ("3.6", Fraction(18, 5)),
    ("4.8", Fraction(24, 5)),
]

# Decimals appropriate for B difficulty (simpler, < 1)
_DECIMAL_POOL_B: list[tuple[str, Fraction]] = [
    ("0.5", Fraction(1, 2)),
    ("0.25", Fraction(1, 4)),
    ("0.75", Fraction(3, 4)),
    ("0.2", Fraction(1, 5)),
    ("0.4", Fraction(2, 5)),
    ("0.6", Fraction(3, 5)),
    ("0.8", Fraction(4, 5)),
]

# Pre-verified conversion table: (display, Fraction, decimal_str, percentage_str)
_CONV_TABLE: list[tuple[str, Fraction, str, str]] = [
    ("1/2", Fraction(1, 2), "0.5", "50%"),
    ("1/4", Fraction(1, 4), "0.25", "25%"),
    ("3/4", Fraction(3, 4), "0.75", "75%"),
    ("1/5", Fraction(1, 5), "0.2", "20%"),
    ("2/5", Fraction(2, 5), "0.4", "40%"),
    ("3/5", Fraction(3, 5), "0.6", "60%"),
    ("4/5", Fraction(4, 5), "0.8", "80%"),
    ("1/8", Fraction(1, 8), "0.125", "12.5%"),
    ("3/8", Fraction(3, 8), "0.375", "37.5%"),
    ("5/8", Fraction(5, 8), "0.625", "62.5%"),
    ("7/8", Fraction(7, 8), "0.875", "87.5%"),
    ("1/10", Fraction(1, 10), "0.1", "10%"),
    ("3/10", Fraction(3, 10), "0.3", "30%"),
    ("7/10", Fraction(7, 10), "0.7", "70%"),
    ("9/10", Fraction(9, 10), "0.9", "90%"),
    ("1/20", Fraction(1, 20), "0.05", "5%"),
    ("3/20", Fraction(3, 20), "0.15", "15%"),
    ("7/20", Fraction(7, 20), "0.35", "35%"),
    ("9/20", Fraction(9, 20), "0.45", "45%"),
    ("11/20", Fraction(11, 20), "0.55", "55%"),
    ("1/25", Fraction(1, 25), "0.04", "4%"),
    ("1/50", Fraction(1, 50), "0.02", "2%"),
]

# Pre-computed (n, m, pct%) triples where n/m = pct/100 exactly
_PCT_TRIPLES: list[tuple[int, int, int]] = []
for _pct in range(5, 100, 5):
    for _m in [20, 40, 50, 60, 80, 100, 200]:
        if (_m * _pct) % 100 == 0:
            _n = _m * _pct // 100
            if _n > 0:
                _PCT_TRIPLES.append((_n, _m, _pct))

_DISCOUNTS: list[tuple[int, str]] = [
    (50, "五折"), (60, "六折"), (70, "七折"), (75, "七五折"),
    (80, "八折"), (85, "八五折"), (90, "九折"), (95, "九五折"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _frac_str(f: Fraction) -> str:
    """Format Fraction as 'n' for whole numbers or 'a/b' otherwise."""
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def _mixed_str(f: Fraction) -> str:
    """Format Fraction as Chinese mixed number 'a又b/c', or plain str otherwise."""
    if f.denominator == 1:
        return str(f.numerator)
    if f.numerator > f.denominator:
        whole = f.numerator // f.denominator
        rem = f.numerator % f.denominator
        if rem == 0:
            return str(whole)
        return f"{whole}又{rem}/{f.denominator}"
    return f"{f.numerator}/{f.denominator}"


def _nice_denoms_for(difficulty: str) -> list[int]:
    """Return nice denominator pool for the given difficulty level."""
    if difficulty == "A":
        return _NICE_DENOMS_A
    if difficulty == "C":
        return _NICE_DENOMS_C
    return _NICE_DENOMS_B


def _max_int_for(difficulty: str) -> int:
    """Return max integer value for the given difficulty level."""
    if difficulty == "A":
        return _MAX_INT_A
    if difficulty == "C":
        return _MAX_INT_C
    return _MAX_INT_B


def _rand_frac(rng: random.Random, max_denom: int = 12) -> Fraction:
    """Random proper fraction (0 < f < 1) with a nice denominator."""
    pool = [d for d in _NICE_DENOMS_B if d <= max_denom]
    denom = rng.choice(pool)
    numer = rng.randint(1, denom - 1)
    return Fraction(numer, denom)


def _rand_frac_for(rng: random.Random, difficulty: str) -> Fraction:
    """Random proper fraction with denominator pool matching difficulty."""
    denoms = _nice_denoms_for(difficulty)
    denom = rng.choice(denoms)
    numer = rng.randint(1, denom - 1)
    return Fraction(numer, denom)


def _rand_int(rng: random.Random, lo: int = 2, hi: int = 12) -> int:
    return rng.randint(lo, hi)


def _rand_int_for(rng: random.Random, difficulty: str, lo: int = 2) -> int:
    """Random integer with upper bound matching difficulty."""
    return rng.randint(lo, _max_int_for(difficulty))


def _rand_mixed(rng: random.Random, difficulty: str) -> Fraction:
    """Random mixed number (> 1) as an improper Fraction."""
    max_int = _max_int_for(difficulty)
    whole = rng.randint(1, min(max_int, 5))  # whole part 1-5
    frac = _rand_frac_for(rng, difficulty)
    return Fraction(whole) + frac


def _lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // math.gcd(a, b)


def _simplify_int_ratio(a: int, b: int) -> tuple[int, int]:
    """Reduce integer ratio a:b to lowest terms."""
    g = math.gcd(abs(a), abs(b))
    return (a // g, b // g)


def _simplify_frac_ratio(f1: Fraction, f2: Fraction) -> tuple[int, int]:
    """Reduce ratio of two fractions to simplest integer ratio."""
    common = _lcm(f1.denominator, f2.denominator)
    a = int(f1 * common)
    b = int(f2 * common)
    return _simplify_int_ratio(a, b)


def _decimal_str(f: Fraction) -> str:
    """Convert a Fraction to decimal display string (exact finite decimals only)."""
    # Multiply by power of 10 to get integer
    d = f.denominator
    if d == 1:
        return str(f.numerator)
    # Find power of 10 that makes it an integer
    for _ in range(10):
        if d % 2 == 0:
            d //= 2
        elif d % 5 == 0:
            d //= 5
        else:
            break
    if d != 1:
        # Not a finite decimal — fall back to fraction string
        return _frac_str(f)
    # Compute decimal representation
    val = f.numerator * 10**8 // f.denominator
    val_str = f"{val / 10**8:.8f}".rstrip("0").rstrip(".")
    return val_str



# ---------------------------------------------------------------------------
# Diagnosis-aligned carry/borrow helpers
# ---------------------------------------------------------------------------

def _int_needs_carry(a: int, b: int) -> bool:
    """True if adding a+b requires at least one carry."""
    while a or b:
        if a % 10 + b % 10 >= 10:
            return True
        a //= 10
        b //= 10
    return False


def _int_count_carries(a: int, b: int) -> int:
    """Count digit positions requiring carry in a+b."""
    n = 0
    while a or b:
        if a % 10 + b % 10 >= 10:
            n += 1
        a //= 10
        b //= 10
    return n


def _int_needs_borrow(a: int, b: int) -> bool:
    """True if subtracting a-b requires at least one borrow (a >= b assumed)."""
    while a or b:
        if a % 10 < b % 10:
            return True
        a //= 10
        b //= 10
    return False


def _int_count_borrows(a: int, b: int) -> int:
    """Count digit positions requiring borrow in a-b."""
    n = 0
    while a or b:
        if a % 10 < b % 10:
            n += 1
        a //= 10
        b //= 10
    return n


# ---------------------------------------------------------------------------
# E01: 基础事实错误 (Basic Fact Error)
# ---------------------------------------------------------------------------

def _gen_basic_fact(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """基础事实错误 — simple arithmetic facts, 2 operands."""
    op = rng.choice(["+", "-", "×", "÷"])

    if difficulty == "A":
        if op == "+":
            a, b = rng.randint(1, 10), rng.randint(1, 10)
        elif op == "-":
            a = rng.randint(2, 18)
            b = rng.randint(1, a)
        elif op == "×":
            a, b = rng.randint(2, 9), rng.randint(2, 9)
        else:
            b = rng.randint(2, 9)
            q = rng.randint(1, 9)
            a = b * q
    elif difficulty == "B":
        if op == "+":
            a, b = rng.randint(10, 25), rng.randint(10, 25)
        elif op == "-":
            a = rng.randint(20, 50)
            b = rng.randint(10, a)
        elif op == "×":
            a = rng.randint(3, 12)
            b = rng.randint(3, 9)
        else:
            b = rng.randint(2, 12)
            q = rng.randint(3, 12)
            a = b * q
    else:
        if op == "+":
            a, b = rng.randint(25, 50), rng.randint(25, 50)
        elif op == "-":
            a = rng.randint(40, 100)
            b = rng.randint(10, a - 1)
        elif op == "×":
            a = rng.randint(5, 20)
            b = rng.randint(3, 12)
        else:
            b = rng.randint(2, 12)
            q = rng.randint(5, 20)
            a = b * q

    if op == "+":
        result = a + b
    elif op == "-":
        result = a - b
    elif op == "×":
        result = a * b
    else:
        result = a // b

    return GeneratedProblem(
        problem=f"{a}{op}{b}=",
        correct_answer=str(result),
        error_code="E01",
        knowledge_point="基础口算与运算事实",
        difficulty=difficulty,
        hint="仔细回忆口诀或运算规则，一步一步算",
    )


# ---------------------------------------------------------------------------
# E02: 进位错误 (Carry Error)
# ---------------------------------------------------------------------------

def _gen_carry(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """进位错误 — multi-digit addition requiring carry."""
    target = {"A": 1, "B": 2, "C": 3}[difficulty]

    for _ in range(200):
        if difficulty == "A":
            a = rng.randint(11, 49)
            b = rng.randint(11, 49)
        elif difficulty == "B":
            a = rng.randint(100, 499)
            b = rng.randint(100, 499)
        else:
            a = rng.randint(100, 999)
            b = rng.randint(100, 999)
        if _int_count_carries(a, b) >= target:
            break
    else:
        a, b = {"A": (28, 35), "B": (178, 256), "C": (567, 438)}[difficulty]

    result = a + b
    return GeneratedProblem(
        problem=f"{a}+{b}=",
        correct_answer=str(result),
        error_code="E02",
        knowledge_point="进位加法与乘法",
        difficulty=difficulty,
        hint="哪一位满十，就要向前一位进1",
    )


# ---------------------------------------------------------------------------
# E03: 退位错误 (Borrow Error)
# ---------------------------------------------------------------------------

def _gen_borrow(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """退位错误 — multi-digit subtraction requiring borrow."""
    target = {"A": 1, "B": 2, "C": 3}[difficulty]

    for _ in range(200):
        if difficulty == "A":
            a = rng.randint(21, 99)
            b = rng.randint(11, a - 1)
        elif difficulty == "B":
            a = rng.randint(200, 999)
            b = rng.randint(100, a - 1)
        else:
            a = rng.randint(1000, 9999)
            b = rng.randint(100, a - 1)
        if _int_count_borrows(a, b) >= target:
            break
    else:
        a, b = {"A": (52, 18), "B": (402, 178), "C": (1000, 467)}[difficulty]

    result = a - b
    return GeneratedProblem(
        problem=f"{a}-{b}=",
        correct_answer=str(result),
        error_code="E03",
        knowledge_point="退位减法",
        difficulty=difficulty,
        hint="看到本位不够减时，先向前一位借1，再继续算",
    )


# ---------------------------------------------------------------------------
# E04: 数位对齐错误 (Place Value Alignment Error)
# ---------------------------------------------------------------------------

def _gen_place_value(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """数位对齐错误 — different digit lengths make misalignment likely."""
    if difficulty == "A":
        if rng.choice([True, False]):
            a = rng.randint(10, 99)
            b = rng.randint(2, 9)
            result = a + b
            op = "+"
        else:
            a = rng.randint(100, 199)
            b = rng.randint(2, 9)
            result = a - b
            op = "-"
    elif difficulty == "B":
        if rng.choice([True, False]):
            a = rng.randint(100, 999)
            b = rng.randint(10, 99)
            result = a + b
            op = "+"
        else:
            a = rng.randint(1000, 9999)
            b = rng.randint(10, 99)
            result = a - b
            op = "-"
    else:
        if rng.choice([True, False]):
            a = rng.randint(1000, 9999)
            b = rng.randint(10, 99)
            result = a + b
            op = "+"
        else:
            a = rng.randint(10000, 99999)
            b = rng.randint(100, 999)
            result = a - b
            op = "-"

    return GeneratedProblem(
        problem=f"{a}{op}{b}=",
        correct_answer=str(result),
        error_code="E04",
        knowledge_point="多位数竖式对齐",
        difficulty=difficulty,
        hint="写竖式时先对齐个位，再检查每一列代表什么数位",
    )


# ---------------------------------------------------------------------------
# E05: 运算顺序错误 (Operation Order Error)
# ---------------------------------------------------------------------------

def _gen_operation_order(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """运算顺序错误 — mixed operations where left-to-right gives wrong answer."""
    if difficulty == "A":
        for _ in range(100):
            a = rng.randint(1, 10)
            b = rng.randint(2, 9)
            c = rng.randint(2, 9)
            correct = a + b * c
            wrong = (a + b) * c
            if correct != wrong:
                break
        return GeneratedProblem(
            problem=f"{a}+{b}×{c}=",
            correct_answer=str(correct),
            error_code="E05",
            knowledge_point="四则混合运算顺序",
            difficulty=difficulty,
            hint="先算乘除，再算加减",
        )

    if difficulty == "B":
        for _ in range(100):
            a = rng.randint(10, 30)
            b = rng.randint(2, 9)
            c = rng.randint(2, 9)
            d = rng.randint(1, 10)
            product = b * c
            if a > product:
                correct = a - product + d
                break
        return GeneratedProblem(
            problem=f"{a}-{b}×{c}+{d}=",
            correct_answer=str(correct),
            error_code="E05",
            knowledge_point="四则混合运算顺序",
            difficulty=difficulty,
            hint="先算乘除，再算加减，从左到右",
        )

    # C: with parentheses or multi-operation
    kind = rng.choice(["paren", "div_mul"])
    if kind == "paren":
        for _ in range(100):
            a = rng.randint(2, 20)
            b = rng.randint(2, 9)
            c = rng.randint(5, 15)
            d = rng.randint(1, c - 1)
            inner = c - d
            correct = a + b * inner
            wrong = a + b * c - d
            if correct != wrong and inner > 0:
                break
        return GeneratedProblem(
            problem=f"{a}+{b}×({c}-{d})=",
            correct_answer=str(correct),
            error_code="E05",
            knowledge_point="四则混合运算顺序（含括号）",
            difficulty=difficulty,
            hint="有括号先算括号里的，再算乘除，最后算加减",
        )
    for _ in range(100):
        b = rng.randint(2, 9)
        q = rng.randint(2, 9)
        a = b * q
        c = rng.randint(2, 9)
        d = rng.randint(2, 9)
        correct = q + c * d
        wrong = (q + c) * d
        if correct != wrong:
            break
    return GeneratedProblem(
        problem=f"{a}÷{b}+{c}×{d}=",
        correct_answer=str(correct),
        error_code="E05",
        knowledge_point="四则混合运算顺序（乘除并存）",
        difficulty=difficulty,
        hint="先算乘除，再算加减，同级从左到右",
    )


# ---------------------------------------------------------------------------
# E06: 小数点/分数单位错误 (Decimal/Fraction Unit Error)
# ---------------------------------------------------------------------------

def _gen_decimal_fraction(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """小数点/分数单位错误 — decimal arithmetic where point shifts are common."""
    if difficulty == "A":
        op = rng.choice(["+", "-", "×"])
        if op == "+":
            a_i, a_d = rng.randint(1, 9), rng.randint(1, 9)
            b_i, b_d = rng.randint(1, 9), rng.randint(1, 9)
            a_f = Fraction(a_i * 10 + a_d, 10)
            b_f = Fraction(b_i * 10 + b_d, 10)
            result = a_f + b_f
            return GeneratedProblem(
                problem=f"{a_i}.{a_d}+{b_i}.{b_d}=",
                correct_answer=_decimal_str(result),
                error_code="E06",
                knowledge_point="小数与分数运算",
                difficulty=difficulty,
                hint="小数点对齐，逐位相加",
            )
        if op == "-":
            a_i, a_d = rng.randint(2, 9), rng.randint(1, 9)
            b_i, b_d = rng.randint(1, max(1, a_i - 1)), rng.randint(0, 9)
            a_f = Fraction(a_i * 10 + a_d, 10)
            b_f = Fraction(b_i * 10 + b_d, 10)
            if a_f <= b_f:
                a_f, b_f = b_f, a_f
            result = a_f - b_f
            return GeneratedProblem(
                problem=f"{_decimal_str(a_f)}-{_decimal_str(b_f)}=",
                correct_answer=_decimal_str(result),
                error_code="E06",
                knowledge_point="小数与分数运算",
                difficulty=difficulty,
                hint="小数点对齐，逐位相减",
            )
        # ×
        a_d = rng.randint(1, 9)
        n = rng.randint(2, 9)
        a_f = Fraction(a_d, 10)
        result = a_f * n
        return GeneratedProblem(
            problem=f"0.{a_d}×{n}=",
            correct_answer=_decimal_str(result),
            error_code="E06",
            knowledge_point="小数与分数运算",
            difficulty=difficulty,
            hint="先按整数乘，再定小数位数",
        )

    if difficulty == "B":
        op = rng.choice(["×", "÷"])
        if op == "×":
            a_i = rng.randint(1, 5)
            a_d = rng.randint(1, 99)
            n = rng.randint(2, 9)
            a_f = Fraction(a_i * 100 + a_d, 100)
            result = a_f * n
            return GeneratedProblem(
                problem=f"{a_i}.{a_d:02d}×{n}=",
                correct_answer=_decimal_str(result),
                error_code="E06",
                knowledge_point="小数与分数运算",
                difficulty=difficulty,
                hint="先按整数乘，再数小数位数",
            )
        # ÷ (construct backwards for clean quotient)
        n = rng.randint(2, 9)
        q_i = rng.randint(1, 9)
        q_d = rng.randint(1, 9)
        q_f = Fraction(q_i * 10 + q_d, 10)
        a_f = q_f * n
        return GeneratedProblem(
            problem=f"{_decimal_str(a_f)}÷{n}=",
            correct_answer=_decimal_str(q_f),
            error_code="E06",
            knowledge_point="小数与分数运算",
            difficulty=difficulty,
            hint="先按整数除，再定小数位数",
        )

    # C
    op = rng.choice(["×", "÷"])
    if op == "×":
        a_d = rng.randint(1, 999)
        n = rng.randint(2, 9)
        a_f = Fraction(a_d, 1000)
        result = a_f * n
        return GeneratedProblem(
            problem=f"0.{a_d:03d}×{n}=",
            correct_answer=_decimal_str(result),
            error_code="E06",
            knowledge_point="小数与分数运算",
            difficulty=difficulty,
            hint="先按整数乘，再数小数位数",
        )
    # ÷ by a small decimal (construct backwards)
    d_i = rng.randint(1, 9)
    d_d = rng.randint(1, 9)
    d_f = Fraction(d_i * 10 + d_d, 10)
    q = rng.randint(2, 9)
    a_f = d_f * q
    return GeneratedProblem(
        problem=f"{_decimal_str(a_f)}÷{_decimal_str(d_f)}=",
        correct_answer=str(q),
        error_code="E06",
        knowledge_point="小数与分数运算",
        difficulty=difficulty,
        hint="先确定小数位数，再按整数除法算",
    )


# ---------------------------------------------------------------------------
# E07: 抄题/转写错误 (Transcription Error)
# ---------------------------------------------------------------------------

def _gen_transcription(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """抄题/转写错误 — problems with easily confusable digits (6/9, 1/7, 3/8)."""
    _CONFUSABLE = {1, 3, 6, 7, 8, 9}

    def _has_confusable(n: int) -> bool:
        return any(int(d) in _CONFUSABLE for d in str(abs(n)))

    for _ in range(200):
        if difficulty == "A":
            a = rng.randint(10, 69)
            b = rng.randint(10, 39)
        elif difficulty == "B":
            a = rng.randint(100, 699)
            b = rng.randint(100, 399)
        else:
            a = rng.randint(100, 999)
            b = rng.randint(100, 999)
        if _has_confusable(a) and _has_confusable(b):
            break

    if rng.choice([True, False]):
        result = a + b
        op = "+"
    else:
        if a < b:
            a, b = b, a
        result = a - b
        op = "-"

    return GeneratedProblem(
        problem=f"{a}{op}{b}=",
        correct_answer=str(result),
        error_code="E07",
        knowledge_point="抄题与数字转写",
        difficulty=difficulty,
        hint="先对照题目检查数字和符号有没有抄错",
    )


# ---------------------------------------------------------------------------
# E08: 步骤遗漏 (Missing Step Error)
# ---------------------------------------------------------------------------

def _gen_missing_step(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """步骤遗漏 — multi-digit multiplication with partial products."""
    if difficulty == "A":
        a = rng.randint(11, 29)
        b = rng.randint(3, 9)
    elif difficulty == "B":
        a = rng.randint(11, 49)
        b = rng.randint(11, 29)
    else:
        a = rng.randint(100, 299)
        b = rng.randint(11, 49)

    result = a * b
    return GeneratedProblem(
        problem=f"{a}×{b}=",
        correct_answer=str(result),
        error_code="E08",
        knowledge_point="多位数乘法步骤",
        difficulty=difficulty,
        hint="列竖式，每一位都要乘到，部分积要对齐数位",
    )


# ---------------------------------------------------------------------------
# E09: 算理理解不足 (Conceptual Understanding Error)
# ---------------------------------------------------------------------------

def _gen_conceptual(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """算理理解不足 — problems testing conceptual understanding."""
    if difficulty == "A":
        # a×a= (a² vs 2a confusion) or special properties (×0, ÷1)
        kind = rng.choice(["square", "zero", "identity"])
        if kind == "square":
            a = rng.randint(3, 9)
            result = a * a
            return GeneratedProblem(
                problem=f"{a}×{a}=",
                correct_answer=str(result),
                error_code="E09",
                knowledge_point="算理与概念理解",
                difficulty=difficulty,
                hint="这是同一个数乘自己，不是乘以2",
            )
        if kind == "zero":
            a = rng.randint(2, 15)
            return GeneratedProblem(
                problem=f"0×{a}=",
                correct_answer="0",
                error_code="E09",
                knowledge_point="算理与概念理解",
                difficulty=difficulty,
                hint="任何数乘以0都等于0",
            )
        a = rng.randint(2, 15)
        return GeneratedProblem(
            problem=f"{a}÷1=",
            correct_answer=str(a),
            error_code="E09",
            knowledge_point="算理与概念理解",
            difficulty=difficulty,
            hint="任何数除以1都等于它自己",
        )

    if difficulty == "B":
        # a×b= (area vs perimeter confusion) or √n
        kind = rng.choice(["area_perimeter", "square", "sqrt"])
        if kind == "area_perimeter":
            for _ in range(100):
                a = rng.randint(3, 12)
                b = rng.randint(3, 12)
                if a != b and a * b != 2 * (a + b):
                    break
            result = a * b
            return GeneratedProblem(
                problem=f"{a}×{b}=",
                correct_answer=str(result),
                error_code="E09",
                knowledge_point="算理与概念理解",
                difficulty=difficulty,
                hint="这是在算乘积，不是算周长2×(长+宽)",
            )
        if kind == "sqrt":
            # √n = ?  (perfect squares 4..144)
            base = rng.randint(2, 12)
            n = base * base
            return GeneratedProblem(
                problem=f"√{n}=",
                correct_answer=str(base),
                error_code="E09",
                knowledge_point="算理与概念理解",
                difficulty=difficulty,
                hint='√n 是"哪个数乘自己等于n"，想一想几×几等于这个数',
            )
        a = rng.randint(4, 12)
        result = a * a
        return GeneratedProblem(
            problem=f"{a}×{a}=",
            correct_answer=str(result),
            error_code="E09",
            knowledge_point="算理与概念理解",
            difficulty=difficulty,
            hint="a×a=a²，不是a×2",
        )

    # C: (a+b)² vs a²+b², power/exponent, or √(a²+b²)
    kind = rng.choice(["double_square", "triple", "mixed", "sqrt"])
    if kind == "double_square":
        for _ in range(100):
            a = rng.randint(2, 9)
            b = rng.randint(2, 9)
            if a != b:
                break
        s1 = a * a
        s2 = b * b
        result = s1 + s2
        return GeneratedProblem(
            problem=f"{a}²+{b}²=",
            correct_answer=str(result),
            error_code="E09",
            knowledge_point="算理与概念理解",
            difficulty=difficulty,
            hint="先分别算出每个数的平方，再相加",
        )
    if kind == "triple":
        a = rng.randint(2, 6)
        result = a * a * a
        return GeneratedProblem(
            problem=f"{a}³=",
            correct_answer=str(result),
            error_code="E09",
            knowledge_point="算理与概念理解",
            difficulty=difficulty,
            hint="a³=a×a×a，三个a相乘",
        )
    if kind == "sqrt":
        # √(a²+b²) = ?  — Pythagorean conceptual understanding
        a = rng.randint(3, 8)
        b = rng.choice([x for x in range(3, 9) if x != a])
        s = a * a + b * b
        root = int(math.isqrt(s))
        if root * root == s:
            return GeneratedProblem(
                problem=f"√({a}²+{b}²)=",
                correct_answer=str(root),
                error_code="E09",
                knowledge_point="算理与概念理解",
                difficulty=difficulty,
                hint="先算a²+b²的和，再想哪个整数的平方等于这个和",
            )
        # not a perfect square — show as simplified radical
        return GeneratedProblem(
            problem=f"{a}²+{b}²=",
            correct_answer=str(s),
            error_code="E09",
            knowledge_point="算理与概念理解",
            difficulty=difficulty,
            hint="先分别算平方，再加起来",
        )
    a = rng.randint(3, 9)
    b = rng.randint(3, 9)
    result = a * b
    return GeneratedProblem(
        problem=f"{a}×{b}=",
        correct_answer=str(result),
        error_code="E09",
        knowledge_point="算理与概念理解",
        difficulty=difficulty,
        hint="这是乘法运算，注意和加法、周长公式区分",
    )


# ---------------------------------------------------------------------------
# E10: 审题与单位理解错误 (Wording / Unit Error)
# ---------------------------------------------------------------------------

def _gen_wording_unit(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """审题与单位理解错误 — problems where operator confusion or misreading is likely."""
    kind = rng.choice(["operator_confuse", "unit_convert"])

    if kind == "operator_confuse":
        # Arithmetic problems where ×/+/- confusion is plausible
        if difficulty == "A":
            # a+b= where student might compute a×b
            a = rng.randint(3, 9)
            b = rng.randint(3, 9)
            result = a + b
            return GeneratedProblem(
                problem=f"{a}+{b}=",
                correct_answer=str(result),
                error_code="E10",
                knowledge_point="单位换算与审题",
                difficulty=difficulty,
                hint="看清运算符号是加还是乘，再决定算法",
            )
        if difficulty == "B":
            # a×b= where student might compute a+b
            a = rng.randint(3, 12)
            b = rng.randint(3, 9)
            result = a * b
            return GeneratedProblem(
                problem=f"{a}×{b}=",
                correct_answer=str(result),
                error_code="E10",
                knowledge_point="单位换算与审题",
                difficulty=difficulty,
                hint="看清运算符号是乘还是加，再决定算法",
            )
        # a-b= where student might compute a+b
        a = rng.randint(20, 60)
        b = rng.randint(10, a - 1)
        result = a - b
        return GeneratedProblem(
            problem=f"{a}-{b}=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="单位换算与审题",
            difficulty=difficulty,
            hint="看清运算符号是减还是加，再决定算法",
        )

    # unit_convert: unit conversion problems
    _CONVERSIONS = [
        ("米", "厘米", 100),
        ("千克", "克", 1000),
        ("千米", "米", 1000),
        ("分米", "厘米", 10),
    ]
    if difficulty == "A":
        unit_from, unit_to, factor = rng.choice(_CONVERSIONS[:2])
        val = rng.randint(2, 9)
        result = val * factor
        return GeneratedProblem(
            problem=f"{val}{unit_from}=（　）{unit_to}",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="单位换算与审题",
            difficulty=difficulty,
            hint=f"1{unit_from}={factor}{unit_to}",
        )
    if difficulty == "B":
        unit_from, unit_to, factor = rng.choice(_CONVERSIONS)
        val_int = rng.randint(2, 9)
        val_dec = rng.randint(1, 9)
        val_f = Fraction(val_int * 10 + val_dec, 10)
        result_f = val_f * factor
        return GeneratedProblem(
            problem=f"{val_int}.{val_dec}{unit_from}=（　）{unit_to}",
            correct_answer=_decimal_str(result_f),
            error_code="E10",
            knowledge_point="单位换算与审题",
            difficulty=difficulty,
            hint=f"1{unit_from}={factor}{unit_to}，小数也要参与换算",
        )
    # C: word problem with unit conversion
    templates = [
        _gen_unit_word_problem_c(rng),
    ]
    return templates[0]


def _gen_unit_word_problem_c(rng: random.Random) -> GeneratedProblem:
    """Generate a C-level word problem involving unit conversion."""
    kind = rng.choice(["perimeter_km_m", "area_m2_dm2", "sum_km_m"])
    if kind == "perimeter_km_m":
        # 操场长0.x千米，宽y米，周长是多少米？— 需要km→m换算
        km_val = rng.randint(1, 9)  # 0.1~0.9 km
        width_m = rng.choice([50, 60, 80, 100])
        length_m = km_val * 1000
        perimeter = 2 * (length_m + width_m)
        return GeneratedProblem(
            problem=f"长方形操场长0.{km_val}千米，宽{width_m}米，周长是多少米？",
            correct_answer=str(perimeter),
            error_code="E10",
            knowledge_point="单位换算与审题",
            difficulty="C",
            hint=f"先把0.{km_val}千米换算成米，再用周长公式",
        )
    if kind == "area_m2_dm2":
        # 花坛面积x平方分米，长y分米，宽多少分米？答案换算成平方米
        length_dm = rng.choice([20, 30, 40, 50])
        width_dm = rng.choice([10, 15, 20])
        area_dm2 = length_dm * width_dm
        area_m2 = Fraction(area_dm2, 100)
        return GeneratedProblem(
            problem=f"长方形花坛面积是{area_dm2}平方分米，已知长{length_dm}分米，宽是多少分米？再把面积换算成多少平方米？",
            correct_answer=_decimal_str(area_m2),
            error_code="E10",
            knowledge_point="单位换算与审题",
            difficulty="C",
            hint="先算宽=面积÷长，再换算：100平方分米=1平方米",
        )
    # sum_km_m: 两条路，一条x千米一条y米，共多少米？
    km_val = rng.randint(1, 5)
    m_val = rng.choice([200, 300, 400, 500, 800])
    total_m = km_val * 1000 + m_val
    return GeneratedProblem(
        problem=f"小明家到学校有{km_val}千米，学校到图书馆有{m_val}米，小明家到图书馆一共多少米？（经过学校）",
        correct_answer=str(total_m),
        error_code="E10",
        knowledge_point="单位换算与审题",
        difficulty="C",
        hint=f"先把{km_val}千米换算成米，再加起来",
    )


# ---------------------------------------------------------------------------
# E11: 习惯性未验算 (No Checking Error)
# ---------------------------------------------------------------------------

def _gen_no_checking(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """习惯性未验算 — problems where estimation reveals obviously wrong answers."""
    if difficulty == "A":
        # Multiplication facts with common wrong answers
        kind = rng.choice(["mul_fact", "add_fact"])
        if kind == "mul_fact":
            a = rng.choice([6, 7, 8, 9])
            b = rng.choice([6, 7, 8, 9])
            result = a * b
        else:
            a = rng.randint(20, 50)
            b = rng.randint(20, 50)
            result = a + b
        return GeneratedProblem(
            problem=f"{a}×{b}=" if kind == "mul_fact" else f"{a}+{b}=",
            correct_answer=str(result),
            error_code="E11",
            knowledge_point="估算与验算习惯",
            difficulty=difficulty,
            hint="算完后想一想：这个答案合理吗？",
        )

    if difficulty == "B":
        kind = rng.choice(["near_round", "large_mul", "add_check"])
        if kind == "near_round":
            a = rng.choice([25, 50, 75, 99])
            b = rng.choice([4, 6, 8, 11])
            result = a * b
            return GeneratedProblem(
                problem=f"{a}×{b}=",
                correct_answer=str(result),
                error_code="E11",
                knowledge_point="估算与验算习惯",
                difficulty=difficulty,
                hint=f"可以先估算：{a}×{b}大约是多少？",
            )
        if kind == "large_mul":
            a = rng.randint(11, 49)
            b = rng.randint(11, 49)
            result = a * b
            return GeneratedProblem(
                problem=f"{a}×{b}=",
                correct_answer=str(result),
                error_code="E11",
                knowledge_point="估算与验算习惯",
                difficulty=difficulty,
                hint="先估算大约多少，精确计算后再对照检查",
            )
        a = rng.randint(100, 500)
        b = rng.randint(100, 500)
        result = a + b
        return GeneratedProblem(
            problem=f"{a}+{b}=",
            correct_answer=str(result),
            error_code="E11",
            knowledge_point="估算与验算习惯",
            difficulty=difficulty,
            hint="算完后用减法验算：和-一个加数=另一个加数",
        )

    # C
    kind = rng.choice(["big_mul", "big_add", "near_hundred"])
    if kind == "big_mul":
        a = rng.randint(25, 99)
        b = rng.randint(11, 49)
        result = a * b
        return GeneratedProblem(
            problem=f"{a}×{b}=",
            correct_answer=str(result),
            error_code="E11",
            knowledge_point="估算与验算习惯",
            difficulty=difficulty,
            hint="先估算：把两个数各看成接近的整十数相乘，再精确计算",
        )
    if kind == "big_add":
        a = rng.randint(1000, 9999)
        b = rng.randint(1000, 9999)
        result = a + b
        return GeneratedProblem(
            problem=f"{a}+{b}=",
            correct_answer=str(result),
            error_code="E11",
            knowledge_point="估算与验算习惯",
            difficulty=difficulty,
            hint="估算一下和大概是几千，精确算后再对照",
        )
    a = rng.choice([99, 98, 199, 299])
    b = rng.choice([37, 48, 56, 73])
    result = a * b
    return GeneratedProblem(
        problem=f"{a}×{b}=",
        correct_answer=str(result),
        error_code="E11",
        knowledge_point="估算与验算习惯",
        difficulty=difficulty,
        hint=f"把{a}看成接近的整百数估算，精确计算后检查是否合理",
    )


# ---------------------------------------------------------------------------
# Default / Fallback (E99)
# ---------------------------------------------------------------------------

def _generate_default(difficulty: str, rng: random.Random) -> GeneratedProblem:
    f1 = _rand_frac_for(rng, difficulty)
    f2 = _rand_frac_for(rng, difficulty)
    op = rng.choice(["+", "-", "×", "÷"])
    if op == "+":
        result = f1 + f2
    elif op == "-":
        a, b = max(f1, f2), min(f1, f2)
        f1, f2 = a, b
        result = a - b
    elif op == "×":
        result = f1 * f2
    else:
        result = f1 / f2
    return GeneratedProblem(
        problem=f"{_frac_str(f1)}{op}{_frac_str(f2)}=",
        correct_answer=_frac_str(result),
        error_code="E99",
        knowledge_point="分数基础运算",
        difficulty=difficulty,
        hint="仔细审题，一步一步计算",
    )


# ---------------------------------------------------------------------------
# Generator registry — aligned with diagnosis.py E-code definitions
# ---------------------------------------------------------------------------

_GENERATORS: dict[str, type] = {
    "E01": _gen_basic_fact,
    "E02": _gen_carry,
    "E03": _gen_borrow,
    "E04": _gen_place_value,
    "E05": _gen_operation_order,
    "E06": _gen_decimal_fraction,
    "E07": _gen_transcription,
    "E08": _gen_missing_step,
    "E09": _gen_conceptual,
    "E10": _gen_wording_unit,
    "E11": _gen_no_checking,
}


# ---------------------------------------------------------------------------
# Backward-compatible aliases (imported by tests)
# ---------------------------------------------------------------------------

def _gen_fraction_multiply(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """Backward-compatible alias — delegates to exercise-type generator."""
    return _gen_frac_mul(rng, difficulty)


def _gen_circle(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """Backward-compatible alias — delegates to exercise-type generator."""
    return _gen_geo_circle_area(rng, difficulty)


def _gen_ratio(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """Backward-compatible alias — produces ratio problems with ':' or '/' answers."""
    if difficulty == "A":
        g = _rand_int(rng, 2, 8)
        a = g * _rand_int(rng, 2, 6)
        b = g * _rand_int(rng, 2, 6)
        while b == a:
            b = g * _rand_int(rng, 2, 6)
        sa, sb = _simplify_int_ratio(a, b)
        return GeneratedProblem(
            problem=f"化简比 {a}:{b}",
            correct_answer=f"{sa}:{sb}",
            error_code="E04",
            knowledge_point="化简整数比",
            difficulty=difficulty,
            hint="找两个数的最大公因数，同时除以它",
        )
    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        while f1 == f2:
            f2 = _rand_frac_for(rng, "B")
        a, b = _simplify_frac_ratio(f1, f2)
        return GeneratedProblem(
            problem=f"化简比 {_frac_str(f1)}:{_frac_str(f2)}",
            correct_answer=f"{a}:{b}",
            error_code="E04",
            knowledge_point="化简分数比",
            difficulty=difficulty,
            hint="先通分，把两个分数变成同分母，再按整数比化简",
        )
    a = _rand_int(rng, 1, 5)
    b = _rand_int(rng, 1, 5)
    while b == a:
        b = _rand_int(rng, 1, 5)
    total_parts = a + b
    k = _rand_int(rng, 3, 10)
    total = total_parts * k
    ask_larger = rng.choice([True, False])
    if ask_larger:
        answer = str(k * max(a, b))
        q = "较大数是多少？"
    else:
        answer = str(k * min(a, b))
        q = "较小数是多少？"
    return GeneratedProblem(
        problem=f"把{total}按{a}:{b}分配，{q}",
        correct_answer=answer,
        error_code="E04",
        knowledge_point="按比分配",
        difficulty=difficulty,
        hint=f"总份数={total_parts}份，先算每份是多少，再乘以对应份数",
    )



# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_problems(
    error_code: str,
    difficulty: str = "B",
    count: int = 5,
    seed: int | None = None,
) -> list[GeneratedProblem]:
    gen = _GENERATORS.get(error_code, _generate_default)
    rng = random.Random(seed)
    results: list[GeneratedProblem] = []
    seen: set[str] = set()
    attempts = 0
    while len(results) < count and attempts < count * 20:
        p = gen(difficulty, rng)
        if p.problem not in seen:
            seen.add(p.problem)
            results.append(p)
        attempts += 1
    return results


def generate_quiz_problems(
    error_codes: list[str],
    difficulty: str = "B",
    total_count: int = 5,
    seed: int | None = None,
    difficulty_distribution: dict[str, float] | None = None,
) -> list[GeneratedProblem]:
    """Generate a set of problems, optionally with mixed difficulty levels.

    Args:
        error_codes: Target error codes to cover.
        difficulty: Default difficulty when *difficulty_distribution* is None.
        total_count: Total number of problems to generate.
        seed: Random seed for reproducibility.
        difficulty_distribution: Mapping of difficulty level to its proportion,
            e.g. ``{"A": 0.6, "B": 0.4}``.  When provided, *difficulty* is
            ignored and problems are generated at mixed levels.
    """
    if not error_codes:
        error_codes = ["E03"]
    rng = random.Random(seed)

    if difficulty_distribution is None:
        # Original behaviour: single difficulty for all problems
        per_code = max(1, total_count // len(error_codes))
        remainder = total_count - per_code * len(error_codes)
        all_problems: list[GeneratedProblem] = []
        for i, code in enumerate(error_codes):
            count = per_code + (1 if i < remainder else 0)
            problems = generate_problems(code, difficulty, count, seed=rng.randint(0, 2**31))
            all_problems.extend(problems)
    else:
        # Mixed difficulty: allocate problem counts per difficulty tier,
        # then distribute each tier across error codes.
        all_problems: list[GeneratedProblem] = []
        diff_levels = list(difficulty_distribution.keys())
        remaining = total_count
        counts_by_diff: dict[str, int] = {}
        for idx, diff in enumerate(diff_levels):
            if idx == len(diff_levels) - 1:
                counts_by_diff[diff] = remaining
            else:
                count = round(total_count * difficulty_distribution[diff])
                counts_by_diff[diff] = max(0, count)
                remaining -= counts_by_diff[diff]
        for diff, count in counts_by_diff.items():
            if count <= 0:
                continue
            per_code = max(1, count // len(error_codes))
            rem = count - per_code * len(error_codes)
            for i, code in enumerate(error_codes):
                n = per_code + (1 if i < rem else 0)
                if n <= 0:
                    continue
                problems = generate_problems(code, diff, n, seed=rng.randint(0, 2**31))
                all_problems.extend(problems)

    rng.shuffle(all_problems)
    return all_problems[:total_count]


# ---------------------------------------------------------------------------
# Exercise-type-based generators (parallel dispatch to E01-E11 system)
# ---------------------------------------------------------------------------

def _gen_mental_int_add(rng: random.Random, difficulty: str) -> GeneratedProblem:
    a = rng.randint(2, 9)
    b = rng.randint(2, 9)
    op = rng.choice(["+", "-"])
    if op == "+":
        result = a + b
    else:
        if a < b:
            a, b = b, a
        result = a - b
    return GeneratedProblem(
        problem=f"{a}{op}{b}=",
        correct_answer=str(result),
        error_code="E01",
        knowledge_point="整数口算",
        difficulty=difficulty,
        hint="直接心算",
        exercise_type="ET-0101",
    )


def _gen_mental_int_mul(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.randint(2, 9)
        b = rng.randint(2, 9)
        return GeneratedProblem(
            problem=f"{a}×{b}=",
            correct_answer=str(a * b),
            error_code="E01",
            knowledge_point="乘法口算",
            difficulty=difficulty,
            hint="用乘法口诀",
            exercise_type="ET-0103",
        )
    a = rng.choice([25, 50, 125, 15])
    b = rng.choice([4, 8, 2, 6])
    result = a * b
    return GeneratedProblem(
        problem=f"{a}×{b}=",
        correct_answer=str(result),
        error_code="E01",
        knowledge_point="特殊数口算",
        difficulty=difficulty,
        hint="记住25×4=100, 125×8=1000等",
        exercise_type="ET-0103",
    )


def _gen_mental_decimal(rng: random.Random, difficulty: str) -> GeneratedProblem:
    op = rng.choice(["+", "-", "×", "÷"])
    if op in ("+", "-"):
        a_dec = round(rng.uniform(0.1, 5.0), 1)
        b_dec = round(rng.uniform(0.1, 5.0), 1)
        if op == "-" and a_dec < b_dec:
            a_dec, b_dec = b_dec, a_dec
        result = round(a_dec + b_dec if op == "+" else a_dec - b_dec, 2)
        return GeneratedProblem(
            problem=f"{a_dec}{op}{b_dec}=",
            correct_answer=str(result),
            error_code="E06",
            knowledge_point="小数口算",
            difficulty=difficulty,
            hint="小数点对齐心算",
            exercise_type="ET-0104",
        )
    if op == "×":
        a = Fraction(rng.randint(1, 9), 10)
        b = rng.randint(2, 9)
        result = a * b
        return GeneratedProblem(
            problem=f"{float(a):.1f}×{b}=",
            correct_answer=_decimal_str(result),
            error_code="E06",
            knowledge_point="小数乘整数口算",
            difficulty=difficulty,
            hint="先按整数乘，再定小数位",
            exercise_type="ET-0104",
        )
    b = Fraction(rng.randint(1, 9), 10)
    a_frac = b * rng.randint(2, 9)
    return GeneratedProblem(
        problem=f"{float(a_frac):.1f}÷{float(b):.1f}=",
        correct_answer=_decimal_str(a_frac / b),
        error_code="E06",
        knowledge_point="小数除法口算",
        difficulty=difficulty,
        hint="转化为分数计算",
        exercise_type="ET-0104",
    )


def _gen_mental_fraction(rng: random.Random, difficulty: str) -> GeneratedProblem:
    f1 = _rand_frac_for(rng, difficulty)
    f2 = _rand_frac_for(rng, difficulty)
    op = rng.choice(["+", "-", "×"])
    if op == "+":
        result = f1 + f2
    elif op == "-":
        hi, lo = max(f1, f2), min(f1, f2)
        f1, f2 = hi, lo
        result = hi - lo
    else:
        result = f1 * f2
    return GeneratedProblem(
        problem=f"{_frac_str(f1)}{op}{_frac_str(f2)}=",
        correct_answer=_frac_str(result),
        error_code="E01",
        knowledge_point="分数口算",
        difficulty=difficulty,
        hint="直接心算",
        exercise_type="ET-0105",
    )


def _gen_mental_percent(rng: random.Random, difficulty: str) -> GeneratedProblem:
    pct = rng.choice([10, 20, 25, 50, 75])
    base = rng.choice([20, 40, 50, 80, 100, 200])
    result = base * pct // 100
    return GeneratedProblem(
        problem=f"{pct}%×{base}=",
        correct_answer=str(result),
        error_code="E05",
        knowledge_point="百分数口算",
        difficulty=difficulty,
        hint="百分数=÷100×百分比",
        exercise_type="ET-0106",
    )


def _gen_mental_mixed(rng: random.Random, difficulty: str) -> GeneratedProblem:
    f = _rand_frac_for(rng, difficulty)
    dec_entry = rng.choice(_DECIMAL_POOL_B)
    dec_display, dec_frac = dec_entry
    result = f * dec_frac
    return GeneratedProblem(
        problem=f"{_frac_str(f)}×{dec_display}=",
        correct_answer=_frac_str(result),
        error_code="E09",
        knowledge_point="分数×小数口算",
        difficulty=difficulty,
        hint="统一化成分数",
        exercise_type="ET-0107",
    )


def _gen_vertical_add_sub(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.randint(100, 500)
        b = rng.randint(100, 400)
        if rng.random() < 0.5:
            result = a + b
            op = "+"
        else:
            if a < b:
                a, b = b, a
            result = a - b
            op = "-"
    elif difficulty == "B":
        a = rng.randint(1000, 5000)
        b = rng.randint(1000, 4000)
        if rng.random() < 0.5:
            result = a + b
            op = "+"
        else:
            if a < b:
                a, b = b, a
            result = a - b
            op = "-"
    else:
        a = rng.randint(10000, 99999)
        b = rng.randint(10000, 99999)
        if rng.random() < 0.5:
            result = a + b
            op = "+"
        else:
            if a < b:
                a, b = b, a
            result = a - b
            op = "-"
    return GeneratedProblem(
        problem=f"{a}{op}{b}=",
        correct_answer=str(result),
        error_code="E03",
        knowledge_point="多位数加减竖式",
        difficulty=difficulty,
        hint="列竖式，注意数位对齐和进退位",
        exercise_type="ET-0201",
    )


def _gen_vertical_mul(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty in ("A", "B"):
        a = rng.randint(11, 99)
        b = rng.randint(11, 99)
    else:
        a = rng.randint(100, 999)
        b = rng.randint(11, 99)
    result = a * b
    return GeneratedProblem(
        problem=f"{a}×{b}=",
        correct_answer=str(result),
        error_code="E02",
        knowledge_point="多位数乘法竖式",
        difficulty=difficulty,
        hint="列竖式，部分积要对齐数位",
        exercise_type="ET-0202" if difficulty in ("A", "B") else "ET-0203",
    )


def _gen_vertical_div(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        b = rng.randint(2, 9)
        q = rng.randint(11, 99)
    elif difficulty == "B":
        b = rng.randint(11, 49)
        q = rng.randint(11, 49)
    else:
        b = rng.randint(11, 99)
        q = rng.randint(11, 99)
    a = b * q
    return GeneratedProblem(
        problem=f"{a}÷{b}=",
        correct_answer=str(q),
        error_code="E02",
        knowledge_point="除法竖式",
        difficulty=difficulty,
        hint="列竖式，从高位除起",
        exercise_type="ET-0204",
    )


def _gen_step_int(rng: random.Random, difficulty: str) -> GeneratedProblem:
    a = rng.randint(2, 20)
    b = rng.randint(2, 12)
    c = rng.randint(2, 12)
    has_paren = rng.choice([True, False])
    if has_paren:
        pattern = rng.choice(["add_div", "sub_div", "add_mul", "sub_mul"])
        if pattern == "add_div":
            result = (a + b) * c
            return GeneratedProblem(
                problem=f"({a}+{b})×{c}=",
                correct_answer=str(result),
                error_code="E05",
                knowledge_point="整数脱式（有括号）",
                difficulty=difficulty,
                hint="先算括号里的",
                exercise_type="ET-0302",
            )
        if pattern == "sub_div":
            if a <= b:
                a = b + rng.randint(1, 10)
            result = (a - b) * c
            return GeneratedProblem(
                problem=f"({a}-{b})×{c}=",
                correct_answer=str(result),
                error_code="E05",
                knowledge_point="整数脱式（有括号）",
                difficulty=difficulty,
                hint="先算括号里的",
                exercise_type="ET-0302",
            )
        if pattern == "add_mul":
            result = a + b * c
            return GeneratedProblem(
                problem=f"{a}+{b}×{c}=",
                correct_answer=str(result),
                error_code="E05",
                knowledge_point="整数脱式（先乘后加）",
                difficulty=difficulty,
                hint="先算乘法，再算加法",
                exercise_type="ET-0301",
            )
        result = a * b - c
        return GeneratedProblem(
            problem=f"{a}×{b}-{c}=",
            correct_answer=str(result),
            error_code="E05",
            knowledge_point="整数脱式（先乘后减）",
            difficulty=difficulty,
            hint="先算乘法，再算减法",
            exercise_type="ET-0301",
        )
    result = a + b * c
    return GeneratedProblem(
        problem=f"{a}+{b}×{c}=",
        correct_answer=str(result),
        error_code="E05",
        knowledge_point="整数脱式（先乘除后加减）",
        difficulty=difficulty,
        hint="先算乘除，再算加减",
        exercise_type="ET-0301",
    )


def _gen_step_decimal(rng: random.Random, difficulty: str) -> GeneratedProblem:
    a = round(rng.uniform(1.0, 10.0), 1)
    b = round(rng.uniform(0.5, 5.0), 1)
    c = round(rng.uniform(0.5, 3.0), 1)
    has_paren = rng.choice([True, False])
    if has_paren:
        result = round((a + b) * c, 2)
        return GeneratedProblem(
            problem=f"({a}+{b})×{c}=",
            correct_answer=str(result),
            error_code="E05",
            knowledge_point="小数脱式（有括号）",
            difficulty=difficulty,
            hint="先算括号里",
            exercise_type="ET-0303",
        )
    result = round(a * b + c, 2)
    return GeneratedProblem(
        problem=f"{a}×{b}+{c}=",
        correct_answer=str(result),
        error_code="E05",
        knowledge_point="小数脱式",
        difficulty=difficulty,
        hint="先算乘法，再算加法",
        exercise_type="ET-0303",
    )


def _gen_step_fraction(rng: random.Random, difficulty: str) -> GeneratedProblem:
    f1 = _rand_frac_for(rng, difficulty)
    f2 = _rand_frac_for(rng, difficulty)
    f3 = _rand_frac_for(rng, difficulty)
    has_paren = rng.choice([True, False])
    if has_paren:
        result = (f1 + f2) * f3
        return GeneratedProblem(
            problem=f"({_frac_str(f1)}+{_frac_str(f2)})×{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E03",
            knowledge_point="分数脱式（有括号）",
            difficulty=difficulty,
            hint="先算括号里",
            exercise_type="ET-0304",
        )
    product = f2 * f3
    result = f1 + product
    return GeneratedProblem(
        problem=f"{_frac_str(f1)}+{_frac_str(f2)}×{_frac_str(f3)}=",
        correct_answer=_frac_str(result),
        error_code="E03",
        knowledge_point="分数脱式（先乘后加）",
        difficulty=difficulty,
        hint="先算乘法，再算加法",
        exercise_type="ET-0304",
    )


def _gen_step_mixed(rng: random.Random, difficulty: str) -> GeneratedProblem:
    f = _rand_frac_for(rng, difficulty)
    dec_entry = rng.choice(_DECIMAL_POOL_B)
    dec_display, dec_frac = dec_entry
    f2 = _rand_frac_for(rng, difficulty)
    result = f * dec_frac + f2
    return GeneratedProblem(
        problem=f"{_frac_str(f)}×{dec_display}+{_frac_str(f2)}=",
        correct_answer=_frac_str(result),
        error_code="E09",
        knowledge_point="混合脱式（分数+小数）",
        difficulty=difficulty,
        hint="统一化成分数再算",
        exercise_type="ET-0305",
    )


def _gen_shortcut_round(rng: random.Random, difficulty: str) -> GeneratedProblem:
    patterns = [
        (25, 4, 100), (25, 8, 200), (25, 12, 300),
        (125, 8, 1000), (125, 4, 500), (125, 16, 2000),
        (50, 2, 100), (50, 4, 200),
    ]
    a, b, expected = rng.choice(patterns)
    return GeneratedProblem(
        problem=f"{a}×{b}=",
        correct_answer=str(expected),
        error_code="E10",
        knowledge_point="凑整巧算",
        difficulty=difficulty,
        hint=f"记住{a}×{b}={expected}",
        exercise_type="ET-0406",
    )


def _gen_shortcut_distrib(rng: random.Random, difficulty: str) -> GeneratedProblem:
    kind = rng.choice(["forward", "reverse"])
    if kind == "forward":
        f = _rand_frac_for(rng, difficulty)
        n = _rand_int_for(rng, difficulty)
        m = _rand_int_for(rng, difficulty)
        result = f * (n + m)
        return GeneratedProblem(
            problem=f"{_frac_str(f)}×({n}+{m})=",
            correct_answer=_frac_str(result),
            error_code="E10",
            knowledge_point="乘法分配律",
            difficulty=difficulty,
            hint=f"用分配律：{_frac_str(f)}×{n}+{_frac_str(f)}×{m}",
            exercise_type="ET-0403",
        )
    f = _rand_frac_for(rng, difficulty)
    n = _rand_int_for(rng, difficulty)
    m = _rand_int_for(rng, difficulty)
    result = f * n + f * m
    return GeneratedProblem(
        problem=f"{_frac_str(f)}×{n}+{_frac_str(f)}×{m}=",
        correct_answer=_frac_str(result),
        error_code="E10",
        knowledge_point="乘法分配律（逆用）",
        difficulty=difficulty,
        hint=f"提取{_frac_str(f)}：{_frac_str(f)}×({n}+{m})",
        exercise_type="ET-0403",
    )


def _gen_shortcut_decompose(rng: random.Random, difficulty: str) -> GeneratedProblem:
    kind = rng.choice(["plus_one", "near_round"])
    if kind == "plus_one":
        n = rng.randint(2, 20)
        f = _rand_frac_for(rng, difficulty)
        result = f * n + f
        return GeneratedProblem(
            problem=f"{_frac_str(f)}×{n}+{_frac_str(f)}=",
            correct_answer=_frac_str(result),
            error_code="E10",
            knowledge_point="拆项巧算（+1凑整）",
            difficulty=difficulty,
            hint=f"把{_frac_str(f)}看成{_frac_str(f)}×1，提取公因数",
            exercise_type="ET-0407",
        )
    n = rng.choice([99, 98, 101, 102])
    m = rng.randint(2, 9)
    result = n * m
    base = (n + 1) if n < 100 else (n - 1)
    return GeneratedProblem(
        problem=f"{n}×{m}=",
        correct_answer=str(result),
        error_code="E10",
        knowledge_point="拆项巧算",
        difficulty=difficulty,
        hint=f"把{n}拆成{base}-{1 if n < 100 else -1}来算",
        exercise_type="ET-0407",
    )


def _gen_word_int(rng: random.Random, difficulty: str) -> GeneratedProblem:
    n = rng.randint(2, 9)
    m = rng.randint(10, 30)
    templates = [
        (f"{n}的{m}倍是多少？", str(n * m), "整数文字题——倍数"),
        (f"{n*m}比{m}多多少？", str(n * m - m), "整数文字题——差"),
        (f"{m}的{n}倍与{m//2}的和是多少？", str(m * n + m // 2), "整数文字题——综合"),
    ]
    if difficulty != "C":
        problem, answer, kp = templates[0] if difficulty == "A" else rng.choice(templates[:2])
    else:
        problem, answer, kp = rng.choice(templates)
    return GeneratedProblem(
        problem=problem,
        correct_answer=answer,
        error_code="E05",
        knowledge_point=kp,
        difficulty=difficulty,
        hint="把文字翻译成算式",
        exercise_type="ET-0501",
    )


def _gen_word_frac(rng: random.Random, difficulty: str) -> GeneratedProblem:
    f = _rand_frac_for(rng, difficulty)
    n = _rand_int_for(rng, difficulty)
    result = f * n
    templates = [
        (f"{n}的{_frac_str(f)}是多少？", _frac_str(result)),
        (f"{_frac_str(f)}的{_frac_str(Fraction(1, 2))}是多少？", _frac_str(f * Fraction(1, 2))),
    ]
    problem, answer = rng.choice(templates)
    return GeneratedProblem(
        problem=problem,
        correct_answer=answer,
        error_code="E01",
        knowledge_point="分数文字题",
        difficulty=difficulty,
        hint="求一个数的几分之几用乘法",
        exercise_type="ET-0502",
    )


def _gen_word_pct(rng: random.Random, difficulty: str) -> GeneratedProblem:
    pct = rng.choice([10, 20, 25, 50, 75])
    base = rng.choice([40, 60, 80, 100, 200])
    result = base * pct // 100
    return GeneratedProblem(
        problem=f"{base}的{pct}%是多少？",
        correct_answer=str(result),
        error_code="E05",
        knowledge_point="百分数文字题",
        difficulty=difficulty,
        hint="求一个数的百分之几=乘法",
        exercise_type="ET-0503",
    )


def _gen_word_ratio(rng: random.Random, difficulty: str) -> GeneratedProblem:
    a = rng.randint(1, 5)
    b = rng.randint(1, 5)
    while b == a:
        b = rng.randint(1, 5)
    k = rng.randint(3, 10)
    total = (a + b) * k
    return GeneratedProblem(
        problem=f"把{total}按{a}:{b}分配，较大数是多少？",
        correct_answer=str(k * max(a, b)),
        error_code="E04",
        knowledge_point="按比分配",
        difficulty=difficulty,
        hint=f"总份数={a + b}，先算每份",
        exercise_type="ET-0504",
    )


def _gen_word_comprehensive(rng: random.Random, difficulty: str) -> GeneratedProblem:
    denom = rng.choice([6, 10, 12, 15, 20])
    f1 = Fraction(rng.randint(1, denom - 1), denom)
    f2 = Fraction(rng.randint(1, denom - 1), denom)
    for _ in range(100):
        if f2 < f1:
            break
        f2 = Fraction(rng.randint(1, denom - 1), denom)
    else:
        f1 = Fraction(3, 5)
        f2 = Fraction(1, 2)
    diff_val = f1 - f2
    unit_val = Fraction(1, 1) / diff_val if diff_val != 0 else Fraction(1, 1)
    if unit_val.denominator != 1 or unit_val <= 0:
        f1 = Fraction(3, 5)
        f2 = Fraction(1, 2)
        diff_val = f1 - f2
        unit_val = Fraction(1, 1) / diff_val
    return GeneratedProblem(
        problem=f"一个数的{_frac_str(f1)}比它的{_frac_str(f2)}多{int(diff_val * unit_val)}，这个数是多少？",
        correct_answer=str(int(unit_val)),
        error_code="E05",
        knowledge_point="综合文字题",
        difficulty=difficulty,
        hint="设这个数为x，列方程",
        exercise_type="ET-0505",
    )


def _gen_geo_circle_perimeter(rng: random.Random, difficulty: str) -> GeneratedProblem:
    r = rng.randint(2, 10)
    coeff = 2 * r
    return GeneratedProblem(
        problem=f"半径{r}cm的圆的周长",
        correct_answer=f"{coeff}π cm",
        error_code="E07",
        knowledge_point="圆的周长",
        difficulty=difficulty,
        hint="周长=2×π×半径",
        exercise_type="ET-0601",
    )


def _gen_geo_circle_area(rng: random.Random, difficulty: str) -> GeneratedProblem:
    r = rng.randint(2, 10)
    coeff = r * r
    return GeneratedProblem(
        problem=f"半径{r}cm的圆的面积",
        correct_answer=f"{coeff}π cm²",
        error_code="E07",
        knowledge_point="圆的面积",
        difficulty=difficulty,
        hint="面积=π×半径²",
        exercise_type="ET-0602",
    )


def _gen_geo_annulus(rng: random.Random, difficulty: str) -> GeneratedProblem:
    R = rng.randint(4, 10)
    r = rng.randint(2, R - 1)
    coeff = R * R - r * r
    return GeneratedProblem(
        problem=f"外圆半径{R}cm、内圆半径{r}cm的环形面积",
        correct_answer=f"{coeff}π cm²",
        error_code="E07",
        knowledge_point="环形面积",
        difficulty=difficulty,
        hint="环形面积=π(R²-r²)",
        exercise_type="ET-0603",
    )


def _gen_geo_sector(rng: random.Random, difficulty: str) -> GeneratedProblem:
    r = rng.randint(3, 8)
    angle = rng.choice([60, 90, 120, 150, 180])
    num_coeff = r * r * angle
    den_coeff = 360
    from math import gcd
    g = gcd(num_coeff, den_coeff)
    num_coeff //= g
    den_coeff //= g
    if den_coeff == 1:
        answer = f"{num_coeff}π cm²"
    else:
        answer = f"{num_coeff}/{den_coeff}π cm²"
    return GeneratedProblem(
        problem=f"半径{r}cm、圆心角{angle}°的扇形面积",
        correct_answer=answer,
        error_code="E07",
        knowledge_point="扇形面积",
        difficulty=difficulty,
        hint="扇形面积=n/360×πr²",
        exercise_type="ET-0604",
    )


def _gen_geo_composite(rng: random.Random, difficulty: str) -> GeneratedProblem:
    kind = rng.choice(["rect_semicircle", "l_shape"])
    if kind == "rect_semicircle":
        w = rng.choice([4, 6, 8])
        h = rng.choice([3, 4, 5])
        d = w
        r = d // 2
        area = w * h + Fraction(r * r, 2)
        area_str = f"{w * h}+{r * r}π/2" if r * r > 1 else f"{w * h}+π/2"
        return GeneratedProblem(
            problem=f"长{w}cm、宽{h}cm的矩形，一端加一个直径{d}cm的半圆，总面积",
            correct_answer=f"({area_str}) cm²",
            error_code="E07",
            knowledge_point="组合图形面积",
            difficulty=difficulty,
            hint="矩形面积+半圆面积",
            exercise_type="ET-0605",
        )
    a = rng.randint(3, 8)
    b = rng.randint(2, a)
    c = rng.randint(2, 5)
    area = a * a - b * c
    return GeneratedProblem(
        problem=f"L形图形，外边长{a}cm，缺角宽{b}cm高{c}cm，面积",
        correct_answer=f"{area} cm²",
        error_code="E07",
        knowledge_point="L形面积（割补法）",
        difficulty=difficulty,
        hint="大矩形-小矩形",
        exercise_type="ET-0605",
    )


def _gen_geo_cylinder_volume(rng: random.Random, difficulty: str) -> GeneratedProblem:
    r = rng.randint(2, 6)
    h = rng.randint(5, 15)
    coeff = r * r * h
    return GeneratedProblem(
        problem=f"底面半径{r}cm、高{h}cm的圆柱体积",
        correct_answer=f"{coeff}π cm³",
        error_code="E07",
        knowledge_point="圆柱体积",
        difficulty=difficulty,
        hint="圆柱体积=πr²h",
        exercise_type="ET-0610",
    )


def _gen_geo_cone_volume(rng: random.Random, difficulty: str) -> GeneratedProblem:
    r = rng.randint(2, 6)
    h = rng.randint(6, 18)
    coeff = r * r * h
    from math import gcd as mgcd
    g = mgcd(coeff, 3)
    num = coeff // g
    den = 3 // g
    if den == 1:
        answer = f"{num}π cm³"
    else:
        answer = f"{num}/{den}π cm³"
    return GeneratedProblem(
        problem=f"底面半径{r}cm、高{h}cm的圆锥体积",
        correct_answer=answer,
        error_code="E07",
        knowledge_point="圆锥体积",
        difficulty=difficulty,
        hint="圆锥体积=1/3πr²h",
        exercise_type="ET-0611",
    )


def _gen_frac_add_sub(rng: random.Random, difficulty: str) -> GeneratedProblem:
    f1 = _rand_frac_for(rng, difficulty)
    f2 = _rand_frac_for(rng, difficulty)
    op = rng.choice(["+", "-"])
    if op == "+":
        result = f1 + f2
    else:
        hi, lo = max(f1, f2), min(f1, f2)
        f1, f2 = hi, lo
        result = hi - lo
    return GeneratedProblem(
        problem=f"{_frac_str(f1)}{op}{_frac_str(f2)}=",
        correct_answer=_frac_str(result),
        error_code="E01",
        knowledge_point="分数加减",
        difficulty=difficulty,
        hint="通分后加减",
        exercise_type="ET-0702",
    )


def _gen_frac_convert(rng: random.Random, difficulty: str) -> GeneratedProblem:
    entry = rng.choice(_CONV_TABLE)
    _, frac, dec, pct = entry
    direction = rng.choice(["frac_dec", "dec_frac", "frac_pct", "pct_frac"])
    if direction == "frac_dec":
        return GeneratedProblem(
            problem=f"把{_frac_str(frac)}化成小数",
            correct_answer=dec,
            error_code="E06",
            knowledge_point="分数化小数",
            difficulty=difficulty,
            hint="分子÷分母",
            exercise_type="ET-0706",
        )
    if direction == "dec_frac":
        return GeneratedProblem(
            problem=f"把{dec}化成最简分数",
            correct_answer=_frac_str(frac),
            error_code="E06",
            knowledge_point="小数化分数",
            difficulty=difficulty,
            hint="写成分母10/100/1000的分数再约分",
            exercise_type="ET-0706",
        )
    if direction == "frac_pct":
        return GeneratedProblem(
            problem=f"把{_frac_str(frac)}化成百分数",
            correct_answer=pct,
            error_code="E05",
            knowledge_point="分数化百分数",
            difficulty=difficulty,
            hint="分子÷分母×100%",
            exercise_type="ET-0707",
        )
    return GeneratedProblem(
        problem=f"把{pct}化成最简分数",
        correct_answer=_frac_str(frac),
        error_code="E06",
        knowledge_point="百分数化分数",
        difficulty=difficulty,
        hint="写成分母100再约分",
        exercise_type="ET-0707",
    )


def _gen_unit_convert(rng: random.Random, difficulty: str) -> GeneratedProblem:
    conversions = [
        ("km", "m", 1000, "长度"),
        ("m", "cm", 100, "长度"),
        ("m²", "dm²", 100, "面积"),
        ("dm²", "cm²", 100, "面积"),
        ("m³", "dm³", 1000, "体积"),
        ("L", "mL", 1000, "体积"),
        ("t", "kg", 1000, "质量"),
        ("kg", "g", 1000, "质量"),
        ("小时", "分钟", 60, "时间"),
    ]
    unit_from, unit_to, factor, domain = rng.choice(conversions)
    val = round(rng.uniform(0.5, 10.0), 1)
    result = val * factor
    return GeneratedProblem(
        problem=f"{val}{unit_from}=?{unit_to}",
        correct_answer=f"{result}{unit_to}",
        error_code="E06",
        knowledge_point=f"{domain}单位换算",
        difficulty=difficulty,
        hint=f"1{unit_from}={factor}{unit_to}",
        exercise_type="ET-0801",
    )


def _gen_estimate(rng: random.Random, difficulty: str) -> GeneratedProblem:
    a = round(rng.uniform(2.0, 10.0), 1)
    b = round(rng.uniform(2.0, 10.0), 1)
    op = rng.choice(["×", "+"])
    if op == "×":
        exact = round(a * b, 1)
        approx = round(round(a) * round(b), 1)
        return GeneratedProblem(
            problem=f"估算 {a}×{b} 的结果大约是多少",
            correct_answer=f"约{approx}（精确值{exact}）",
            error_code="E11",
            knowledge_point="计算估算",
            difficulty=difficulty,
            hint="先取近似值再计算",
            exercise_type="ET-0806",
        )
    exact = round(a + b, 1)
    approx = round(round(a) + round(b), 1)
    return GeneratedProblem(
        problem=f"估算 {a}+{b} 的结果大约是多少",
        correct_answer=f"约{approx}（精确值{exact}）",
        error_code="E11",
        knowledge_point="计算估算",
        difficulty=difficulty,
        hint="先取近似值再计算",
        exercise_type="ET-0806",
    )


# ---------------------------------------------------------------------------
# ET-0701: 分数加减——同分母
# ---------------------------------------------------------------------------

def _gen_frac_same_denom(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        denom = rng.choice([2, 3, 4, 5, 6])
        a = rng.randint(1, denom - 1)
        b = rng.randint(1, denom - 1)
        for _ in range(100):
            if not (a + b >= denom and a == b):
                break
            b = rng.randint(1, denom - 1)
        else:
            # denom=2 makes a=b=1 inevitable; just proceed
            pass
        op = rng.choice(["+", "-"])
        if op == "+":
            if a + b >= denom:
                b = rng.randint(1, denom - a - 1) if denom - a > 1 else 1
            f1, f2 = Fraction(a, denom), Fraction(b, denom)
            result = f1 + f2
        else:
            if a <= b:
                a, b = b, a
            f1, f2 = Fraction(a, denom), Fraction(b, denom)
            result = f1 - f2
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}{op}{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="同分母分数加减",
            difficulty=difficulty,
            hint="同分母分数相加减，分母不变，分子相加减",
            exercise_type="ET-0701",
        )
    if difficulty == "B":
        denom = rng.choice([2, 3, 4, 5, 6, 8, 10, 12])
        a = rng.randint(1, denom - 1)
        b = rng.randint(1, denom - 1)
        op = rng.choice(["+", "-"])
        if op == "+":
            f1, f2 = Fraction(a, denom), Fraction(b, denom)
            result = f1 + f2
        else:
            if a <= b:
                a, b = b, a
            f1, f2 = Fraction(a, denom), Fraction(b, denom)
            result = f1 - f2
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}{op}{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="同分母分数加减（需约分）",
            difficulty=difficulty,
            hint="同分母加减后记得约分到最简",
            exercise_type="ET-0701",
        )
    # C: mixed numbers with same denominator
    denom = rng.choice([3, 4, 5, 6, 8])
    w1 = rng.randint(1, 4)
    w2 = rng.randint(1, 4)
    n1 = rng.randint(1, denom - 1)
    n2 = rng.randint(1, denom - 1)
    mf1 = Fraction(w1 * denom + n1, denom)
    mf2 = Fraction(w2 * denom + n2, denom)
    op = rng.choice(["+", "-"])
    if op == "+":
        result = mf1 + mf2
    else:
        if mf1 <= mf2:
            mf1, mf2 = mf2, mf1
        result = mf1 - mf2
    return GeneratedProblem(
        problem=f"{_mixed_str(mf1)}{op}{_mixed_str(mf2)}=",
        correct_answer=_mixed_str(result),
        error_code="E01",
        knowledge_point="同分母带分数加减",
        difficulty=difficulty,
        hint="带分数加减：整数部分和分数部分分别加减",
        exercise_type="ET-0701",
    )


# ---------------------------------------------------------------------------
# ET-0703: 分数乘法
# ---------------------------------------------------------------------------

def _gen_frac_mul(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        kind = rng.choice(["frac_frac", "frac_int"])
        if kind == "frac_frac":
            pool = [2, 3, 4, 5, 6]
            d1 = rng.choice(pool)
            d2 = rng.choice(pool)
            n1 = rng.randint(1, d1 - 1)
            n2 = rng.randint(1, d2 - 1)
            f1, f2 = Fraction(n1, d1), Fraction(n2, d2)
            result = f1 * f2
            return GeneratedProblem(
                problem=f"{_frac_str(f1)}×{_frac_str(f2)}=",
                correct_answer=_frac_str(result),
                error_code="E01",
                knowledge_point="分数乘分数",
                difficulty=difficulty,
                hint="分子乘分子，分母乘分母，能约分先约分",
                exercise_type="ET-0703",
            )
        f = _rand_frac_for(rng, "A")
        n = _rand_int_for(rng, "A")
        result = f * n
        return GeneratedProblem(
            problem=f"{_frac_str(f)}×{n}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="分数乘整数",
            difficulty=difficulty,
            hint="分数×整数：分子乘以整数，分母不变",
            exercise_type="ET-0703",
        )
    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        result = f1 * f2
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}×{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="分数乘法（需约分）",
            difficulty=difficulty,
            hint="先交叉约分，再相乘",
            exercise_type="ET-0703",
        )
    # C: mixed number × fraction
    kind = rng.choice(["mixed_frac", "int_mixed"])
    if kind == "mixed_frac":
        mf = _rand_mixed(rng, "C")
        f = _rand_frac_for(rng, "C")
        result = mf * f
        return GeneratedProblem(
            problem=f"{_mixed_str(mf)}×{_frac_str(f)}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="带分数乘分数",
            difficulty=difficulty,
            hint="先把带分数化成假分数再乘",
            exercise_type="ET-0703",
        )
    n = rng.randint(2, 9)
    mf = _rand_mixed(rng, "C")
    result = Fraction(n) * mf
    return GeneratedProblem(
        problem=f"{n}×{_mixed_str(mf)}=",
        correct_answer=_frac_str(result),
        error_code="E01",
        knowledge_point="整数乘带分数",
        difficulty=difficulty,
        hint="先把带分数化成假分数再乘",
        exercise_type="ET-0703",
    )


# ---------------------------------------------------------------------------
# ET-0704: 分数除法
# ---------------------------------------------------------------------------

def _gen_frac_div(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        kind = rng.choice(["frac_int", "int_frac", "frac_frac"])
        if kind == "frac_int":
            f = _rand_frac_for(rng, "A")
            n = _rand_int_for(rng, "A")
            result = f / n
            return GeneratedProblem(
                problem=f"{_frac_str(f)}÷{n}=",
                correct_answer=_frac_str(result),
                error_code="E02",
                knowledge_point="分数÷整数",
                difficulty=difficulty,
                hint="除以整数=乘以这个整数的倒数",
                exercise_type="ET-0704",
            )
        if kind == "int_frac":
            f = _rand_frac_for(rng, "A")
            n = _rand_int_for(rng, "A")
            result = Fraction(n) / f
            return GeneratedProblem(
                problem=f"{n}÷{_frac_str(f)}=",
                correct_answer=_frac_str(result),
                error_code="E02",
                knowledge_point="整数÷分数",
                difficulty=difficulty,
                hint="除以分数=乘以倒数",
                exercise_type="ET-0704",
            )
        f1 = _rand_frac_for(rng, "A")
        f2 = _rand_frac_for(rng, "A")
        result = f1 / f2
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}÷{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E02",
            knowledge_point="分数÷分数",
            difficulty=difficulty,
            hint="除以一个分数等于乘以它的倒数",
            exercise_type="ET-0704",
        )
    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        result = f1 / f2
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}÷{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E02",
            knowledge_point="分数除法（一般）",
            difficulty=difficulty,
            hint="甲数÷乙数=甲数×乙数的倒数",
            exercise_type="ET-0704",
        )
    # C: mixed number ÷ fraction
    mf = _rand_mixed(rng, "C")
    f = _rand_frac_for(rng, "C")
    result = mf / f
    return GeneratedProblem(
        problem=f"{_mixed_str(mf)}÷{_frac_str(f)}=",
        correct_answer=_frac_str(result),
        error_code="E02",
        knowledge_point="带分数÷分数",
        difficulty=difficulty,
        hint="先把带分数化成假分数，再乘以除数的倒数",
        exercise_type="ET-0704",
    )


# ---------------------------------------------------------------------------
# ET-0705: 分数四则混合
# ---------------------------------------------------------------------------

def _gen_frac_mixed_ops(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        f1 = _rand_frac_for(rng, "A")
        f2 = _rand_frac_for(rng, "A")
        f3 = _rand_frac_for(rng, "A")
        op = rng.choice(["mul_add", "mul_sub"])
        if op == "mul_add":
            result = f1 * f2 + f3
            return GeneratedProblem(
                problem=f"{_frac_str(f1)}×{_frac_str(f2)}+{_frac_str(f3)}=",
                correct_answer=_frac_str(result),
                error_code="E05",
                knowledge_point="分数四则混合（先乘后加）",
                difficulty=difficulty,
                hint="先算乘法，再算加法",
                exercise_type="ET-0705",
            )
        product = f1 * f2
        hi, lo = max(product, f3), min(product, f3)
        result = hi - lo
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}×{_frac_str(f2)}-{_frac_str(lo)}=" if product >= f3
            else f"{_frac_str(f3)}-{_frac_str(f1)}×{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E05",
            knowledge_point="分数四则混合（先乘后减）",
            difficulty=difficulty,
            hint="先算乘法，再算减法",
            exercise_type="ET-0705",
        )
    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        f3 = _rand_frac_for(rng, "B")
        pattern = rng.choice(["add_mul", "add_div", "sub_mul"])
        if pattern == "add_mul":
            result = (f1 + f2) * f3
            return GeneratedProblem(
                problem=f"({_frac_str(f1)}+{_frac_str(f2)})×{_frac_str(f3)}=",
                correct_answer=_frac_str(result),
                error_code="E05",
                knowledge_point="括号改变运算顺序",
                difficulty=difficulty,
                hint="有括号先算括号里的",
                exercise_type="ET-0705",
            )
        if pattern == "add_div":
            result = (f1 + f2) / f3
            return GeneratedProblem(
                problem=f"({_frac_str(f1)}+{_frac_str(f2)})÷{_frac_str(f3)}=",
                correct_answer=_frac_str(result),
                error_code="E05",
                knowledge_point="括号除法混合",
                difficulty=difficulty,
                hint="有括号先算括号里的",
                exercise_type="ET-0705",
            )
        if f1 <= f2:
            f1, f2 = f2, f1
        result = (f1 - f2) * f3
        return GeneratedProblem(
            problem=f"({_frac_str(f1)}-{_frac_str(f2)})×{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E05",
            knowledge_point="括号减乘混合",
            difficulty=difficulty,
            hint="有括号先算括号里的",
            exercise_type="ET-0705",
        )
    # C: three operations with mixed numbers
    mf = _rand_mixed(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    f3 = _rand_frac_for(rng, "C")
    kind = rng.choice(["mul_add_sub", "div_add_mul"])
    if kind == "mul_add_sub":
        product = mf * f2
        result = product + f3
        return GeneratedProblem(
            problem=f"{_mixed_str(mf)}×{_frac_str(f2)}+{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E05",
            knowledge_point="分数四则混合（带分数）",
            difficulty=difficulty,
            hint="先化成假分数，按运算顺序计算",
            exercise_type="ET-0705",
        )
    result = (mf / f2) * f3
    return GeneratedProblem(
        problem=f"{_mixed_str(mf)}÷{_frac_str(f2)}×{_frac_str(f3)}=",
        correct_answer=_frac_str(result),
        error_code="E05",
        knowledge_point="分数除乘混合",
        difficulty=difficulty,
        hint="从左到右依次计算",
        exercise_type="ET-0705",
    )


# ---------------------------------------------------------------------------
# ET-0708: 繁分数化简
# ---------------------------------------------------------------------------

def _gen_frac_complex_simplify(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        f1 = _rand_frac_for(rng, "A")
        f2 = _rand_frac_for(rng, "A")
        result = f1 / f2
        return GeneratedProblem(
            problem=f"化简繁分数 ({_frac_str(f1)})/({_frac_str(f2)})=",
            correct_answer=_frac_str(result),
            error_code="E06",
            knowledge_point="繁分数化简（基础）",
            difficulty=difficulty,
            hint="繁分数=分子÷分母",
            exercise_type="ET-0708",
        )
    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        f3 = _rand_frac_for(rng, "B")
        numerator = f1 + f2
        result = numerator / f3
        return GeneratedProblem(
            problem=f"化简 ({_frac_str(f1)}+{_frac_str(f2)})/{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E06",
            knowledge_point="繁分数化简（分子含运算）",
            difficulty=difficulty,
            hint="先算分子的和，再÷分母",
            exercise_type="ET-0708",
        )
    # C: multi-level complex fraction
    f1 = _rand_frac_for(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    f3 = _rand_frac_for(rng, "C")
    f4 = _rand_frac_for(rng, "C")
    num = f1 + f2
    den = f3 - f4 if f3 > f4 else f4 - f3
    if den == 0:
        f4 = _rand_frac_for(rng, "C")
        while f4 == f3:
            f4 = _rand_frac_for(rng, "C")
        den = abs(f3 - f4)
    result = num / den
    return GeneratedProblem(
        problem=f"化简 ({_frac_str(f1)}+{_frac_str(f2)})/({_frac_str(max(f3,f4))}-{_frac_str(min(f3,f4))})=",
        correct_answer=_frac_str(result),
        error_code="E06",
        knowledge_point="繁分数化简（复杂）",
        difficulty=difficulty,
        hint="分别化简分子和分母，再相除",
        exercise_type="ET-0708",
    )


# ---------------------------------------------------------------------------
# ET-0709: 带分数加减
# ---------------------------------------------------------------------------

def _gen_mixed_number_add_sub(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        denom = rng.choice([2, 3, 4, 5, 6])
        w1, w2 = rng.randint(1, 5), rng.randint(1, 5)
        n1 = rng.randint(1, denom - 1)
        n2 = rng.randint(1, denom - 1)
        mf1 = Fraction(w1 * denom + n1, denom)
        mf2 = Fraction(w2 * denom + n2, denom)
        op = "+"
        result = mf1 + mf2
        return GeneratedProblem(
            problem=f"{_mixed_str(mf1)}+{_mixed_str(mf2)}=",
            correct_answer=_mixed_str(result),
            error_code="E01",
            knowledge_point="同分母带分数加法",
            difficulty=difficulty,
            hint="整数部分相加，分数部分相加",
            exercise_type="ET-0709",
        )
    if difficulty == "B":
        d1 = rng.choice([2, 3, 4, 5, 6])
        d2 = rng.choice([2, 3, 4, 5, 6])
        while d2 == d1:
            d2 = rng.choice([2, 3, 4, 5, 6])
        w1, w2 = rng.randint(1, 5), rng.randint(1, 5)
        mf1 = Fraction(w1 * d1 + rng.randint(1, d1 - 1), d1)
        mf2 = Fraction(w2 * d2 + rng.randint(1, d2 - 1), d2)
        op = rng.choice(["+", "-"])
        if op == "+":
            result = mf1 + mf2
        else:
            if mf1 <= mf2:
                mf1, mf2 = mf2, mf1
            result = mf1 - mf2
        return GeneratedProblem(
            problem=f"{_mixed_str(mf1)}{op}{_mixed_str(mf2)}=",
            correct_answer=_mixed_str(result),
            error_code="E01",
            knowledge_point="异分母带分数加减",
            difficulty=difficulty,
            hint="先通分，再加减",
            exercise_type="ET-0709",
        )
    # C: with borrowing/regrouping
    denom = rng.choice([3, 4, 5, 6])
    w1 = rng.randint(3, 8)
    w2 = rng.randint(1, w1 - 1)
    n1 = rng.randint(1, denom - 1)
    n2 = rng.randint(n1 + 1, denom - 1) if n1 < denom - 1 else rng.randint(1, denom - 1)
    mf1 = Fraction(w1 * denom + n1, denom)
    mf2 = Fraction(w2 * denom + n2, denom)
    if mf1 <= mf2:
        mf1, mf2 = mf2, mf1
    result = mf1 - mf2
    return GeneratedProblem(
        problem=f"{_mixed_str(mf1)}-{_mixed_str(mf2)}=",
        correct_answer=_mixed_str(result),
        error_code="E03",
        knowledge_point="带分数减法（退位）",
        difficulty=difficulty,
        hint="分数部分不够减时，从整数部分借1",
        exercise_type="ET-0709",
    )


# ---------------------------------------------------------------------------
# ET-0710: 分数连乘
# ---------------------------------------------------------------------------

def _gen_frac_chain_mul(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        f1 = _rand_frac_for(rng, "A")
        f2 = _rand_frac_for(rng, "A")
        f3 = _rand_frac_for(rng, "A")
        result = f1 * f2 * f3
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}×{_frac_str(f2)}×{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="分数连乘",
            difficulty=difficulty,
            hint="逐个相乘，能约分先约分",
            exercise_type="ET-0710",
        )
    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        f3 = _rand_frac_for(rng, "B")
        result = f1 * f2 * f3
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}×{_frac_str(f2)}×{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="分数连乘（需约分）",
            difficulty=difficulty,
            hint="先把所有分子分母交叉约分，再相乘",
            exercise_type="ET-0710",
        )
    # C: mixed numbers
    mf1 = _rand_mixed(rng, "C")
    mf2 = _rand_mixed(rng, "C")
    f3 = _rand_frac_for(rng, "C")
    result = mf1 * mf2 * f3
    return GeneratedProblem(
        problem=f"{_mixed_str(mf1)}×{_mixed_str(mf2)}×{_frac_str(f3)}=",
        correct_answer=_frac_str(result),
        error_code="E01",
        knowledge_point="带分数连乘",
        difficulty=difficulty,
        hint="先全部化成假分数，再约分相乘",
        exercise_type="ET-0710",
    )


# ---------------------------------------------------------------------------
# ET-0711: 分数连除
# ---------------------------------------------------------------------------

def _gen_frac_chain_div(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        n = rng.randint(2, 12)
        d1 = rng.randint(2, 6)
        d2 = rng.randint(2, 6)
        result = Fraction(n) / d1 / d2
        return GeneratedProblem(
            problem=f"{n}÷{d1}÷{d2}=",
            correct_answer=_frac_str(result),
            error_code="E02",
            knowledge_point="整数连除",
            difficulty=difficulty,
            hint="从左到右依次除",
            exercise_type="ET-0711",
        )
    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        f3 = _rand_frac_for(rng, "B")
        result = f1 / f2 / f3
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}÷{_frac_str(f2)}÷{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E02",
            knowledge_point="分数连除",
            difficulty=difficulty,
            hint="把所有除法变成乘以倒数，一次算",
            exercise_type="ET-0711",
        )
    # C: mixed ÷ ×
    mf = _rand_mixed(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    f3 = _rand_frac_for(rng, "C")
    kind = rng.choice(["div_mul", "mul_div"])
    if kind == "div_mul":
        result = mf / f2 * f3
        return GeneratedProblem(
            problem=f"{_mixed_str(mf)}÷{_frac_str(f2)}×{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E02",
            knowledge_point="分数除乘混合",
            difficulty=difficulty,
            hint="从左到右：先除后乘",
            exercise_type="ET-0711",
        )
    result = mf * f2 / f3
    return GeneratedProblem(
        problem=f"{_mixed_str(mf)}×{_frac_str(f2)}÷{_frac_str(f3)}=",
        correct_answer=_frac_str(result),
        error_code="E02",
        knowledge_point="分数乘除混合",
        difficulty=difficulty,
        hint="从左到右：先乘后除",
        exercise_type="ET-0711",
    )


# ---------------------------------------------------------------------------
# ET-0712: 比与分数综合
# ---------------------------------------------------------------------------

def _gen_ratio_frac_combo(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.randint(2, 8)
        b = rng.randint(2, 8)
        while b == a:
            b = rng.randint(2, 8)
        g = math.gcd(a, b)
        sa, sb = a // g, b // g
        return GeneratedProblem(
            problem=f"把比{a}:{b}化成最简分数",
            correct_answer=f"{sa}/{sb}",
            error_code="E04",
            knowledge_point="比化分数",
            difficulty=difficulty,
            hint="比的前项÷后项=分数",
            exercise_type="ET-0712",
        )
    if difficulty == "B":
        f = _rand_frac_for(rng, "B")
        n = _rand_int_for(rng, "B")
        m = _rand_int_for(rng, "B")
        while m == n:
            m = _rand_int_for(rng, "B")
        total = n + m
        result_a = Fraction(n) * f
        result_b = Fraction(m) * f
        return GeneratedProblem(
            problem=f"把{int(Fraction(total) * f)}按{n}:{m}分配，各是多少？",
            correct_answer=f"{int(result_a)}和{int(result_b)}",
            error_code="E04",
            knowledge_point="分数与比的结合",
            difficulty=difficulty,
            hint="先算总量，再按比分",
            exercise_type="ET-0712",
        )
    # C: comprehensive
    f = _rand_frac_for(rng, "C")
    a = rng.randint(2, 6)
    b = rng.randint(2, 6)
    while b == a:
        b = rng.randint(2, 6)
    c = rng.randint(2, 6)
    total_parts = a + b + c
    base = rng.choice([60, 90, 120, 180])
    total = int(base * f)
    if total <= 0 or total % total_parts != 0:
        total = base
    part_a = total * a // total_parts
    part_b = total * b // total_parts
    part_c = total - part_a - part_b
    return GeneratedProblem(
        problem=f"把{total}按{a}:{b}:{c}分配，求各部分",
        correct_answer=f"{part_a}、{part_b}、{part_c}",
        error_code="E04",
        knowledge_point="三按比分配",
        difficulty=difficulty,
        hint=f"总份数={total_parts}，先算每份，再乘各比例",
        exercise_type="ET-0712",
    )


# ---------------------------------------------------------------------------
# ET-0401: 乘法交换律
# ---------------------------------------------------------------------------

def _gen_shortcut_commutative(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        pairs = [(25, 4, 100), (125, 8, 1000), (50, 2, 100), (25, 8, 200)]
        a, b, _ = rng.choice(pairs)
        c = rng.randint(2, 9)
        result = a * b * c
        return GeneratedProblem(
            problem=f"{a}×{c}×{b}=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="乘法交换律",
            difficulty=difficulty,
            hint=f"交换位置：先算{a}×{b}={a*b}",
            exercise_type="ET-0401",
        )
    if difficulty == "B":
        pairs = [(25, 4, 100), (25, 8, 200), (125, 8, 1000), (125, 4, 500)]
        a, b, _ = rng.choice(pairs)
        c = rng.randint(11, 30)
        result = a * b * c
        return GeneratedProblem(
            problem=f"{a}×{c}×{b}=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="乘法交换律（复杂）",
            difficulty=difficulty,
            hint=f"交换乘数位置，先凑整：{a}×{b}={a*b}",
            exercise_type="ET-0401",
        )
    # C: with fractions
    f = Fraction(1, 4)
    n = rng.randint(2, 9)
    m = rng.choice([4, 8, 12, 16])
    result = f * n * m
    return GeneratedProblem(
        problem=f"{_frac_str(f)}×{n}×{m}=",
        correct_answer=_frac_str(result),
        error_code="E10",
        knowledge_point="乘法交换律（分数）",
        difficulty=difficulty,
        hint=f"交换顺序先算{_frac_str(f)}×{m}，再乘{n}",
        exercise_type="ET-0401",
    )


# ---------------------------------------------------------------------------
# ET-0402: 乘法结合律
# ---------------------------------------------------------------------------

def _gen_shortcut_associative(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        pairs = [(125, 8, 1000), (25, 4, 100), (50, 2, 100), (25, 40, 1000)]
        a, b, _ = rng.choice(pairs)
        c = rng.randint(2, 9)
        result = a * b * c
        return GeneratedProblem(
            problem=f"{a}×({b}×{c})=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="乘法结合律",
            difficulty=difficulty,
            hint=f"先算括号里{b}×{c}，再乘{a}",
            exercise_type="ET-0402",
        )
    if difficulty == "B":
        a = rng.choice([0.125, 0.25, 1.25, 2.5])
        a_frac = Fraction(str(a))
        b = rng.choice([8, 4, 4, 4])
        c = rng.randint(2, 9)
        result = a_frac * b * c
        result_str = _decimal_str(result) if result.denominator != 1 else str(result)
        # check if it's a nice decimal
        if result.denominator != 1:
            try:
                result_str = _decimal_str(result)
            except Exception:
                result_str = _frac_str(result)
        return GeneratedProblem(
            problem=f"{a}×{b}×{c}=",
            correct_answer=result_str,
            error_code="E10",
            knowledge_point="乘法结合律（小数）",
            difficulty=difficulty,
            hint=f"先算{a}×{b}凑整",
            exercise_type="ET-0402",
        )
    # C: with fractions
    f = rng.choice([Fraction(1, 8), Fraction(1, 4), Fraction(3, 4)])
    n = rng.choice([8, 4, 4])
    m = rng.randint(2, 12)
    result = f * n * m
    return GeneratedProblem(
        problem=f"{_frac_str(f)}×{n}×{m}=",
        correct_answer=_frac_str(result),
        error_code="E10",
        knowledge_point="乘法结合律（分数）",
        difficulty=difficulty,
        hint=f"先算{_frac_str(f)}×{n}，再乘{m}",
        exercise_type="ET-0402",
    )


# ---------------------------------------------------------------------------
# ET-0404: 减法性质
# ---------------------------------------------------------------------------

def _gen_shortcut_sub_prop(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.choice([100, 200, 300, 500, 1000])
        b = rng.randint(10, 80)
        c = rng.randint(10, 80)
        while a - b - c < 0:
            c = rng.randint(10, 40)
        result = a - b - c
        return GeneratedProblem(
            problem=f"{a}-{b}-{c}=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="减法性质 a-b-c=a-(b+c)",
            difficulty=difficulty,
            hint=f"先算{b}+{c}={b+c}，再用{a}减",
            exercise_type="ET-0404",
        )
    if difficulty == "B":
        a = rng.choice([100, 200, 500, 1000])
        b = rng.randint(10, 100)
        c = rng.randint(10, 100)
        while a - (b + c) < 0:
            c = rng.randint(10, 50)
        result = a - (b + c)
        return GeneratedProblem(
            problem=f"{a}-({b}+{c})=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="减法性质逆用 a-(b+c)=a-b-c",
            difficulty=difficulty,
            hint=f"去括号：{a}-{b}-{c}",
            exercise_type="ET-0404",
        )
    # C: with decimals
    a = rng.choice([10.0, 20.0, 50.0, 100.0])
    b = round(rng.uniform(1.5, 10.0), 1)
    c = round(rng.uniform(1.5, 10.0), 1)
    a_f, b_f, c_f = Fraction(str(a)), Fraction(str(b)), Fraction(str(c))
    result_f = a_f - b_f - c_f
    result_str = _decimal_str(result_f)
    return GeneratedProblem(
        problem=f"{a}-{b}-{c}=",
        correct_answer=result_str,
        error_code="E10",
        knowledge_point="减法性质（小数）",
        difficulty=difficulty,
        hint=f"先算{b}+{c}={round(b+c, 1)}，再减",
        exercise_type="ET-0404",
    )


# ---------------------------------------------------------------------------
# ET-0405: 除法性质
# ---------------------------------------------------------------------------

def _gen_shortcut_div_prop(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.choice([100, 200, 300, 500, 1000])
        b = rng.choice([2, 4, 5, 10, 25])
        c = rng.choice([2, 4, 5, 10, 25])
        while b * c == 0 or a % (b * c) != 0:
            c = rng.choice([2, 4, 5, 10, 25])
        result = a // b // c
        return GeneratedProblem(
            problem=f"{a}÷{b}÷{c}=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="除法性质 a÷b÷c=a÷(b×c)",
            difficulty=difficulty,
            hint=f"先算{b}×{c}={b*c}，再除",
            exercise_type="ET-0405",
        )
    if difficulty == "B":
        a = rng.choice([100, 200, 500, 1000, 2000])
        b = rng.choice([2, 4, 5, 10, 20, 25])
        c = rng.choice([2, 4, 5, 10, 20, 25])
        while a % (b * c) != 0:
            c = rng.choice([2, 4, 5, 10, 20, 25])
        result = a // (b * c)
        return GeneratedProblem(
            problem=f"{a}÷({b}×{c})=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="除法性质逆用 a÷(b×c)=a÷b÷c",
            difficulty=difficulty,
            hint=f"去括号：{a}÷{b}÷{c}",
            exercise_type="ET-0405",
        )
    # C: with decimals
    a = rng.choice([10.0, 20.0, 50.0, 100.0])
    b = rng.choice([0.5, 2.5, 0.25, 0.2])
    c = rng.choice([2, 4, 5, 10])
    a_f = Fraction(str(a))
    b_f = Fraction(str(b))
    result_f = a_f / b_f / c
    result_str = _decimal_str(result_f)
    return GeneratedProblem(
        problem=f"{a}÷{b}÷{c}=",
        correct_answer=result_str,
        error_code="E10",
        knowledge_point="除法性质（小数）",
        difficulty=difficulty,
        hint=f"先把{b}和{c}乘起来再除",
        exercise_type="ET-0405",
    )


# ---------------------------------------------------------------------------
# ET-0408: 分数简便运算
# ---------------------------------------------------------------------------

def _gen_shortcut_frac(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        f = _rand_frac_for(rng, "A")
        a = rng.randint(2, 9)
        b = rng.randint(2, 9)
        result = f * (a + b)
        return GeneratedProblem(
            problem=f"{_frac_str(f)}×{a}+{_frac_str(f)}×{b}=",
            correct_answer=_frac_str(result),
            error_code="E10",
            knowledge_point="分数分配律",
            difficulty=difficulty,
            hint=f"提取{_frac_str(f)}：{_frac_str(f)}×({a}+{b})",
            exercise_type="ET-0408",
        )
    if difficulty == "B":
        f = _rand_frac_for(rng, "B")
        a = rng.randint(2, 12)
        b = rng.randint(2, 12)
        kind = rng.choice(["forward", "reverse"])
        if kind == "forward":
            result = f * (a - b) if a > b else f * (b - a)
            hi, lo = max(a, b), min(a, b)
            return GeneratedProblem(
                problem=f"{_frac_str(f)}×{hi}-{_frac_str(f)}×{lo}=",
                correct_answer=_frac_str(result),
                error_code="E10",
                knowledge_point="分数分配律（减法）",
                difficulty=difficulty,
                hint=f"提取{_frac_str(f)}：{_frac_str(f)}×({hi}-{lo})",
                exercise_type="ET-0408",
            )
        c = rng.randint(2, 9)
        result = f * a + f * b + f * c
        return GeneratedProblem(
            problem=f"{_frac_str(f)}×{a}+{_frac_str(f)}×{b}+{_frac_str(f)}×{c}=",
            correct_answer=_frac_str(result),
            error_code="E10",
            knowledge_point="分数分配律（三项）",
            difficulty=difficulty,
            hint=f"提取{_frac_str(f)}：{_frac_str(f)}×({a}+{b}+{c})",
            exercise_type="ET-0408",
        )
    # C: complex cases
    f1 = _rand_frac_for(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    n = rng.randint(2, 12)
    # f1×n + f2×n = (f1+f2)×n
    result = (f1 + f2) * n
    return GeneratedProblem(
        problem=f"{_frac_str(f1)}×{n}+{_frac_str(f2)}×{n}=",
        correct_answer=_frac_str(result),
        error_code="E10",
        knowledge_point="分数简便运算（不同分数同因数）",
        difficulty=difficulty,
        hint=f"提取公因数{n}：({_frac_str(f1)}+{_frac_str(f2)})×{n}",
        exercise_type="ET-0408",
    )


# ---------------------------------------------------------------------------
# ET-0901: 化简比
# ---------------------------------------------------------------------------

def _gen_ratio_simplify(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        g = rng.randint(2, 8)
        a = g * rng.randint(2, 6)
        b = g * rng.randint(2, 6)
        while b == a:
            b = g * rng.randint(2, 6)
        sa, sb = _simplify_int_ratio(a, b)
        return GeneratedProblem(
            problem=f"化简比 {a}:{b}",
            correct_answer=f"{sa}:{sb}",
            error_code="E04",
            knowledge_point="化简整数比",
            difficulty=difficulty,
            hint="找最大公因数，同时除以它",
            exercise_type="ET-0901",
        )
    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        while f1 == f2:
            f2 = _rand_frac_for(rng, "B")
        a, b = _simplify_frac_ratio(f1, f2)
        return GeneratedProblem(
            problem=f"化简比 {_frac_str(f1)}:{_frac_str(f2)}",
            correct_answer=f"{a}:{b}",
            error_code="E04",
            knowledge_point="化简分数比",
            difficulty=difficulty,
            hint="先通分再化简",
            exercise_type="ET-0901",
        )
    # C: decimal ratios
    a_dec = round(rng.uniform(0.2, 5.0), 1)
    b_dec = round(rng.uniform(0.2, 5.0), 1)
    while b_dec == a_dec:
        b_dec = round(rng.uniform(0.2, 5.0), 1)
    a_f = Fraction(str(a_dec))
    b_f = Fraction(str(b_dec))
    sa, sb = _simplify_frac_ratio(a_f, b_f)
    return GeneratedProblem(
        problem=f"化简比 {a_dec}:{b_dec}",
        correct_answer=f"{sa}:{sb}",
        error_code="E04",
        knowledge_point="化简小数比",
        difficulty=difficulty,
        hint="先把小数化成整数再化简",
        exercise_type="ET-0901",
    )


# ---------------------------------------------------------------------------
# ET-0902: 求比值
# ---------------------------------------------------------------------------

def _gen_ratio_value(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.randint(2, 12)
        b = rng.randint(2, 12)
        while b == a:
            b = rng.randint(2, 12)
        result = Fraction(a, b)
        return GeneratedProblem(
            problem=f"求比值 {a}:{b}",
            correct_answer=_frac_str(result),
            error_code="E04",
            knowledge_point="求比值（整数）",
            difficulty=difficulty,
            hint="比值=前项÷后项",
            exercise_type="ET-0902",
        )
    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        while f2 == 0:
            f2 = _rand_frac_for(rng, "B")
        result = f1 / f2
        return GeneratedProblem(
            problem=f"求比值 {_frac_str(f1)}:{_frac_str(f2)}",
            correct_answer=_frac_str(result),
            error_code="E04",
            knowledge_point="求比值（分数）",
            difficulty=difficulty,
            hint="前项÷后项，用分数表示",
            exercise_type="ET-0902",
        )
    # C: complex ratios
    mf1 = _rand_mixed(rng, "C")
    mf2 = _rand_mixed(rng, "C")
    while mf2 == 0:
        mf2 = _rand_mixed(rng, "C")
    result = mf1 / mf2
    return GeneratedProblem(
        problem=f"求比值 {_mixed_str(mf1)}:{_mixed_str(mf2)}",
        correct_answer=_frac_str(result),
        error_code="E04",
        knowledge_point="求比值（带分数）",
        difficulty=difficulty,
        hint="先化成假分数再除",
        exercise_type="ET-0902",
    )


# ---------------------------------------------------------------------------
# ET-0903: 按比分配
# ---------------------------------------------------------------------------

def _gen_ratio_distribute(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.randint(1, 5)
        b = rng.randint(1, 5)
        while b == a:
            b = rng.randint(1, 5)
        k = rng.randint(3, 10)
        total = (a + b) * k
        ask = rng.choice(["large", "small", "total_check"])
        if ask == "large":
            return GeneratedProblem(
                problem=f"把{total}按{a}:{b}分配，较大数是多少？",
                correct_answer=str(k * max(a, b)),
                error_code="E04",
                knowledge_point="按比分配（简单）",
                difficulty=difficulty,
                hint=f"总份数={a+b}，每份={k}",
                exercise_type="ET-0903",
            )
        if ask == "small":
            return GeneratedProblem(
                problem=f"把{total}按{a}:{b}分配，较小数是多少？",
                correct_answer=str(k * min(a, b)),
                error_code="E04",
                knowledge_point="按比分配（简单）",
                difficulty=difficulty,
                hint=f"总份数={a+b}，每份={k}",
                exercise_type="ET-0903",
            )
        return GeneratedProblem(
            problem=f"把{total}按{a}:{b}分配，各是多少？",
            correct_answer=f"{k*a}和{k*b}",
            error_code="E04",
            knowledge_point="按比分配",
            difficulty=difficulty,
            hint=f"总份数={a+b}，先算每份",
            exercise_type="ET-0903",
        )
    if difficulty == "B":
        a = rng.randint(1, 5)
        b = rng.randint(1, 5)
        c = rng.randint(1, 5)
        while c == a or c == b:
            c = rng.randint(1, 5)
        total_parts = a + b + c
        base = rng.choice([60, 90, 120, 180])
        pa, pb, pc = base * a // total_parts, base * b // total_parts, base * c // total_parts
        return GeneratedProblem(
            problem=f"把{base}按{a}:{b}:{c}分配，求各部分",
            correct_answer=f"{pa}、{pb}、{pc}",
            error_code="E04",
            knowledge_point="三按比分配",
            difficulty=difficulty,
            hint=f"总份数={total_parts}，先算每份",
            exercise_type="ET-0903",
        )
    # C: with fractions
    f = _rand_frac_for(rng, "C")
    a = rng.randint(1, 4)
    b = rng.randint(1, 4)
    while b == a:
        b = rng.randint(1, 4)
    k = rng.randint(3, 8)
    total = int(Fraction(k * (a + b)) * f)
    if total <= 0:
        total = k * (a + b)
    part_a = total * a // (a + b)
    part_b = total - part_a
    return GeneratedProblem(
        problem=f"把{total}按{a}:{b}分配",
        correct_answer=f"{part_a}和{part_b}",
        error_code="E04",
        knowledge_point="按比分配（分数）",
        difficulty=difficulty,
        hint="先算总份数和每份的量",
        exercise_type="ET-0903",
    )


# ---------------------------------------------------------------------------
# ET-0904: 比例尺计算
# ---------------------------------------------------------------------------

def _gen_ratio_scale(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        scale_choices = [100, 1000, 5000, 10000]
        scale = rng.choice(scale_choices)
        map_dist = rng.randint(1, 10)
        real_dist = map_dist * scale
        return GeneratedProblem(
            problem=f"比例尺1:{scale}，图上距离{map_dist}cm，实际距离是多少cm？",
            correct_answer=f"{real_dist}cm",
            error_code="E07",
            knowledge_point="比例尺计算（基础）",
            difficulty=difficulty,
            hint="实际距离=图上距离×比例尺分母",
            exercise_type="ET-0904",
        )
    if difficulty == "B":
        scale_choices = [1000, 5000, 10000, 50000, 100000]
        scale = rng.choice(scale_choices)
        real_m = rng.choice([50, 100, 200, 500, 1000])
        real_cm = real_m * 100
        map_cm = Fraction(real_cm, scale)
        return GeneratedProblem(
            problem=f"比例尺1:{scale}，实际距离{real_m}m，图上距离是多少cm？",
            correct_answer=f"{_frac_str(map_cm)}cm",
            error_code="E07",
            knowledge_point="比例尺计算（反求）",
            difficulty=difficulty,
            hint="图上距离=实际距离÷比例尺分母",
            exercise_type="ET-0904",
        )
    # C: area scale
    scale = rng.choice([100, 200, 500, 1000])
    map_area = rng.randint(1, 20)
    real_area = map_area * scale * scale
    return GeneratedProblem(
        problem=f"比例尺1:{scale}，图上面积{map_area}cm²，实际面积是多少cm²？",
        correct_answer=f"{real_area}cm²",
        error_code="E07",
        knowledge_point="比例尺面积换算",
        difficulty=difficulty,
        hint="面积比=比例尺的平方",
        exercise_type="ET-0904",
    )


# ---------------------------------------------------------------------------
# ET-0905: 正比例应用
# ---------------------------------------------------------------------------

def _gen_ratio_direct_prop(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        k = rng.randint(2, 10)
        x = rng.randint(1, 10)
        y = k * x
        return GeneratedProblem(
            problem=f"y与x成正比例，当x=1时y={k}，当x={x}时y=？",
            correct_answer=str(y),
            error_code="E05",
            knowledge_point="正比例（基础）",
            difficulty=difficulty,
            hint=f"y=kx，k={k}",
            exercise_type="ET-0905",
        )
    if difficulty == "B":
        x1 = rng.randint(2, 6)
        y1 = x1 * rng.randint(2, 5)
        x2 = rng.randint(7, 15)
        k = Fraction(y1, x1)
        y2 = k * x2
        return GeneratedProblem(
            problem=f"y与x成正比例，x={x1}时y={y1}，x={x2}时y=？",
            correct_answer=_frac_str(y2),
            error_code="E05",
            knowledge_point="正比例（分数）",
            difficulty=difficulty,
            hint=f"先求k=y÷x={_frac_str(k)}，再算y=k×{x2}",
            exercise_type="ET-0905",
        )
    # C: word-style
    items = rng.choice(["苹果", "铅笔", "笔记本"])
    price = rng.randint(3, 15)
    qty1 = rng.randint(2, 5)
    qty2 = rng.randint(6, 15)
    total = price * qty2
    return GeneratedProblem(
        problem=f"买{qty1}个{items}需要{price*qty1}元，买{qty2}个需要多少元？",
        correct_answer=f"{total}元",
        error_code="E05",
        knowledge_point="正比例应用题",
        difficulty=difficulty,
        hint=f"总价和数量成正比例，先算单价",
        exercise_type="ET-0905",
    )


# ---------------------------------------------------------------------------
# ET-0906: 反比例应用
# ---------------------------------------------------------------------------

def _gen_ratio_inverse_prop(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        k = rng.choice([12, 24, 30, 36, 48, 60])
        x1 = rng.randint(2, 6)
        while k % x1 != 0:
            x1 = rng.randint(2, 6)
        y1 = k // x1
        x2 = rng.randint(2, 12)
        while k % x2 != 0 or x2 == x1:
            x2 = rng.randint(2, 12)
        y2 = k // x2
        return GeneratedProblem(
            problem=f"x与y成反比例，x={x1}时y={y1}，x={x2}时y=？",
            correct_answer=str(y2),
            error_code="E05",
            knowledge_point="反比例（基础）",
            difficulty=difficulty,
            hint=f"xy={k}（一定），y={k}÷{x2}",
            exercise_type="ET-0906",
        )
    if difficulty == "B":
        k = rng.choice([12, 24, 30, 36, 60])
        x1 = rng.randint(2, 6)
        while k % x1 != 0:
            x1 = rng.randint(2, 6)
        y1 = k // x1
        x2 = rng.choice([2, 3, 4, 5, 6, 8, 10, 12])
        y2 = Fraction(k, x2)
        return GeneratedProblem(
            problem=f"x与y成反比例，x={x1}时y={y1}，x={x2}时y=？",
            correct_answer=_frac_str(y2),
            error_code="E05",
            knowledge_point="反比例（分数结果）",
            difficulty=difficulty,
            hint=f"xy={k}，y={k}÷x",
            exercise_type="ET-0906",
        )
    # C: word-style
    workers = rng.randint(3, 8)
    days1 = rng.randint(5, 15)
    total_work = workers * days1
    workers2 = rng.randint(2, 10)
    while workers2 == workers:
        workers2 = rng.randint(2, 10)
    days2 = Fraction(total_work, workers2)
    return GeneratedProblem(
        problem=f"{workers}人做一项工程需要{days1}天，{workers2}人需要多少天？",
        correct_answer=_frac_str(days2) if days2.denominator != 1 else str(days2),
        error_code="E05",
        knowledge_point="反比例应用题",
        difficulty=difficulty,
        hint="人数和天数成反比例，总工作量不变",
        exercise_type="ET-0906",
    )


# ---------------------------------------------------------------------------
# ET-0409: 加减法凑整
# ---------------------------------------------------------------------------

def _gen_shortcut_round_int(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.choice([27, 37, 47, 57, 67, 87, 97])
        complement = 100 - a
        b = rng.randint(10, 80)
        result = a + b + complement
        return GeneratedProblem(
            problem=f"{a}+{complement}+{b}=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="凑整加法",
            difficulty=difficulty,
            hint=f"{a}+{complement}=100，再加{b}",
            exercise_type="ET-0409",
        )
    if difficulty == "B":
        a = rng.choice([127, 137, 147, 157, 167, 187, 197])
        complement = 200 - a
        b = rng.randint(20, 150)
        result = a + b + complement
        return GeneratedProblem(
            problem=f"{a}+{b}+{complement}=",
            correct_answer=str(result),
            error_code="E10",
            knowledge_point="凑整加法（进阶）",
            difficulty=difficulty,
            hint=f"找到凑整的配对：{a}+{complement}={a+complement}",
            exercise_type="ET-0409",
        )
    # C: subtraction rounding
    a = rng.choice([100, 200, 500, 1000])
    b = rng.choice([27, 37, 47, 57, 67, 87, 97])
    c = a - b
    result = c
    return GeneratedProblem(
        problem=f"{a}-{b}-{c}=",
        correct_answer="0",
        error_code="E10",
        knowledge_point="凑整减法",
        difficulty=difficulty,
        hint=f"先看{a}-{b}={c}，再减{c}等于0",
        exercise_type="ET-0409",
    )


# ---------------------------------------------------------------------------
# ET-0410: 小数简便运算
# ---------------------------------------------------------------------------

def _gen_shortcut_decimal(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.choice([2.5, 1.25, 0.5, 7.5])
        a_f = Fraction(str(a))
        b = rng.choice([4, 8, 2, 4])
        result = a_f * b
        return GeneratedProblem(
            problem=f"{a}×{b}=",
            correct_answer=_decimal_str(result),
            error_code="E10",
            knowledge_point="小数凑整乘法",
            difficulty=difficulty,
            hint=f"{a}×{b}直接计算，注意小数点",
            exercise_type="ET-0410",
        )
    if difficulty == "B":
        a_str, a_f = rng.choice(_DECIMAL_POOL_B)
        n = rng.randint(2, 12)
        m = rng.randint(2, 12)
        result = a_f * n + a_f * m
        return GeneratedProblem(
            problem=f"{a_str}×{n}+{a_str}×{m}=",
            correct_answer=_decimal_str(result),
            error_code="E10",
            knowledge_point="小数分配律",
            difficulty=difficulty,
            hint=f"提取{a_str}：{a_str}×({n}+{m})",
            exercise_type="ET-0410",
        )
    # C: distributive with decimals
    a_str, a_f = rng.choice(_DECIMAL_POOL)
    n = rng.randint(2, 15)
    m = rng.randint(2, 15)
    kind = rng.choice(["forward", "reverse"])
    if kind == "forward":
        result = a_f * (n + m)
        return GeneratedProblem(
            problem=f"{a_str}×({n}+{m})=",
            correct_answer=_decimal_str(result),
            error_code="E10",
            knowledge_point="小数分配律（正向）",
            difficulty=difficulty,
            hint=f"分配展开：{a_str}×{n}+{a_str}×{m}",
            exercise_type="ET-0410",
        )
    result = a_f * n + a_f * m
    return GeneratedProblem(
        problem=f"{a_str}×{n}+{a_str}×{m}=",
        correct_answer=_decimal_str(result),
        error_code="E10",
        knowledge_point="小数分配律（逆向）",
        difficulty=difficulty,
        hint=f"提取{a_str}：{a_str}×({n}+{m})",
        exercise_type="ET-0410",
    )


# ---------------------------------------------------------------------------
# ET-0205: 小数加减竖式
# ---------------------------------------------------------------------------

def _gen_vertical_decimal_add_sub(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = round(rng.uniform(1.0, 10.0), 1)
        b = round(rng.uniform(1.0, 10.0), 1)
        op = rng.choice(["+", "-"])
        if op == "-":
            a, b = max(a, b), min(a, b)
        result_f = Fraction(str(a)) + Fraction(str(b)) if op == "+" else Fraction(str(a)) - Fraction(str(b))
        return GeneratedProblem(
            problem=f"竖式计算 {a}{op}{b}=",
            correct_answer=_decimal_str(result_f),
            error_code="E01",
            knowledge_point="小数竖式加减",
            difficulty=difficulty,
            hint="小数点对齐，逐位加减",
            exercise_type="ET-0205",
        )
    if difficulty == "B":
        a = round(rng.uniform(10.0, 100.0), 2)
        b = round(rng.uniform(1.0, 50.0), 2)
        op = rng.choice(["+", "-"])
        if op == "-":
            a, b = max(a, b), min(a, b)
        result_f = Fraction(str(a)) + Fraction(str(b)) if op == "+" else Fraction(str(a)) - Fraction(str(b))
        return GeneratedProblem(
            problem=f"竖式计算 {a}{op}{b}=",
            correct_answer=_decimal_str(result_f),
            error_code="E01",
            knowledge_point="小数竖式加减（两位小数）",
            difficulty=difficulty,
            hint="小数点对齐，逐位加减，注意进退位",
            exercise_type="ET-0205",
        )
    # C: three numbers
    a = round(rng.uniform(10.0, 100.0), 2)
    b = round(rng.uniform(1.0, 50.0), 2)
    c = round(rng.uniform(1.0, 30.0), 2)
    op1 = rng.choice(["+", "-"])
    op2 = rng.choice(["+", "-"])
    a_f, b_f, c_f = Fraction(str(a)), Fraction(str(b)), Fraction(str(c))
    if op1 == "+":
        mid = a_f + b_f
    else:
        mid = a_f - b_f if a_f > b_f else b_f - a_f
    if op2 == "+":
        result = mid + c_f
    else:
        result = mid - c_f if mid > c_f else c_f - mid
    return GeneratedProblem(
        problem=f"竖式计算 {a}{op1}{b}{op2}{c}=",
        correct_answer=_decimal_str(result),
        error_code="E01",
        knowledge_point="小数竖式加减（三个数）",
        difficulty=difficulty,
        hint="从左到右依次计算",
        exercise_type="ET-0205",
    )


# ---------------------------------------------------------------------------
# ET-0206: 小数乘除竖式
# ---------------------------------------------------------------------------

def _gen_vertical_decimal_mul_div(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = round(rng.uniform(1.0, 5.0), 1)
        b = rng.randint(2, 9)
        op = rng.choice(["×", "÷"])
        if op == "×":
            result = Fraction(str(a)) * b
            return GeneratedProblem(
                problem=f"竖式计算 {a}×{b}=",
                correct_answer=_decimal_str(result),
                error_code="E01",
                knowledge_point="小数竖式乘法",
                difficulty=difficulty,
                hint="先按整数乘，再数小数位数点小数点",
                exercise_type="ET-0206",
            )
        # division: make sure divisible
        a_int = int(a * 10)
        if a_int % b != 0:
            a_int = b * rng.randint(2, 10)
        a = Fraction(a_int, 10)
        result = a / b
        return GeneratedProblem(
            problem=f"竖式计算 {_decimal_str(a)}÷{b}=",
            correct_answer=_decimal_str(result),
            error_code="E01",
            knowledge_point="小数竖式除法",
            difficulty=difficulty,
            hint="移动小数点转化为整数除法",
            exercise_type="ET-0206",
        )
    if difficulty == "B":
        a = round(rng.uniform(1.0, 10.0), 2)
        b = round(rng.uniform(1.0, 5.0), 1)
        op = rng.choice(["×", "÷"])
        if op == "×":
            result = Fraction(str(a)) * Fraction(str(b))
            return GeneratedProblem(
                problem=f"竖式计算 {a}×{b}=",
                correct_answer=_decimal_str(result),
                error_code="E01",
                knowledge_point="小数竖式乘法（两位）",
                difficulty=difficulty,
                hint="先按整数乘法算，再点小数点",
                exercise_type="ET-0206",
            )
        # division by decimal: a * 10 / (b * 10)
        a_f = Fraction(str(a))
        b_f = Fraction(str(b))
        result = a_f / b_f
        return GeneratedProblem(
            problem=f"竖式计算 {a}÷{b}=",
            correct_answer=_frac_str(result) if result.denominator not in (1, 2, 4, 5, 8, 10, 20, 25, 50, 100) else _decimal_str(result),
            error_code="E01",
            knowledge_point="小数竖式除法（两位）",
            difficulty=difficulty,
            hint="先把除数变整数，被除数同时扩大",
            exercise_type="ET-0206",
        )
    # C: multi-digit
    a = round(rng.uniform(10.0, 50.0), 2)
    b = round(rng.uniform(1.0, 10.0), 1)
    op = rng.choice(["×", "÷"])
    if op == "×":
        result = Fraction(str(a)) * Fraction(str(b))
        return GeneratedProblem(
            problem=f"竖式计算 {a}×{b}=",
            correct_answer=_decimal_str(result),
            error_code="E01",
            knowledge_point="小数竖式乘法（复杂）",
            difficulty=difficulty,
            hint="先按整数乘，再数总共几位小数",
            exercise_type="ET-0206",
        )
    a_f = Fraction(str(a))
    b_f = Fraction(str(b))
    result = a_f / b_f
    ans = _decimal_str(result)
    if "/" in ans:
        ans = _frac_str(result)
    return GeneratedProblem(
        problem=f"竖式计算 {a}÷{b}=",
        correct_answer=ans,
        error_code="E01",
        knowledge_point="小数竖式除法（复杂）",
        difficulty=difficulty,
        hint="移动小数点转化为整数除法",
        exercise_type="ET-0206",
    )


# ---------------------------------------------------------------------------
# ET-0606: 不规则图形面积估算
# ---------------------------------------------------------------------------

def _gen_geo_irregular(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        # Count full squares on a grid
        full = rng.randint(4, 12)
        half = rng.randint(2, 6)
        area = full + half * Fraction(1, 2)
        return GeneratedProblem(
            problem=f"在方格纸上，不规则图形占{full}个完整格和{half}个半格，面积约多少？",
            correct_answer=f"{_frac_str(area)}个方格",
            error_code="E07",
            knowledge_point="不规则图形面积估算（数格法）",
            difficulty=difficulty,
            hint="完整格+半格÷2",
            exercise_type="ET-0606",
        )
    if difficulty == "B":
        # Approximate as combination of known shapes
        w = rng.randint(3, 8)
        h = rng.randint(3, 8)
        r = min(w, h) // 2
        area = Fraction(w * h - r * r * 314, 100)  # approximate
        return GeneratedProblem(
            problem=f"一个不规则图形可近似看作长{w}cm宽{h}cm的矩形减去半径{r}cm的半圆（π≈3.14），面积约多少？",
            correct_answer=f"{float(w*h) - 3.14*r*r/2:.2f}cm²",
            error_code="E07",
            knowledge_point="不规则图形面积（割补法）",
            difficulty=difficulty,
            hint="矩形面积减去半圆面积",
            exercise_type="ET-0606",
        )
    # C: grid approximation with rule
    full = rng.randint(8, 20)
    partial = rng.randint(6, 15)
    area = full + Fraction(partial, 2)
    return GeneratedProblem(
        problem=f"用数格法估算面积：{full}个完整格+{partial}个不满格（每个算半格），面积约为？",
        correct_answer=f"{_frac_str(area)}个方格",
        error_code="E07",
        knowledge_point="不规则图形面积估算（不满半格算半）",
        difficulty=difficulty,
        hint="不满半格算半格（或超过半格算一格）",
        exercise_type="ET-0606",
    )


# ---------------------------------------------------------------------------
# ET-0607: 长方体/正方体表面积
# ---------------------------------------------------------------------------

def _gen_geo_box_surface(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.randint(2, 5)
        result = 6 * a * a
        return GeneratedProblem(
            problem=f"棱长{a}cm的正方体表面积",
            correct_answer=f"{result}cm²",
            error_code="E07",
            knowledge_point="正方体表面积",
            difficulty=difficulty,
            hint="正方体表面积=6×棱长²",
            exercise_type="ET-0607",
        )
    if difficulty == "B":
        a = rng.randint(2, 6)
        b = rng.randint(2, 6)
        c = rng.randint(2, 6)
        result = 2 * (a * b + b * c + a * c)
        return GeneratedProblem(
            problem=f"长{a}cm、宽{b}cm、高{c}cm的长方体表面积",
            correct_answer=f"{result}cm²",
            error_code="E07",
            knowledge_point="长方体表面积",
            difficulty=difficulty,
            hint="长方体表面积=2(长×宽+宽×高+长×高)",
            exercise_type="ET-0607",
        )
    # C: missing face
    a = rng.randint(3, 8)
    b = rng.randint(3, 8)
    c = rng.randint(3, 8)
    full = 2 * (a * b + b * c + a * c)
    missing = a * b
    result = full - missing
    return GeneratedProblem(
        problem=f"长{a}cm宽{b}cm高{c}cm的无盖长方体（缺一个{a}×{b}的面），表面积",
        correct_answer=f"{result}cm²",
        error_code="E07",
        knowledge_point="长方体表面积（缺面）",
        difficulty=difficulty,
        hint="完整表面积减去缺少的面",
        exercise_type="ET-0607",
    )


# ---------------------------------------------------------------------------
# ET-0608: 长方体/正方体体积
# ---------------------------------------------------------------------------

def _gen_geo_box_volume(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        a = rng.randint(2, 6)
        result = a * a * a
        return GeneratedProblem(
            problem=f"棱长{a}cm的正方体体积",
            correct_answer=f"{result}cm³",
            error_code="E07",
            knowledge_point="正方体体积",
            difficulty=difficulty,
            hint="正方体体积=棱长³",
            exercise_type="ET-0608",
        )
    if difficulty == "B":
        a = rng.randint(2, 8)
        b = rng.randint(2, 8)
        c = rng.randint(2, 8)
        result = a * b * c
        return GeneratedProblem(
            problem=f"长{a}cm、宽{b}cm、高{c}cm的长方体体积",
            correct_answer=f"{result}cm³",
            error_code="E07",
            knowledge_point="长方体体积",
            difficulty=difficulty,
            hint="长方体体积=长×宽×高",
            exercise_type="ET-0608",
        )
    # C: volume with decimal dimensions
    a = round(rng.uniform(1.5, 5.0), 1)
    b = round(rng.uniform(1.5, 5.0), 1)
    c = rng.randint(2, 8)
    result = Fraction(str(a)) * Fraction(str(b)) * c
    result_str = _decimal_str(result)
    return GeneratedProblem(
        problem=f"长{a}cm、宽{b}cm、高{c}cm的长方体体积",
        correct_answer=f"{result_str}cm³",
        error_code="E07",
        knowledge_point="长方体体积（小数边长）",
        difficulty=difficulty,
        hint="体积=长×宽×高，注意小数计算",
        exercise_type="ET-0608",
    )


# ---------------------------------------------------------------------------
# ET-0609: 圆柱表面积
# ---------------------------------------------------------------------------

def _gen_geo_cylinder_surface(rng: random.Random, difficulty: str) -> GeneratedProblem:
    if difficulty == "A":
        r = rng.randint(2, 5)
        h = rng.randint(5, 10)
        side = 2 * r * h
        bases = 2 * r * r
        return GeneratedProblem(
            problem=f"底面半径{r}cm、高{h}cm的圆柱表面积（用π表示）",
            correct_answer=f"({side}+{bases})π cm²" if bases > 1 else f"({side}+1)π cm²",
            error_code="E07",
            knowledge_point="圆柱表面积",
            difficulty=difficulty,
            hint="圆柱表面积=侧面积(2πrh)+底面积(2πr²)",
            exercise_type="ET-0609",
        )
    if difficulty == "B":
        r = rng.randint(2, 6)
        h = rng.randint(5, 15)
        coeff = 2 * r * h + 2 * r * r
        return GeneratedProblem(
            problem=f"底面半径{r}cm、高{h}cm的圆柱表面积（用π表示）",
            correct_answer=f"{coeff}π cm²",
            error_code="E07",
            knowledge_point="圆柱表面积（化简）",
            difficulty=difficulty,
            hint=f"2πr(h+r)={coeff}π",
            exercise_type="ET-0609",
        )
    # C: lateral only or with π≈3.14
    r = rng.randint(2, 6)
    h = rng.randint(5, 15)
    coeff = 2 * r * h + 2 * r * r
    area_val = round(coeff * 3.14, 2)
    return GeneratedProblem(
        problem=f"底面半径{r}cm、高{h}cm的圆柱表面积（π≈3.14）",
        correct_answer=f"{area_val}cm²",
        error_code="E07",
        knowledge_point="圆柱表面积（数值计算）",
        difficulty=difficulty,
        hint=f"2×3.14×{r}×({h}+{r})",
        exercise_type="ET-0609",
    )


_EXERCISE_TYPE_GENERATORS: dict[str, type] = {
    "ET-0101": _gen_mental_int_add,
    "ET-0103": _gen_mental_int_mul,
    "ET-0104": _gen_mental_decimal,
    "ET-0105": _gen_mental_fraction,
    "ET-0106": _gen_mental_percent,
    "ET-0107": _gen_mental_mixed,
    "ET-0201": _gen_vertical_add_sub,
    "ET-0202": _gen_vertical_mul,
    "ET-0203": _gen_vertical_mul,
    "ET-0204": _gen_vertical_div,
    "ET-0301": _gen_step_int,
    "ET-0302": _gen_step_int,
    "ET-0303": _gen_step_decimal,
    "ET-0304": _gen_step_fraction,
    "ET-0305": _gen_step_mixed,
    "ET-0403": _gen_shortcut_distrib,
    "ET-0406": _gen_shortcut_round,
    "ET-0407": _gen_shortcut_decompose,
    "ET-0501": _gen_word_int,
    "ET-0502": _gen_word_frac,
    "ET-0503": _gen_word_pct,
    "ET-0504": _gen_word_ratio,
    "ET-0505": _gen_word_comprehensive,
    "ET-0601": _gen_geo_circle_perimeter,
    "ET-0602": _gen_geo_circle_area,
    "ET-0603": _gen_geo_annulus,
    "ET-0604": _gen_geo_sector,
    "ET-0605": _gen_geo_composite,
    "ET-0610": _gen_geo_cylinder_volume,
    "ET-0611": _gen_geo_cone_volume,
    "ET-0702": _gen_frac_add_sub,
    "ET-0706": _gen_frac_convert,
    "ET-0707": _gen_frac_convert,
    "ET-0801": _gen_unit_convert,
    "ET-0802": _gen_unit_convert,
    "ET-0803": _gen_unit_convert,
    "ET-0804": _gen_unit_convert,
    "ET-0805": _gen_unit_convert,
    "ET-0806": _gen_estimate,
    # Fraction operations (分数运算)
    "ET-0701": _gen_frac_same_denom,
    "ET-0703": _gen_frac_mul,
    "ET-0704": _gen_frac_div,
    "ET-0705": _gen_frac_mixed_ops,
    "ET-0708": _gen_frac_complex_simplify,
    "ET-0709": _gen_mixed_number_add_sub,
    "ET-0710": _gen_frac_chain_mul,
    "ET-0711": _gen_frac_chain_div,
    "ET-0712": _gen_ratio_frac_combo,
    # Shortcut/clever calculation (简便运算)
    "ET-0401": _gen_shortcut_commutative,
    "ET-0402": _gen_shortcut_associative,
    "ET-0404": _gen_shortcut_sub_prop,
    "ET-0405": _gen_shortcut_div_prop,
    "ET-0408": _gen_shortcut_frac,
    "ET-0409": _gen_shortcut_round_int,
    "ET-0410": _gen_shortcut_decimal,
    # Ratio & proportion (比与比例)
    "ET-0901": _gen_ratio_simplify,
    "ET-0902": _gen_ratio_value,
    "ET-0903": _gen_ratio_distribute,
    "ET-0904": _gen_ratio_scale,
    "ET-0905": _gen_ratio_direct_prop,
    "ET-0906": _gen_ratio_inverse_prop,
    # Vertical decimal & geometry (竖式/图形)
    "ET-0205": _gen_vertical_decimal_add_sub,
    "ET-0206": _gen_vertical_decimal_mul_div,
    "ET-0606": _gen_geo_irregular,
    "ET-0607": _gen_geo_box_surface,
    "ET-0608": _gen_geo_box_volume,
    "ET-0609": _gen_geo_cylinder_surface,
}


def generate_problems_by_exercise_type(
    exercise_type_id: str,
    difficulty: str = "B",
    count: int = 5,
    seed: int | None = None,
) -> list[GeneratedProblem]:
    gen = _EXERCISE_TYPE_GENERATORS.get(exercise_type_id)
    if gen is None:
        return []
    rng = random.Random(seed)
    results: list[GeneratedProblem] = []
    seen: set[str] = set()
    attempts = 0
    while len(results) < count and attempts < count * 20:
        p = gen(rng, difficulty)
        if p.problem not in seen:
            seen.add(p.problem)
            results.append(p)
        attempts += 1
    return results

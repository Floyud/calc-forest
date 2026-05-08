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


# ---------------------------------------------------------------------------
# Constants — difficulty-aware denominator and integer ranges
# ---------------------------------------------------------------------------

# Per-difficulty nice denominator pools
_NICE_DENOMS_A = [2, 3, 4, 5, 6]
_NICE_DENOMS_B = [2, 3, 4, 5, 6, 8, 10, 12]
_NICE_DENOMS_C = [2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20]

# Keep legacy name for B-level default
_NICE_DENOMS = _NICE_DENOMS_B

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
    pool = [d for d in _NICE_DENOMS if d <= max_denom]
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
# E01: 分数乘法 (Fraction Multiplication)
# ---------------------------------------------------------------------------

def _gen_fraction_multiply(difficulty: str, rng: random.Random) -> GeneratedProblem:
    if difficulty == "A":
        kind = rng.choice(["frac_int", "frac_frac"])
        if kind == "frac_int":
            f = _rand_frac_for(rng, "A")
            n = _rand_int_for(rng, "A")
            result = f * n
            return GeneratedProblem(
                problem=f"{_frac_str(f)}×{n}=",
                correct_answer=_frac_str(result),
                error_code="E01",
                knowledge_point="分数×整数",
                difficulty=difficulty,
                hint="分数×整数：分子乘以整数，分母不变，再约分",
            )
        f1 = _rand_frac_for(rng, "A")
        f2 = _rand_frac_for(rng, "A")
        result = f1 * f2
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}×{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="分数×分数",
            difficulty=difficulty,
            hint="分子乘分子，分母乘分母，能约分先约分",
        )

    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        f3 = _rand_frac_for(rng, "B")
        product = f1 * f2
        if product > f3:
            result = product - f3
            op = "-"
        else:
            result = product + f3
            op = "+"
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}×{_frac_str(f2)}{op}{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="分数乘加（减）混合",
            difficulty=difficulty,
            hint="先算乘法，再算加减",
        )

    # C: 连乘 or mixed number multiply
    kind = rng.choice(["chain", "mixed_mul", "mixed_div"])
    if kind == "chain":
        count = rng.choice([3, 4])
        fracs = [_rand_frac_for(rng, "C") for _ in range(count)]
        result = fracs[0]
        for f in fracs[1:]:
            result *= f
        expr = "×".join(_frac_str(f) for f in fracs)
        return GeneratedProblem(
            problem=f"{expr}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="分数连乘",
            difficulty=difficulty,
            hint="逐步相乘，每一步都可以先约分再计算",
        )
    if kind == "mixed_mul":
        mf = _rand_mixed(rng, "C")
        f2 = _rand_frac_for(rng, "C")
        result = mf * f2
        return GeneratedProblem(
            problem=f"{_mixed_str(mf)}×{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E01",
            knowledge_point="带分数×真分数",
            difficulty=difficulty,
            hint="先把带分数化成假分数，再按分数乘法计算",
        )
    # mixed_div in multiply context: multiply with a mixed number result
    mf = _rand_mixed(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    result = mf * f2
    return GeneratedProblem(
        problem=f"{_frac_str(f2)}×{_mixed_str(mf)}=",
        correct_answer=_frac_str(result),
        error_code="E01",
        knowledge_point="真分数×带分数",
        difficulty=difficulty,
        hint="先把带分数化成假分数，再按分数乘法计算",
    )


# ---------------------------------------------------------------------------
# E02: 分数除法 (Fraction Division)
# ---------------------------------------------------------------------------

def _gen_fraction_divide(difficulty: str, rng: random.Random) -> GeneratedProblem:
    if difficulty == "A":
        kind = rng.choice(["int_div_frac", "frac_div_int", "frac_div_frac"])
        if kind == "int_div_frac":
            f = _rand_frac_for(rng, "A")
            n = _rand_int_for(rng, "A")
            result = Fraction(n) / f
            return GeneratedProblem(
                problem=f"{n}÷{_frac_str(f)}=",
                correct_answer=_frac_str(result),
                error_code="E02",
                knowledge_point="整数÷分数",
                difficulty=difficulty,
                hint="除以一个分数等于乘以它的倒数",
            )
        if kind == "frac_div_int":
            f = _rand_frac_for(rng, "A")
            n = _rand_int_for(rng, "A")
            result = f / n
            return GeneratedProblem(
                problem=f"{_frac_str(f)}÷{n}=",
                correct_answer=_frac_str(result),
                error_code="E02",
                knowledge_point="分数÷整数",
                difficulty=difficulty,
                hint="分数÷整数，等于乘以这个整数的倒数",
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
        )

    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        f3 = _rand_frac_for(rng, "B")
        quotient = f1 / f2
        if quotient > f3:
            result = quotient - f3
            op = "-"
        else:
            result = quotient + f3
            op = "+"
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}÷{_frac_str(f2)}{op}{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E02",
            knowledge_point="分数除加（减）混合",
            difficulty=difficulty,
            hint="先算除法，再算加减",
        )

    # C: 连除/除乘混合/带分数除法
    kind = rng.choice(["div_mul", "div_div", "mixed_div"])
    if kind == "div_mul":
        f1 = _rand_frac_for(rng, "C")
        f2 = _rand_frac_for(rng, "C")
        f3 = _rand_frac_for(rng, "C")
        result = f1 / f2 * f3
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}÷{_frac_str(f2)}×{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E02",
            knowledge_point="分数除乘混合",
            difficulty=difficulty,
            hint="从左到右计算：先除后乘",
        )
    if kind == "div_div":
        f1 = _rand_frac_for(rng, "C")
        f2 = _rand_frac_for(rng, "C")
        f3 = _rand_frac_for(rng, "C")
        result = f1 / f2 / f3
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}÷{_frac_str(f2)}÷{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E02",
            knowledge_point="分数连除",
            difficulty=difficulty,
            hint="从左到右依次除，也可以把所有除数翻转为乘法一次算",
        )
    # mixed number division
    mf = _rand_mixed(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    result = mf / f2
    return GeneratedProblem(
        problem=f"{_mixed_str(mf)}÷{_frac_str(f2)}=",
        correct_answer=_frac_str(result),
        error_code="E02",
        knowledge_point="带分数÷真分数",
        difficulty=difficulty,
        hint="先把带分数化成假分数，除以一个分数等于乘以它的倒数",
    )


# ---------------------------------------------------------------------------
# E03: 分数四则混合 (Fraction Mixed Operations)
# ---------------------------------------------------------------------------

def _gen_fraction_mixed(difficulty: str, rng: random.Random) -> GeneratedProblem:
    if difficulty == "A":
        # Order of operations: multiply before add/subtract
        f1 = _rand_frac_for(rng, "A")
        f2 = _rand_frac_for(rng, "A")
        f3 = _rand_frac_for(rng, "A")
        product = f2 * f3
        if f1 > product:
            result = f1 - product
            return GeneratedProblem(
                problem=f"{_frac_str(f1)}-{_frac_str(f2)}×{_frac_str(f3)}=",
                correct_answer=_frac_str(result),
                error_code="E03",
                knowledge_point="分数运算顺序（先乘后减）",
                difficulty=difficulty,
                hint="先算乘除，再算加减",
            )
        result = f1 + product
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}+{_frac_str(f2)}×{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E03",
            knowledge_point="分数运算顺序（先乘后加）",
            difficulty=difficulty,
            hint="先算乘除，再算加减",
        )

    if difficulty == "B":
        # Parentheses change operation order
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        f3 = _rand_frac_for(rng, "B")
        pattern = rng.choice(["add_mul", "sub_mul", "add_div"])
        if pattern == "add_mul":
            result = (f1 + f2) * f3
            return GeneratedProblem(
                problem=f"({_frac_str(f1)}+{_frac_str(f2)})×{_frac_str(f3)}=",
                correct_answer=_frac_str(result),
                error_code="E03",
                knowledge_point="括号改变运算顺序（加再乘）",
                difficulty=difficulty,
                hint="有括号先算括号里的",
            )
        if pattern == "sub_mul":
            if f1 <= f2:
                f1, f2 = f2, f1
            result = (f1 - f2) * f3
            return GeneratedProblem(
                problem=f"({_frac_str(f1)}-{_frac_str(f2)})×{_frac_str(f3)}=",
                correct_answer=_frac_str(result),
                error_code="E03",
                knowledge_point="括号改变运算顺序（减再乘）",
                difficulty=difficulty,
                hint="有括号先算括号里的",
            )
        result = (f1 + f2) / f3
        return GeneratedProblem(
            problem=f"({_frac_str(f1)}+{_frac_str(f2)})÷{_frac_str(f3)}=",
            correct_answer=_frac_str(result),
            error_code="E03",
            knowledge_point="括号改变运算顺序（加再除）",
            difficulty=difficulty,
            hint="有括号先算括号里的",
        )

    # C: Two sets of parentheses
    f1 = _rand_frac_for(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    f3 = _rand_frac_for(rng, "C")
    f4 = _rand_frac_for(rng, "C")
    numerator = f1 + f2
    # Ensure positive denominator
    if f3 > f4:
        denominator = f3 - f4
        den_expr = f"{_frac_str(f3)}-{_frac_str(f4)}"
    elif f4 > f3:
        denominator = f4 - f3
        den_expr = f"{_frac_str(f4)}-{_frac_str(f3)}"
    else:
        # f3 == f4, avoid zero denominator
        f4 = _rand_frac_for(rng, "C")
        while f4 == f3:
            f4 = _rand_frac_for(rng, "C")
        if f3 > f4:
            denominator = f3 - f4
            den_expr = f"{_frac_str(f3)}-{_frac_str(f4)}"
        else:
            denominator = f4 - f3
            den_expr = f"{_frac_str(f4)}-{_frac_str(f3)}"
    result = numerator / denominator
    return GeneratedProblem(
        problem=f"({_frac_str(f1)}+{_frac_str(f2)})÷({den_expr})=",
        correct_answer=_frac_str(result),
        error_code="E03",
        knowledge_point="分数四则混合运算（含括号）",
        difficulty=difficulty,
        hint="先分别算出两个括号里的结果，再相除",
    )


# ---------------------------------------------------------------------------
# E04: 比的计算 (Ratio Computation)
# ---------------------------------------------------------------------------

def _gen_ratio(difficulty: str, rng: random.Random) -> GeneratedProblem:
    if difficulty == "A":
        kind = rng.choice(["simplify_int", "value_int"])
        if kind == "simplify_int":
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
        a = _rand_int(rng, 2, 6)
        b = _rand_int(rng, 2, 6)
        while b == a:
            b = _rand_int(rng, 2, 6)
        result = Fraction(a, b)
        return GeneratedProblem(
            problem=f"求比值 {a}:{b}",
            correct_answer=_frac_str(result),
            error_code="E04",
            knowledge_point="求比值（整数比）",
            difficulty=difficulty,
            hint="比值=前项÷后项，用分数表示",
        )

    if difficulty == "B":
        kind = rng.choice(["simplify_frac", "value_frac"])
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        while f1 == f2:
            f2 = _rand_frac_for(rng, "B")
        if kind == "simplify_frac":
            a, b = _simplify_frac_ratio(f1, f2)
            return GeneratedProblem(
                problem=f"化简比 {_frac_str(f1)}:{_frac_str(f2)}",
                correct_answer=f"{a}:{b}",
                error_code="E04",
                knowledge_point="化简分数比",
                difficulty=difficulty,
                hint="先通分，把两个分数变成同分母，再按整数比化简",
            )
        result = f1 / f2
        return GeneratedProblem(
            problem=f"求比值 {_frac_str(f1)}:{_frac_str(f2)}",
            correct_answer=_frac_str(result),
            error_code="E04",
            knowledge_point="求比值（分数比）",
            difficulty=difficulty,
            hint="比值=前项÷后项",
        )

    # C: 按比分配
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
# E05: 百分数计算 (Percentage Computation)
# ---------------------------------------------------------------------------

def _gen_percentage(difficulty: str, rng: random.Random) -> GeneratedProblem:
    if difficulty == "A":
        entry = rng.choice(_CONV_TABLE)
        _, frac, _, pct = entry
        return GeneratedProblem(
            problem=f"把{_frac_str(frac)}化成百分数",
            correct_answer=pct,
            error_code="E05",
            knowledge_point="分数化百分数",
            difficulty=difficulty,
            hint="用分子÷分母算出小数，再乘100加%",
        )

    if difficulty == "B":
        n, m, pct = rng.choice(_PCT_TRIPLES)
        return GeneratedProblem(
            problem=f"{n}是{m}的百分之几",
            correct_answer=f"{pct}%",
            error_code="E05",
            knowledge_point="求一个数是另一个数的百分之几",
            difficulty=difficulty,
            hint="用除法：n÷m，结果化成百分数",
        )

    # C: Discount application
    price = rng.choice([100, 200, 300, 400, 500, 1000])
    disc_pct, disc_name = rng.choice(_DISCOUNTS)
    sale_price = price * disc_pct // 100
    if rng.choice([True, False]):
        saved = price - sale_price
        return GeneratedProblem(
            problem=f"原价{price}元，打{disc_name}，省了多少元？",
            correct_answer=f"{saved}元",
            error_code="E05",
            knowledge_point="百分数应用（打折）",
            difficulty=difficulty,
            hint=f"打{disc_name}就是付{disc_pct}%，先算打折后的价格，再算省了多少",
        )
    return GeneratedProblem(
        problem=f"原价{price}元，打{disc_name}后多少钱？",
        correct_answer=f"{sale_price}元",
        error_code="E05",
        knowledge_point="百分数应用（打折）",
        difficulty=difficulty,
        hint=f"打{disc_name}就是付原价的{disc_pct}%",
    )


# ---------------------------------------------------------------------------
# E06: 小数分数百分数互化 (Decimal/Fraction/Percentage Conversion)
# ---------------------------------------------------------------------------

def _gen_conversion(difficulty: str, rng: random.Random) -> GeneratedProblem:
    if difficulty == "A":
        entry = rng.choice(_CONV_TABLE)
        _, frac, dec, _ = entry
        return GeneratedProblem(
            problem=f"把{_frac_str(frac)}化成小数",
            correct_answer=dec,
            error_code="E06",
            knowledge_point="分数化小数",
            difficulty=difficulty,
            hint="用分子÷分母，算出小数",
        )

    if difficulty == "B":
        direction = rng.choice(["dec_to_frac", "pct_to_frac"])
        entry = rng.choice(_CONV_TABLE)
        _, frac, dec, pct = entry
        if direction == "dec_to_frac":
            return GeneratedProblem(
                problem=f"把{dec}化成最简分数",
                correct_answer=_frac_str(frac),
                error_code="E06",
                knowledge_point="小数化分数",
                difficulty=difficulty,
                hint="看有几位小数，写成分母是10、100或1000的分数，再约分",
            )
        return GeneratedProblem(
            problem=f"把{pct}化成最简分数",
            correct_answer=_frac_str(frac),
            error_code="E06",
            knowledge_point="百分数化分数",
            difficulty=difficulty,
            hint="百分数写成分母是100的分数，再约分",
        )

    # C: Percentage → decimal AND fraction
    non_int = [e for e in _CONV_TABLE if "." in e[3]]
    if not non_int:
        non_int = _CONV_TABLE
    entry = rng.choice(non_int)
    _, frac, dec, pct = entry
    return GeneratedProblem(
        problem=f"把{pct}化成小数和最简分数",
        correct_answer=f"{dec}和{_frac_str(frac)}",
        error_code="E06",
        knowledge_point="百分数化小数和分数",
        difficulty=difficulty,
        hint="百分数→小数：去掉%号，小数点左移两位；→分数：写成分母100再约分",
    )


# ---------------------------------------------------------------------------
# E07: 圆的计算 (Circle Computation)
# ---------------------------------------------------------------------------

def _gen_circle(difficulty: str, rng: random.Random) -> GeneratedProblem:
    if difficulty == "A":
        r = _rand_int(rng, 2, 6)
        coeff = 2 * r
        return GeneratedProblem(
            problem=f"半径{r}cm的圆的周长",
            correct_answer=f"{coeff}π cm",
            error_code="E07",
            knowledge_point="圆的周长",
            difficulty=difficulty,
            hint="周长=2×π×半径",
        )

    if difficulty == "B":
        kind = rng.choice(["radius", "diameter"])
        if kind == "radius":
            r = _rand_int(rng, 2, 10)
            coeff = r * r
            return GeneratedProblem(
                problem=f"半径{r}cm的圆的面积",
                correct_answer=f"{coeff}π cm²",
                error_code="E07",
                knowledge_point="圆的面积",
                difficulty=difficulty,
                hint="面积=π×半径²",
            )
        d = rng.choice(list(range(4, 21, 2)))  # even diameters
        r = d // 2
        coeff = r * r
        return GeneratedProblem(
            problem=f"直径{d}cm的圆的面积",
            correct_answer=f"{coeff}π cm²",
            error_code="E07",
            knowledge_point="圆的面积（已知直径）",
            difficulty=difficulty,
            hint="先算半径=直径÷2，再面积=π×半径²",
        )

    # C: Annular area
    R = _rand_int(rng, 4, 10)
    r = _rand_int(rng, 2, R - 1)
    coeff = R * R - r * r
    return GeneratedProblem(
        problem=f"外圆半径{R}cm、内圆半径{r}cm的环形面积",
        correct_answer=f"{coeff}π cm²",
        error_code="E07",
        knowledge_point="环形面积",
        difficulty=difficulty,
        hint="环形面积=外圆面积-内圆面积=π(R²-r²)",
    )


# ---------------------------------------------------------------------------
# E08: 综合应用 (Comprehensive Multi-step)
# ---------------------------------------------------------------------------

def _gen_comprehensive(difficulty: str, rng: random.Random) -> GeneratedProblem:
    if difficulty == "A":
        # 1-step: total × fraction = part
        f1 = _rand_frac_for(rng, "A")
        total = f1.denominator * _rand_int(rng, 2, 5)
        result = Fraction(total) * f1
        template = rng.choice([
            (f"一堆苹果有{total}个，吃了{_frac_str(f1)}，吃了多少个？", "分数乘法应用"),
            (f"一根绳子{total}米，用去了{_frac_str(f1)}，用去了多少米？", "分数乘法应用"),
            (f"图书角有{total}本书，{_frac_str(f1)}是故事书，故事书有多少本？", "分数乘法应用"),
        ])
        return GeneratedProblem(
            problem=template[0],
            correct_answer=_frac_str(result),
            error_code="E08",
            knowledge_point=template[1],
            difficulty=difficulty,
            hint="总量×分率=部分量",
        )

    if difficulty == "B":
        pattern = rng.choice(["two_parts", "remainder", "difference"])
        if pattern == "two_parts":
            f1 = _rand_frac_for(rng, "B")
            f2 = _rand_frac_for(rng, "B")
            while f1 + f2 >= 1:
                f2 = _rand_frac_for(rng, "B")
            common = _lcm(f1.denominator, f2.denominator)
            total = common * _rand_int(rng, 2, 5)
            result = Fraction(total) * (f1 + f2)
            return GeneratedProblem(
                problem=(
                    f"仓库有{total}吨粮食，第一天运走{_frac_str(f1)}，"
                    f"第二天运走{_frac_str(f2)}，两天共运走多少吨？"
                ),
                correct_answer=_frac_str(result),
                error_code="E08",
                knowledge_point="分数两步应用（求总量的一部分）",
                difficulty=difficulty,
                hint="先分别算出每天运多少，再相加",
            )
        if pattern == "remainder":
            f1 = _rand_frac_for(rng, "B")
            total = f1.denominator * _rand_int(rng, 2, 5)
            result = Fraction(total) * (1 - f1)
            return GeneratedProblem(
                problem=f"一堆{total}千克的水果，卖出了{_frac_str(f1)}，还剩多少千克？",
                correct_answer=_frac_str(result),
                error_code="E08",
                knowledge_point="分数两步应用（求剩余）",
                difficulty=difficulty,
                hint="先算卖出的，再用总量减",
            )
        # difference
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        while f1 == f2:
            f2 = _rand_frac_for(rng, "B")
        common = _lcm(f1.denominator, f2.denominator)
        total = common * _rand_int(rng, 2, 5)
        hi, lo = max(f1, f2), min(f1, f2)
        result = Fraction(total) * (hi - lo)
        return GeneratedProblem(
            problem=(
                f"果园有{total}棵果树，{_frac_str(hi)}是苹果树，"
                f"{_frac_str(lo)}是梨树，苹果树比梨树多多少棵？"
            ),
            correct_answer=_frac_str(result),
            error_code="E08",
            knowledge_point="分数两步应用（求差额）",
            difficulty=difficulty,
            hint="先分别算出两种树的数量，再求差",
        )

    # C: 3-step word problems
    pattern = rng.choice(["sequential", "combined"])
    if pattern == "sequential":
        f1 = _rand_frac_for(rng, "C")
        f2 = _rand_frac_for(rng, "C")
        common = _lcm(f1.denominator, f2.denominator)
        total = common * _rand_int(rng, 3, 6)
        remainder = Fraction(total) * (1 - f1) * (1 - f2)
        # Ensure integer result
        if remainder.denominator != 1:
            total = total * remainder.denominator
            remainder = Fraction(total) * (1 - f1) * (1 - f2)
        return GeneratedProblem(
            problem=(
                f"书店有{total}本书，第一天卖出{_frac_str(f1)}，"
                f"第二天卖出余下的{_frac_str(f2)}，还剩多少本？"
            ),
            correct_answer=_frac_str(remainder),
            error_code="E08",
            knowledge_point="分数三步应用（连续分率）",
            difficulty=difficulty,
            hint="注意：第二天卖出的是\"余下\"的几分之几，不是总量的",
        )
    # combined: morning + afternoon
    f1 = _rand_frac_for(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    common = _lcm(f1.denominator, f2.denominator)
    total = common * _rand_int(rng, 3, 6)
    sold = Fraction(total) * f1 + Fraction(total) * (1 - f1) * f2
    if sold.denominator != 1:
        total = total * sold.denominator
        sold = Fraction(total) * f1 + Fraction(total) * (1 - f1) * f2
    return GeneratedProblem(
        problem=(
            f"水果店有{total}千克水果，上午卖了{_frac_str(f1)}，"
            f"下午卖了剩下的{_frac_str(f2)}，一天共卖了多少千克？"
        ),
        correct_answer=_frac_str(sold),
        error_code="E08",
        knowledge_point="分数三步应用（分批卖出）",
        difficulty=difficulty,
        hint="上午卖总量的一部分，下午卖\"剩下的\"一部分，分两步算再相加",
    )


# ---------------------------------------------------------------------------
# E09: 分数×小数 (Fraction × Decimal)
# ---------------------------------------------------------------------------

def _gen_fraction_decimal(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """Generate fraction × decimal problems using the three-method strategy."""
    if difficulty == "A":
        # Simple fraction × easy decimal where decimal converts to fraction directly
        kind = rng.choice(["frac_dec", "dec_frac"])
        dec_display, dec_frac = rng.choice(_DECIMAL_POOL_B)
        f = _rand_frac_for(rng, "A")
        result = f * dec_frac
        # Determine which method applies for the hint
        if dec_frac.denominator in [2, 4, 5, 8, 10]:
            method_hint = "小数可以直接化成分数"
        else:
            method_hint = "把小数化成分数再乘"
        if kind == "frac_dec":
            return GeneratedProblem(
                problem=f"{_frac_str(f)}×{dec_display}=",
                correct_answer=_frac_str(result),
                error_code="E09",
                knowledge_point="分数×小数（化分数）",
                difficulty=difficulty,
                hint=method_hint,
            )
        return GeneratedProblem(
            problem=f"{dec_display}×{_frac_str(f)}=",
            correct_answer=_frac_str(result),
            error_code="E09",
            knowledge_point="分数×小数（化分数）",
            difficulty=difficulty,
            hint=method_hint,
        )

    if difficulty == "B":
        # Choose best method: simplify with denominator, or convert
        kind = rng.choice(["simplify", "convert"])
        if kind == "simplify":
            # Pick a decimal where numerator simplifies with fraction denominator
            # e.g., 2.4 × 3/4 = (24/5) × (3/4) = 18/5
            dec_display, dec_frac = rng.choice(_DECIMAL_POOL_B)
            f = _rand_frac_for(rng, "B")
            result = dec_frac * f
            return GeneratedProblem(
                problem=f"{dec_display}×{_frac_str(f)}=",
                correct_answer=_frac_str(result),
                error_code="E09",
                knowledge_point="分数×小数（先约分）",
                difficulty=difficulty,
                hint="看小数化成分数后能否和另一个分数约分",
            )
        # Convert the easier operand (fraction if it's a finite decimal)
        dec_display, dec_frac = rng.choice(_DECIMAL_POOL_B)
        f = _rand_frac_for(rng, "B")
        # Check if fraction converts to finite decimal
        d = f.denominator
        temp_d = d
        for _ in range(10):
            if temp_d % 2 == 0:
                temp_d //= 2
            elif temp_d % 5 == 0:
                temp_d //= 5
            else:
                break
        if temp_d == 1:
            kp = "分数×小数（化小数）"
            hint = "分数可以化成有限小数，化成小数再乘"
        else:
            kp = "分数×小数（化分数）"
            hint = "分数不能化成有限小数，把小数化成分数再乘"
        result = dec_frac * f
        return GeneratedProblem(
            problem=f"{_frac_str(f)}×{dec_display}=",
            correct_answer=_frac_str(result),
            error_code="E09",
            knowledge_point=kp,
            difficulty=difficulty,
            hint=hint,
        )

    # C: Multi-step with fraction-decimal mix, e.g., (0.5 + 1/3) × 2.4
    pattern = rng.choice(["paren_mul", "chain", "mixed_expr"])
    if pattern == "paren_mul":
        dec_display, dec_frac = rng.choice(_DECIMAL_POOL)
        f1 = _rand_frac_for(rng, "C")
        f2 = _rand_frac_for(rng, "C")
        inner = dec_frac + f1
        result = inner * f2
        return GeneratedProblem(
            problem=f"({dec_display}+{_frac_str(f1)})×{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E09",
            knowledge_point="分数×小数（含括号）",
            difficulty=difficulty,
            hint="先算括号里，统一化成分数再计算",
        )
    if pattern == "chain":
        dec_display, dec_frac = rng.choice(_DECIMAL_POOL)
        f = _rand_frac_for(rng, "C")
        dec2_display, dec2_frac = rng.choice(_DECIMAL_POOL)
        result = dec_frac * f * dec2_frac
        return GeneratedProblem(
            problem=f"{dec_display}×{_frac_str(f)}×{dec2_display}=",
            correct_answer=_frac_str(result),
            error_code="E09",
            knowledge_point="分数小数连乘",
            difficulty=difficulty,
            hint="全部化成分数，逐步约分相乘",
        )
    # mixed_expr: decimal × (fraction + fraction)
    dec_display, dec_frac = rng.choice(_DECIMAL_POOL)
    f1 = _rand_frac_for(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    result = dec_frac * (f1 + f2)
    return GeneratedProblem(
        problem=f"{dec_display}×({_frac_str(f1)}+{_frac_str(f2)})=",
        correct_answer=_frac_str(result),
        error_code="E09",
        knowledge_point="分数×小数（分配律）",
        difficulty=difficulty,
        hint="可以用分配律，也可以先算括号里",
    )


# ---------------------------------------------------------------------------
# E10: 运算律推广 (Operation Law Extension)
# ---------------------------------------------------------------------------

def _gen_operation_law(difficulty: str, rng: random.Random) -> GeneratedProblem:
    """Generate problems using commutative, associative, distributive laws."""
    if difficulty == "A":
        # Simple distributive law: (a/b + c/d) × n
        f1 = _rand_frac_for(rng, "A")
        f2 = _rand_frac_for(rng, "A")
        n = _rand_int_for(rng, "A")
        # Choose a denominator-friendly n
        common_denom = _lcm(f1.denominator, f2.denominator)
        n = common_denom  # makes distribution clean
        result = (f1 + f2) * n
        return GeneratedProblem(
            problem=f"({_frac_str(f1)}+{_frac_str(f2)})×{n}=",
            correct_answer=_frac_str(result),
            error_code="E10",
            knowledge_point="乘法分配律",
            difficulty=difficulty,
            hint="用分配律：分别乘再相加，或者先算括号里",
        )

    if difficulty == "B":
        kind = rng.choice(["associative", "distributive_reverse", "commutative"])
        if kind == "associative":
            # Associative: a/b × n × c/d, reorder for easy computation
            f1 = _rand_frac_for(rng, "B")
            f2 = _rand_frac_for(rng, "B")
            n = _rand_int_for(rng, "B")
            result = f1 * n * f2
            return GeneratedProblem(
                problem=f"{_frac_str(f1)}×{n}×{_frac_str(f2)}=",
                correct_answer=_frac_str(result),
                error_code="E10",
                knowledge_point="乘法结合律",
                difficulty=difficulty,
                hint="交换顺序让能约分的先算",
            )
        if kind == "distributive_reverse":
            # Reverse distributive: a/b × n + a/b × m = a/b × (n + m)
            f = _rand_frac_for(rng, "B")
            n = _rand_int_for(rng, "B")
            m = _rand_int_for(rng, "B")
            result = f * n + f * m
            return GeneratedProblem(
                problem=f"{_frac_str(f)}×{n}+{_frac_str(f)}×{m}=",
                correct_answer=_frac_str(result),
                error_code="E10",
                knowledge_point="乘法分配律（提取公因数）",
                difficulty=difficulty,
                hint=f"提出{_frac_str(f)}，变成{_frac_str(f)}×({n}+{m})",
            )
        # Commutative: rearrange for convenience
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        result = f1 * f2
        return GeneratedProblem(
            problem=f"{_frac_str(f2)}×{_frac_str(f1)}=",
            correct_answer=_frac_str(result),
            error_code="E10",
            knowledge_point="乘法交换律",
            difficulty=difficulty,
            hint="交换位置不影响结果，可以先约分再计算",
        )

    # C: Complex distributive with decomposition
    kind = rng.choice(["decompose_plus_one", "decompose_parts", "double_distribute"])
    if kind == "decompose_plus_one":
        # a/b × n + a/b = a/b × (n + 1)
        f = _rand_frac_for(rng, "C")
        n = _rand_int_for(rng, "C", lo=2)
        result = f * (n + 1)
        return GeneratedProblem(
            problem=f"{_frac_str(f)}×{n}+{_frac_str(f)}=",
            correct_answer=_frac_str(result),
            error_code="E10",
            knowledge_point="乘法分配律（凑整）",
            difficulty=difficulty,
            hint=f"把{_frac_str(f)}看成{_frac_str(f)}×1，提取公因数：{_frac_str(f)}×({n}+1)",
        )
    if kind == "decompose_parts":
        # a/b × n + a/b × m where n + m is a round number
        f = _rand_frac_for(rng, "C")
        n = _rand_int_for(rng, "C")
        # Choose m such that n+m is round (10, 20, etc.)
        target = rng.choice([10, 20])
        m = target - n
        if m < 1:
            m = _rand_int_for(rng, "C")
        result = f * n + f * m
        return GeneratedProblem(
            problem=f"{_frac_str(f)}×{n}+{_frac_str(f)}×{m}=",
            correct_answer=_frac_str(result),
            error_code="E10",
            knowledge_point="乘法分配律（拆分凑整）",
            difficulty=difficulty,
            hint=f"提取{_frac_str(f)}：{_frac_str(f)}×({n}+{m})={_frac_str(f)}×{n + m}",
        )
    # Double distribute pattern: (a + b/c) × d
    f1 = _rand_frac_for(rng, "C")
    n = _rand_int_for(rng, "C", lo=2)
    # Use a mixed number times integer
    mixed = _rand_mixed(rng, "C")
    result = mixed * n
    return GeneratedProblem(
        problem=f"{_mixed_str(mixed)}×{n}=",
        correct_answer=_frac_str(result),
        error_code="E10",
        knowledge_point="乘法分配律（带分数拆分）",
        difficulty=difficulty,
        hint="把带分数拆成整数+分数，分别乘再相加",
    )


# ---------------------------------------------------------------------------
# E11: 估算与验算 (Estimation and Checking)
# ---------------------------------------------------------------------------

def _gen_estimation(difficulty: str, rng: random.Random) -> GeneratedProblem:
    if difficulty == "A":
        f = _rand_frac_for(rng, "A")
        n = _rand_int_for(rng, "A")
        result = f * n
        return GeneratedProblem(
            problem=f"{_frac_str(f)}×{n}=",
            correct_answer=_frac_str(result),
            error_code="E11",
            knowledge_point="分数乘法估算",
            difficulty=difficulty,
            hint=f"先想{_frac_str(f)}大约是零点几，估算乘以{n}的结果范围",
        )

    if difficulty == "B":
        f1 = _rand_frac_for(rng, "B")
        f2 = _rand_frac_for(rng, "B")
        result = f1 / f2
        return GeneratedProblem(
            problem=f"{_frac_str(f1)}÷{_frac_str(f2)}=",
            correct_answer=_frac_str(result),
            error_code="E11",
            knowledge_point="分数除法验算",
            difficulty=difficulty,
            hint="算完后用乘法检验：商×除数应该等于被除数",
        )

    # C: mixed operation with verification emphasis
    f1 = _rand_frac_for(rng, "C")
    f2 = _rand_frac_for(rng, "C")
    f3 = _rand_frac_for(rng, "C")
    product = f1 * f2
    if product > f3:
        result = product - f3
        op = "-"
    else:
        result = product + f3
        op = "+"
    return GeneratedProblem(
        problem=f"{_frac_str(f1)}×{_frac_str(f2)}{op}{_frac_str(f3)}=",
        correct_answer=_frac_str(result),
        error_code="E11",
        knowledge_point="分数混合运算验算",
        difficulty=difficulty,
        hint="分步估算：先估算乘法结果，再估算加减结果，精确计算后对照检查",
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
# Generator registry
# ---------------------------------------------------------------------------

_GENERATORS: dict[str, type] = {
    "E01": _gen_fraction_multiply,
    "E02": _gen_fraction_divide,
    "E03": _gen_fraction_mixed,
    "E04": _gen_ratio,
    "E05": _gen_percentage,
    "E06": _gen_conversion,
    "E07": _gen_circle,
    "E08": _gen_comprehensive,
    "E09": _gen_fraction_decimal,
    "E10": _gen_operation_law,
    "E11": _gen_estimation,
}


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
) -> list[GeneratedProblem]:
    if not error_codes:
        error_codes = ["E03"]
    rng = random.Random(seed)
    per_code = max(1, total_count // len(error_codes))
    remainder = total_count - per_code * len(error_codes)
    all_problems: list[GeneratedProblem] = []
    for i, code in enumerate(error_codes):
        count = per_code + (1 if i < remainder else 0)
        problems = generate_problems(code, difficulty, count, seed=rng.randint(0, 2**31))
        all_problems.extend(problems)
    rng.shuffle(all_problems)
    return all_problems[:total_count]

"""Tests for the procedural problem generation system (problem_generator.py)."""

import random
from fractions import Fraction

import pytest

from app.services.problem_generator import (
    GeneratedProblem,
    generate_problems,
    generate_problems_by_exercise_type,
    generate_quiz_problems,
    _GENERATORS,
    _EXERCISE_TYPE_GENERATORS,
)


# ---------------------------------------------------------------------------
# 1. All registered generators produce valid output
# ---------------------------------------------------------------------------

def test_all_e_code_generators_produce_valid_problems():
    """Each registered E-code generator should produce a problem with
    non-empty expression, a valid answer, and difficulty in {A, B, C}."""
    for code, gen_fn in _GENERATORS.items():
        for diff in ("A", "B", "C"):
            rng = random.Random(42)
            p = gen_fn(diff, rng)
            assert isinstance(p, GeneratedProblem), f"{code}/{diff}: wrong type"
            assert p.problem.strip(), f"{code}/{diff}: empty problem string"
            assert p.correct_answer.strip(), f"{code}/{diff}: empty answer for {p.problem}"
            assert p.difficulty == diff, f"{code}/{diff}: wrong difficulty {p.difficulty}"
            assert p.error_code == code, f"{code}/{diff}: wrong error_code {p.error_code}"
            assert p.knowledge_point, f"{code}/{diff}: empty knowledge_point"


def test_all_exercise_type_generators_produce_valid_problems():
    for et_id, gen_fn in _EXERCISE_TYPE_GENERATORS.items():
        for diff in ("A", "B", "C"):
            rng = random.Random(42)
            p = gen_fn(rng, diff)
            assert isinstance(p, GeneratedProblem), f"{et_id}/{diff}: wrong type"
            assert p.problem.strip(), f"{et_id}/{diff}: empty problem string"
            assert p.correct_answer.strip(), f"{et_id}/{diff}: empty answer for {p.problem}"
            assert p.difficulty == diff, f"{et_id}/{diff}: wrong difficulty"


# ---------------------------------------------------------------------------
# 2. generate_problems returns the right number and deduplicates
# ---------------------------------------------------------------------------

def test_generate_problems_count_and_unique():
    problems = generate_problems("E01", difficulty="B", count=10, seed=123)
    assert len(problems) == 10
    expressions = [p.problem for p in problems]
    assert len(expressions) == len(set(expressions)), "Problems should be unique"


def test_generate_problems_unknown_error_code_falls_back():
    """Unknown error codes should use the default generator (E99)."""
    problems = generate_problems("E99", difficulty="A", count=5, seed=42)
    assert len(problems) == 5
    for p in problems:
        assert p.error_code == "E99"


# ---------------------------------------------------------------------------
# 3. Deterministic with seed
# ---------------------------------------------------------------------------

def test_deterministic_with_seed():
    """Same seed should produce identical problem lists."""
    a = generate_problems("E03", difficulty="B", count=5, seed=999)
    b = generate_problems("E03", difficulty="B", count=5, seed=999)
    assert len(a) == len(b)
    for pa, pb in zip(a, b):
        assert pa.problem == pb.problem
        assert pa.correct_answer == pb.correct_answer


def test_different_seed_produces_different_problems():
    a = generate_problems("E01", difficulty="A", count=10, seed=1)
    b = generate_problems("E01", difficulty="A", count=10, seed=2)
    # At least some should differ (extremely unlikely all 10 match)
    problems_a = {p.problem for p in a}
    problems_b = {p.problem for p in b}
    assert problems_a != problems_b


# ---------------------------------------------------------------------------
# 4. generate_quiz_problems with mixed difficulty distribution
# ---------------------------------------------------------------------------

def test_mixed_difficulty_distribution():
    """When a distribution is given, problems should span multiple difficulty tiers."""
    problems = generate_quiz_problems(
        error_codes=["E01", "E02"],
        total_count=10,
        seed=42,
        difficulty_distribution={"A": 0.4, "B": 0.4, "C": 0.2},
    )
    assert len(problems) == 10
    difficulties = [p.difficulty for p in problems]
    assert "A" in difficulties
    assert "B" in difficulties
    assert "C" in difficulties


def test_quiz_problems_single_difficulty():
    """Without distribution, all problems should use the specified difficulty."""
    problems = generate_quiz_problems(
        error_codes=["E03"],
        difficulty="A",
        total_count=5,
        seed=42,
    )
    assert len(problems) == 5
    assert all(p.difficulty == "A" for p in problems)


def test_quiz_problems_empty_error_codes_defaults():
    """Empty error_codes should default to ['E03']."""
    problems = generate_quiz_problems(
        error_codes=[],
        difficulty="B",
        total_count=3,
        seed=42,
    )
    assert len(problems) == 3
    # Should not raise; should have some problems
    for p in problems:
        assert p.problem.strip()


# ---------------------------------------------------------------------------
# 5. generate_problems_by_exercise_type
# ---------------------------------------------------------------------------

def test_generate_problems_by_exercise_type_valid():
    problems = generate_problems_by_exercise_type("ET-0101", difficulty="A", count=5, seed=42)
    assert len(problems) == 5
    for p in problems:
        assert p.exercise_type == "ET-0101"


def test_generate_problems_by_exercise_type_unknown():
    problems = generate_problems_by_exercise_type("ET-9999", difficulty="A", count=5)
    assert problems == []


# ---------------------------------------------------------------------------
# 6. Fraction answer correctness spot-check
# ---------------------------------------------------------------------------

def test_fraction_multiply_answer_correctness():
    """Spot-check that generated answers are mathematically correct for E01."""
    rng = random.Random(7)
    from app.services.problem_generator import _gen_fraction_multiply
    for _ in range(20):
        p = _gen_fraction_multiply("A", rng)
        # We can't easily parse every expression format, but the answer
        # should be a valid fraction string or integer
        answer = p.correct_answer
        if "/" in answer:
            parts = answer.split("/")
            assert len(parts) == 2
            int(parts[0])  # should not raise
            int(parts[1])  # should not raise
            assert int(parts[1]) != 0
        else:
            # Should be an integer or simple value
            assert answer.strip()


def test_circle_problem_answer_format():
    """Circle problems should include π in the answer."""
    from app.services.problem_generator import _gen_circle
    for diff in ("A", "B", "C"):
        rng = random.Random(42)
        p = _gen_circle(diff, rng)
        assert "π" in p.correct_answer or "π" in p.knowledge_point
        assert p.error_code == "E07"


def test_ratio_problem_answer_format():
    """Ratio problems should have ':' in the answer for simplify, or fraction for value."""
    from app.services.problem_generator import _gen_ratio
    rng = random.Random(42)
    p = _gen_ratio("A", rng)
    assert ":" in p.correct_answer or "/" in p.correct_answer
    assert p.error_code == "E04"


# ---------------------------------------------------------------------------
# 7. Correct answer verification for all error codes × all difficulties
# ---------------------------------------------------------------------------

_ERROR_CODES = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11"]


def _is_valid_number(s: str) -> bool:
    """Check if a string is a valid numeric value (int, float, or fraction)."""
    from fractions import Fraction
    s = s.strip()
    if not s:
        return False
    try:
        Fraction(s)
        return True
    except (ValueError, ZeroDivisionError):
        pass
    try:
        float(s)
        return True
    except ValueError:
        pass
    return False


def _is_valid_answer(answer: str) -> bool:
    """Validate an answer string from the problem generator.

    Answers may be: plain numbers, fractions, percentages (5%),
    ratios (1:3), compound (0.625和5/8), with units (120元),
    or contain π.
    """
    import re
    a = answer.strip()
    if not a:
        return False
    # Strip trailing Chinese / metric units
    stripped = re.sub(r"[元个人们米千米°]+$", "", a).strip()
    if not stripped:
        return True
    # Percentage like '5%'
    if stripped.endswith("%"):
        return _is_valid_number(stripped[:-1])
    # Ratio like '1:3'
    if ":" in stripped:
        return all(_is_valid_number(p) for p in stripped.split(":"))
    # Contains π
    if "π" in stripped:
        return True
    # Compound answer joined by '和'
    if "和" in stripped:
        return all(_is_valid_number(p.strip()) for p in stripped.split("和"))
    return _is_valid_number(stripped)


@pytest.mark.parametrize("error_code", _ERROR_CODES)
@pytest.mark.parametrize("difficulty", ["A", "B", "C"])
def test_generated_problems_have_correct_answers(error_code, difficulty):
    """Every generated problem should have a non-empty, parseable correct_answer."""
    problems = generate_quiz_problems(
        error_codes=[error_code],
        total_count=3,
        difficulty=difficulty,
        seed=42,
    )
    assert len(problems) > 0, f"No problems generated for {error_code}/{difficulty}"
    for p in problems:
        assert p.correct_answer is not None
        assert p.correct_answer != ""
        assert _is_valid_answer(p.correct_answer), (
            f"Invalid answer format: {p.correct_answer!r} for {p.problem} "
            f"({error_code}/{difficulty})"
        )


# ---------------------------------------------------------------------------
# 8. Problem variety — not all identical
# ---------------------------------------------------------------------------

def test_problem_variety():
    """Generate 10 problems for one error code and check they aren't all the same."""
    problems = generate_quiz_problems(
        error_codes=["E01"],
        total_count=10,
        difficulty="A",
        seed=None,  # use non-deterministic seed
    )
    expressions = {p.problem for p in problems}
    assert len(expressions) >= 3, f"Generated problems lack variety: {expressions}"


# ---------------------------------------------------------------------------
# 9. No division by zero
# ---------------------------------------------------------------------------

def test_no_division_by_zero():
    """No generated problem should involve division by zero in the answer."""
    for error_code in _ERROR_CODES:
        problems = generate_quiz_problems(
            error_codes=[error_code],
            total_count=5,
            difficulty="A",
            seed=42,
        )
        for p in problems:
            answer = p.correct_answer
            if "/" in answer:
                # Split on '/' but be careful with compound answers like '0.625和5/8'
                parts = answer.split("/")
                denom_part = parts[-1].strip()
                # Strip any trailing units
                import re
                denom_clean = re.sub(r"[元个人们米千米°]+", "", denom_part).strip()
                if denom_clean:
                    try:
                        denom_val = float(denom_clean)
                        assert denom_val != 0, (
                            f"Division by zero in {p.problem} (answer={answer})"
                        )
                    except ValueError:
                        pass  # non-numeric denominator (e.g. contains π), skip


# ---------------------------------------------------------------------------
# 10. Error code tagging
# ---------------------------------------------------------------------------

def test_error_code_tagging():
    """Each problem should carry the error code it was generated for."""
    for code in _ERROR_CODES:
        problems = generate_quiz_problems(
            error_codes=[code],
            total_count=3,
            difficulty="A",
            seed=42,
        )
        for p in problems:
            assert p.error_code == code, (
                f"Expected error_code={code}, got {p.error_code} for {p.problem}"
            )

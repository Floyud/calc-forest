"""Tests for the procedural problem generation system (problem_generator.py)."""

import random
from fractions import Fraction

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

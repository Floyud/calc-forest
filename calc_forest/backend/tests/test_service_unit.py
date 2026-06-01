"""Unit tests for pure service-layer logic.

Tests pure functions (no DB) from:
- growth_milestone.compute_stage()
- mastery_service._bkt_forward, _zone, _days_since
- archetype.classify_student
- profiles.summarize_profile
- summaries.summarize_class
"""
import math
from datetime import datetime, timedelta, timezone

import pytest

from app.schemas import DiagnosisResponse, ErrorCode, ErrorTag, GuidanceMode


# ===========================================================================
# growth_milestone.compute_stage
# ===========================================================================
class TestComputeStage:
    """Tests for growth_milestone.compute_stage()."""

    def test_zero_days_returns_seed(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(0) == "seed"

    def test_negative_days_returns_seed(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(-5) == "seed"

    def test_day_1_seed(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(1) == "seed"

    def test_day_3_sprout(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(3) == "sprout"

    def test_day_7_first_leaf(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(7) == "first_leaf"

    def test_day_14_taller(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(14) == "taller"

    def test_day_21_branching(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(21) == "branching"

    def test_day_30_sturdy(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(30) == "sturdy"

    def test_day_45_bud(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(45) == "bud"

    def test_day_60_flowering(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(60) == "flowering"

    def test_day_90_mature(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(90) == "mature"

    def test_day_100_still_mature(self):
        from app.services.growth_milestone import compute_stage
        assert compute_stage(100) == "mature"

    def test_day_2_seed(self):
        """Between seed(1) and sprout(3)."""
        from app.services.growth_milestone import compute_stage
        assert compute_stage(2) == "seed"

    def test_day_5_sprout(self):
        """Between sprout(3) and first_leaf(7)."""
        from app.services.growth_milestone import compute_stage
        assert compute_stage(5) == "sprout"

    def test_accuracy_boost_with_mastery(self):
        """High accuracy + mastery_count >= 3 → stage promoted."""
        from app.services.growth_milestone import compute_stage
        # 30 days = sturdy, but with accuracy 0.85 and mastery 3 → bud
        base = compute_stage(30)
        boosted = compute_stage(30, accuracy=0.85, mastery_count=3)
        assert base == "sturdy"
        assert boosted == "bud"

    def test_accuracy_boost_no_mastery(self):
        """accuracy >= 0.80 but mastery_count < 3 → no boost."""
        from app.services.growth_milestone import compute_stage
        result = compute_stage(30, accuracy=0.85, mastery_count=2)
        assert result == "sturdy"  # not boosted

    def test_accuracy_demotion(self):
        from app.services.growth_milestone import compute_stage
        result = compute_stage(14, accuracy=0.40)
        assert result == "first_leaf"

    def test_accuracy_demotion_only_after_7_days(self):
        """accuracy < 0.50 but days <= 7 → no demotion."""
        from app.services.growth_milestone import compute_stage
        result = compute_stage(5, accuracy=0.40)
        assert result == "sprout"  # no demotion for early stages

    def test_accuracy_none_returns_base(self):
        """accuracy=None → returns base stage, no adjustment."""
        from app.services.growth_milestone import compute_stage
        result = compute_stage(30, accuracy=None)
        assert result == "sturdy"

    def test_mature_cannot_be_boosted_further(self):
        """Mature is the max stage, cannot be boosted."""
        from app.services.growth_milestone import compute_stage
        result = compute_stage(90, accuracy=0.95, mastery_count=5)
        assert result == "mature"

    def test_seed_cannot_be_demoted(self):
        """Seed is the min stage, cannot be demoted."""
        from app.services.growth_milestone import compute_stage
        result = compute_stage(1, accuracy=0.10)
        assert result == "seed"

    def test_float_days(self):
        """Float days_completed should work."""
        from app.services.growth_milestone import compute_stage
        assert compute_stage(2.5) == "seed"
        assert compute_stage(3.0) == "sprout"


# ===========================================================================
# mastery_service._bkt_forward, _zone, _days_since
# ===========================================================================
class TestBKTForward:
    """Tests for mastery_service._bkt_forward()."""

    def test_import(self):
        from app.services.mastery_service import _bkt_forward, BKTParams
        assert callable(_bkt_forward)

    def test_no_observations_returns_p_l0(self):
        from app.services.mastery_service import _bkt_forward, BKTParams
        params = BKTParams(p_l0=0.3, p_t=0.1, p_g=0.2, p_s=0.1)
        result = _bkt_forward(params, [])
        assert result == 0.3

    def test_all_correct_increases_mastery(self):
        from app.services.mastery_service import _bkt_forward, BKTParams
        params = BKTParams(p_l0=0.3, p_t=0.1, p_g=0.2, p_s=0.1)
        after_one_correct = _bkt_forward(params, [True])
        after_five_correct = _bkt_forward(params, [True] * 5)
        assert after_one_correct > params.p_l0
        assert after_five_correct > after_one_correct

    def test_all_wrong_decreases_mastery(self):
        from app.services.mastery_service import _bkt_forward, BKTParams
        params = BKTParams(p_l0=0.3, p_t=0.1, p_g=0.2, p_s=0.1)
        after_one_wrong = _bkt_forward(params, [False])
        assert after_one_wrong < params.p_l0

    def test_order_matters(self):
        """Temporal ordering: [correct, wrong] != [wrong, correct]."""
        from app.services.mastery_service import _bkt_forward, BKTParams
        params = BKTParams(p_l0=0.3, p_t=0.1, p_g=0.2, p_s=0.1)
        cw = _bkt_forward(params, [True, False])
        wc = _bkt_forward(params, [False, True])
        # They should differ because BKT processes sequentially
        assert cw != wc

    def test_mastery_approaches_ceiling(self):
        """After many correct answers, mastery should be high but < 1.0."""
        from app.services.mastery_service import _bkt_forward, BKTParams
        params = BKTParams(p_l0=0.3, p_t=0.1, p_g=0.2, p_s=0.1)
        result = _bkt_forward(params, [True] * 50)
        assert result >= 0.95
        assert result <= 0.999  # ceiling cap

    def test_e01_params(self):
        """E01 (Basic facts) params should exist and be reasonable."""
        from app.services.mastery_service import ERROR_CODE_PARAMS
        e01 = ERROR_CODE_PARAMS["E01"]
        assert 0 < e01.p_l0 < 1
        assert 0 < e01.p_t < 1
        assert 0 < e01.p_g < 1
        assert 0 < e01.p_s < 1

    def test_all_11_error_codes_have_params(self):
        """All E01-E11 should have calibrated parameters."""
        from app.services.mastery_service import ERROR_CODE_PARAMS, ERROR_CODES
        for code in ERROR_CODES:
            assert code in ERROR_CODE_PARAMS, f"Missing params for {code}"

    def test_result_is_rounded_to_4_decimals(self):
        from app.services.mastery_service import _bkt_forward, BKTParams
        params = BKTParams(p_l0=0.3, p_t=0.1, p_g=0.2, p_s=0.1)
        result = _bkt_forward(params, [True, False, True])
        # Check rounding: result should have at most 4 decimal places
        assert result == round(result, 4)


class TestZone:
    """Tests for mastery_service._zone()."""

    def test_mastered(self):
        from app.services.mastery_service import _zone
        assert _zone(0.85) == "mastered"
        assert _zone(0.95) == "mastered"
        assert _zone(1.0) == "mastered"

    def test_learning(self):
        from app.services.mastery_service import _zone
        assert _zone(0.50) == "learning"
        assert _zone(0.84) == "learning"
        assert _zone(0.70) == "learning"

    def test_needs_practice(self):
        from app.services.mastery_service import _zone
        assert _zone(0.0) == "needs_practice"
        assert _zone(0.49) == "needs_practice"
        assert _zone(0.10) == "needs_practice"

    def test_boundary_050(self):
        from app.services.mastery_service import _zone
        assert _zone(0.5) == "learning"

    def test_boundary_085(self):
        from app.services.mastery_service import _zone
        assert _zone(0.85) == "mastered"


class TestDaysSince:
    """Tests for mastery_service._days_since()."""

    def test_none_returns_zero(self):
        from app.services.mastery_service import _days_since
        assert _days_since(None) == 0.0

    def test_empty_string_returns_zero(self):
        from app.services.mastery_service import _days_since
        assert _days_since("") == 0.0

    def test_recent_timestamp_small_days(self):
        from app.services.mastery_service import _days_since
        recent = datetime.now(timezone.utc).isoformat()
        result = _days_since(recent)
        assert result < 1.0  # less than a day ago

    def test_old_timestamp_large_days(self):
        from app.services.mastery_service import _days_since
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        result = _days_since(old)
        assert result >= 29.0  # approximately 30 days

    def test_future_timestamp_returns_zero(self):
        """Future timestamps should return 0 (clamped by max())."""
        from app.services.mastery_service import _days_since
        future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        result = _days_since(future)
        assert result == 0.0

    def test_invalid_format_returns_zero(self):
        from app.services.mastery_service import _days_since
        assert _days_since("not-a-date") == 0.0


# ===========================================================================
# archetype.classify_student
# ===========================================================================
class TestClassifyStudent:
    """Tests for archetype.classify_student()."""

    def test_insufficient_data_returns_growth_potential(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.8, accuracy_trend="stable", total_attempts=3
        )
        assert result.archetype_id == "growth_potential"
        assert result.confidence == 0.3
        assert "3" in result.evidence[0]  # "仅 3 次作答记录"

    def test_exactly_5_attempts_is_enough(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.85, accuracy_trend="stable", total_attempts=5
        )
        assert result.archetype_id != "growth_potential" or result.confidence != 0.3

    def test_solid_steady_high_accuracy_stable(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.85, accuracy_trend="stable", total_attempts=20
        )
        assert result.archetype_id == "solid_steady"
        assert result.archetype == "扎实稳健型"

    def test_solid_steady_high_accuracy_improving(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.90, accuracy_trend="improving", total_attempts=20
        )
        assert result.archetype_id == "solid_steady"

    def test_steady_progress_improving_trend(self):
        """Improving trend but accuracy < 0.80 → steady_progress."""
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.65, accuracy_trend="improving", total_attempts=15
        )
        assert result.archetype_id == "steady_progress"
        assert result.archetype == "稳步进步型"

    def test_climbing_hard_low_accuracy(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.45, accuracy_trend="stable", total_attempts=15
        )
        assert result.archetype_id == "climbing_hard"
        assert result.archetype == "努力攀登型"

    def test_climbing_hard_long_wrong_streak(self):
        """accuracy OK but wrong streak >= 3 → climbing_hard."""
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.70, accuracy_trend="stable",
            total_attempts=15, current_streak_wrong=4
        )
        assert result.archetype_id == "climbing_hard"

    def test_growth_potential_default(self):
        """accuracy 0.65-0.80, stable, no streaks → growth_potential."""
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.70, accuracy_trend="stable", total_attempts=15
        )
        assert result.archetype_id == "growth_potential"
        assert result.archetype == "成长潜力型"

    def test_mastery_count_boosts_confidence(self):
        from app.services.archetype import classify_student
        r0 = classify_student(0.85, "stable", total_attempts=20, mastery_count=0)
        r3 = classify_student(0.85, "stable", total_attempts=20, mastery_count=3)
        assert r3.confidence > r0.confidence

    def test_evidence_includes_accuracy(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.75, accuracy_trend="improving", total_attempts=10
        )
        assert any("75%" in e for e in result.evidence)

    def test_evidence_includes_trend(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.75, accuracy_trend="improving", total_attempts=10
        )
        assert any("上升" in e for e in result.evidence)

    def test_evidence_includes_streak(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.50, accuracy_trend="declining",
            total_attempts=10, current_streak_correct=5
        )
        assert any("5" in e and "正确" in e for e in result.evidence)

    def test_evidence_includes_mastery_count(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.85, accuracy_trend="stable",
            total_attempts=20, mastery_count=4
        )
        assert any("4" in e and "掌握" in e for e in result.evidence)

    def test_accuracy_none_with_improving_trend(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=None, accuracy_trend="improving", total_attempts=10
        )
        assert result.archetype_id == "steady_progress"

    def test_declining_trend_in_evidence(self):
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.50, accuracy_trend="declining", total_attempts=10
        )
        assert any("下降" in e for e in result.evidence)

    def test_confidence_cap_at_095(self):
        """Confidence should not exceed 0.95."""
        from app.services.archetype import classify_student
        result = classify_student(
            accuracy=0.95, accuracy_trend="stable",
            total_attempts=30, mastery_count=10
        )
        assert result.confidence <= 0.95


# ===========================================================================
# profiles.summarize_profile (pure function)
# ===========================================================================
def _make_diagnosis(student_id: str, code: str, correct: bool) -> DiagnosisResponse:
    """Helper to create DiagnosisResponse for testing."""
    ec = ErrorCode(code) if code in ErrorCode._value2member_map_ else ErrorCode.UNKNOWN
    return DiagnosisResponse(
        record_id="test",
        student_id=student_id,
        is_correct=correct,
        error_code=code,
        error_label="test",
        confidence=0.9,
        primary_error=ErrorTag(
            code=ec,
            label="test",
            confidence=0.9,
            evidence="test",
            teacher_action="test",
            student_feedback="test",
        ),
        teacher_summary="test",
    )


class TestSummarizeProfile:
    """Tests for profiles.summarize_profile()."""

    def test_empty_diagnoses(self):
        from app.services.profiles import summarize_profile
        result = summarize_profile("S001", [])
        assert result["student_id"] == "S001"
        assert result["attempt_count"] == 0
        assert result["accuracy"] is None
        assert result["dominant_error_tags"] == []

    def test_all_correct(self):
        from app.services.profiles import summarize_profile
        diags = [
            _make_diagnosis("S001", "OK", True),
            _make_diagnosis("S001", "OK", True),
            _make_diagnosis("S001", "OK", True),
        ]
        result = summarize_profile("S001", diags)
        assert result["attempt_count"] == 3
        assert result["accuracy"] == 1.0
        assert result["dominant_error_tags"] == []

    def test_mixed_errors(self):
        from app.services.profiles import summarize_profile
        diags = [
            _make_diagnosis("S001", "E01", False),
            _make_diagnosis("S001", "E02", False),
            _make_diagnosis("S001", "E01", False),
            _make_diagnosis("S001", "OK", True),
        ]
        result = summarize_profile("S001", diags)
        assert result["attempt_count"] == 4
        assert result["accuracy"] == 0.25
        assert result["dominant_error_tags"][0] == "E01"

    def test_filters_other_students(self):
        """Only diagnoses for the target student_id should be included."""
        from app.services.profiles import summarize_profile
        diags = [
            _make_diagnosis("S001", "E01", False),
            _make_diagnosis("S002", "E02", False),
            _make_diagnosis("S001", "OK", True),
        ]
        result = summarize_profile("S001", diags)
        assert result["attempt_count"] == 2
        assert result["accuracy"] == 0.5

    def test_dominant_tags_max_3(self):
        from app.services.profiles import summarize_profile
        diags = [
            _make_diagnosis("S001", f"E{i:02d}", False)
            for i in range(1, 8)  # E01-E07
        ]
        result = summarize_profile("S001", diags)
        assert len(result["dominant_error_tags"]) <= 3

    def test_ok_filtered_from_dominant_tags(self):
        from app.services.profiles import summarize_profile
        diags = [
            _make_diagnosis("S001", "OK", True),
            _make_diagnosis("S001", "OK", True),
        ]
        result = summarize_profile("S001", diags)
        assert "OK" not in result["dominant_error_tags"]


# ===========================================================================
# summaries.summarize_class (pure function)
# ===========================================================================
class TestSummarizeClass:
    """Tests for summaries.summarize_class()."""

    def test_empty_diagnoses(self):
        from app.services.summaries import summarize_class
        result = summarize_class([])
        assert result["attempt_count"] == 0
        assert result["top_error_tags"] == []

    def test_all_correct(self):
        from app.services.summaries import summarize_class
        diags = [
            _make_diagnosis("S001", "OK", True),
            _make_diagnosis("S001", "OK", True),
        ]
        result = summarize_class(diags)
        assert result["top_error_tags"] == []

    def test_error_distribution(self):
        from app.services.summaries import summarize_class
        diags = [
            _make_diagnosis("S001", "E01", False),
            _make_diagnosis("S001", "E02", False),
            _make_diagnosis("S001", "E01", False),
            _make_diagnosis("S001", "E01", False),
            _make_diagnosis("S002", "OK", True),
        ]
        result = summarize_class(diags)
        assert result["top_error_tags"][0]["code"] == "E01"
        assert result["top_error_tags"][0]["count"] == 3
        assert result["top_error_tags"][1]["code"] == "E02"

    def test_max_5_error_tags(self):
        from app.services.summaries import summarize_class
        diags = [
            _make_diagnosis("S001", f"E{i:02d}", False)
            for i in range(1, 12)  # E01-E11
        ]
        result = summarize_class(diags)
        assert len(result["top_error_tags"]) <= 5

    def test_teacher_brief_always_present(self):
        from app.services.summaries import summarize_class
        result = summarize_class([])
        assert "teacher_brief" in result
        assert "审核" in result["teacher_brief"]

    def test_correct_answers_excluded_from_errors(self):
        """Only incorrect diagnoses should appear in error tags."""
        from app.services.summaries import summarize_class
        diags = [
            _make_diagnosis("S001", "E01", True),   # correct but tagged E01
            _make_diagnosis("S001", "E02", False),   # incorrect
        ]
        result = summarize_class(diags)
        # Only E02 should appear (the incorrect one)
        codes = [t["code"] for t in result["top_error_tags"]]
        assert "E01" not in codes
        assert "E02" in codes


# ===========================================================================
# mastery_service constants validation
# ===========================================================================
class TestMasteryConstants:
    """Validate BKT parameter constants."""

    def test_all_params_in_valid_range(self):
        from app.services.mastery_service import ERROR_CODE_PARAMS
        for code, params in ERROR_CODE_PARAMS.items():
            assert 0 < params.p_l0 < 1, f"{code} p_l0 out of range"
            assert 0 < params.p_t < 1, f"{code} p_t out of range"
            assert 0 < params.p_g < 0.5, f"{code} p_g too high (guess > 50%)"
            assert 0 < params.p_s < 0.5, f"{code} p_s too high (slip > 50%)"

    def test_forgetting_rate_reasonable(self):
        from app.services.mastery_service import FORGETTING_RATE
        assert 0 < FORGETTING_RATE < 0.1  # less than 10% per day

    def test_11_error_codes_defined(self):
        from app.services.mastery_service import ERROR_CODES
        assert len(ERROR_CODES) == 11
        assert ERROR_CODES[0] == "E01"
        assert ERROR_CODES[-1] == "E11"


# ===========================================================================
# growth_milestone stage constants validation
# ===========================================================================
class TestGrowthStageConstants:
    """Validate growth stage constants."""

    def test_thresholds_and_keys_match_length(self):
        from app.services.growth_milestone import STAGE_THRESHOLDS, STAGE_KEYS
        assert len(STAGE_THRESHOLDS) == len(STAGE_KEYS)

    def test_thresholds_ascending(self):
        from app.services.growth_milestone import STAGE_THRESHOLDS
        for i in range(1, len(STAGE_THRESHOLDS)):
            assert STAGE_THRESHOLDS[i] > STAGE_THRESHOLDS[i - 1]

    def test_first_stage_is_seed(self):
        from app.services.growth_milestone import STAGE_KEYS
        assert STAGE_KEYS[0] == "seed"

    def test_last_stage_is_mature(self):
        from app.services.growth_milestone import STAGE_KEYS
        assert STAGE_KEYS[-1] == "mature"

    def test_9_stages_total(self):
        from app.services.growth_milestone import STAGE_KEYS
        assert len(STAGE_KEYS) == 9


# ===========================================================================
# forest_service.compute_emotional_state
# ===========================================================================
class TestComputeEmotionalState:
    def test_empty_weekly_high_overall_thriving(self):
        from app.services.forest_service import compute_emotional_state
        result = compute_emotional_state([], overall_accuracy=0.92)
        assert result["state"] == "thriving"

    def test_empty_weekly_mid_overall_stable(self):
        from app.services.forest_service import compute_emotional_state
        result = compute_emotional_state([], overall_accuracy=0.60)
        assert result["state"] == "stable"

    def test_empty_weekly_low_overall_wilting(self):
        from app.services.forest_service import compute_emotional_state
        result = compute_emotional_state([], overall_accuracy=0.30)
        assert result["state"] == "wilting"

    def test_single_week_low_overall_wilting(self):
        from app.services.forest_service import compute_emotional_state
        result = compute_emotional_state([{"accuracy": 0.70}])
        assert result["state"] == "wilting"

    def test_strong_upward_trend_thriving(self):
        from app.services.forest_service import compute_emotional_state
        weeks = [
            {"accuracy": 0.50},
            {"accuracy": 0.60},
            {"accuracy": 0.75},
        ]
        result = compute_emotional_state(weeks)
        assert result["state"] == "thriving"

    def test_moderate_upward_trend_happy(self):
        from app.services.forest_service import compute_emotional_state
        weeks = [
            {"accuracy": 0.65},
            {"accuracy": 0.70},
            {"accuracy": 0.75},
        ]
        result = compute_emotional_state(weeks)
        assert result["state"] == "happy"

    def test_flat_trend_stable(self):
        from app.services.forest_service import compute_emotional_state
        weeks = [
            {"accuracy": 0.70},
            {"accuracy": 0.71},
            {"accuracy": 0.70},
        ]
        result = compute_emotional_state(weeks)
        assert result["state"] == "stable"

    def test_moderate_decline_struggling(self):
        from app.services.forest_service import compute_emotional_state
        weeks = [
            {"accuracy": 0.75},
            {"accuracy": 0.65},
            {"accuracy": 0.60},
        ]
        result = compute_emotional_state(weeks)
        assert result["state"] == "struggling"

    def test_moderate_decline_wilting(self):
        from app.services.forest_service import compute_emotional_state
        weeks = [
            {"accuracy": 0.75},
            {"accuracy": 0.70},
            {"accuracy": 0.65},
        ]
        result = compute_emotional_state(weeks)
        assert result["state"] == "wilting"

    def test_steep_decline_struggling(self):
        from app.services.forest_service import compute_emotional_state
        weeks = [
            {"accuracy": 0.85},
            {"accuracy": 0.60},
            {"accuracy": 0.40},
        ]
        result = compute_emotional_state(weeks)
        assert result["state"] == "struggling"

    def test_very_high_overall_thriving(self):
        from app.services.forest_service import compute_emotional_state
        weeks = [
            {"accuracy": 0.94},
            {"accuracy": 0.96},
        ]
        result = compute_emotional_state(weeks, overall_accuracy=0.96)
        assert result["state"] == "thriving"

    def test_intensity_is_rounded(self):
        from app.services.forest_service import compute_emotional_state
        weeks = [
            {"accuracy": 0.50},
            {"accuracy": 0.75},
        ]
        result = compute_emotional_state(weeks)
        intensity_str = str(result["intensity"])
        if "." in intensity_str:
            assert len(intensity_str.split(".")[1]) <= 2


# ===========================================================================
# dify_client._CircuitBreaker
# ===========================================================================
class TestCircuitBreaker:
    def test_initial_state_closed(self):
        from app.services.dify_client import _CircuitBreaker
        cb = _CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        assert cb.should_skip() is False
        assert cb.is_open is False

    def test_opens_after_threshold(self):
        from app.services.dify_client import _CircuitBreaker
        cb = _CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        cb.record_failure()
        cb.record_failure()
        assert cb.should_skip() is False
        cb.record_failure()
        assert cb.is_open is True
        assert cb.should_skip() is True

    def test_success_resets(self):
        from app.services.dify_client import _CircuitBreaker
        cb = _CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.is_open is False
        assert cb.failure_count == 0

    def test_recovery_timeout_allows_probe(self):
        import time
        from app.services.dify_client import _CircuitBreaker
        cb = _CircuitBreaker(failure_threshold=2, recovery_timeout=0.01)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is True
        time.sleep(0.02)
        assert cb.should_skip() is False
        assert cb.is_open is False

    def test_below_threshold_stays_closed(self):
        from app.services.dify_client import _CircuitBreaker
        cb = _CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
        for _ in range(4):
            cb.record_failure()
        assert cb.is_open is False


# ===========================================================================
# utils.json_column, utils.placeholders
# ===========================================================================
class TestUtils:
    def test_json_column_valid(self):
        from app.services.utils import json_column
        row = {"data": '[1, 2, 3]'}
        assert json_column(row, "data") == [1, 2, 3]

    def test_json_column_none_returns_default(self):
        from app.services.utils import json_column
        row = {"data": None}
        assert json_column(row, "data") == []

    def test_json_column_none_custom_default(self):
        from app.services.utils import json_column
        row = {"data": None}
        assert json_column(row, "data", default={}) == {}

    def test_json_column_invalid_returns_default(self):
        from app.services.utils import json_column
        row = {"data": "not-json"}
        assert json_column(row, "data") == []

    def test_json_column_dict_value(self):
        from app.services.utils import json_column
        row = {"data": '{"key": "val"}'}
        assert json_column(row, "data") == {"key": "val"}

    def test_placeholders_zero(self):
        from app.services.utils import placeholders
        assert placeholders(0) == ""

    def test_placeholders_one(self):
        from app.services.utils import placeholders
        assert placeholders(1) == "?"

    def test_placeholders_three(self):
        from app.services.utils import placeholders
        assert placeholders(3) == "?,?,?"


# ===========================================================================
# student_feedback_builder.build_student_guidance
# ===========================================================================
class TestBuildStudentGuidance:
    def test_correct_answer(self):
        from app.pipeline.student_feedback_builder import build_student_guidance
        result = build_student_guidance(
            code=ErrorCode.BASIC_FACT,
            guidance_mode=GuidanceMode.STANDARD,
            diagnosis_feedback="test feedback",
            is_correct=True,
            practice_count=3,
        )
        assert "做对" in result.message
        assert result.key_takeaway != "test feedback"

    def test_wrong_answer(self):
        from app.pipeline.student_feedback_builder import build_student_guidance
        result = build_student_guidance(
            code=ErrorCode.BORROW,
            guidance_mode=GuidanceMode.STANDARD,
            diagnosis_feedback="退位处理有误",
            is_correct=False,
            practice_count=3,
        )
        assert "没关系" in result.message
        assert "退位处理有误" in result.message
        assert "退位处理有误" in result.key_takeaway

    def test_standard_mode_next_step(self):
        from app.pipeline.student_feedback_builder import build_student_guidance
        result = build_student_guidance(
            code=ErrorCode.OPERATION_ORDER,
            guidance_mode=GuidanceMode.STANDARD,
            diagnosis_feedback="",
            is_correct=False,
            practice_count=5,
        )
        assert "5" in result.next_step
        assert "短练习" in result.next_step

    def test_exploration_mode_next_step(self):
        from app.pipeline.student_feedback_builder import build_student_guidance
        result = build_student_guidance(
            code=ErrorCode.CARRY,
            guidance_mode=GuidanceMode.EXPLORATION,
            diagnosis_feedback="",
            is_correct=False,
            practice_count=4,
        )
        assert "变式题" in result.next_step

    def test_challenge_mode_next_step(self):
        from app.pipeline.student_feedback_builder import build_student_guidance
        result = build_student_guidance(
            code=ErrorCode.DECIMAL_FRACTION_UNIT,
            guidance_mode=GuidanceMode.CHALLENGE,
            diagnosis_feedback="",
            is_correct=False,
            practice_count=2,
        )
        assert "别的方法" in result.next_step

    def test_guiding_questions_max_2(self):
        from app.pipeline.student_feedback_builder import build_student_guidance
        result = build_student_guidance(
            code=ErrorCode.BASIC_FACT,
            guidance_mode=GuidanceMode.STANDARD,
            diagnosis_feedback="",
            is_correct=False,
            practice_count=3,
        )
        assert len(result.guiding_questions) <= 2

    def test_unknown_code_falls_back(self):
        from app.pipeline.student_feedback_builder import build_student_guidance
        result = build_student_guidance(
            code=ErrorCode.CONCEPTUAL_UNDERSTANDING,
            guidance_mode=GuidanceMode.STANDARD,
            diagnosis_feedback="",
            is_correct=False,
            practice_count=3,
        )
        assert len(result.guiding_questions) > 0

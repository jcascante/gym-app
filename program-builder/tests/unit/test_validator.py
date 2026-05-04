"""Tests for the validation engine -- written FIRST (TDD RED phase)."""


from src.core.validation.validator import (
    Severity,
    Validator,
)


def _make_session_metrics(
    fatigue: float,
    volume_by_muscle: dict[str, float] | None = None,
) -> dict:
    return {
        "fatigue_score": fatigue,
        "volume_summary": {"hard_sets_weighted": volume_by_muscle or {}},
    }


# ---------------------------------------------------------------------------
# Hard Constraints -- Strength
# ---------------------------------------------------------------------------

class TestMaxWeeklyVolumeByMuscle:
    def test_under_limit_passes(self) -> None:
        validator = Validator()
        violations = validator.check_max_weekly_volume(
            weekly_volume={"quads": 18.0, "glutes": 12.0},
            limits={"quads": 20, "glutes": 20},
        )
        assert len(violations) == 0

    def test_over_limit_detected(self) -> None:
        validator = Validator()
        violations = validator.check_max_weekly_volume(
            weekly_volume={"quads": 26.0, "glutes": 12.0},
            limits={"quads": 20, "glutes": 20},
        )
        assert len(violations) == 1
        assert violations[0].key == "quads"
        assert violations[0].severity == Severity.HARD

    def test_exactly_at_limit_passes(self) -> None:
        validator = Validator()
        violations = validator.check_max_weekly_volume(
            weekly_volume={"quads": 20.0},
            limits={"quads": 20},
        )
        assert len(violations) == 0

    def test_multiple_violations(self) -> None:
        validator = Validator()
        violations = validator.check_max_weekly_volume(
            weekly_volume={"quads": 26.0, "glutes": 22.0},
            limits={"quads": 20, "glutes": 20},
        )
        assert len(violations) == 2


class TestMinWeeklyVolumeByPattern:
    def test_above_min_passes(self) -> None:
        validator = Validator()
        violations = validator.check_min_weekly_volume(
            weekly_volume={"vertical_pull": 6.0, "horizontal_pull": 8.0},
            limits={"vertical_pull": 4, "horizontal_pull": 6},
        )
        assert len(violations) == 0

    def test_below_min_detected(self) -> None:
        validator = Validator()
        violations = validator.check_min_weekly_volume(
            weekly_volume={"vertical_pull": 2.0},
            limits={"vertical_pull": 4},
        )
        assert len(violations) == 1
        assert violations[0].key == "vertical_pull"

    def test_missing_key_treated_as_zero(self) -> None:
        validator = Validator()
        violations = validator.check_min_weekly_volume(
            weekly_volume={},
            limits={"vertical_pull": 4},
        )
        assert len(violations) == 1


class TestMaxFatiguePerSession:
    def test_under_limit_passes(self) -> None:
        validator = Validator()
        violations = validator.check_session_fatigue(
            fatigue=8.5, limit=10.0
        )
        assert len(violations) == 0

    def test_over_limit_detected(self) -> None:
        validator = Validator()
        violations = validator.check_session_fatigue(
            fatigue=12.0, limit=10.0
        )
        assert len(violations) == 1
        assert violations[0].severity == Severity.HARD


class TestMaxFatiguePerWeek:
    def test_under_limit_passes(self) -> None:
        validator = Validator()
        violations = validator.check_weekly_fatigue(
            fatigue=30.0, limit=38.0
        )
        assert len(violations) == 0

    def test_over_limit_detected(self) -> None:
        validator = Validator()
        violations = validator.check_weekly_fatigue(
            fatigue=42.0, limit=38.0
        )
        assert len(violations) == 1


# ---------------------------------------------------------------------------
# Hard Constraints -- Conditioning
# ---------------------------------------------------------------------------

class TestConditioningConstraints:
    def test_intense_minutes_under_limit(self) -> None:
        validator = Validator()
        violations = validator.check_max_intense_minutes(
            intense_minutes=40.0, limit=45.0
        )
        assert len(violations) == 0

    def test_intense_minutes_over_limit(self) -> None:
        validator = Validator()
        violations = validator.check_max_intense_minutes(
            intense_minutes=50.0, limit=45.0
        )
        assert len(violations) == 1

    def test_z2_minutes_above_min(self) -> None:
        validator = Validator()
        violations = validator.check_min_z2_minutes(
            z2_minutes=100.0, limit=90.0
        )
        assert len(violations) == 0

    def test_z2_minutes_below_min(self) -> None:
        validator = Validator()
        violations = validator.check_min_z2_minutes(
            z2_minutes=50.0, limit=90.0
        )
        assert len(violations) == 1


# ---------------------------------------------------------------------------
# Soft Warnings
# ---------------------------------------------------------------------------

class TestSoftWarnings:
    def test_warning_collected_not_hard(self) -> None:
        validator = Validator()
        violations = validator.check_soft_warnings(
            conditions=[
                (True, "Vertical pull volume is below recommended."),
                (False, "This should not appear."),
            ]
        )
        assert len(violations) == 1
        assert violations[0].severity == Severity.SOFT
        assert "Vertical pull" in violations[0].message

    def test_no_warnings_when_all_false(self) -> None:
        validator = Validator()
        violations = validator.check_soft_warnings(
            conditions=[(False, "nope")]
        )
        assert len(violations) == 0


# ---------------------------------------------------------------------------
# Full Validation
# ---------------------------------------------------------------------------

class TestFullValidation:
    def test_valid_plan_no_violations(self) -> None:
        validator = Validator()
        result = validator.validate_week(
            weekly_volume={"quads": 18.0},
            volume_limits_max={"quads": 20},
            volume_limits_min={},
            session_fatigues=[6.0, 7.0, 5.0, 8.0],
            session_fatigue_limit=10.0,
            weekly_fatigue_limit=38.0,
        )
        assert result.is_valid
        assert len(result.hard_violations) == 0

    def test_plan_with_violations(self) -> None:
        validator = Validator()
        result = validator.validate_week(
            weekly_volume={"quads": 26.0},
            volume_limits_max={"quads": 20},
            volume_limits_min={},
            session_fatigues=[12.0, 7.0, 5.0, 8.0],
            session_fatigue_limit=10.0,
            weekly_fatigue_limit=38.0,
        )
        assert not result.is_valid
        assert len(result.hard_violations) >= 2

"""Tests for prescription + load resolver -- written FIRST (TDD RED phase)."""

import pytest

from src.core.prescription.load_resolver import LoadResolver
from src.core.prescription.prescription_resolver import PrescriptionResolver

# ---------------------------------------------------------------------------
# RPE-to-Percentage Table
# ---------------------------------------------------------------------------

class TestRPETable:
    def test_rpe_10_reps_1(self) -> None:
        pct = LoadResolver.rpe_to_percentage(rpe=10, reps=1)
        assert pct == 1.0

    def test_rpe_7_reps_5(self) -> None:
        pct = LoadResolver.rpe_to_percentage(rpe=7, reps=5)
        assert 0.70 < pct < 0.85

    def test_rpe_8_reps_5(self) -> None:
        pct = LoadResolver.rpe_to_percentage(rpe=8, reps=5)
        assert 0.75 < pct < 0.90

    def test_rpe_6_reps_3(self) -> None:
        pct = LoadResolver.rpe_to_percentage(rpe=6, reps=3)
        assert 0.75 < pct < 0.90

    def test_rpe_8point5_reps_5(self) -> None:
        pct = LoadResolver.rpe_to_percentage(rpe=8.5, reps=5)
        assert 0.77 < pct < 0.88

    def test_rpe_must_be_in_range(self) -> None:
        with pytest.raises(ValueError):
            LoadResolver.rpe_to_percentage(rpe=11, reps=5)

    def test_reps_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            LoadResolver.rpe_to_percentage(rpe=8, reps=0)


# ---------------------------------------------------------------------------
# Load Calculation
# ---------------------------------------------------------------------------

class TestLoadCalculation:
    def test_load_from_e1rm(self) -> None:
        load = LoadResolver.compute_load(e1rm=160, rpe=7, reps=5)
        assert 110 < load < 140

    def test_load_from_e1rm_high_rpe(self) -> None:
        load = LoadResolver.compute_load(e1rm=160, rpe=10, reps=1)
        assert load == 160.0

    def test_load_scales_with_e1rm(self) -> None:
        load_light = LoadResolver.compute_load(e1rm=100, rpe=8, reps=5)
        load_heavy = LoadResolver.compute_load(e1rm=200, rpe=8, reps=5)
        assert load_heavy > load_light
        assert abs(load_heavy - 2 * load_light) < 0.01


# ---------------------------------------------------------------------------
# Rounding
# ---------------------------------------------------------------------------

class TestRounding:
    def test_plate_2p5kg_rounds_down(self) -> None:
        result = LoadResolver.round_load(123.3, profile="plate_2p5kg")
        assert result == 122.5

    def test_plate_2p5kg_rounds_up(self) -> None:
        result = LoadResolver.round_load(123.8, profile="plate_2p5kg")
        assert result == 125.0

    def test_plate_2p5kg_exact(self) -> None:
        result = LoadResolver.round_load(120.0, profile="plate_2p5kg")
        assert result == 120.0

    def test_db_2kg(self) -> None:
        result = LoadResolver.round_load(23.5, profile="db_2kg")
        assert result in (22.0, 24.0)

    def test_none_profile_no_rounding(self) -> None:
        result = LoadResolver.round_load(123.456, profile="none")
        assert result == 123.456

    def test_unknown_profile_raises(self) -> None:
        with pytest.raises(ValueError):
            LoadResolver.round_load(100, profile="unknown")


# ---------------------------------------------------------------------------
# Backoff Load
# ---------------------------------------------------------------------------

class TestBackoffLoad:
    def test_backoff_factor(self) -> None:
        top_load = 120.0
        backoff = LoadResolver.compute_backoff_load(
            top_load=top_load,
            factor=0.90,
            rounding_profile="plate_2p5kg",
        )
        assert backoff == 107.5

    def test_backoff_factor_0p88(self) -> None:
        top_load = 190.0
        backoff = LoadResolver.compute_backoff_load(
            top_load=top_load,
            factor=0.88,
            rounding_profile="plate_2p5kg",
        )
        assert backoff == 167.5 or backoff == 167.0

    def test_backoff_no_rounding(self) -> None:
        backoff = LoadResolver.compute_backoff_load(
            top_load=100.0,
            factor=0.90,
            rounding_profile="none",
        )
        assert backoff == 90.0


# ---------------------------------------------------------------------------
# PrescriptionResolver: Top-Set + Backoff Mode
# ---------------------------------------------------------------------------

class TestTopSetBackoff:
    def test_squat_week1(self) -> None:
        resolver = PrescriptionResolver()
        ctx = {
            "week": 1,
            "athlete": {
                "level": "intermediate",
                "e1rm": {"squat": 160},
            },
            "rules": {"rounding_profile": "plate_2p5kg"},
        }
        prescription_def = {
            "mode": "top_set_plus_backoff",
            "output_mapping": {
                "reps_expr": "choose(ctx.week,[5,5,3,5])",
                "target_rpe_expr": "choose(ctx.week,[7,8,8.5,6])",
                "backoff_sets_expr": "choose(ctx.week,[3,3,4,2])",
                "backoff_reps_expr": "choose(ctx.week,[5,5,3,5])",
                "backoff_load_factor_expr": "0.90",
            },
        }
        result = resolver.resolve(
            prescription_def=prescription_def,
            ctx=ctx,
            e1rm_key="squat",
        )
        assert result["top_set"]["reps"] == 5
        assert result["top_set"]["target_rpe"] == 7
        assert result["top_set"]["sets"] == 1
        assert result["top_set"]["load_kg"] > 100
        assert result["top_set"]["load_kg"] % 2.5 == 0
        assert len(result["backoff"]) == 1
        assert result["backoff"][0]["sets"] == 3
        assert result["backoff"][0]["load_kg"] < result["top_set"]["load_kg"]
        assert result["rounding_profile"] == "plate_2p5kg"

    def test_squat_week3_heavier(self) -> None:
        resolver = PrescriptionResolver()
        ctx = {
            "week": 3,
            "athlete": {
                "level": "intermediate",
                "e1rm": {"squat": 160},
            },
            "rules": {"rounding_profile": "plate_2p5kg"},
        }
        prescription_def = {
            "mode": "top_set_plus_backoff",
            "output_mapping": {
                "reps_expr": "choose(ctx.week,[5,5,3,5])",
                "target_rpe_expr": "choose(ctx.week,[7,8,8.5,6])",
                "backoff_sets_expr": "choose(ctx.week,[3,3,4,2])",
                "backoff_reps_expr": "choose(ctx.week,[5,5,3,5])",
                "backoff_load_factor_expr": "0.90",
            },
        }
        result = resolver.resolve(
            prescription_def=prescription_def,
            ctx=ctx,
            e1rm_key="squat",
        )
        assert result["top_set"]["reps"] == 3
        assert result["top_set"]["target_rpe"] == 8.5
        assert result["backoff"][0]["sets"] == 4


# ---------------------------------------------------------------------------
# PrescriptionResolver: Reps-Range-RIR Mode
# ---------------------------------------------------------------------------

class TestRepsRangeRIR:
    def test_accessory_hyp(self) -> None:
        resolver = PrescriptionResolver()
        ctx = {
            "week": 1,
            "rules": {"accessory_rir_target": 2},
        }
        prescription_def = {
            "mode": "reps_range_rir",
            "output_mapping": {
                "sets_expr": "choose(ctx.week,[3,3,4,2])",
                "reps_min_expr": "10",
                "reps_max_expr": "15",
                "target_rir_expr": "ctx.rules.accessory_rir_target",
            },
        }
        result = resolver.resolve(
            prescription_def=prescription_def,
            ctx=ctx,
        )
        assert result["sets"] == 3
        assert result["reps_range"] == [10, 15]
        assert result["target_rir"] == 2

    def test_secondary_strength(self) -> None:
        resolver = PrescriptionResolver()
        ctx = {"week": 2}
        prescription_def = {
            "mode": "reps_range_rir",
            "output_mapping": {
                "sets_expr": "choose(ctx.week,[3,3,4,2])",
                "reps_min_expr": "5",
                "reps_max_expr": "8",
                "target_rir_expr": "2",
            },
        }
        result = resolver.resolve(
            prescription_def=prescription_def,
            ctx=ctx,
        )
        assert result["sets"] == 3
        assert result["reps_range"] == [5, 8]
        assert result["target_rir"] == 2


# ---------------------------------------------------------------------------
# PrescriptionResolver: Conditioning Steady State
# ---------------------------------------------------------------------------

class TestConditioningSteadyState:
    def test_z2_steady_week1(self) -> None:
        resolver = PrescriptionResolver()
        ctx = {
            "week": 1,
            "conditioning": {
                "method": "HR_ZONES",
                "hr_zone_formula": "KARVONEN_HRR",
                "hr_max": 190,
                "hr_rest": 55,
            },
        }
        prescription_def = {
            "mode": "steady_state",
            "output_mapping": {
                "duration_minutes_expr": "choose(ctx.week,[35,40,45,30])",
                "intensity_target_expr": "z(2)",
                "notes_expr": "'Conversational pace'",
            },
        }
        result = resolver.resolve(
            prescription_def=prescription_def,
            ctx=ctx,
        )
        assert result["duration_minutes"] == 35
        assert result["intensity"]["target"] == "z(2)"
        assert result["notes"] == "Conversational pace"

    def test_z2_steady_week4_deload(self) -> None:
        resolver = PrescriptionResolver()
        ctx = {
            "week": 4,
            "conditioning": {
                "method": "HR_ZONES",
                "hr_zone_formula": "KARVONEN_HRR",
                "hr_max": 190,
                "hr_rest": 55,
            },
        }
        prescription_def = {
            "mode": "steady_state",
            "output_mapping": {
                "duration_minutes_expr": "choose(ctx.week,[35,40,45,30])",
                "intensity_target_expr": "z(2)",
                "notes_expr": "'Conversational pace'",
            },
        }
        result = resolver.resolve(
            prescription_def=prescription_def,
            ctx=ctx,
        )
        assert result["duration_minutes"] == 30


# ---------------------------------------------------------------------------
# PrescriptionResolver: Conditioning Intervals
# ---------------------------------------------------------------------------

class TestConditioningIntervals:
    def test_threshold_week1(self) -> None:
        resolver = PrescriptionResolver()
        ctx = {
            "week": 1,
            "conditioning": {
                "method": "HR_ZONES",
                "hr_zone_formula": "KARVONEN_HRR",
                "hr_max": 190,
                "hr_rest": 55,
            },
        }
        prescription_def = {
            "mode": "intervals",
            "output_mapping": {
                "warmup_minutes_expr": "10",
                "work_intervals_expr": "choose(ctx.week,[4,5,6,3])",
                "work_minutes_expr": "choose(ctx.week,[4,4,4,3])",
                "rest_minutes_expr": "2",
                "intensity_target_expr": "thr()",
                "cooldown_minutes_expr": "8",
                "notes_expr": "'Sustainable hard effort'",
            },
        }
        result = resolver.resolve(
            prescription_def=prescription_def,
            ctx=ctx,
        )
        assert result["warmup_minutes"] == 10
        assert result["work"]["intervals"] == 4
        assert result["work"]["minutes_each"] == 4
        assert result["work"]["intensity"]["target"] == "thr()"
        assert result["rest_minutes"] == 2
        assert result["cooldown_minutes"] == 8
        assert result["notes"] == "Sustainable hard effort"

    def test_vo2_week2(self) -> None:
        resolver = PrescriptionResolver()
        ctx = {
            "week": 2,
            "conditioning": {
                "method": "HR_ZONES",
                "hr_zone_formula": "KARVONEN_HRR",
                "hr_max": 190,
                "hr_rest": 55,
            },
        }
        prescription_def = {
            "mode": "intervals",
            "output_mapping": {
                "warmup_minutes_expr": "10",
                "work_intervals_expr": "choose(ctx.week,[6,7,8,5])",
                "work_seconds_expr": "60",
                "rest_seconds_expr": "90",
                "intensity_target_expr": "vo2()",
                "cooldown_minutes_expr": "8",
                "notes_expr": "'Very hard but controlled'",
            },
        }
        result = resolver.resolve(
            prescription_def=prescription_def,
            ctx=ctx,
        )
        assert result["work"]["intervals"] == 7
        assert result["work"]["seconds_each"] == 60
        assert result["rest_seconds"] == 90

"""Tests for the metrics engine -- written FIRST (TDD RED phase)."""

from src.core.metrics.metrics_engine import MetricsEngine
from src.models.exercise_library import Exercise


def _make_exercise(
    id: str,
    fatigue_cost: float = 0.5,
    muscles: dict[str, float] | None = None,
) -> Exercise:
    return Exercise(
        id=id,
        name=id.replace("_", " ").title(),
        patterns=["squat"],
        muscles=muscles or {"quads": 1.0},
        equipment=[],
        swap_group=None,
        fatigue_cost=fatigue_cost,
        contraindications=[],
        tags=[],
    )


# ---------------------------------------------------------------------------
# Fatigue Scoring
# ---------------------------------------------------------------------------

class TestFatigueScoring:
    def test_single_set_fatigue(self) -> None:
        engine = MetricsEngine()
        ex = _make_exercise("back_squat", fatigue_cost=0.9)
        score = engine.compute_set_fatigue(
            exercise=ex,
            rpe=7,
            sets=1,
        )
        assert 0.5 < score < 1.5

    def test_multiple_sets_scale_fatigue(self) -> None:
        engine = MetricsEngine()
        ex = _make_exercise("back_squat", fatigue_cost=0.9)
        single = engine.compute_set_fatigue(exercise=ex, rpe=7, sets=1)
        triple = engine.compute_set_fatigue(exercise=ex, rpe=7, sets=3)
        assert abs(triple - 3 * single) < 0.01

    def test_higher_rpe_higher_fatigue(self) -> None:
        engine = MetricsEngine()
        ex = _make_exercise("back_squat", fatigue_cost=0.9)
        low = engine.compute_set_fatigue(exercise=ex, rpe=6, sets=1)
        high = engine.compute_set_fatigue(exercise=ex, rpe=9, sets=1)
        assert high > low

    def test_higher_fatigue_cost_higher_fatigue(self) -> None:
        engine = MetricsEngine()
        light = _make_exercise("leg_ext", fatigue_cost=0.2)
        heavy = _make_exercise("squat", fatigue_cost=0.9)
        light_score = engine.compute_set_fatigue(
            exercise=light, rpe=7, sets=3
        )
        heavy_score = engine.compute_set_fatigue(
            exercise=heavy, rpe=7, sets=3
        )
        assert heavy_score > light_score

    def test_accessory_low_fatigue(self) -> None:
        engine = MetricsEngine()
        ex = _make_exercise("leg_extension", fatigue_cost=0.2)
        score = engine.compute_set_fatigue(exercise=ex, rpe=6, sets=3)
        assert score < 1.0


# ---------------------------------------------------------------------------
# Session Fatigue
# ---------------------------------------------------------------------------

class TestSessionFatigue:
    def test_session_fatigue_sums_blocks(self) -> None:
        engine = MetricsEngine()
        blocks = [
            {
                "exercise": _make_exercise("back_squat", fatigue_cost=0.9),
                "sets": 4,
                "rpe": 7,
            },
            {
                "exercise": _make_exercise("rdl", fatigue_cost=0.6),
                "sets": 3,
                "rpe": 7,
            },
            {
                "exercise": _make_exercise(
                    "leg_ext", fatigue_cost=0.2
                ),
                "sets": 3,
                "rpe": 6,
            },
        ]
        fatigue = engine.compute_session_fatigue(blocks)
        assert fatigue > 3.0
        assert fatigue < 15.0


# ---------------------------------------------------------------------------
# Volume Summary (Hard Sets Weighted)
# ---------------------------------------------------------------------------

class TestVolumeSummary:
    def test_volume_summary_by_muscle(self) -> None:
        engine = MetricsEngine()
        blocks = [
            {
                "exercise": _make_exercise(
                    "back_squat",
                    muscles={"quads": 1.0, "glutes": 0.7, "erectors": 0.4},
                ),
                "sets": 4,
            },
            {
                "exercise": _make_exercise(
                    "leg_ext",
                    muscles={"quads": 1.0},
                ),
                "sets": 3,
            },
        ]
        volume = engine.compute_volume_summary(blocks)
        assert volume["quads"] == 4 * 1.0 + 3 * 1.0
        assert volume["glutes"] == 4 * 0.7
        assert volume["erectors"] == 4 * 0.4

    def test_empty_blocks_no_volume(self) -> None:
        engine = MetricsEngine()
        volume = engine.compute_volume_summary([])
        assert volume == {}


# ---------------------------------------------------------------------------
# Tonnage
# ---------------------------------------------------------------------------

class TestTonnage:
    def test_tonnage_calculation(self) -> None:
        engine = MetricsEngine()
        blocks = [
            {
                "exercise_id": "back_squat",
                "sets": 1,
                "reps": 5,
                "load_kg": 120.0,
            },
            {
                "exercise_id": "back_squat",
                "sets": 3,
                "reps": 5,
                "load_kg": 107.5,
            },
        ]
        tonnage = engine.compute_tonnage(blocks)
        expected = (1 * 5 * 120.0) + (3 * 5 * 107.5)
        assert tonnage["back_squat"] == expected

    def test_tonnage_multiple_exercises(self) -> None:
        engine = MetricsEngine()
        blocks = [
            {
                "exercise_id": "back_squat",
                "sets": 1,
                "reps": 5,
                "load_kg": 120.0,
            },
            {
                "exercise_id": "bench_press",
                "sets": 1,
                "reps": 6,
                "load_kg": 85.0,
            },
        ]
        tonnage = engine.compute_tonnage(blocks)
        assert "back_squat" in tonnage
        assert "bench_press" in tonnage
        assert tonnage["back_squat"] == 600.0
        assert tonnage["bench_press"] == 510.0

    def test_tonnage_no_load_excluded(self) -> None:
        engine = MetricsEngine()
        blocks = [
            {"exercise_id": "leg_ext", "sets": 3, "reps": 12},
        ]
        tonnage = engine.compute_tonnage(blocks)
        assert tonnage == {}


# ---------------------------------------------------------------------------
# Conditioning Metrics
# ---------------------------------------------------------------------------

class TestConditioningMetrics:
    def test_conditioning_fatigue_by_duration(self) -> None:
        engine = MetricsEngine()
        score = engine.compute_conditioning_fatigue(
            duration_minutes=35,
            intensity_level=2,
        )
        assert 0.1 < score < 0.5

    def test_higher_intensity_higher_fatigue(self) -> None:
        engine = MetricsEngine()
        z2 = engine.compute_conditioning_fatigue(
            duration_minutes=35, intensity_level=2
        )
        thr = engine.compute_conditioning_fatigue(
            duration_minutes=35, intensity_level=4
        )
        assert thr > z2

    def test_longer_duration_higher_fatigue(self) -> None:
        engine = MetricsEngine()
        short = engine.compute_conditioning_fatigue(
            duration_minutes=20, intensity_level=2
        )
        long = engine.compute_conditioning_fatigue(
            duration_minutes=45, intensity_level=2
        )
        assert long > short

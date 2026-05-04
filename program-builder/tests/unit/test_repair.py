"""Tests for the repair engine -- written FIRST (TDD RED phase)."""


from src.core.repair.engine import RepairEngine, RepairResult
from src.core.repair.strategies import (
    DropOptionalBlocks,
    ReduceAccessorySets,
    ReduceBackoffSets,
    ReduceIntervalRepeats,
    SwapToLowerFatigueVariant,
)
from src.models.exercise_library import Exercise


def _make_exercise(
    id: str,
    fatigue_cost: float = 0.5,
    swap_group: str | None = None,
    tags: list[str] | None = None,
) -> Exercise:
    return Exercise(
        id=id,
        name=id.replace("_", " ").title(),
        patterns=["squat"],
        muscles={"quads": 1.0},
        equipment=[],
        swap_group=swap_group,
        fatigue_cost=fatigue_cost,
        contraindications=[],
        tags=tags or [],
    )


# ---------------------------------------------------------------------------
# ReduceAccessorySets
# ---------------------------------------------------------------------------

class TestReduceAccessorySets:
    def test_reduces_accessory_sets(self) -> None:
        strategy = ReduceAccessorySets()
        blocks = [
            {"type": "main_lift", "sets": 4},
            {"type": "accessory", "sets": 3},
            {"type": "accessory", "sets": 3},
        ]
        modified = strategy.apply(blocks)
        accessory_sets = [
            b["sets"] for b in modified if b["type"] == "accessory"
        ]
        assert all(s < 3 for s in accessory_sets)

    def test_does_not_touch_main_lift(self) -> None:
        strategy = ReduceAccessorySets()
        blocks = [
            {"type": "main_lift", "sets": 4},
            {"type": "accessory", "sets": 3},
        ]
        modified = strategy.apply(blocks)
        main = [b for b in modified if b["type"] == "main_lift"]
        assert main[0]["sets"] == 4

    def test_does_not_reduce_below_1(self) -> None:
        strategy = ReduceAccessorySets()
        blocks = [{"type": "accessory", "sets": 1}]
        modified = strategy.apply(blocks)
        assert modified is None


# ---------------------------------------------------------------------------
# SwapToLowerFatigueVariant
# ---------------------------------------------------------------------------

class TestSwapToLowerFatigueVariant:
    def test_swaps_to_lower_fatigue(self) -> None:
        heavy = _make_exercise(
            "back_squat", fatigue_cost=0.9, swap_group="squat_main"
        )
        light = _make_exercise(
            "front_squat", fatigue_cost=0.7, swap_group="squat_main"
        )
        strategy = SwapToLowerFatigueVariant(
            available_exercises=[heavy, light]
        )
        block = {
            "exercise": heavy,
            "type": "main_lift",
        }
        result = strategy.apply_to_block(block)
        assert result is not None
        assert result["exercise"].fatigue_cost < 0.9

    def test_no_swap_when_already_lowest(self) -> None:
        light = _make_exercise(
            "front_squat", fatigue_cost=0.7, swap_group="squat_main"
        )
        strategy = SwapToLowerFatigueVariant(
            available_exercises=[light]
        )
        block = {"exercise": light, "type": "main_lift"}
        result = strategy.apply_to_block(block)
        assert result is None


# ---------------------------------------------------------------------------
# ReduceBackoffSets
# ---------------------------------------------------------------------------

class TestReduceBackoffSets:
    def test_reduces_backoff_sets(self) -> None:
        strategy = ReduceBackoffSets()
        prescription = {
            "top_set": {"sets": 1, "reps": 5, "load_kg": 120},
            "backoff": [{"sets": 3, "reps": 5, "load_kg": 107.5}],
        }
        result = strategy.apply(prescription)
        assert result is not None
        assert result["backoff"][0]["sets"] < 3

    def test_does_not_reduce_below_1(self) -> None:
        strategy = ReduceBackoffSets()
        prescription = {
            "top_set": {"sets": 1, "reps": 5, "load_kg": 120},
            "backoff": [{"sets": 1, "reps": 5, "load_kg": 107.5}],
        }
        result = strategy.apply(prescription)
        assert result is None


# ---------------------------------------------------------------------------
# DropOptionalBlocks
# ---------------------------------------------------------------------------

class TestDropOptionalBlocks:
    def test_drops_optional_block(self) -> None:
        strategy = DropOptionalBlocks()
        blocks = [
            {"type": "main_lift", "optional": False},
            {"type": "accessory", "optional": True},
        ]
        result = strategy.apply(blocks)
        assert result is not None
        assert len(result) == 1
        assert result[0]["type"] == "main_lift"

    def test_no_optional_blocks_returns_none(self) -> None:
        strategy = DropOptionalBlocks()
        blocks = [{"type": "main_lift", "optional": False}]
        result = strategy.apply(blocks)
        assert result is None


# ---------------------------------------------------------------------------
# ReduceIntervalRepeats
# ---------------------------------------------------------------------------

class TestReduceIntervalRepeats:
    def test_reduces_intervals(self) -> None:
        strategy = ReduceIntervalRepeats()
        prescription = {
            "work": {"intervals": 6, "minutes_each": 4},
            "warmup_minutes": 10,
            "cooldown_minutes": 8,
        }
        result = strategy.apply(prescription)
        assert result is not None
        assert result["work"]["intervals"] < 6

    def test_does_not_reduce_below_2(self) -> None:
        strategy = ReduceIntervalRepeats()
        prescription = {
            "work": {"intervals": 2, "minutes_each": 4},
        }
        result = strategy.apply(prescription)
        assert result is None


# ---------------------------------------------------------------------------
# RepairEngine
# ---------------------------------------------------------------------------

class TestRepairEngine:
    def test_strategies_applied_in_order(self) -> None:
        engine = RepairEngine(
            strategy_order=[
                "reduce_accessory_sets",
                "drop_optional_blocks",
            ],
            max_repairs_per_session=10,
            max_repairs_per_plan=50,
        )
        assert engine.strategy_names == [
            "reduce_accessory_sets",
            "drop_optional_blocks",
        ]

    def test_respects_max_repairs_per_session(self) -> None:
        engine = RepairEngine(
            strategy_order=["reduce_accessory_sets"],
            max_repairs_per_session=2,
            max_repairs_per_plan=50,
        )
        session_blocks = [
            {"type": "accessory", "sets": 10},
            {"type": "accessory", "sets": 10},
        ]
        result = engine.repair_session(session_blocks)
        assert isinstance(result, RepairResult)
        assert result.repairs_applied <= 2

    def test_respects_max_repairs_per_plan(self) -> None:
        engine = RepairEngine(
            strategy_order=["reduce_accessory_sets"],
            max_repairs_per_session=10,
            max_repairs_per_plan=3,
        )
        assert engine.max_repairs_per_plan == 3

    def test_returns_repairs_list(self) -> None:
        engine = RepairEngine(
            strategy_order=["reduce_accessory_sets"],
            max_repairs_per_session=10,
            max_repairs_per_plan=50,
        )
        session_blocks = [
            {"type": "accessory", "sets": 4},
        ]
        result = engine.repair_session(session_blocks)
        assert isinstance(result.repairs, list)

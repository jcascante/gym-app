"""Repair engine: applies strategies in order to fix constraint violations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.repair.strategies import (
    DropOptionalBlocks,
    ReduceAccessorySets,
    ReduceBackoffSets,
    ReduceIntervalRepeats,
)


@dataclass
class RepairAction:
    strategy: str
    description: str


@dataclass
class RepairResult:
    blocks: list[dict[str, Any]]
    repairs: list[RepairAction] = field(default_factory=list)
    repairs_applied: int = 0
    exhausted: bool = False


STRATEGY_REGISTRY: dict[str, type] = {
    "reduce_accessory_sets": ReduceAccessorySets,
    "drop_optional_blocks": DropOptionalBlocks,
    "reduce_backoff_sets": ReduceBackoffSets,
    "reduce_interval_repeats": ReduceIntervalRepeats,
}


class RepairEngine:
    def __init__(
        self,
        strategy_order: list[str],
        max_repairs_per_session: int = 10,
        max_repairs_per_plan: int = 50,
    ) -> None:
        self._strategy_order = strategy_order
        self._max_session = max_repairs_per_session
        self._max_plan = max_repairs_per_plan
        self._plan_repairs = 0

    @property
    def strategy_names(self) -> list[str]:
        return list(self._strategy_order)

    @property
    def max_repairs_per_plan(self) -> int:
        return self._max_plan

    def repair_session(
        self, session_blocks: list[dict[str, Any]]
    ) -> RepairResult:
        result = RepairResult(blocks=list(session_blocks))
        repairs_this_session = 0

        for strategy_name in self._strategy_order:
            if repairs_this_session >= self._max_session:
                break
            if self._plan_repairs >= self._max_plan:
                result.exhausted = True
                break

            if strategy_name not in STRATEGY_REGISTRY:
                continue

            strategy_cls = STRATEGY_REGISTRY[strategy_name]

            if strategy_name == "reduce_accessory_sets":
                strategy = strategy_cls()
                modified = strategy.apply(result.blocks)
                if modified is not None:
                    result.blocks = modified
                    result.repairs.append(
                        RepairAction(
                            strategy=strategy_name,
                            description="Reduced accessory sets by 1",
                        )
                    )
                    repairs_this_session += 1
                    self._plan_repairs += 1

            elif strategy_name == "drop_optional_blocks":
                strategy = strategy_cls()
                modified = strategy.apply(result.blocks)
                if modified is not None:
                    result.blocks = modified
                    result.repairs.append(
                        RepairAction(
                            strategy=strategy_name,
                            description="Dropped optional blocks",
                        )
                    )
                    repairs_this_session += 1
                    self._plan_repairs += 1

        result.repairs_applied = repairs_this_session
        return result

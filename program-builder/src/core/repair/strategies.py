"""Repair strategies for constraint violations."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.models.exercise_library import Exercise


class ReduceAccessorySets:
    """Reduce sets on accessory blocks by 1 each."""

    def apply(self, blocks: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        modified = copy.deepcopy(blocks)
        changed = False
        for block in modified:
            if block.get("type") == "accessory" and block.get("sets", 1) > 1:
                block["sets"] -= 1
                changed = True
        return modified if changed else None


class SwapToLowerFatigueVariant:
    """Swap an exercise to a lower-fatigue variant in the same swap group."""

    def __init__(self, available_exercises: list[Exercise]) -> None:
        self._exercises = available_exercises

    def apply_to_block(
        self, block: dict[str, Any]
    ) -> dict[str, Any] | None:
        current: Exercise = block["exercise"]
        if current.swap_group is None:
            return None

        candidates = [
            ex
            for ex in self._exercises
            if ex.swap_group == current.swap_group
            and ex.fatigue_cost < current.fatigue_cost
        ]
        if not candidates:
            return None

        best = min(candidates, key=lambda ex: ex.fatigue_cost)
        result = copy.deepcopy(block)
        result["exercise"] = best
        return result


class ReduceBackoffSets:
    """Reduce backoff sets by 1."""

    def apply(self, prescription: dict[str, Any]) -> dict[str, Any] | None:
        result = copy.deepcopy(prescription)
        backoff = result.get("backoff", [])
        changed = False
        for entry in backoff:
            if entry.get("sets", 1) > 1:
                entry["sets"] -= 1
                changed = True
        return result if changed else None


class DropOptionalBlocks:
    """Remove blocks marked as optional."""

    def apply(self, blocks: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        remaining = [b for b in blocks if not b.get("optional", False)]
        if len(remaining) == len(blocks):
            return None
        return remaining


class ReduceIntervalRepeats:
    """Reduce interval count by 1 for conditioning prescriptions."""

    def apply(self, prescription: dict[str, Any]) -> dict[str, Any] | None:
        result = copy.deepcopy(prescription)
        work = result.get("work", {})
        intervals = work.get("intervals", 0)
        if intervals > 2:
            work["intervals"] = intervals - 1
            return result
        return None

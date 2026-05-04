"""Metrics engine: fatigue scoring, volume aggregation, tonnage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.models.exercise_library import Exercise


# RPE -> intensity factor for fatigue model
_INTENSITY_FACTOR: dict[float, float] = {
    6: 0.6, 6.5: 0.7, 7: 0.8, 7.5: 0.85, 8: 0.9,
    8.5: 0.95, 9: 1.0, 9.5: 1.05, 10: 1.1,
}


class MetricsEngine:
    def compute_set_fatigue(
        self,
        exercise: Exercise,
        rpe: float,
        sets: int,
    ) -> float:
        intensity = self._intensity_factor(rpe)
        return round(exercise.fatigue_cost * intensity * sets, 4)

    def compute_session_fatigue(
        self, blocks: list[dict[str, Any]]
    ) -> float:
        total = 0.0
        for block in blocks:
            total += self.compute_set_fatigue(
                exercise=block["exercise"],
                rpe=block.get("rpe", 7),
                sets=block.get("sets", 1),
            )
        return round(total, 2)

    def compute_volume_summary(
        self, blocks: list[dict[str, Any]]
    ) -> dict[str, float]:
        volume: dict[str, float] = {}
        for block in blocks:
            ex: Exercise = block["exercise"]
            sets = block.get("sets", 1)
            for muscle, activation in ex.muscles.items():
                volume[muscle] = volume.get(muscle, 0) + sets * activation
        return {k: round(v, 2) for k, v in volume.items()}

    def compute_tonnage(
        self, blocks: list[dict[str, Any]]
    ) -> dict[str, float]:
        tonnage: dict[str, float] = {}
        for block in blocks:
            load = block.get("load_kg")
            if load is None:
                continue
            ex_id = block["exercise_id"]
            sets = block.get("sets", 1)
            reps = block.get("reps", 1)
            tonnage[ex_id] = tonnage.get(ex_id, 0) + sets * reps * load
        return {k: round(v, 2) for k, v in tonnage.items()}

    def compute_conditioning_fatigue(
        self,
        duration_minutes: int,
        intensity_level: int,
    ) -> float:
        base = duration_minutes / 60.0
        intensity_mult = 0.5 + intensity_level * 0.15
        return round(base * intensity_mult, 4)

    def _intensity_factor(self, rpe: float) -> float:
        if rpe in _INTENSITY_FACTOR:
            return _INTENSITY_FACTOR[rpe]
        lower = max(k for k in _INTENSITY_FACTOR if k <= rpe)
        upper = min(k for k in _INTENSITY_FACTOR if k >= rpe)
        if lower == upper:
            return _INTENSITY_FACTOR[lower]
        lo = _INTENSITY_FACTOR[lower]
        hi = _INTENSITY_FACTOR[upper]
        frac = (rpe - lower) / (upper - lower)
        return lo + (hi - lo) * frac

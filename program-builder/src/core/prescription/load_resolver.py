"""Load calculation: RPE tables, e1RM-based load computation, rounding."""

from __future__ import annotations

import math

RPE_TABLE: dict[float, dict[int, float]] = {
    10: {
        1: 1.00, 2: 0.955, 3: 0.922, 4: 0.892, 5: 0.863,
        6: 0.837, 7: 0.811, 8: 0.786, 9: 0.762, 10: 0.739,
    },
    9.5: {
        1: 0.978, 2: 0.939, 3: 0.907, 4: 0.878, 5: 0.850,
        6: 0.824, 7: 0.799, 8: 0.774, 9: 0.751, 10: 0.723,
    },
    9: {
        1: 0.955, 2: 0.922, 3: 0.892, 4: 0.863, 5: 0.837,
        6: 0.811, 7: 0.786, 8: 0.762, 9: 0.739, 10: 0.707,
    },
    8.5: {
        1: 0.939, 2: 0.907, 3: 0.878, 4: 0.850, 5: 0.824,
        6: 0.799, 7: 0.774, 8: 0.751, 9: 0.723, 10: 0.694,
    },
    8: {
        1: 0.922, 2: 0.892, 3: 0.863, 4: 0.837, 5: 0.811,
        6: 0.786, 7: 0.762, 8: 0.739, 9: 0.707, 10: 0.680,
    },
    7.5: {
        1: 0.907, 2: 0.878, 3: 0.850, 4: 0.824, 5: 0.799,
        6: 0.774, 7: 0.751, 8: 0.723, 9: 0.694, 10: 0.667,
    },
    7: {
        1: 0.892, 2: 0.863, 3: 0.837, 4: 0.811, 5: 0.786,
        6: 0.762, 7: 0.739, 8: 0.707, 9: 0.680, 10: 0.653,
    },
    6.5: {
        1: 0.878, 2: 0.850, 3: 0.824, 4: 0.799, 5: 0.774,
        6: 0.751, 7: 0.723, 8: 0.694, 9: 0.667, 10: 0.640,
    },
    6: {
        1: 0.863, 2: 0.837, 3: 0.811, 4: 0.786, 5: 0.762,
        6: 0.739, 7: 0.707, 8: 0.680, 9: 0.653, 10: 0.627,
    },
}

ROUNDING_PROFILES: dict[str, float | None] = {
    "none": None,
    "plate_2p5kg": 2.5,
    "db_2kg": 2.0,
    "kb_4kg": 4.0,
}


class LoadResolver:
    @staticmethod
    def rpe_to_percentage(rpe: float, reps: int) -> float:
        if rpe < 6 or rpe > 10:
            raise ValueError(f"RPE must be between 6 and 10, got {rpe}")
        if reps < 1 or reps > 10:
            raise ValueError(f"Reps must be between 1 and 10, got {reps}")

        if rpe in RPE_TABLE and reps in RPE_TABLE[rpe]:
            return RPE_TABLE[rpe][reps]

        lower_rpe = math.floor(rpe * 2) / 2
        upper_rpe = math.ceil(rpe * 2) / 2
        if lower_rpe == upper_rpe:
            return RPE_TABLE[lower_rpe][reps]

        lo = RPE_TABLE[lower_rpe][reps]
        hi = RPE_TABLE[upper_rpe][reps]
        frac = (rpe - lower_rpe) / 0.5
        return lo + (hi - lo) * frac

    @staticmethod
    def compute_load(e1rm: float, rpe: float, reps: int) -> float:
        pct = LoadResolver.rpe_to_percentage(rpe, reps)
        return round(e1rm * pct, 2)

    @staticmethod
    def round_load(load: float, profile: str) -> float:
        if profile not in ROUNDING_PROFILES:
            raise ValueError(
                f"Unknown rounding profile '{profile}'. "
                f"Available: {list(ROUNDING_PROFILES.keys())}"
            )
        increment = ROUNDING_PROFILES[profile]
        if increment is None:
            return load
        return round(round(load / increment) * increment, 2)

    @staticmethod
    def compute_backoff_load(
        top_load: float, factor: float, rounding_profile: str
    ) -> float:
        raw = top_load * factor
        return LoadResolver.round_load(raw, rounding_profile)

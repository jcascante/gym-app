"""Resolve prescription definitions into concrete values using the expression engine."""

from __future__ import annotations

from typing import Any

from src.core.expression.evaluator import ExpressionEvaluator
from src.core.prescription.load_resolver import LoadResolver


class PrescriptionResolver:
    def __init__(self) -> None:
        self._evaluator = ExpressionEvaluator()

    def resolve(
        self,
        prescription_def: dict[str, Any],
        ctx: dict[str, Any],
        e1rm_key: str | None = None,
    ) -> dict[str, Any]:
        mode = prescription_def["mode"]
        mapping = prescription_def.get("output_mapping", {})

        if mode == "top_set_plus_backoff":
            return self._resolve_top_set_backoff(mapping, ctx, e1rm_key)
        if mode == "reps_range_rir":
            return self._resolve_reps_range_rir(mapping, ctx)
        if mode == "reps_range_rir_multi":
            variables = prescription_def.get("variables", {}) or {}
            merged = {**variables, **mapping}
            if "sets_expr" not in merged and "per_exercise_sets_expr" in merged:
                merged["sets_expr"] = merged["per_exercise_sets_expr"]
            return self._resolve_reps_range_rir(merged, ctx)
        if mode == "steady_state":
            return self._resolve_steady_state(mapping, ctx)
        if mode == "intervals":
            return self._resolve_intervals(mapping, ctx)
        if mode == "conditional_block":
            return self._resolve_top_set_backoff(mapping, ctx, e1rm_key)

        raise ValueError(f"Unknown prescription mode: {mode}")

    def _eval(self, expr: str, ctx: dict[str, Any]) -> Any:
        return self._evaluator.evaluate(expr, ctx=ctx)

    def _resolve_top_set_backoff(
        self,
        mapping: dict[str, str],
        ctx: dict[str, Any],
        e1rm_key: str | None,
    ) -> dict[str, Any]:
        sets = int(self._eval(mapping["sets_expr"], ctx)) if "sets_expr" in mapping else 1
        reps = int(self._eval(mapping["reps_expr"], ctx))
        target_rpe = float(self._eval(mapping["target_rpe_expr"], ctx))
        backoff_sets = int(self._eval(mapping["backoff_sets_expr"], ctx))
        backoff_reps = int(self._eval(mapping["backoff_reps_expr"], ctx))
        backoff_factor = float(
            self._eval(mapping["backoff_load_factor_expr"], ctx)
        )

        rounding = ctx.get("rules", {}).get("rounding_profile", "none")
        e1rm = self._get_e1rm(ctx, e1rm_key)

        raw_load = LoadResolver.compute_load(e1rm, target_rpe, reps)
        top_load = LoadResolver.round_load(raw_load, rounding)
        backoff_load = LoadResolver.compute_backoff_load(
            top_load, backoff_factor, rounding
        )

        return {
            "top_set": {
                "sets": sets,
                "reps": reps,
                "target_rpe": target_rpe,
                "load_kg": top_load,
            },
            "backoff": [
                {
                    "sets": backoff_sets,
                    "reps": backoff_reps,
                    "load_kg": backoff_load,
                }
            ],
            "rounding_profile": rounding,
        }

    def _resolve_reps_range_rir(
        self, mapping: dict[str, str], ctx: dict[str, Any]
    ) -> dict[str, Any]:
        sets = int(self._eval(mapping["sets_expr"], ctx))
        reps_min = int(self._eval(mapping["reps_min_expr"], ctx))
        reps_max = int(self._eval(mapping["reps_max_expr"], ctx))
        target_rir = int(self._eval(mapping["target_rir_expr"], ctx))

        return {
            "sets": sets,
            "reps_range": [reps_min, reps_max],
            "target_rir": target_rir,
            "load_note": (
                "Select load (or supply accessory baselines to compute)."
            ),
        }

    def _resolve_steady_state(
        self, mapping: dict[str, str], ctx: dict[str, Any]
    ) -> dict[str, Any]:
        duration = int(self._eval(mapping["duration_minutes_expr"], ctx))
        intensity_target = self._eval(mapping["intensity_target_expr"], ctx)
        notes = str(self._eval(mapping["notes_expr"], ctx))

        method = ctx.get("conditioning", {}).get("method", "RPE")

        return {
            "duration_minutes": duration,
            "intensity": {
                "method": method,
                "target": str(intensity_target),
            },
            "notes": notes,
        }

    def _resolve_intervals(
        self, mapping: dict[str, str], ctx: dict[str, Any]
    ) -> dict[str, Any]:
        warmup = int(self._eval(mapping["warmup_minutes_expr"], ctx))
        intervals = int(self._eval(mapping["work_intervals_expr"], ctx))
        intensity_target = self._eval(mapping["intensity_target_expr"], ctx)
        cooldown = int(self._eval(mapping["cooldown_minutes_expr"], ctx))
        notes = str(self._eval(mapping["notes_expr"], ctx))
        method = ctx.get("conditioning", {}).get("method", "RPE")

        work: dict[str, Any] = {
            "intervals": intervals,
            "intensity": {
                "method": method,
                "target": str(intensity_target),
            },
        }

        if "work_minutes_expr" in mapping:
            work["minutes_each"] = int(
                self._eval(mapping["work_minutes_expr"], ctx)
            )
        if "work_seconds_expr" in mapping:
            work["seconds_each"] = int(
                self._eval(mapping["work_seconds_expr"], ctx)
            )

        result: dict[str, Any] = {
            "warmup_minutes": warmup,
            "work": work,
            "cooldown_minutes": cooldown,
            "notes": notes,
        }

        if "rest_minutes_expr" in mapping:
            result["rest_minutes"] = int(
                self._eval(mapping["rest_minutes_expr"], ctx)
            )
        if "rest_seconds_expr" in mapping:
            result["rest_seconds"] = int(
                self._eval(mapping["rest_seconds_expr"], ctx)
            )

        return result

    def _get_e1rm(self, ctx: dict[str, Any], key: str | None) -> float:
        if key is None:
            raise ValueError("e1rm_key is required for load calculation")
        e1rm_dict = ctx.get("athlete", {}).get("e1rm", {})
        if key not in e1rm_dict:
            raise ValueError(f"e1RM for '{key}' not found in athlete data")
        return float(e1rm_dict[key])

"""Plan endpoints."""

from __future__ import annotations

import copy

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from src.api.dependencies import get_exercise_library
from src.models.generated_plan import GeneratedPlan
from src.models.plan_overrides import (
    AppliedOverride,
    ApplyOverridesRequest,
    ApplyOverridesResponse,
    RejectedOverride,
)
from src.models.exercise_library import ExerciseLibrary

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/apply-overrides")
async def apply_overrides(
    body: ApplyOverridesRequest,
    library: ExerciseLibrary = Depends(get_exercise_library),
) -> ApplyOverridesResponse:
    try:
        plan = GeneratedPlan.model_validate(body.plan)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    exercise_index = {ex.id: ex for ex in library.exercises}

    # Build block lookup: block_id → (original_exercise_id, original_exercise_name)
    block_lookup: dict[str, tuple[str, str]] = {}
    for week in plan.weeks:
        for session in week.sessions:
            for block in session.blocks:
                block_lookup[block.block_id] = (
                    block.exercise.id,
                    block.exercise.name,
                )

    applied: list[AppliedOverride] = []
    rejected: list[RejectedOverride] = []

    plan_dict = copy.deepcopy(body.plan)

    for override in body.overrides:
        if override.block_id not in block_lookup:
            rejected.append(
                RejectedOverride(
                    block_id=override.block_id,
                    new_exercise_id=override.new_exercise_id,
                    reason="block_not_found",
                )
            )
            continue

        if override.new_exercise_id not in exercise_index:
            rejected.append(
                RejectedOverride(
                    block_id=override.block_id,
                    new_exercise_id=override.new_exercise_id,
                    reason="exercise_not_found",
                )
            )
            continue

        original_id, original_name = block_lookup[override.block_id]
        original_ex = exercise_index.get(original_id)
        new_ex = exercise_index[override.new_exercise_id]

        if original_ex is not None:
            same_swap_group = (
                original_ex.swap_group is not None
                and new_ex.swap_group == original_ex.swap_group
            )
            shares_pattern = bool(
                set(new_ex.patterns) & set(original_ex.patterns)
            )
            if not same_swap_group and not shares_pattern:
                rejected.append(
                    RejectedOverride(
                        block_id=override.block_id,
                        new_exercise_id=override.new_exercise_id,
                        reason="incompatible_exercise",
                    )
                )
                continue

        # Apply to plan_dict in-place
        for week_d in plan_dict["weeks"]:
            for session_d in week_d["sessions"]:
                for block_d in session_d["blocks"]:
                    if block_d["block_id"] == override.block_id:
                        block_d["exercise"]["id"] = new_ex.id
                        block_d["exercise"]["name"] = new_ex.name

        applied.append(
            AppliedOverride(
                block_id=override.block_id,
                original_exercise_id=original_id,
                original_exercise_name=original_name,
                new_exercise_id=new_ex.id,
                new_exercise_name=new_ex.name,
            )
        )
        # Update block_lookup so subsequent overrides see the updated exercise
        block_lookup[override.block_id] = (new_ex.id, new_ex.name)

    return ApplyOverridesResponse(
        plan=plan_dict,
        applied=applied,
        rejected=rejected,
    )

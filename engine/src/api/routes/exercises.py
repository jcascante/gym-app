"""Exercise endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_exercise_library
from src.models.exercise_alternatives import (
    ExerciseAlternative,
    ExerciseAlternativesRequest,
    ExerciseAlternativesResponse,
)
from src.models.exercise_library import Exercise, ExerciseLibrary

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _is_equipment_compatible(ex: Exercise, athlete_equipment: list[str]) -> bool:
    if not ex.equipment:
        return True
    return set(ex.equipment).issubset(set(athlete_equipment))


def _has_restriction_conflict(ex: Exercise, restrictions: list[str]) -> bool:
    if not restrictions:
        return False
    return bool(set(ex.contraindications) & set(restrictions))


@router.post("/alternatives")
async def get_exercise_alternatives(
    body: ExerciseAlternativesRequest,
    library: ExerciseLibrary = Depends(get_exercise_library),
) -> ExerciseAlternativesResponse:
    exercise_index = {ex.id: ex for ex in library.exercises}

    original = exercise_index.get(body.exercise_id)
    if original is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exercise '{body.exercise_id}' not found",
        )

    exclude_set = set(body.exclude_ids)
    original_patterns = set(original.patterns)

    swap_group_matches: list[ExerciseAlternative] = []
    pattern_matches: list[ExerciseAlternative] = []
    swap_group_ids: set[str] = set()

    for ex in library.exercises:
        if ex.id == body.exercise_id:
            continue
        if ex.id in exclude_set:
            continue
        if not _is_equipment_compatible(ex, body.athlete_equipment):
            continue
        if _has_restriction_conflict(ex, body.restrictions):
            continue

        if original.swap_group and ex.swap_group == original.swap_group:
            swap_group_matches.append(
                ExerciseAlternative(
                    id=ex.id,
                    name=ex.name,
                    patterns=ex.patterns,
                    tags=ex.tags,
                    swap_group=ex.swap_group,
                    fatigue_cost=ex.fatigue_cost,
                    match_reason="swap_group",
                )
            )
            swap_group_ids.add(ex.id)
        elif set(ex.patterns) & original_patterns:
            pattern_matches.append(
                ExerciseAlternative(
                    id=ex.id,
                    name=ex.name,
                    patterns=ex.patterns,
                    tags=ex.tags,
                    swap_group=ex.swap_group,
                    fatigue_cost=ex.fatigue_cost,
                    match_reason="pattern_match",
                )
            )

    alternatives = (swap_group_matches + pattern_matches)[: body.limit]

    return ExerciseAlternativesResponse(
        original_exercise_id=body.exercise_id,
        alternatives=alternatives,
    )

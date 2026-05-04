"""Models for the exercise alternatives endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExerciseAlternativesRequest(BaseModel):
    exercise_id: str
    athlete_equipment: list[str]
    restrictions: list[str] = Field(default_factory=list)
    exclude_ids: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=20)


class ExerciseAlternative(BaseModel):
    id: str
    name: str
    patterns: list[str]
    tags: list[str]
    swap_group: str | None
    fatigue_cost: float
    match_reason: Literal["swap_group", "pattern_match"]


class ExerciseAlternativesResponse(BaseModel):
    original_exercise_id: str
    alternatives: list[ExerciseAlternative]

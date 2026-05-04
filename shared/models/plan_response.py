"""Shared response schema produced by program-builder and consumed by backend."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExerciseRef(BaseModel):
    id: str
    name: str

    model_config = {"extra": "allow"}


class PlanBlock(BaseModel):
    block_id: str
    type: str
    exercise: ExerciseRef
    prescription: dict[str, Any]

    model_config = {"extra": "allow"}


class GeneratedSession(BaseModel):
    day: int = Field(ge=1, le=7)
    tags: list[str] = Field(default_factory=list)
    blocks: list[PlanBlock]
    metrics: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class GeneratedWeek(BaseModel):
    week: int = Field(ge=1)
    sessions: list[GeneratedSession]

    model_config = {"extra": "allow"}


class GeneratedPlan(BaseModel):
    program_id: str
    program_version: str
    generated_at: str
    inputs_echo: dict[str, Any]
    weeks: list[GeneratedWeek]
    warnings: list[Any] = Field(default_factory=list)
    repairs: list[Any] = Field(default_factory=list)
    plan_summary: dict[str, Any] | None = None

    model_config = {"extra": "allow"}

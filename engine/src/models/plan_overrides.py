"""Models for the apply-overrides endpoint."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class OverrideRequest(BaseModel):
    block_id: str
    new_exercise_id: str


class AppliedOverride(BaseModel):
    block_id: str
    original_exercise_id: str
    original_exercise_name: str
    new_exercise_id: str
    new_exercise_name: str


class RejectedOverride(BaseModel):
    block_id: str
    new_exercise_id: str
    reason: str


class ApplyOverridesRequest(BaseModel):
    plan: dict[str, Any]
    overrides: list[OverrideRequest]


class ApplyOverridesResponse(BaseModel):
    plan: dict[str, Any]
    applied: list[AppliedOverride]
    rejected: list[RejectedOverride]

"""Pydantic schemas for GeneratedPlan endpoints."""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GeneratedPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    notes: str | None = None
    engine_program_id: str
    engine_program_version: str
    inputs_echo: dict[str, Any] | None = None
    plan_data: dict[str, Any]


class GeneratedPlanSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    subscription_id: UUID
    name: str
    notes: str | None
    engine_program_id: str
    engine_program_version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Set once the client starts this plan
    assignment_id: UUID | None = None


class GeneratedPlanResponse(GeneratedPlanSummary):
    inputs_echo: dict[str, Any] | None
    plan_data: dict[str, Any]


class GeneratedPlanUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    notes: str | None = None
    plan_data: dict[str, Any] | None = None


class StartPlanRequest(BaseModel):
    start_date: date
    assignment_name: str | None = Field(None, max_length=255)


class StartPlanResponse(BaseModel):
    assignment_id: UUID
    program_id: UUID
    start_date: date
    end_date: date
    status: str

"""Pydantic schemas for GeneratedPlan endpoints."""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class GeneratedPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None
    engine_program_id: str
    engine_program_version: str
    inputs_echo: Optional[dict[str, Any]] = None
    plan_data: dict[str, Any]


class GeneratedPlanSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    subscription_id: UUID
    name: str
    notes: Optional[str]
    engine_program_id: str
    engine_program_version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GeneratedPlanResponse(GeneratedPlanSummary):
    inputs_echo: Optional[dict[str, Any]]
    plan_data: dict[str, Any]


class GeneratedPlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    plan_data: Optional[dict[str, Any]] = None

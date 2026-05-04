from typing import Any

from pydantic import BaseModel, Field

from src.models.enums import Level, Modality


class Athlete(BaseModel):
    level: Level
    equipment: list[str]
    restrictions: list[str] = Field(default_factory=list)
    e1rm: dict[str, float] | None = None
    time_budget_minutes: float | None = Field(default=None, ge=10, le=240)
    modality: Modality | None = None

    model_config = {"extra": "allow"}


class PlanRequest(BaseModel):
    program_id: str
    program_version: str
    weeks: int = Field(ge=1, le=52)
    days_per_week: int = Field(ge=1, le=7)
    athlete: Athlete
    rules: dict[str, Any] | None = None
    conditioning: dict[str, Any] | None = None
    seed: int | None = Field(default=None, ge=0)

    model_config = {"extra": "allow"}

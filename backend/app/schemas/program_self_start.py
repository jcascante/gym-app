"""
Schemas for the client self-service program start flow.

POST /api/v1/programs/templates/{id}/preview
POST /api/v1/programs/templates/{id}/start
GET  /api/v1/workouts/assignments/{id}/today
PATCH /api/v1/workouts/assignments/{id}/progress
PATCH /api/v1/workouts/assignments/{id}/feedback
"""
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Template browsing
# ---------------------------------------------------------------------------


class TemplateListItem(BaseModel):
    """Minimal template card shown in the browsing list."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str  # "engine" | "coach"
    name: str
    description: str | None
    program_type: str | None
    difficulty_level: str | None
    duration_weeks: int
    days_per_week: int
    tags: list[str]
    times_assigned: int


class TemplateListResponse(BaseModel):
    templates: list[TemplateListItem]
    total: int


# ---------------------------------------------------------------------------
# Preview / start
# ---------------------------------------------------------------------------


class SelfStartRequest(BaseModel):
    """Body for both /preview and /start."""

    source: str = Field(..., pattern="^(engine|coach)$")
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine inputs dict (ignored for coach templates)",
    )
    # For engine-based programs the movements are embedded inside inputs,
    # but we accept them here too for the legacy strength wizard path.
    movements: list[dict[str, Any]] = Field(default_factory=list)
    start_date: date | None = None  # required for /start, ignored for /preview
    assignment_name: str | None = None


class SelfStartResponse(BaseModel):
    """Response after POST /templates/{id}/start."""

    assignment_id: str
    program_id: str
    start_date: date
    end_date: date
    status: str


# ---------------------------------------------------------------------------
# Today's workout
# ---------------------------------------------------------------------------


class ExercisePrescription(BaseModel):
    """Single exercise as prescribed for today."""

    id: str  # program_day_exercise UUID
    exercise_name: str
    sets: int
    reps: int | None
    reps_target: int | None
    weight_lbs: float | None
    rpe_target: float | None
    percentage_1rm: float | None
    rest_seconds: int | None
    notes: str | None
    coaching_cues: str | None
    exercise_order: int | None


class TodayWorkoutResponse(BaseModel):
    """GET /workouts/assignments/{id}/today"""

    assignment_id: str
    program_day_id: str
    week_number: int
    day_number: int
    day_name: str
    exercises: list[ExercisePrescription]
    current_week: int
    current_day: int
    progress_percentage: float
    progress_health: str


# ---------------------------------------------------------------------------
# Assignment management overrides
# ---------------------------------------------------------------------------


class ProgressOverrideRequest(BaseModel):
    """PATCH /assignments/{id}/progress — coach manual override."""

    current_week: int | None = Field(None, ge=1)
    current_day: int | None = Field(None, ge=1)
    status: str | None = None


class FeedbackRequest(BaseModel):
    """PATCH /assignments/{id}/feedback — client submits rating + text."""

    client_rating: float | None = Field(None, ge=1.0, le=5.0)
    client_feedback: str | None = None


class DayLogSummary(BaseModel):
    """One logged day within an assignment — used to show per-day status."""

    workout_log_id: str
    program_day_id: str | None
    day_status: str  # "completed" | "skipped" | "partial"
    workout_date: str  # ISO datetime string


class AssignmentResponse(BaseModel):
    """Generic assignment state response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    program_id: str
    client_id: str
    assignment_name: str | None
    start_date: date
    end_date: date | None
    status: str
    current_week: int
    current_day: int
    workouts_completed: int
    workouts_skipped: int
    progress_percentage: float
    progress_health: str
    client_rating: float | None
    client_feedback: str | None

"""
Workout Log Pydantic schemas.

Schemas for creating, retrieving, and managing workout logs.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import WorkoutStatus

# ============================================================================
# Workout Log Creation & Updates
# ============================================================================

class WorkoutLogCreate(BaseModel):
    """Request to create a new workout log."""
    assignment_id: UUID = Field(..., description="ID of the program assignment")
    status: WorkoutStatus = Field(
        WorkoutStatus.COMPLETED,
        description="Workout status (completed, skipped, scheduled)"
    )
    duration_minutes: str | None = Field(
        None,
        description="Duration of workout in minutes"
    )
    notes: str | None = Field(
        None,
        description="Client notes about the workout"
    )
    workout_date: datetime | None = Field(
        None,
        description="Date/time of the workout (defaults to now)"
    )


class WorkoutLogUpdate(BaseModel):
    """Request to update a workout log."""
    status: WorkoutStatus | None = Field(
        None,
        description="Updated workout status"
    )
    duration_minutes: str | None = Field(
        None,
        description="Updated duration in minutes"
    )
    notes: str | None = Field(
        None,
        description="Updated notes"
    )


# ============================================================================
# Workout Log Response
# ============================================================================

class WorkoutLogResponse(BaseModel):
    """Workout log response model."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    coach_id: UUID | None = None
    program_id: UUID
    assignment_id: UUID
    status: WorkoutStatus
    workout_date: datetime
    duration_minutes: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class WorkoutHistoryResponse(BaseModel):
    """Paginated workout history response."""
    total: int
    count: int
    offset: int
    limit: int
    workouts: list[WorkoutLogResponse]


class WorkoutStatsResponse(BaseModel):
    """Workout statistics for a client."""
    total_workouts: int
    completed_workouts: int
    skipped_workouts: int
    last_workout_date: str | None = None


class RecentWorkoutResponse(BaseModel):
    """Recent workout with assignment details."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workout_date: datetime
    status: WorkoutStatus
    duration_minutes: str | None = None
    notes: str | None = None
    program_name: str | None = None
    assignment_name: str | None = None

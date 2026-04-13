"""
Schemas for per-set exercise logging within a workout session.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SetLogRequest(BaseModel):
    """One set of an exercise."""

    set_number: int = Field(..., ge=1)
    actual_reps: int | None = None
    actual_weight_lbs: float | None = None
    actual_rpe: float | None = Field(None, ge=1.0, le=10.0)
    notes: str | None = None


class ExerciseLogRequest(BaseModel):
    """All sets for one exercise within a session."""

    program_day_exercise_id: str | None = None  # UUID string, nullable for free-form
    exercise_name: str
    sets: list[SetLogRequest] = Field(..., min_length=1)


class WorkoutLogExtendedRequest(BaseModel):
    """
    Extended POST /workouts body that supports per-set exercise logging
    and links to a program day.
    """

    assignment_id: str  # UUID of ClientProgramAssignment
    program_day_id: str | None = None  # UUID of ProgramDay (nullable for free-form)
    day_status: str = Field("completed", pattern="^(completed|skipped|partial)$")
    duration_minutes: str | None = None
    session_rating: int | None = Field(None, ge=1, le=5)
    notes: str | None = None
    exercise_logs: list[ExerciseLogRequest] = Field(default_factory=list)


class SetLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    set_number: int
    actual_reps: int | None
    actual_weight_lbs: float | None
    actual_rpe: float | None
    notes: str | None
    completed_at: datetime


class ExerciseLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exercise_name: str
    program_day_exercise_id: str | None
    sets: list[SetLogResponse]


class WorkoutLogExtendedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workout_log_id: str
    assignment_id: str
    program_day_id: str | None
    day_status: str | None
    duration_minutes: str | None
    session_rating: int | None
    exercise_logs: list[ExerciseLogResponse]
    # Updated assignment state after auto-advance
    current_week: int
    current_day: int
    assignment_status: str
    progress_percentage: float
    progress_health: str

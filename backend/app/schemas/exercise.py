"""
Exercise Library Pydantic schemas.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExerciseCreate(BaseModel):
    """Create a new exercise in the library."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, description="compound, isolation, cardio, mobility")
    muscle_groups: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    video_url: str | None = None
    thumbnail_url: str | None = None
    is_bilateral: bool = True
    is_timed: bool = False
    default_rest_seconds: int = Field(90, ge=0, le=600)
    difficulty_level: str | None = Field(
        None, description="beginner, intermediate, advanced, elite"
    )


class ExerciseUpdate(BaseModel):
    """Partial update for an exercise."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    muscle_groups: list[str] | None = None
    equipment: list[str] | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    is_bilateral: bool | None = None
    is_timed: bool | None = None
    default_rest_seconds: int | None = Field(None, ge=0, le=600)
    difficulty_level: str | None = None
    is_active: bool | None = None


class ExerciseResponse(BaseModel):
    """Exercise response model."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subscription_id: UUID | None = None
    name: str
    description: str | None = None
    category: str | None = None
    muscle_groups: list[str]
    equipment: list[str]
    video_url: str | None = None
    thumbnail_url: str | None = None
    is_bilateral: bool
    is_timed: bool
    default_rest_seconds: int
    difficulty_level: str | None = None
    is_global: bool
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ExerciseListResponse(BaseModel):
    """Paginated exercise list."""
    exercises: list[ExerciseResponse]
    total: int
    count: int
    offset: int
    limit: int

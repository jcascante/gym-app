"""
Exercise Library Pydantic schemas.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ExerciseCreate(BaseModel):
    """Create a new exercise in the library."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, description="compound, isolation, cardio, mobility")
    muscle_groups: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_bilateral: bool = True
    is_timed: bool = False
    default_rest_seconds: int = Field(90, ge=0, le=600)
    difficulty_level: Optional[str] = Field(
        None, description="beginner, intermediate, advanced, elite"
    )


class ExerciseUpdate(BaseModel):
    """Partial update for an exercise."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    muscle_groups: Optional[list[str]] = None
    equipment: Optional[list[str]] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_bilateral: Optional[bool] = None
    is_timed: Optional[bool] = None
    default_rest_seconds: Optional[int] = Field(None, ge=0, le=600)
    difficulty_level: Optional[str] = None
    is_active: Optional[bool] = None


class ExerciseResponse(BaseModel):
    """Exercise response model."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subscription_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    muscle_groups: list[str]
    equipment: list[str]
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_bilateral: bool
    is_timed: bool
    default_rest_seconds: int
    difficulty_level: Optional[str] = None
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

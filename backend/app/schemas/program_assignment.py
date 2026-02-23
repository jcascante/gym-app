"""
Program Assignment Pydantic schemas.

Schemas for assigning programs to clients, tracking progress, and managing assignments.
"""
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Assignment Creation
# ============================================================================

class AssignProgramRequest(BaseModel):
    """Request to assign a program to a client."""
    client_id: UUID = Field(..., description="ID of the client to assign the program to")
    assignment_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional custom name for this assignment (e.g., 'Winter Bulk 2025')"
    )
    start_date: Optional[date] = Field(
        None,
        description="When the client should start the program (defaults to today)"
    )
    notes: Optional[str] = Field(
        None,
        description="Coach notes about this assignment"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "assignment_name": "Winter Strength Block",
                "start_date": "2025-01-15",
                "notes": "Focus on squat progression"
            }
        }
    )


class AssignProgramResponse(BaseModel):
    """Response after assigning a program to a client."""
    assignment_id: UUID = Field(..., description="ID of the created assignment")
    program_id: UUID = Field(..., description="ID of the assigned program")
    program_name: str = Field(..., description="Name of the program")
    client_id: UUID = Field(..., description="ID of the client")
    client_name: str = Field(..., description="Client's full name")
    assignment_name: Optional[str] = Field(None, description="Custom assignment name")
    start_date: date = Field(..., description="Program start date")
    end_date: Optional[date] = Field(None, description="Expected completion date")
    status: str = Field(..., description="Assignment status")
    created_at: datetime = Field(..., description="When the assignment was created")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "assignment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "program_id": "550e8400-e29b-41d4-a716-446655440000",
                "program_name": "8-Week Linear Strength",
                "client_id": "660e8400-e29b-41d4-a716-446655440001",
                "client_name": "John Doe",
                "assignment_name": "Winter Strength Block",
                "start_date": "2025-01-15",
                "end_date": "2025-03-12",
                "status": "assigned",
                "created_at": "2025-01-15T10:00:00"
            }
        }
    )


# ============================================================================
# Assignment Listing & Details
# ============================================================================

class ProgramAssignmentSummary(BaseModel):
    """Summary of a program assignment for list views."""
    assignment_id: UUID
    program_id: UUID
    program_name: str
    assignment_name: Optional[str] = None
    duration_weeks: int
    days_per_week: int
    start_date: date
    end_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    status: str = Field(..., description="assigned, in_progress, completed, paused, cancelled")
    program_status: Optional[str] = Field(None, description="Program lifecycle status: None (template), 'draft', 'published'")
    current_week: int
    current_day: int
    progress_percentage: float = Field(0.0, description="Percentage complete (0-100)")
    is_active: bool
    assigned_at: datetime
    assigned_by_name: str = Field(..., description="Name of coach who assigned")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "assignment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "program_id": "550e8400-e29b-41d4-a716-446655440000",
                "program_name": "8-Week Linear Strength",
                "assignment_name": "Winter Strength Block",
                "duration_weeks": 8,
                "days_per_week": 4,
                "start_date": "2025-01-15",
                "end_date": "2025-03-12",
                "actual_completion_date": None,
                "status": "in_progress",
                "current_week": 3,
                "current_day": 2,
                "progress_percentage": 37.5,
                "is_active": True,
                "assigned_at": "2025-01-15T10:00:00",
                "assigned_by_name": "Coach Smith"
            }
        }
    )


class ClientProgramsListResponse(BaseModel):
    """Response for listing all programs assigned to a client."""
    client_id: UUID
    client_name: str
    programs: list[ProgramAssignmentSummary]
    total: int = Field(..., description="Total number of assignments")
    active_count: int = Field(0, description="Number of active assignments")
    completed_count: int = Field(0, description="Number of completed assignments")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": "660e8400-e29b-41d4-a716-446655440001",
                "client_name": "John Doe",
                "programs": [],
                "total": 5,
                "active_count": 2,
                "completed_count": 3
            }
        }
    )


# ============================================================================
# Assignment Updates
# ============================================================================

class UpdateAssignmentStatusRequest(BaseModel):
    """Request to update assignment status and progress."""
    status: Optional[str] = Field(
        None,
        pattern="^(assigned|in_progress|completed|paused|cancelled)$",
        description="New status"
    )
    current_week: Optional[int] = Field(None, ge=1, description="Current week number")
    current_day: Optional[int] = Field(None, ge=1, description="Current day number")
    notes: Optional[str] = Field(None, description="Updated notes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "in_progress",
                "current_week": 3,
                "current_day": 2,
                "notes": "Client progressing well, increased squat 1RM"
            }
        }
    )


class UpdateAssignmentStatusResponse(BaseModel):
    """Response after updating assignment status."""
    assignment_id: UUID
    status: str
    current_week: int
    current_day: int
    progress_percentage: float
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "assignment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "in_progress",
                "current_week": 3,
                "current_day": 2,
                "progress_percentage": 37.5,
                "updated_at": "2025-01-22T14:30:00"
            }
        }
    )

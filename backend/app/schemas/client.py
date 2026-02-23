"""
Client management Pydantic schemas for coach workflows.

These schemas define simplified client creation and management for coaches,
focusing on the minimal data needed to quickly add clients and start building programs.
"""
from typing import Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================================================
# Client Creation (Minimal)
# ============================================================================

class CreateClientRequest(BaseModel):
    """
    Schema for coaches to create new clients with minimal information.

    Only requires essential data to get started. Coach can add more details later.
    """
    email: EmailStr = Field(
        ...,
        description="Client's email address (used to check if client already exists)"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Client's first name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Client's last name"
    )
    phone_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Client's phone number (optional)"
    )
    send_welcome_email: bool = Field(
        default=True,
        description="Whether to send a welcome email with login credentials"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "send_welcome_email": True
            }
        }
    )


class CreateClientResponse(BaseModel):
    """
    Response after creating or finding a client.
    """
    client_id: UUID = Field(..., description="Client's user ID")
    email: EmailStr = Field(..., description="Client's email")
    name: str = Field(..., description="Client's full name")
    is_new: bool = Field(
        ...,
        description="True if newly created, False if existing user was found"
    )
    profile_complete: bool = Field(
        ...,
        description="Whether client has filled out their full profile"
    )
    already_assigned: bool = Field(
        default=False,
        description="Whether this coach is already assigned to this client"
    )
    temporary_password: str | None = Field(
        default=None,
        description="Temporary password for newly created clients (only shown once)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john.doe@example.com",
                "name": "John Doe",
                "is_new": True,
                "profile_complete": False,
                "already_assigned": False,
                "temporary_password": "aB3$dEfGhI9!"
            }
        }
    )


# ============================================================================
# Client Profile (Structured)
# ============================================================================

class ClientBasicInfo(BaseModel):
    """Basic client information."""
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other|prefer_not_to_say)$")
    phone_number: Optional[str] = None


class ClientAnthropometrics(BaseModel):
    """Client body measurements."""
    current_weight: Optional[float] = Field(None, gt=0)
    current_height: Optional[float] = Field(None, gt=0)
    weight_unit: str = Field(default="lbs", pattern="^(lbs|kg)$")
    height_unit: str = Field(default="inches", pattern="^(inches|cm)$")
    body_fat_percentage: Optional[float] = Field(None, ge=0, le=100)
    goal_weight: Optional[float] = Field(None, gt=0)


class OneRepMax(BaseModel):
    """Single 1RM entry for an exercise."""
    weight: float = Field(..., gt=0)
    unit: str = Field(..., pattern="^(lbs|kg)$")
    tested_date: date
    verified: bool = Field(
        default=False,
        description="Whether this was verified by coach (vs self-reported)"
    )


class ClientTrainingExperience(BaseModel):
    """Client's training history and experience."""
    overall_experience_level: Optional[str] = Field(
        None,
        pattern="^(beginner|novice|intermediate|advanced|elite)$"
    )
    years_training: Optional[float] = Field(None, ge=0)
    strength_training_experience: Optional[str] = None
    one_rep_maxes: Dict[str, OneRepMax] = Field(
        default_factory=dict,
        description="Dictionary mapping exercise name to 1RM data"
    )
    current_training_frequency: Optional[int] = Field(None, ge=0, le=7)


class ClientInjury(BaseModel):
    """Single injury record."""
    injury: str
    injury_date: Optional[date] = None
    recovery_status: str = Field(
        ...,
        pattern="^(fully_recovered|recovering|chronic|requires_modification)$"
    )
    affected_movements: list[str] = Field(
        default_factory=list,
        description="List of exercises that should be modified or avoided"
    )
    notes: Optional[str] = None


class ClientHealthInfo(BaseModel):
    """Client health and medical information."""
    medical_clearance: bool = Field(
        default=False,
        description="Whether client has medical clearance to train"
    )
    clearance_date: Optional[date] = None
    injuries: list[ClientInjury] = Field(default_factory=list)
    medical_conditions: list[Dict[str, Any]] = Field(default_factory=list)
    medications: list[Dict[str, Any]] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


class ClientTrainingPreferences(BaseModel):
    """Client's training preferences and availability."""
    available_days_per_week: Optional[int] = Field(None, ge=1, le=7)
    preferred_training_days: list[str] = Field(default_factory=list)
    session_duration: Optional[int] = Field(
        None,
        gt=0,
        description="Preferred session length in minutes"
    )
    gym_access: Optional[str] = Field(
        None,
        pattern="^(full_gym|home_gym|minimal_equipment|bodyweight_only)$"
    )
    available_equipment: list[str] = Field(default_factory=list)
    preferred_exercises: list[str] = Field(default_factory=list)
    disliked_exercises: list[str] = Field(default_factory=list)


class ClientFitnessGoals(BaseModel):
    """Client's fitness goals and motivation."""
    primary_goal: Optional[str] = Field(
        None,
        pattern="^(strength|hypertrophy|fat_loss|athletic_performance|general_fitness|rehabilitation)$"
    )
    secondary_goals: list[str] = Field(default_factory=list)
    specific_goals: Optional[str] = None
    target_date: Optional[date] = None
    motivation: Optional[str] = None


class ClientProfile(BaseModel):
    """
    Complete structured client profile.

    This schema defines the structure for the User.profile JSONB field
    when the user role is CLIENT.
    """
    basic_info: Optional[ClientBasicInfo] = None
    anthropometrics: Optional[ClientAnthropometrics] = None
    training_experience: Optional[ClientTrainingExperience] = None
    fitness_goals: Optional[ClientFitnessGoals] = None
    health_info: Optional[ClientHealthInfo] = None
    training_preferences: Optional[ClientTrainingPreferences] = None
    notes: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Coach notes and client notes"
    )


class ClientProfileUpdate(BaseModel):
    """
    Partial update schema for client profile.
    All fields are optional to allow granular updates.
    """
    basic_info: Optional[ClientBasicInfo] = None
    anthropometrics: Optional[ClientAnthropometrics] = None
    training_experience: Optional[ClientTrainingExperience] = None
    fitness_goals: Optional[ClientFitnessGoals] = None
    health_info: Optional[ClientHealthInfo] = None
    training_preferences: Optional[ClientTrainingPreferences] = None
    notes: Optional[Dict[str, str]] = None


# ============================================================================
# Client List View (Coach perspective)
# ============================================================================

class ClientSummary(BaseModel):
    """
    Summary view of a client for coach's client list.
    """
    id: UUID = Field(..., description="Client's user ID")
    email: EmailStr
    first_name: str
    last_name: str
    name: str = Field(..., description="Full name (first + last)")
    profile_photo: Optional[str] = Field(None, description="URL to profile photo")

    # Quick stats
    active_programs: int = Field(
        default=0,
        description="Number of active programs assigned"
    )
    last_workout: Optional[datetime] = Field(
        None,
        description="When client last logged a workout"
    )
    status: str = Field(
        default="active",
        description="Client status: active, inactive, new",
        pattern="^(active|inactive|new)$"
    )

    # Profile completeness
    profile_complete: bool = Field(
        default=False,
        description="Whether client has completed their profile"
    )
    has_one_rep_maxes: bool = Field(
        default=False,
        description="Whether client has any 1RMs recorded"
    )

    # Assignment info
    assigned_at: datetime = Field(..., description="When coach-client relationship started")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "name": "John Doe",
                "profile_photo": None,
                "active_programs": 1,
                "last_workout": "2025-01-20T10:30:00",
                "status": "active",
                "profile_complete": True,
                "has_one_rep_maxes": True,
                "assigned_at": "2025-01-15T10:00:00"
            }
        }
    )


class ClientListResponse(BaseModel):
    """
    Response for coach's client list endpoint.
    """
    clients: list[ClientSummary]
    total: int = Field(..., description="Total number of clients")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "clients": [],
                "total": 5
            }
        }
    )


# ============================================================================
# Client Detail View (Coach perspective)
# ============================================================================

class ClientDetailResponse(BaseModel):
    """
    Detailed client information for coach view.
    """
    id: UUID
    email: EmailStr
    profile: Optional[ClientProfile] = None
    is_active: bool

    # Assignment info
    assigned_at: datetime
    assigned_by: UUID = Field(..., description="Coach who assigned this client")

    # Stats
    active_programs: int = Field(default=0)
    completed_programs: int = Field(default=0)
    total_workouts: int = Field(default=0)
    last_workout: Optional[datetime] = None

    # Account status
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john.doe@example.com",
                "profile": None,
                "is_active": True,
                "assigned_at": "2025-01-15T10:00:00",
                "assigned_by": "660e8400-e29b-41d4-a716-446655440000",
                "active_programs": 1,
                "completed_programs": 0,
                "total_workouts": 15,
                "last_workout": "2025-01-20T10:30:00",
                "last_login_at": "2025-01-20T10:00:00",
                "created_at": "2025-01-15T10:00:00"
            }
        }
    )


# ============================================================================
# 1RM Management
# ============================================================================

class UpdateOneRepMaxRequest(BaseModel):
    """
    Request to add or update a client's 1RM for an exercise.
    """
    exercise_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of exercise (e.g., 'Squat', 'Bench Press')"
    )
    weight: float = Field(..., gt=0, description="Weight in lbs or kg")
    unit: str = Field(..., pattern="^(lbs|kg)$", description="Weight unit")
    tested_date: date = Field(
        ...,
        description="Date when 1RM was tested"
    )
    verified: bool = Field(
        default=True,
        description="Whether coach verified this (vs self-reported by client)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exercise_name": "Squat",
                "weight": 315.0,
                "unit": "lbs",
                "tested_date": "2025-01-15",
                "verified": True
            }
        }
    )


class OneRepMaxResponse(BaseModel):
    """Response after updating 1RM."""
    client_id: UUID
    exercise_name: str
    weight: float
    unit: str
    tested_date: date
    verified: bool
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": "550e8400-e29b-41d4-a716-446655440000",
                "exercise_name": "Squat",
                "weight": 315.0,
                "unit": "lbs",
                "tested_date": "2025-01-15",
                "verified": True,
                "updated_at": "2025-01-15T10:30:00"
            }
        }
    )

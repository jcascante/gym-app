"""
Program-related Pydantic schemas for request/response validation.
"""
from datetime import date
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Input Schemas (What frontend sends)
# ============================================================================

class MovementInput(BaseModel):
    """Single movement/exercise input for strength program."""
    name: str = Field(..., description="Exercise name (e.g., 'Squat', 'Bench Press')")
    one_rm: float = Field(..., gt=0, description="One rep max in pounds")
    max_reps_at_80_percent: int = Field(
        ...,
        ge=1,
        le=20,
        description="Maximum reps performed at 80% of 1RM"
    )
    target_weight: float = Field(..., gt=0, description="Target 5x5 weight in pounds")


class ProgramInputs(BaseModel):
    """Input data for generating a strength program."""
    builder_type: str = Field(
        default="strength_linear_5x5",
        description="Type of program builder used"
    )
    name: str | None = Field(
        None,
        description="Custom program name (auto-generated if not provided)"
    )
    description: str | None = Field(
        None,
        description="Program description"
    )
    movements: list[MovementInput] = Field(
        ...,
        min_items=1,
        max_items=4,
        description="Exercises for the program (1-4 movements)"
    )
    duration_weeks: int = Field(
        default=8,
        description="Program duration in weeks"
    )
    days_per_week: int = Field(
        default=4,
        description="Training sessions per week"
    )
    is_template: bool = Field(
        default=True,
        description="Save as reusable template"
    )
    client_id: str | None = Field(
        None,
        description="When provided, creates a client-specific draft program and assignment instead of a template"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "builder_type": "strength_linear_5x5",
                "name": "8-Week Linear Strength",
                "movements": [
                    {
                        "name": "Squat",
                        "one_rm": 315,
                        "max_reps_at_80_percent": 12,
                        "target_weight": 275
                    },
                    {
                        "name": "Bench Press",
                        "one_rm": 225,
                        "max_reps_at_80_percent": 10,
                        "target_weight": 185
                    }
                ],
                "is_template": True
            }
        }


# ============================================================================
# Calculation Output Schemas
# ============================================================================

class MovementCalculations(BaseModel):
    """Calculated data for a single movement."""
    name: str
    weekly_jump_percent: int
    weekly_jump_lbs: float
    ramp_up_percent: int
    ramp_up_base_lbs: float


class ExerciseDetail(BaseModel):
    """Single exercise within a workout day."""
    id: str | None = None  # DB UUID, present on saved programs
    exercise_name: str
    sets: int
    reps: int
    weight_lbs: float | None = None  # None for test weeks
    percentage_1rm: int | None = None
    notes: str = ""


class DayDetail(BaseModel):
    """Single training day."""
    id: str | None = None
    day_number: int
    name: str
    suggested_day_of_week: str | None = None
    exercises: list[ExerciseDetail]


class WeekDetail(BaseModel):
    """Single training week."""
    week_number: int
    name: str
    days: list[DayDetail]


class ProgramPreview(BaseModel):
    """
    Preview of generated program (calculation results without saving).
    This is what the backend returns for validation against frontend preview.
    """
    algorithm_version: str
    input_data: dict[str, Any]
    calculated_data: dict[str, MovementCalculations]
    weeks: list[WeekDetail]


# ============================================================================
# Database Response Schemas
# ============================================================================

class ProgramResponse(BaseModel):
    """Program stored in database (simplified for listing)."""
    id: str
    subscription_id: str | None
    created_by_user_id: str | None
    name: str
    description: str | None
    builder_type: str | None
    algorithm_version: str | None
    duration_weeks: int
    days_per_week: int
    is_template: bool
    is_public: bool
    times_assigned: int = 0
    status: str | None = None
    assignment_id: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProgramListResponse(BaseModel):
    """Response for listing programs."""
    programs: list[ProgramResponse]
    total: int


class ProgramDetailResponse(ProgramResponse):
    """Full program details including all weeks/days/exercises."""
    input_data: dict[str, Any]
    calculated_data: dict[str, Any]
    weeks: list[WeekDetail]

    class Config:
        from_attributes = True


# ============================================================================
# Calculation Constants Schema
# ============================================================================

class CalculationConstants(BaseModel):
    """
    Calculation constants/lookup tables for program generation.
    Frontend fetches these to ensure calculations match backend.
    """
    version: str = Field(..., description="Algorithm version")
    builder_type: str = Field(..., description="Builder type these constants apply to")
    weekly_jump_table: dict[int, int] = Field(
        ...,
        description="Maps max reps at 80% to weekly progression percentage"
    )
    ramp_up_table: dict[int, int] = Field(
        ...,
        description="Maps max reps at 80% to starting percentage of 1RM"
    )
    protocol_by_week: dict[int, dict[str, int]] = Field(
        ...,
        description="Sets and reps for each week"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "version": "v1.0.0",
                "builder_type": "strength_linear_5x5",
                "weekly_jump_table": {
                    "1": 5, "2": 5, "3": 5,
                    "10": 4, "11": 3,
                    "20": 2
                },
                "ramp_up_table": {
                    "1": 51, "2": 52,
                    "10": 60,
                    "20": 70
                },
                "protocol_by_week": {
                    "1": {"sets": 5, "reps": 5},
                    "6": {"sets": 3, "reps": 3},
                    "7": {"sets": 2, "reps": 2},
                    "8": {"sets": 1, "reps": 1}
                }
            }
        }


# ============================================================================
# Template-Based System Schemas
# ============================================================================

class TemplateParameter(BaseModel):
    """Schema for template parameter definition."""
    key: str = Field(..., description="Parameter key (e.g., 'goal', 'focus_lifts')")
    label: str = Field(..., description="Human-readable label")
    type: str = Field(..., description="Parameter type: text, number, select, multi-select")
    required: bool = Field(True, description="Whether parameter is required")
    options: list[str] | None = Field(None, description="Options for select types")
    validation: dict[str, Any] | None = Field(None, description="Validation rules (min, max, pattern)")
    help_text: str | None = Field(None, description="Help text for users")


class ProgramTemplateBase(BaseModel):
    """Base schema for program template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    program_type: str = Field(..., description="strength, conditioning, hypertrophy, power, sport_specific, general_fitness")
    difficulty_level: str | None = Field(None, description="beginner, intermediate, advanced, elite")
    duration_weeks: int = Field(..., gt=0, le=52)
    days_per_week: int = Field(..., gt=0, le=7)

    is_template: bool = Field(default=True)
    is_default: bool = Field(default=False)
    is_public: bool = Field(default=False)

    required_parameters: list[TemplateParameter] = Field(default_factory=list)
    optional_parameters: list[TemplateParameter] = Field(default_factory=list)

    tags: list[str] = Field(default_factory=list)
    goals: list[str] | None = None
    target_gender: str | None = None
    equipment_required: list[str] | None = None

    thumbnail_url: str | None = None
    video_url: str | None = None


class ProgramTemplateCreate(ProgramTemplateBase):
    """Schema for creating a program template."""
    pass


class ProgramTemplateUpdate(BaseModel):
    """Schema for updating a program template."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    program_type: str | None = None
    difficulty_level: str | None = None
    duration_weeks: int | None = Field(None, gt=0, le=52)
    days_per_week: int | None = Field(None, gt=0, le=7)

    is_public: bool | None = None

    required_parameters: list[TemplateParameter] | None = None
    optional_parameters: list[TemplateParameter] | None = None

    tags: list[str] | None = None
    goals: list[str] | None = None
    target_gender: str | None = None
    equipment_required: list[str] | None = None

    thumbnail_url: str | None = None
    video_url: str | None = None


class ProgramTemplateResponse(ProgramTemplateBase):
    """Schema for program template response."""
    id: str
    subscription_id: str | None
    created_by: str
    times_assigned: int = 0
    average_rating: float | None = None
    average_completion_rate: float | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProgramTemplateListResponse(BaseModel):
    """Schema for list of templates response."""
    templates: list[ProgramTemplateResponse]
    total: int
    page: int = 1
    page_size: int = 20


class ExerciseBase(BaseModel):
    """Base schema for exercise."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, description="compound, isolation, cardio, mobility")
    muscle_groups: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)

    video_url: str | None = None
    thumbnail_url: str | None = None

    is_bilateral: bool = True
    is_timed: bool = False
    default_rest_seconds: int = 90

    difficulty_level: str | None = None


class ExerciseCreate(ExerciseBase):
    """Schema for creating an exercise."""
    pass


class ExerciseResponse(ExerciseBase):
    """Schema for exercise response."""
    id: str
    subscription_id: str | None
    created_by: str | None
    is_global: bool
    is_verified: bool
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ExerciseListResponse(BaseModel):
    """Schema for list of exercises response."""
    exercises: list[ExerciseResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============================================================================
# Generate-for-Client Flow Schemas
# ============================================================================

class MovementParam(BaseModel):
    """Client-specific parameters for a single movement."""
    name: str = Field(..., description="Movement name matching template (e.g., 'Squat')")
    one_rm: float = Field(..., gt=0, description="Client 1RM in lbs")
    max_reps_at_80_percent: int = Field(..., ge=1, le=20, description="Max reps at 80% 1RM")
    target_weight: float = Field(..., gt=0, description="Target 5x5 starting weight in lbs")


class GenerateForClientRequest(BaseModel):
    """Request to generate a client-specific program from a template."""
    client_id: str = Field(..., description="Client user UUID")
    movements: list[MovementParam] = Field(..., min_items=1, max_items=4)
    start_date: date | None = Field(None, description="Program start date (defaults to today)")
    notes: str | None = Field(None, description="Coach notes for this assignment")


class GenerateForClientResponse(BaseModel):
    """Response after generating a client program draft."""
    program_id: str
    assignment_id: str
    client_id: str
    status: str  # "draft"


class UpdateExerciseRequest(BaseModel):
    """Partial update for a single exercise in a draft program."""
    sets: int | None = None
    reps: int | None = None
    reps_target: int | None = None
    weight_lbs: float | None = None
    load_value: float | None = None
    notes: str | None = None


class UpdateExerciseResponse(BaseModel):
    """Response after updating an exercise."""
    exercise_id: str
    sets: int
    reps: int | None
    reps_target: int | None
    weight_lbs: float | None
    load_value: float | None
    notes: str | None
    updated_at: str


class PublishProgramResponse(BaseModel):
    """Response after publishing a draft program."""
    program_id: str
    status: str  # "published"
    published_at: str

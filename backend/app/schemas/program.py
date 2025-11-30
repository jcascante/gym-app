"""
Program-related Pydantic schemas for request/response validation.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date


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
    name: Optional[str] = Field(
        None,
        description="Custom program name (auto-generated if not provided)"
    )
    description: Optional[str] = Field(
        None,
        description="Program description"
    )
    movements: List[MovementInput] = Field(
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
    exercise_name: str
    sets: int
    reps: int
    weight_lbs: Optional[float] = None  # None for test weeks
    percentage_1rm: Optional[int] = None
    notes: str = ""


class DayDetail(BaseModel):
    """Single training day."""
    day_number: int
    name: str
    suggested_day_of_week: Optional[str] = None
    exercises: List[ExerciseDetail]


class WeekDetail(BaseModel):
    """Single training week."""
    week_number: int
    name: str
    days: List[DayDetail]


class ProgramPreview(BaseModel):
    """
    Preview of generated program (calculation results without saving).
    This is what the backend returns for validation against frontend preview.
    """
    algorithm_version: str
    input_data: Dict[str, Any]
    calculated_data: Dict[str, MovementCalculations]
    weeks: List[WeekDetail]


# ============================================================================
# Database Response Schemas
# ============================================================================

class ProgramResponse(BaseModel):
    """Program stored in database (simplified for listing)."""
    id: str
    subscription_id: Optional[str]
    created_by_user_id: Optional[str]
    name: str
    description: Optional[str]
    builder_type: str
    algorithm_version: str
    duration_weeks: int
    days_per_week: int
    is_template: bool
    is_public: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProgramDetailResponse(ProgramResponse):
    """Full program details including all weeks/days/exercises."""
    input_data: Dict[str, Any]
    calculated_data: Dict[str, Any]
    weeks: List[WeekDetail]

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
    weekly_jump_table: Dict[int, int] = Field(
        ...,
        description="Maps max reps at 80% to weekly progression percentage"
    )
    ramp_up_table: Dict[int, int] = Field(
        ...,
        description="Maps max reps at 80% to starting percentage of 1RM"
    )
    protocol_by_week: Dict[int, Dict[str, int]] = Field(
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
    options: Optional[List[str]] = Field(None, description="Options for select types")
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation rules (min, max, pattern)")
    help_text: Optional[str] = Field(None, description="Help text for users")


class ProgramTemplateBase(BaseModel):
    """Base schema for program template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    program_type: str = Field(..., description="strength, conditioning, hypertrophy, power, sport_specific, general_fitness")
    difficulty_level: Optional[str] = Field(None, description="beginner, intermediate, advanced, elite")
    duration_weeks: int = Field(..., gt=0, le=52)
    days_per_week: int = Field(..., gt=0, le=7)

    is_template: bool = Field(default=True)
    is_default: bool = Field(default=False)
    is_public: bool = Field(default=False)

    required_parameters: List[TemplateParameter] = Field(default_factory=list)
    optional_parameters: List[TemplateParameter] = Field(default_factory=list)

    tags: List[str] = Field(default_factory=list)
    goals: Optional[List[str]] = None
    target_gender: Optional[str] = None
    equipment_required: Optional[List[str]] = None

    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None


class ProgramTemplateCreate(ProgramTemplateBase):
    """Schema for creating a program template."""
    pass


class ProgramTemplateUpdate(BaseModel):
    """Schema for updating a program template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    program_type: Optional[str] = None
    difficulty_level: Optional[str] = None
    duration_weeks: Optional[int] = Field(None, gt=0, le=52)
    days_per_week: Optional[int] = Field(None, gt=0, le=7)

    is_public: Optional[bool] = None

    required_parameters: Optional[List[TemplateParameter]] = None
    optional_parameters: Optional[List[TemplateParameter]] = None

    tags: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    target_gender: Optional[str] = None
    equipment_required: Optional[List[str]] = None

    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None


class ProgramTemplateResponse(ProgramTemplateBase):
    """Schema for program template response."""
    id: str
    subscription_id: Optional[str]
    created_by: str
    times_assigned: int = 0
    average_rating: Optional[float] = None
    average_completion_rate: Optional[float] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProgramTemplateListResponse(BaseModel):
    """Schema for list of templates response."""
    templates: List[ProgramTemplateResponse]
    total: int
    page: int = 1
    page_size: int = 20


class ProgramAssignmentCreate(BaseModel):
    """Schema for assigning a template to a client."""
    template_id: str
    client_id: str
    assignment_parameters: Dict[str, Any] = Field(..., description="Parameter values for this assignment")
    start_date: date
    coach_notes: Optional[str] = None


class ProgramAssignmentResponse(BaseModel):
    """Schema for program assignment response."""
    id: str
    template_id: str
    client_id: str
    assigned_by: str
    program_id: str
    assignment_parameters: Dict[str, Any]
    start_date: str
    end_date: Optional[str]
    status: str
    completion_percentage: float
    workouts_completed: int
    workouts_total: int
    current_week: int
    current_day: int
    created_at: str

    class Config:
        from_attributes = True


class ProgramAssignmentListResponse(BaseModel):
    """Schema for list of assignments response."""
    assignments: List[ProgramAssignmentResponse]
    total: int


class ExerciseBase(BaseModel):
    """Base schema for exercise."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, description="compound, isolation, cardio, mobility")
    muscle_groups: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)

    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    is_bilateral: bool = True
    is_timed: bool = False
    default_rest_seconds: int = 90

    difficulty_level: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    """Schema for creating an exercise."""
    pass


class ExerciseResponse(ExerciseBase):
    """Schema for exercise response."""
    id: str
    subscription_id: Optional[str]
    created_by: Optional[str]
    is_global: bool
    is_verified: bool
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ExerciseListResponse(BaseModel):
    """Schema for list of exercises response."""
    exercises: List[ExerciseResponse]
    total: int
    page: int = 1
    page_size: int = 50

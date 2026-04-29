from typing import Any

from pydantic import BaseModel, Field

from src.models.enums import BlockType, ExerciseLibraryRefType, ParameterFieldType
from src.models.exercise_library import Exercise


class ParameterField(BaseModel):
    key: str = Field(min_length=1)
    type: ParameterFieldType
    required: bool | None = None
    required_if: str | None = None
    visible_if: str | None = None
    default_expr: str | None = None
    min: float | None = None
    max: float | None = None
    enum: list[str] | None = None
    description: str | None = None

    model_config = {"extra": "allow"}


class ParameterSpec(BaseModel):
    fields: list[ParameterField] = Field(min_length=1)

    model_config = {"extra": "allow"}


class ExerciseLibraryRef(BaseModel):
    type: ExerciseLibraryRefType
    path: str
    exercises: list[Exercise] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class ExerciseSelector(BaseModel):
    count: int = Field(ge=1, le=10)
    include_tags: list[str] = Field(min_length=1)
    exclude_tags: list[str] | None = None
    prefer_tags: list[str] | None = None
    allow_repeats: bool | None = None

    model_config = {"extra": "allow"}


class BlockConstraints(BaseModel):
    block_fatigue_cap_expr: str | None = None

    model_config = {"extra": "allow"}


class Block(BaseModel):
    id: str
    type: BlockType
    tags: list[str] | None = None
    optional: bool | None = None
    exercise_selector: ExerciseSelector
    prescription_ref: str
    constraints: BlockConstraints | None = None

    model_config = {"extra": "allow"}


class Session(BaseModel):
    day_index: int = Field(ge=1, le=7)
    tags: list[str]
    optional: bool | None = None
    blocks: list[Block] = Field(min_length=1)

    model_config = {"extra": "allow"}


class WeeksRange(BaseModel):
    min: int = Field(ge=1)
    max: int = Field(ge=1)


class DaysPerWeekRange(BaseModel):
    min: int = Field(ge=1, le=7)
    max: int = Field(ge=1, le=7)


class Template(BaseModel):
    weeks: WeeksRange
    days_per_week: DaysPerWeekRange
    sessions: list[Session] = Field(min_length=1)

    model_config = {"extra": "allow"}


class Prescription(BaseModel):
    mode: str
    variables: dict[str, str] | None = None
    output_mapping: dict[str, str] | None = None

    model_config = {"extra": "allow"}


class ProgramDefinition(BaseModel):
    program_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    name: str | None = None
    description: str | None = None
    parameter_spec: ParameterSpec
    exercise_library_ref: ExerciseLibraryRef | None = None
    template: Template
    prescriptions: dict[str, Prescription] = Field(min_length=1)
    rules: dict[str, Any]
    validation: dict[str, Any]

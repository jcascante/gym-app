"""Tests for domain models -- written FIRST (TDD RED phase)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.models.enums import (
    BlockType,
    ConditioningMethod,
    Level,
    Modality,
    Muscle,
    Pattern,
)
from src.models.errors import EngineError, ErrorType
from src.models.exercise_library import Exercise, ExerciseLibrary
from src.models.generated_plan import (
    GeneratedPlan,
)
from src.models.plan_request import Athlete, PlanRequest
from src.models.program_definition import (
    ProgramDefinition,
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TestEnums:
    def test_pattern_has_14_members(self) -> None:
        assert len(Pattern) == 14

    def test_muscle_has_17_members(self) -> None:
        assert len(Muscle) == 17

    def test_level_values(self) -> None:
        assert set(Level) == {"novice", "intermediate", "advanced"}

    def test_conditioning_method_values(self) -> None:
        assert set(ConditioningMethod) == {"HR_ZONES", "PACE", "POWER", "RPE"}

    def test_block_type_values(self) -> None:
        assert "main_lift" in set(BlockType)
        assert "conditioning_steady" in set(BlockType)

    def test_pattern_string_value(self) -> None:
        assert Pattern.SQUAT == "squat"
        assert Pattern.CONDITIONING_INTERVALS == "conditioning_intervals"

    def test_muscle_string_value(self) -> None:
        assert Muscle.QUADS == "quads"
        assert Muscle.FOREARMS_GRIP == "forearms_grip"


# ---------------------------------------------------------------------------
# Exercise / ExerciseLibrary
# ---------------------------------------------------------------------------

class TestExercise:
    def test_valid_exercise(self) -> None:
        ex = Exercise(
            id="back_squat",
            name="Back Squat",
            patterns=["squat"],
            muscles={"quads": 1.0, "glutes": 0.7, "erectors": 0.4},
            equipment=["barbell", "rack"],
            swap_group="squat_main",
            fatigue_cost=0.9,
            contraindications=[],
            tags=["main", "squat_main", "barbell"],
        )
        assert ex.id == "back_squat"
        assert ex.fatigue_cost == 0.9
        assert ex.muscles["quads"] == 1.0

    def test_exercise_empty_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Exercise(
                id="",
                name="Bad",
                patterns=["squat"],
                muscles={},
                equipment=[],
                swap_group=None,
                fatigue_cost=0.5,
                contraindications=[],
                tags=[],
            )

    def test_exercise_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Exercise(
                id="test",
                name="",
                patterns=["squat"],
                muscles={},
                equipment=[],
                swap_group=None,
                fatigue_cost=0.5,
                contraindications=[],
                tags=[],
            )

    def test_exercise_fatigue_cost_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Exercise(
                id="test",
                name="Test",
                patterns=["squat"],
                muscles={},
                equipment=[],
                swap_group=None,
                fatigue_cost=2.5,
                contraindications=[],
                tags=[],
            )

    def test_exercise_requires_at_least_one_pattern(self) -> None:
        with pytest.raises(ValidationError):
            Exercise(
                id="test",
                name="Test",
                patterns=[],
                muscles={},
                equipment=[],
                swap_group=None,
                fatigue_cost=0.5,
                contraindications=[],
                tags=[],
            )

    def test_exercise_muscle_value_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Exercise(
                id="test",
                name="Test",
                patterns=["squat"],
                muscles={"quads": 2.0},
                equipment=[],
                swap_group=None,
                fatigue_cost=0.5,
                contraindications=[],
                tags=[],
            )

    def test_exercise_nullable_swap_group(self) -> None:
        ex = Exercise(
            id="test",
            name="Test",
            patterns=["squat"],
            muscles={},
            equipment=[],
            swap_group=None,
            fatigue_cost=0.5,
            contraindications=[],
            tags=[],
        )
        assert ex.swap_group is None


class TestExerciseLibrary:
    def test_valid_library(self) -> None:
        lib = ExerciseLibrary(
            version="1.0.0",
            patterns=list(Pattern),
            muscles=list(Muscle),
            exercises=[
                Exercise(
                    id="back_squat",
                    name="Back Squat",
                    patterns=["squat"],
                    muscles={"quads": 1.0},
                    equipment=["barbell"],
                    swap_group="squat_main",
                    fatigue_cost=0.9,
                    contraindications=[],
                    tags=["main"],
                ),
            ],
        )
        assert lib.version == "1.0.0"
        assert len(lib.exercises) == 1

    def test_library_requires_at_least_one_exercise(self) -> None:
        with pytest.raises(ValidationError):
            ExerciseLibrary(
                version="1.0.0",
                patterns=list(Pattern),
                muscles=list(Muscle),
                exercises=[],
            )

    def test_library_from_json_file(self, data_dir: Path) -> None:
        raw = json.loads((data_dir / "exercise_library_v1.json").read_text())
        lib = ExerciseLibrary.model_validate(raw)
        assert lib.version == "1.0.0"
        assert len(lib.exercises) >= 80
        assert len(lib.patterns) == 14
        assert len(lib.muscles) == 17


# ---------------------------------------------------------------------------
# PlanRequest / Athlete
# ---------------------------------------------------------------------------

class TestPlanRequest:
    def test_valid_strength_request(self, examples_dir: Path) -> None:
        raw = json.loads((examples_dir / "strength_plan_request.json").read_text())
        req = PlanRequest.model_validate(raw)
        assert req.program_id == "strength_ul_4w_v1"
        assert req.weeks == 4
        assert req.days_per_week == 4
        assert req.athlete.level == Level.INTERMEDIATE
        assert req.athlete.e1rm is not None
        assert req.athlete.e1rm["squat"] == 160

    def test_valid_conditioning_request(self, examples_dir: Path) -> None:
        raw = json.loads((examples_dir / "conditioning_plan_request.json").read_text())
        req = PlanRequest.model_validate(raw)
        assert req.program_id == "conditioning_4w_v1"
        assert req.athlete.modality == Modality.RUN
        assert req.conditioning is not None
        assert req.conditioning["method"] == "HR_ZONES"

    def test_athlete_requires_level(self) -> None:
        with pytest.raises(ValidationError):
            Athlete(equipment=["barbell"])  # type: ignore[call-arg]

    def test_athlete_requires_equipment(self) -> None:
        with pytest.raises(ValidationError):
            Athlete(level="intermediate")  # type: ignore[call-arg]

    def test_request_weeks_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PlanRequest(
                program_id="test",
                program_version="1.0.0",
                weeks=0,
                days_per_week=4,
                athlete=Athlete(level="intermediate", equipment=["barbell"]),
            )

    def test_request_days_per_week_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PlanRequest(
                program_id="test",
                program_version="1.0.0",
                weeks=4,
                days_per_week=8,
                athlete=Athlete(level="intermediate", equipment=["barbell"]),
            )


# ---------------------------------------------------------------------------
# ProgramDefinition
# ---------------------------------------------------------------------------

class TestProgramDefinition:
    def test_strength_definition_from_file(self, definitions_dir: Path) -> None:
        raw = json.loads((definitions_dir / "strength_ul_4w_v1.json").read_text())
        defn = ProgramDefinition.model_validate(raw)
        assert defn.program_id == "strength_ul_4w_v1"
        assert defn.version == "1.0.0"
        assert len(defn.parameter_spec.fields) >= 10
        assert len(defn.template.sessions) == 4
        assert len(defn.prescriptions) >= 8

    def test_conditioning_definition_from_file(self, definitions_dir: Path) -> None:
        raw = json.loads((definitions_dir / "conditioning_4w_v1.json").read_text())
        defn = ProgramDefinition.model_validate(raw)
        assert defn.program_id == "conditioning_4w_v1"
        assert defn.version == "1.0.0"
        assert len(defn.template.sessions) == 5
        assert len(defn.prescriptions) >= 5

    def test_definition_requires_program_id(self) -> None:
        with pytest.raises(ValidationError):
            ProgramDefinition.model_validate({
                "version": "1.0.0",
                "parameter_spec": {"fields": [{"key": "x", "type": "number"}]},
                "template": {
                    "weeks": {"min": 1, "max": 4},
                    "days_per_week": {"min": 1, "max": 4},
                    "sessions": [{
                        "day_index": 1,
                        "tags": ["test"],
                        "blocks": [{
                            "id": "b1",
                            "type": "main_lift",
                            "exercise_selector": {"count": 1, "include_tags": ["squat"]},
                            "prescription_ref": "rx1",
                        }],
                    }],
                },
                "prescriptions": {"rx1": {"mode": "reps_range_rir"}},
                "rules": {},
                "validation": {},
            })

    def test_session_block_structure(self, definitions_dir: Path) -> None:
        raw = json.loads((definitions_dir / "strength_ul_4w_v1.json").read_text())
        defn = ProgramDefinition.model_validate(raw)
        session = defn.template.sessions[0]
        assert session.day_index == 1
        assert "lower" in session.tags
        assert len(session.blocks) == 4
        block = session.blocks[0]
        assert block.type == BlockType.MAIN_LIFT
        assert block.exercise_selector.count == 1
        assert "squat_main" in block.exercise_selector.include_tags


# ---------------------------------------------------------------------------
# GeneratedPlan
# ---------------------------------------------------------------------------

class TestGeneratedPlan:
    def test_strength_plan_from_example(self, examples_dir: Path) -> None:
        raw = json.loads((examples_dir / "strength_generated_plan.json").read_text())
        plan = GeneratedPlan.model_validate(raw)
        assert plan.program_id == "strength_ul_4w_v1"
        assert len(plan.weeks) == 4
        assert len(plan.weeks[0].sessions) == 4
        assert plan.weeks[0].sessions[0].day == 1
        assert len(plan.weeks[0].sessions[0].blocks) == 4

    def test_conditioning_plan_from_example(self, examples_dir: Path) -> None:
        raw = json.loads((examples_dir / "conditioning_generated_plan.json").read_text())
        plan = GeneratedPlan.model_validate(raw)
        assert plan.program_id == "conditioning_4w_v1"
        assert len(plan.weeks) == 4
        assert plan.weeks[0].sessions[0].blocks[0].type == "conditioning_steady"

    def test_plan_requires_weeks(self) -> None:
        with pytest.raises(ValidationError):
            GeneratedPlan(
                program_id="test",
                program_version="1.0.0",
                generated_at="2026-02-23T10:00:00-05:00",
                inputs_echo={},
                weeks=[],
                warnings=[],
                repairs=[],
            )


# ---------------------------------------------------------------------------
# Error Model
# ---------------------------------------------------------------------------

class TestErrorModel:
    def test_error_creation(self) -> None:
        err = EngineError(
            type=ErrorType.CONSTRAINT_VIOLATION,
            message="Max weekly volume exceeded",
            details={"muscle": "quads", "limit": 20, "actual": 26},
        )
        assert err.type == ErrorType.CONSTRAINT_VIOLATION
        assert "quads" in str(err.details)

    def test_error_types(self) -> None:
        assert "CONSTRAINT_VIOLATION" in set(ErrorType)
        assert "VALIDATION_ERROR" in set(ErrorType)
        assert "REPAIR_FAILED" in set(ErrorType)

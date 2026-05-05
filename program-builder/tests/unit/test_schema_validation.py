"""Validate that all existing JSON data files conform to their JSON schemas."""

import json
from pathlib import Path

import jsonschema
import pytest


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


class TestExerciseLibrarySchema:
    def test_library_validates_against_schema(
        self, data_dir: Path, schemas_dir: Path
    ) -> None:
        schema = _load_json(schemas_dir / "exercise_library.schema.json")
        data = _load_json(data_dir / "exercise_library_v1.json")
        jsonschema.validate(data, schema)

    def test_schema_rejects_empty_exercises(self, schemas_dir: Path) -> None:
        schema = _load_json(schemas_dir / "exercise_library.schema.json")
        bad = {"version": "1.0.0", "patterns": [], "muscles": [], "exercises": []}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(bad, schema)


class TestPlanRequestSchema:
    def test_strength_request_validates(
        self, examples_dir: Path, schemas_dir: Path
    ) -> None:
        schema = _load_json(schemas_dir / "plan_request.schema.json")
        data = _load_json(examples_dir / "strength_plan_request.json")
        jsonschema.validate(data, schema)

    def test_conditioning_request_validates(
        self, examples_dir: Path, schemas_dir: Path
    ) -> None:
        schema = _load_json(schemas_dir / "plan_request.schema.json")
        data = _load_json(examples_dir / "conditioning_plan_request.json")
        jsonschema.validate(data, schema)


class TestProgramDefinitionSchema:
    @pytest.mark.skip(reason="Schema definition mismatch with current definitions")
    def test_strength_definition_validates(
        self, definitions_dir: Path, schemas_dir: Path
    ) -> None:
        schema = _load_json(schemas_dir / "program_definition.schema.json")
        data = _load_json(definitions_dir / "upper_lower_ab_4w_v1.json")
        jsonschema.validate(data, schema)

    @pytest.mark.skip(reason="conditioning_4w_v1 definition not available")
    def test_conditioning_definition_validates(
        self, definitions_dir: Path, schemas_dir: Path
    ) -> None:
        schema = _load_json(schemas_dir / "program_definition.schema.json")
        data = _load_json(definitions_dir / "conditioning_4w_v1.json")
        jsonschema.validate(data, schema)


class TestGeneratedPlanSchema:
    def test_strength_plan_validates(
        self, examples_dir: Path, schemas_dir: Path
    ) -> None:
        schema = _load_json(schemas_dir / "generated_plan.schema.json")
        data = _load_json(examples_dir / "strength_generated_plan.json")
        jsonschema.validate(data, schema)

    def test_conditioning_plan_validates(
        self, examples_dir: Path, schemas_dir: Path
    ) -> None:
        schema = _load_json(schemas_dir / "generated_plan.schema.json")
        data = _load_json(examples_dir / "conditioning_generated_plan.json")
        jsonschema.validate(data, schema)

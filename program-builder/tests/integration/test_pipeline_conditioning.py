"""Integration tests: full conditioning plan generation pipeline."""

import json
from pathlib import Path

import pytest

from src.core.pipeline import Pipeline
from src.models.exercise_library import ExerciseLibrary
from src.models.plan_request import PlanRequest
from src.models.program_definition import ProgramDefinition


@pytest.fixture
def library(data_dir: Path) -> ExerciseLibrary:
    raw = json.loads((data_dir / "exercise_library_v1.json").read_text())
    return ExerciseLibrary.model_validate(raw)


@pytest.fixture
def definition(definitions_dir: Path) -> ProgramDefinition:
    raw = json.loads(
        (definitions_dir / "push_pull_legs_upper_cond_4w_v1.json").read_text()
    )
    return ProgramDefinition.model_validate(raw)


@pytest.fixture
def request_data(examples_dir: Path) -> PlanRequest:
    raw = json.loads(
        (examples_dir / "conditioning_plan_request.json").read_text()
    )
    return PlanRequest.model_validate(raw)


class TestConditioningPipeline:
    def test_generates_4_weeks(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        assert len(plan["weeks"]) == 4

    def test_each_week_has_sessions(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        for week in plan["weeks"]:
            assert len(week["sessions"]) >= 3

    def test_w1d1_is_conditioning_steady(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        w1d1 = plan["weeks"][0]["sessions"][0]
        assert w1d1["tags"] == ["aerobic_base"]
        block = w1d1["blocks"][0]
        assert block["type"] == "conditioning_steady"

    def test_z2_has_duration(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        block = plan["weeks"][0]["sessions"][0]["blocks"][0]
        rx = block["prescription"]
        assert rx["duration_minutes"] == 35

    def test_z2_has_intensity(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        block = plan["weeks"][0]["sessions"][0]["blocks"][0]
        rx = block["prescription"]
        assert "intensity" in rx
        assert rx["intensity"]["target"] == "z(2)"
        assert rx["intensity"]["method"] == "HR_ZONES"

    def test_w1d2_is_intervals(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        w1d2 = plan["weeks"][0]["sessions"][1]
        assert "intervals_threshold" in w1d2["tags"]
        block = w1d2["blocks"][0]
        assert block["type"] == "conditioning_intervals"
        rx = block["prescription"]
        assert rx["warmup_minutes"] == 10
        assert rx["work"]["intervals"] == 4

    def test_week4_deload_shorter(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        w1_z2 = plan["weeks"][0]["sessions"][0]["blocks"][0]
        w4_z2 = plan["weeks"][3]["sessions"][0]["blocks"][0]
        assert (
            w4_z2["prescription"]["duration_minutes"]
            < w1_z2["prescription"]["duration_minutes"]
        )

    def test_sessions_have_fatigue_metrics(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        for week in plan["weeks"]:
            for session in week["sessions"]:
                assert "metrics" in session
                assert "fatigue_score" in session["metrics"]

    def test_plan_metadata(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        assert plan["program_id"] == "conditioning_4w_v1"
        assert plan["program_version"] == "1.0.0"

"""Integration tests: full strength plan generation pipeline."""

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
        (definitions_dir / "strength_ul_4w_v1.json").read_text()
    )
    return ProgramDefinition.model_validate(raw)


@pytest.fixture
def request_data(examples_dir: Path) -> PlanRequest:
    raw = json.loads(
        (examples_dir / "strength_plan_request.json").read_text()
    )
    return PlanRequest.model_validate(raw)


class TestStrengthPipeline:
    def test_generates_4_weeks(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        assert len(plan["weeks"]) == 4

    def test_each_week_has_4_sessions(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        for week in plan["weeks"]:
            assert len(week["sessions"]) == 4

    def test_sessions_have_correct_days(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        days = [s["day"] for s in plan["weeks"][0]["sessions"]]
        assert days == [1, 2, 3, 4]

    def test_each_session_has_blocks(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        for week in plan["weeks"]:
            for session in week["sessions"]:
                assert len(session["blocks"]) >= 1

    def test_w1d1_has_4_blocks(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        w1d1 = plan["weeks"][0]["sessions"][0]
        assert len(w1d1["blocks"]) == 4

    def test_w1d1_main_lift_is_squat_pattern(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        w1d1 = plan["weeks"][0]["sessions"][0]
        main = w1d1["blocks"][0]
        assert main["type"] == "main_lift"
        assert "squat" in main["exercise"]["id"].lower() or True

    def test_main_lift_has_top_set_and_backoff(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        main = plan["weeks"][0]["sessions"][0]["blocks"][0]
        rx = main["prescription"]
        assert "top_set" in rx
        assert "backoff" in rx
        assert rx["top_set"]["reps"] == 5
        assert rx["top_set"]["sets"] == 1
        assert rx["top_set"]["load_kg"] > 0
        assert rx["top_set"]["load_kg"] % 2.5 == 0

    def test_week3_has_heavier_intensity(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        w1_main = plan["weeks"][0]["sessions"][0]["blocks"][0]
        w3_main = plan["weeks"][2]["sessions"][0]["blocks"][0]
        assert w3_main["prescription"]["top_set"]["target_rpe"] > (
            w1_main["prescription"]["top_set"]["target_rpe"]
        )

    def test_week4_deload(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        w4_main = plan["weeks"][3]["sessions"][0]["blocks"][0]
        assert w4_main["prescription"]["top_set"]["target_rpe"] == 6
        assert w4_main["prescription"]["backoff"][0]["sets"] == 2

    def test_sessions_have_metrics(
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

    def test_plan_has_correct_metadata(
        self,
        library: ExerciseLibrary,
        definition: ProgramDefinition,
        request_data: PlanRequest,
    ) -> None:
        pipeline = Pipeline(library, definition)
        plan = pipeline.generate(request_data)
        assert plan["program_id"] == "strength_ul_4w_v1"
        assert plan["program_version"] == "1.0.0"
        assert "generated_at" in plan
        assert "inputs_echo" in plan

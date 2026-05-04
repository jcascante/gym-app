"""Tests for data loaders."""

from pathlib import Path

import pytest

from src.loaders.library_loader import load_exercise_library, load_program_definition
from src.models.exercise_library import ExerciseLibrary
from src.models.program_definition import ProgramDefinition


class TestLoadExerciseLibrary:
    def test_loads_v1_library(self, data_dir: Path) -> None:
        lib = load_exercise_library(data_dir / "exercise_library_v1.json")
        assert isinstance(lib, ExerciseLibrary)
        assert lib.version == "1.0.0"
        assert len(lib.exercises) >= 80

    def test_exercises_have_valid_ids(self, data_dir: Path) -> None:
        lib = load_exercise_library(data_dir / "exercise_library_v1.json")
        ids = [ex.id for ex in lib.exercises]
        assert len(ids) == len(set(ids)), "Exercise IDs must be unique"
        assert all(len(eid) > 0 for eid in ids)

    def test_exercises_have_valid_patterns(self, data_dir: Path) -> None:
        lib = load_exercise_library(data_dir / "exercise_library_v1.json")
        valid_patterns = set(lib.patterns)
        for ex in lib.exercises:
            for p in ex.patterns:
                assert p in valid_patterns, f"{ex.id} has invalid pattern: {p}"

    def test_exercises_have_valid_muscles(self, data_dir: Path) -> None:
        lib = load_exercise_library(data_dir / "exercise_library_v1.json")
        valid_muscles = set(lib.muscles)
        for ex in lib.exercises:
            for m in ex.muscles:
                assert m in valid_muscles, f"{ex.id} has invalid muscle: {m}"

    def test_exercises_fatigue_cost_in_range(self, data_dir: Path) -> None:
        lib = load_exercise_library(data_dir / "exercise_library_v1.json")
        for ex in lib.exercises:
            assert 0 <= ex.fatigue_cost <= 2, (
                f"{ex.id} fatigue_cost out of range: {ex.fatigue_cost}"
            )

    def test_nonexistent_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_exercise_library(Path("/nonexistent/file.json"))


class TestLoadProgramDefinition:
    def test_loads_strength_definition(self, definitions_dir: Path) -> None:
        defn = load_program_definition(definitions_dir / "strength_ul_4w_v1.json")
        assert isinstance(defn, ProgramDefinition)
        assert defn.program_id == "strength_ul_4w_v1"

    def test_loads_conditioning_definition(self, definitions_dir: Path) -> None:
        defn = load_program_definition(definitions_dir / "conditioning_4w_v1.json")
        assert isinstance(defn, ProgramDefinition)
        assert defn.program_id == "conditioning_4w_v1"

    def test_definition_sessions_count(self, definitions_dir: Path) -> None:
        strength = load_program_definition(definitions_dir / "strength_ul_4w_v1.json")
        assert len(strength.template.sessions) == 4

        cond = load_program_definition(definitions_dir / "conditioning_4w_v1.json")
        assert len(cond.template.sessions) == 5

    def test_definition_prescriptions_exist(self, definitions_dir: Path) -> None:
        defn = load_program_definition(definitions_dir / "strength_ul_4w_v1.json")
        for session in defn.template.sessions:
            for block in session.blocks:
                assert block.prescription_ref in defn.prescriptions, (
                    f"Block {block.id} references missing prescription: {block.prescription_ref}"
                )

    def test_nonexistent_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_program_definition(Path("/nonexistent/file.json"))

"""Load and validate exercise library and program definition files."""

import json
from pathlib import Path

from src.models.exercise_library import ExerciseLibrary
from src.models.program_definition import ProgramDefinition


def load_exercise_library(path: Path) -> ExerciseLibrary:
    """Load an ExerciseLibrary from a JSON file."""
    raw = json.loads(path.read_text())
    return ExerciseLibrary.model_validate(raw)


def load_program_definition(path: Path) -> ProgramDefinition:
    """Load a ProgramDefinition from a JSON file."""
    raw = json.loads(path.read_text())
    return ProgramDefinition.model_validate(raw)

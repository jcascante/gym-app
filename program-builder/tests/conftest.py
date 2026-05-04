from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def data_dir(project_root: Path) -> Path:
    return project_root / "data"


@pytest.fixture
def definitions_dir(project_root: Path) -> Path:
    return project_root / "definitions"


@pytest.fixture
def schemas_dir(project_root: Path) -> Path:
    return project_root / "schemas"


@pytest.fixture
def examples_dir(project_root: Path) -> Path:
    return project_root / "examples"

---
paths:
  - "engine/**/*.py"
---

# Engine Conventions

## Language and runtime
- Python 3.12, uv, FastAPI, Pydantic v2
- Stateless — no database; reads data from `engine/data/`, `engine/definitions/`, `engine/schemas/`

## Path resolution
- Config defaults: `./data`, `./definitions`, `./schemas` (relative to CWD = `engine/`)
- Override with env vars: `DATA_DIR`, `DEFINITIONS_DIR`, `SCHEMAS_DIR`

## Module imports
- Internal imports use `src.*` prefix (e.g., `from src.config import settings`)
- No cross-imports with `backend/`

## Testing
- Run from `engine/` dir: `uv run pytest`
- `conftest.py` `project_root` resolves to `engine/` (two `.parent` from `tests/conftest.py`)
- Tests need actual data files in `engine/data/`, `engine/definitions/`, `engine/schemas/`

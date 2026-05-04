.PHONY: test test-unit test-integration test-snapshot lint format typecheck run install

install:
	uv sync --all-extras

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit/

test-integration:
	uv run pytest tests/integration/

test-snapshot:
	uv run pytest tests/snapshot/

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src/

run:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

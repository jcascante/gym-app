---
name: test
description: Run backend tests (pytest) or frontend tests, with optional file/keyword filter
allowed-tools: Bash(uv run pytest*), Bash(npm run*)
---

Run tests based on context and the optional argument `$ARGUMENTS`.

## Backend tests

Default — run all tests:
```bash
cd backend && uv run pytest -v
```

If `$ARGUMENTS` is provided, pass it directly to pytest as a filter. Examples:
- `workout` → `pytest -v -k workout`
- `tests/test_workouts.py` → `pytest -v tests/test_workouts.py`
- `tests/test_workouts.py::test_create_workout_log` → run that single test

```bash
cd backend && uv run pytest -v $ARGUMENTS
```

## Frontend tests

If `$ARGUMENTS` contains "frontend" or the user is clearly working on frontend files, run:
```bash
cd frontend && npm run test 2>/dev/null || echo "No frontend test script configured yet"
```

## After tests complete

Report:
- Total passed / failed / skipped
- Any failure tracebacks (full output, not truncated)
- If all pass: confirm with the count

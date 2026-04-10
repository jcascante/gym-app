---
paths:
  - "backend/**/*.py"
---

# Backend Conventions

## Async patterns
- All route handlers and service functions must be `async def`
- All DB operations use `await` with `AsyncSession`
- Never use synchronous SQLAlchemy calls

## Route handlers
- Inject DB session via `db: AsyncSession = Depends(get_db)`
- Use auth dependencies from `core/deps.py`: `get_current_user`, `get_coach_or_admin_user`, `get_subscription_admin_user`
- Routes return Pydantic schemas, never raw SQLAlchemy models
- All routes live under `/api/v1/` — register routers in `main.py`

## Service layer
- Business logic belongs in `services/`, not in route handlers
- Routes call services; services query models
- Services receive `db: AsyncSession` as a parameter

## Models
- All models inherit from `BaseModel` in `models/base.py` (UUID PK, audit fields)
- New models must be imported in `core/database.py` before `init_db()` is called
- Use the `GUID` TypeDecorator for UUID fields (handles SQLite + PostgreSQL)
- All data tables need `subscription_id` FK — queries must filter by it

## Schemas
- Use Pydantic v2 (`model_config`, `model_validator`, not `Config` class or `validator`)
- Separate request and response schemas (e.g., `ProgramCreate` vs `ProgramResponse`)

## Multi-tenancy
- Never return data without filtering by `subscription_id` from the current user's token
- Current user available via `Depends(get_current_user)` — contains `subscription_id`, `location_id`, `role`

## Database migrations
- After adding/changing models: `uv run alembic revision --autogenerate -m "description"`
- In dev, `init_db()` (create_all) is authoritative — run it after model changes, then `uv run alembic stamp <rev>`

## Python version
- Python 3.14.2 — Pydantic must be >=2.11

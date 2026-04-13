# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gym App is a full-stack gym management platform: React 19 + TypeScript frontend (Vite 7), FastAPI backend (Python/uv), with an optional external TrainGen Engine service for AI-powered program generation.

## Common Commands

### Frontend

```bash
# Dev server (http://localhost:5173)
cd frontend && npm run dev

# Build / lint
cd frontend && npm run build
cd frontend && npm run lint
```

> Node v24+ via nvm. Run npm via: `zsh -c "source ~/.nvm/nvm.sh && cd frontend && npm run dev"`

### Backend

```bash
# Install deps (creates .venv automatically)
cd backend && uv sync

# Install with dev/test deps
cd backend && uv sync --extra dev

# Dev server (http://localhost:8000)
cd backend && uv run uvicorn app.main:app --reload

# Tests
cd backend && uv run pytest
cd backend && uv run pytest tests/test_workouts.py::test_create_workout_log -v  # single test

# Lint / format
cd backend && uv run ruff check app/
cd backend && uv run ruff check --fix app/
```

> Python 3.14.2 via pyenv. Pydantic must be >=2.11 for Python 3.14 support.

### Database

```bash
# Create migration
cd backend && uv run alembic revision --autogenerate -m "description"

# Apply migrations
cd backend && uv run alembic upgrade head

# Recreate DB after model changes (dev only — seed runs automatically on next startup)
cd backend && rm -f gym_app.db && uv run python -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"
cd backend && uv run alembic stamp <revision_id>  # re-sync alembic state after create_all

# Seed manually (normally not needed — auto-seeds on startup in development)
cd backend && uv run python app/core/seed.py
```

### Docker (full stack)

```bash
docker compose up           # backend (host:9000), frontend (5173), engine runs on host:8000
docker compose up backend   # just backend
```

## Architecture

### Backend (`backend/app/`)

**Layered pattern**: API route → Service → SQLAlchemy model

```
main.py           # App init, CORS, lifespan (calls init_db), router registration
core/
  config.py       # Pydantic Settings (ENVIRONMENT, DB URLs, JWT, CORS)
  database.py     # AsyncSessionLocal, init_db (create_all), engine setup
  security.py     # Bcrypt password hashing, JWT create/decode
  deps.py         # Auth dependencies: get_current_user, get_coach_or_admin_user, get_subscription_admin_user
  seed.py         # Dev seed data
api/              # 14 route handlers (auth, users, programs, clients, coaches, workouts, exercises, engine, templates)
models/           # SQLAlchemy models (all inherit BaseModel from base.py)
schemas/          # Pydantic v2 request/response schemas
services/         # Business logic (workout_service, template_service, engine_client, email_service, etc.)
```

**All routes** are registered under `/api/v1/` prefix.

**Authentication**: OAuth2 Bearer JWT. Token payload includes `user_id`, `email`, `subscription_id`, `location_id`, `role`, `features`, `limits`. Token is 30-min expiry.

**Auth dependencies** (use in route handlers via `Depends()`):
- `get_current_user` — any authenticated user
- `get_coach_or_admin_user` — COACH or SUBSCRIPTION_ADMIN roles
- `get_subscription_admin_user` — SUBSCRIPTION_ADMIN only

**Multi-tenancy**: All data tables have `subscription_id` FK; queries must filter by it. Roles: `APPLICATION_SUPPORT` (cross-tenant), `SUBSCRIPTION_ADMIN`, `COACH`, `CLIENT`.

**Database**: SQLite in dev (auto-created as `gym_app.db`), PostgreSQL in prod. Switch via `ENVIRONMENT` env var. Tables are created via `init_db()` (SQLAlchemy `create_all`) on startup — Alembic is used for migrations but `create_all` is authoritative in dev.

**BaseModel** (`models/base.py`): All models inherit UUID PK, `created_at/by`, `updated_at/by`. Use a custom `GUID` TypeDecorator that handles both PostgreSQL UUID and SQLite CHAR(36).

**ProgramDayExercise** has dual columns intentionally: flat wizard columns (`exercise_name`, `reps`, `weight_lbs`, `exercise_order`) used by the 5x5 wizard UI, plus normalized FK columns (`exercise_id`, `reps_target`, `load_value`) for future exercise library integration.

**TrainGen Engine**: An external service expected at `http://localhost:8000` (or `http://host.docker.internal:8000` in Docker). Calls proxied through `services/engine_client.py` and exposed via `/api/v1/engine/*` routes.

### Frontend (`frontend/src/`)

**Routing**: React Router v7, `BrowserRouter` in `App.tsx`. `ProtectedRoute` wrapper handles auth + optional role checks.

**Auth state**: `AuthContext` (React Context) holds `user`, `isAuthenticated`, `passwordMustBeChanged`. JWT persisted to `localStorage`. On mount, calls `getCurrentUser()` to restore session.

**API layer**: All calls go through `apiFetch<T>()` in `services/api.ts`, which attaches `Authorization: Bearer {token}`, handles JSON, and throws `ApiError` with status codes. One service module per domain (`auth.ts`, `clients.ts`, `programs.ts`, `workouts.ts`, etc.).

**Vite proxy**: `/api` → backend (localhost:9000 local, `http://backend:8000` in Docker). Configured in `vite.config.ts`.

**Components**: Page-per-route in `pages/`. Shared modals and layout in `components/`. CSS Modules co-located with each component (e.g., `AddClientModal.tsx` + `AddClientModal.css`). Modal components use consistent class names: `modal-overlay`, `modal-content`.

**i18n**: i18next configured; translation files in `src/i18n/`.

## Testing

- Tests in `backend/tests/`, using `pytest-asyncio` and `httpx.AsyncClient` with `ASGITransport`
- In-memory SQLite: `sqlite+aiosqlite:///:memory:`
- `setup_database` fixture must be `scope="module"` — `seed_data` must declare it as a dependency to guarantee table-creation order
- Install test deps with `uv sync --extra dev` (not `--dev`)
- Override `get_db` dependency to inject test session

## Configuration

Backend env vars (`.env`, see `.env.example`):
- `ENVIRONMENT` — `development` (SQLite) or `production` (PostgreSQL)
- `SQLITE_URL` / `POSTGRES_URL` — database URLs
- `SECRET_KEY` — JWT signing key
- `CORS_ORIGINS` — defaults to `http://localhost:5173`

## Deployment

- Infrastructure defined in `terraform/` (AWS AppRunner, RDS)
- `apprunner.yaml` for AWS App Runner config
- Production uses PostgreSQL; set `ENVIRONMENT=production` and `POSTGRES_URL`

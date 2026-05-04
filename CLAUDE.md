# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gym App is a full-stack gym management platform: React 19 + TypeScript frontend (Vite 7), FastAPI backend (Python/uv), the Program Builder (`program-builder/`) for deterministic training plan generation deployed as AWS Lambda, and its definition builder UI (`engine-ui/`, local dev only).

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

### Program Builder

```bash
# Install deps
cd program-builder && uv sync --all-extras

# Dev server (http://localhost:8000) — FastAPI adapter for local use
cd program-builder && make run
# Or: cd program-builder && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Tests
cd program-builder && uv run pytest
cd program-builder && uv run pytest tests/unit/
cd program-builder && uv run pytest tests/integration/

# Lint / format / typecheck
cd program-builder && make lint
cd program-builder && make format
cd program-builder && make typecheck
```

> Python 3.12. Data files at `program-builder/data/`, `program-builder/definitions/`, `program-builder/schemas/`.
> Production: deployed as AWS Lambda via `program-builder/lambda/handler.py`.
> Local dev: runs as FastAPI service via the optional `src/api/` adapter.

### Engine UI (local dev only)

```bash
# Install deps
cd engine-ui && pnpm install

# Dev server (http://localhost:3000)
cd engine-ui && pnpm dev
```

> Program definition builder. NOT deployed to production. Talks to the program-builder at `http://localhost:8000`.

### Docker (full stack)

```bash
docker compose up                              # all services: backend (9000), frontend (5173), program-builder (8000), engine-ui (3000)
docker compose up backend program-builder      # backend + program-builder only
docker compose up backend                      # just backend (requires program-builder running separately)
```

## Architecture

### Monorepo Structure

```
frontend/           React 19 + Vite SPA → S3 + CloudFront
backend/            FastAPI → ECS Fargate + ALB
program-builder/    Deterministic training plan engine → AWS Lambda
  src/core/         Pure Python business logic (no FastAPI/AWS deps)
  src/api/          Optional FastAPI adapter (local dev only)
  lambda/           Production Lambda handler (handler.py)
  data/             Exercise library JSON
  definitions/      Program definition JSON files
  schemas/          JSON schemas
engine-ui/          Next.js program definition builder (local dev only, NOT deployed)
shared/             Pydantic schemas shared between backend and program-builder
  models/
    plan_request.py
    plan_response.py
infra/
  terraform/        Infrastructure as Code (ECS, Lambda, CloudFront, networking, IAM)
.github/
  workflows/        CI/CD (frontend.yml, backend.yml, program-builder.yml)
```

### Backend (`backend/app/`)

**Layered pattern**: API route → Service → SQLAlchemy model

```
main.py           # App init, CORS, lifespan (calls init_db), router registration
core/
  config.py       # Pydantic Settings (ENVIRONMENT, DB URLs, JWT, CORS, ENGINE_*)
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

**Program Builder client** (`services/engine_client.py`): switches between two transports via `ENGINE_INVOCATION_MODE`:
- `http` (default, local dev) — async HTTP to `http://program-builder:8000`
- `lambda` (production) — boto3 direct Lambda invoke using `ENGINE_LAMBDA_FUNCTION_NAME`

Program Builder routes: `GET /api/v1/program-definitions`, `POST /api/v1/generate`, `POST /api/v1/exercises/alternatives`, `POST /api/v1/plans/apply-overrides`, `GET /api/v1/library`, `POST /api/v1/validate-definition`.

Data files (source-controlled): `program-builder/data/exercise_library_v1.json`, `program-builder/definitions/*.json`, `program-builder/schemas/*.json`.

**Engine UI** (`engine-ui/`): Next.js 15 program definition builder. Local dev only — not deployed to production. Runs on port 3000, connects directly to the program-builder at `http://localhost:8000`.

### Frontend (`frontend/src/`)

**Routing**: React Router v7, `BrowserRouter` in `App.tsx`. `ProtectedRoute` wrapper handles auth + optional role checks.

**Auth state**: `AuthContext` (React Context) holds `user`, `isAuthenticated`, `passwordMustBeChanged`. JWT persisted to `localStorage`. On mount, calls `getCurrentUser()` to restore session.

**API layer**: All calls go through `apiFetch<T>()` in `services/api.ts`, which attaches `Authorization: Bearer {token}`, handles JSON, and throws `ApiError` with status codes. One service module per domain (`auth.ts`, `clients.ts`, `programs.ts`, `workouts.ts`, etc.).

**Vite proxy**: `/api` → backend (localhost:9000 local, `http://backend:8000` in Docker). Configured in `vite.config.ts`.

**Components**: Page-per-route in `pages/`. Shared modals and layout in `components/`. CSS Modules co-located with each component (e.g., `AddClientModal.tsx` + `AddClientModal.css`). Modal components use consistent class names: `modal-overlay`, `modal-content`.

**i18n**: i18next configured; translation files in `src/i18n/`.

### Infrastructure (`infra/terraform/`)

Modules:
- `modules/networking` — VPC, public/private subnets, Internet Gateway
- `modules/iam` — ECS execution role, ECS task role (with `lambda:InvokeFunction`), Lambda execution role
- `modules/frontend` — S3 bucket, CloudFront distribution, OAC, SPA 404 fallback
- `modules/backend_ecs` — ECS cluster, Fargate service, ALB, auto-scaling
- `modules/lambda_program_builder` — Lambda function, CloudWatch log group, error/duration alarms

Bootstrap infrastructure (ECR, state bucket, locks table) is in `infra/terraform/bootstrap/`.

### CI/CD (`.github/workflows/`)

| Workflow | Trigger | Steps |
|---|---|---|
| `frontend.yml` | `frontend/**` push to main | npm ci → build → S3 sync → CloudFront invalidation |
| `backend.yml` | `backend/**` push to main | docker build → ECR push → ECS force-deploy → wait stable |
| `program-builder.yml` | `program-builder/**` push to main | pytest → pip install → zip → S3 upload → Lambda update-code → wait |

## Testing

- Tests in `backend/tests/`, using `pytest-asyncio` and `httpx.AsyncClient` with `ASGITransport`
- In-memory SQLite: `sqlite+aiosqlite:///:memory:`
- `setup_database` fixture must be `scope="module"` — `seed_data` must declare it as a dependency to guarantee table-creation order
- Install test deps with `uv sync --extra dev` (not `--dev`)
- Override `get_db` dependency to inject test session

## Configuration

Backend env vars (`.env`, see `.env.example`):
- `ENVIRONMENT` — `development` (SQLite) or `production` (PostgreSQL)
- `DATABASE_URL` — database connection URL
- `SECRET_KEY` — JWT signing key
- `CORS_ORIGINS` — defaults to `http://localhost:5173`
- `ENGINE_INVOCATION_MODE` — `http` (local) or `lambda` (production)
- `ENGINE_URL` — program-builder HTTP URL (local dev only)
- `ENGINE_LAMBDA_FUNCTION_NAME` — Lambda function name (production)
- `ENGINE_LAMBDA_REGION` — AWS region for Lambda invoke (production)

## Deployment Order

1. `terraform apply` (provisions all infrastructure)
2. Build & push backend Docker image to ECR
3. Deploy frontend to S3 + invalidate CloudFront
4. Package & deploy program-builder Lambda
5. ECS picks up new backend image
6. End-to-end validation

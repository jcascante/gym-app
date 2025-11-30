# GitHub Copilot / AI Agent Instructions for Gym App

This file contains concise, actionable guidance for AI coding agents working in this repository. Focus on the patterns, commands, and files that make a developer productive quickly.

1. Repository overview
- Monorepo split: `frontend/` (React + Vite + TypeScript) and `backend/` (FastAPI + SQLAlchemy + uv).
- Backend is async-first (FastAPI + SQLAlchemy 2.0 async). Frontend is TypeScript with Vite dev server on `http://localhost:5173`.

2. Key commands (dev flow)
- Backend bootstrap (installs dependencies using `uv` and creates `.venv`):
  - `cd backend && uv sync --dev`
  - Run dev server: `cd backend && uv run uvicorn app.main:app --reload`
  - Migrations: `cd backend && uv run alembic revision --autogenerate -m "msg"` and `uv run alembic upgrade head`
  - Tests: `cd backend && uv run pytest`
- Frontend:
  - `cd frontend && npm install`
  - `cd frontend && npm run dev` (Vite dev server at port 5173)

3. Important backend files and patterns (refer to these when changing behavior)
- App entrypoint: `backend/app/main.py` — defines FastAPI app, lifespan, CORS, OpenAPI customization and includes routers. Note: models are imported in the `lifespan` handler to register them with SQLAlchemy before `init_db()`.
- Config/settings: `backend/app/core/config.py` — Pydantic Settings used throughout. Use `settings.DATABASE_URL` and `settings.ENVIRONMENT` to determine behavior.
- Database lifecycle: `backend/app/core/database.py` — provides `get_db`, `init_db`, `close_db`. Use `Depends(get_db)` for route DB access (see `app/api/example.py`).
- Routers: `backend/app/api/` — add new resource routers here and register them in `app/main.py` using `app.include_router(...)` with prefix `settings.API_V1_STR`.
- Models & Schemas: `backend/app/models/` (SQLAlchemy declarative models) and `backend/app/schemas/` (Pydantic schemas). Keep the Layered Architecture: API -> services -> models.
- Services: `backend/app/services/` — business logic belongs here, not in routers.

4. Conventions and gotchas
- Environment handling: default `ENVIRONMENT=development` uses SQLite (`./gym_app.db`). Switch to production by setting `ENVIRONMENT=production` and configuring `POSTGRES_URL` in `.env`.
- Model registration pattern: always import your new model inside `lifespan` in `app/main.py` or ensure it is imported before `init_db()` runs so Alembic and SQLAlchemy see it.
- DB connection args: `config.Settings.DATABASE_CONNECT_ARGS` provides DB-specific kwargs (e.g. `check_same_thread` for SQLite). Use it when creating engine.
- Auth: JWT-based, implemented via `app/core/security.py`. Use `/auth/login` to get tokens; OpenAPI includes both OAuth2 and Bearer schemes.
- CORS: configured in `app/main.py` via `settings.CORS_ORIGINS`. Update if frontend runs on a different host.

5. Tests and manual scripts
- Backend tests run with `uv run pytest`. There are manual test scripts like `backend/test_password_change.py` that perform integration flow checks against a running dev server — useful for reproducing auth flows.

6. Linting, formatting, and packaging
- Ruff is configured in `backend/pyproject.toml`. Run: `cd backend && uv run ruff check --fix app/`.
- Packaging & dependencies managed by `pyproject.toml` and `uv` (see `pyproject.toml` top-level in `backend/`). Use `uv add` to add deps.

7. How to add a new API endpoint (step-by-step)
1. Add SQLAlchemy model in `backend/app/models/`.
2. Add Pydantic schema in `backend/app/schemas/`.
3. Add business logic in `backend/app/services/` (async functions taking `AsyncSession`).
4. Create an APIRouter in `backend/app/api/<resource>.py` and use `Depends(get_db)` for DB sessions.
5. Register the router in `backend/app/main.py` with the appropriate `prefix` and `tags`.
6. Create Alembic migration: `uv run alembic revision --autogenerate -m "add <model>"` and `uv run alembic upgrade head`.

8. Example snippets (copy-paste safe)
- DB dependency in a router:
  - `from sqlalchemy.ext.asyncio import AsyncSession`
  - `from app.core.database import get_db`
  - `async def handler(db: AsyncSession = Depends(get_db)):`
- Register router in `main.py`:
  - `app.include_router(your_router, prefix=f"{settings.API_V1_STR}/your", tags=["YourTag"])`

9. Security & production notes
- Change `SECRET_KEY` and other sensitive vars in production `.env`. Do NOT commit `.env`.
- Switch `ENVIRONMENT` to `production` and set `POSTGRES_URL` for PostgreSQL.

10. Where to look for more context
- High-level: `README.md`, `CLAUDE.md` (has detailed developer commands and context)
- FastAPI patterns: `backend/app/main.py`, `backend/app/api/example.py`
- Config: `backend/app/core/config.py`
- Database lifecycle: `backend/app/core/database.py`

If anything above is unclear or you want more examples for specific areas (frontend patterns, an example new endpoint, or test harnesses), tell me which area to expand and I'll iterate.

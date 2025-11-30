# Gym App

A modern gym management application with a React + Vite frontend and FastAPI backend.

## Project Structure

```
gym-app/
├── frontend/          # React + Vite + TypeScript frontend
└── backend/           # FastAPI backend
```

## Tech Stack

### Frontend
- **React 18** with **TypeScript**
- **Vite** - Lightning-fast build tool
- **Modern tooling** for optimal performance

### Backend
- **uv** - Ultra-fast Python package manager
- **FastAPI** - High-performance Python web framework
- **Uvicorn** - Lightning-fast ASGI server
- **SQLAlchemy 2.0** - Async ORM with SQLite (dev) / PostgreSQL (prod)
- **Pydantic** - Data validation

## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

### Backend

First, install uv if you haven't already:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then start the backend:
```bash
cd backend
uv sync --dev              # Install dependencies (automatic venv creation)
cp .env.example .env       # Configure environment (uses SQLite by default)
uv run uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000
API documentation at http://localhost:8000/docs

## Demo Credentials

After running the seed script (`uv run python -m app.core.seed`), you can use these test accounts:

### Platform Support (Cross-subscription access)
- **Email**: `support@gymapp.com`
- **Password**: `Support123!`
- **Role**: APPLICATION_SUPPORT

### Test Gym Subscription

**Admin:**
- **Email**: `admin@testgym.com`
- **Password**: `Admin123!`
- **Role**: SUBSCRIPTION_ADMIN

**Coach:**
- **Email**: `coach@testgym.com`
- **Password**: `Coach123!`
- **Role**: COACH

**Client:**
- **Email**: `client@testgym.com`
- **Password**: `Client123!`
- **Role**: CLIENT

**Client:**
- **Email**: `j.ksknt@gmail.com`
- **Password**: `Test123!`
- **Role**: CLIENT

⚠️ **Important**: These are development credentials only. Change them in production!

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development guidance.

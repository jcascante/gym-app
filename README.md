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

After running the seed script (`uv run python -m app.core.seed`), you can use these test accounts:
### Platform Support (Cross-subscription access)
- **Email**: `support@gymapp.com`
- **Password**: `Support123!`
- **Role**: APPLICATION_SUPPORT
### Test Gym Subscription

**Admin:**
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
- **Role**: CLIENT

⚠️ **Important**: These are development credentials only. Change them in production!
See `DEPLOYMENT.md` for step-by-step deployment instructions and GitHub secrets setup.

## Development


## Deployment & Local Docker

This project includes a multi-stage Dockerfile that builds the frontend and backend
into a single image (frontend served by `nginx`, backend served by `uvicorn`, both
managed by `supervisord`). The container listens on port `8080` (nginx) and proxies
API requests to the backend.

Local build & run (from repo root):

```bash
# Build the image (from repo root)
docker build -t gym-app:latest -f backend/Dockerfile .

# Run it (nginx on 8080)
docker run --rm -p 8080:8080 \
	-e ENVIRONMENT=production \
	-e DATABASE_URL="sqlite:///./gym_app.db" \
	--name gym-app gym-app:latest
```

Verify:

```bash
curl http://localhost:8080/health   # -> {"status":"healthy"}
curl http://localhost:8080/         # -> serves frontend index.html
curl http://localhost:8080/api/v1/  # -> proxied to backend API (adjust prefix)
```

Notes:
- The Docker image bundles frontend build output into `/var/www/frontend`.
- API routes are proxied by nginx from `/api/` (the backend uses `settings.API_V1_STR`;
	ensure that matches your API prefix, commonly `/api/v1`).
- Do NOT use SQLite in production — set `DATABASE_URL` to a managed PostgreSQL instance
	and ensure networking (VPC, security groups) allows App Runner to reach it.

App Runner / Production

- Option A (recommended): push the built image to ECR and create an App Runner
	service that pulls the image. Configure the App Runner service port to `8080` and
	set environment variables (e.g. `DATABASE_URL`) via the console or Secrets Manager.

- Option B (source-based build): configure App Runner to build from the repository
	(path `backend/`). If you choose source-based builds, set the build and start
	commands in App Runner to match the `apprunner.yaml` or the commands below:

	Build commands:
	```bash
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt
	npx vite build
	```

	Start command:
	```bash
	uvicorn app.main:app --host 0.0.0.0 --port 8000
	```

- If you use App Runner source builds, you will need to either serve the frontend
  from the Python app (mount `dist`) or rely on a build pipeline to produce a
  container image — the repository currently contains a container-focused setup.

CI / ECR pipeline (recommended)

- Create a GitHub Actions workflow (or other CI) that:
  - builds the Docker image (`docker build -f backend/Dockerfile .`),
  - pushes it to ECR,
  - updates App Runner or creates a new deployment.

If you want, I can add a ready-to-use GitHub Actions workflow that builds the image,
pushes to ECR, and triggers an App Runner deployment.

## GitHub Actions CI/CD — Secrets & Variables Setup

The repository includes `.github/workflows/ci-ecr-apprunner.yml` which automatically:
1. Builds the Docker image (from `backend/Dockerfile`).
2. Pushes it to Amazon ECR.
3. (Optional) Triggers an App Runner service update with the new image.

Before the workflow can run, you must configure GitHub repository secrets and variables.

### Required GitHub Secrets

Store these securely in: **Repository → Settings → Secrets and variables → Actions → Secrets**

- `AWS_ACCESS_KEY_ID` — IAM user access key (permissions: ECR push, AppRunner update)
- `AWS_SECRET_ACCESS_KEY` — IAM user secret key
- `APP_RUNNER_SERVICE_ARN` (optional) — App Runner service ARN for automatic deployment

### Required GitHub Variables

Store these in: **Repository → Settings → Secrets and variables → Actions → Variables**

- `AWS_REGION` — e.g., `us-east-1`
- `AWS_ACCOUNT_ID` — Your AWS account ID (numeric)
- `ECR_REPOSITORY` — ECR repository name, e.g., `gym-app-backend`

### Quick Setup with GitHub CLI

If you have `gh` CLI installed, run (from repo root):

```bash
# Create secrets (replace values)
gh secret set AWS_ACCESS_KEY_ID --body 'AKIA...'
gh secret set AWS_SECRET_ACCESS_KEY --body 'wJalrXUtnFEMI...'
gh secret set APP_RUNNER_SERVICE_ARN --body 'arn:aws:apprunner:region:account:service/name/id'  # optional

# Create variables
gh variable set AWS_REGION --value 'us-east-1'
gh variable set AWS_ACCOUNT_ID --value '123456789012'
gh variable set ECR_REPOSITORY --value 'gym-app-backend'
```

### IAM Permissions

The IAM user needs permissions to:
- **ECR**: `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, `ecr:GetDownloadUrlForLayer`, `ecr:PutImage`, `ecr:InitiateLayerUpload`, `ecr:UploadLayerPart`, `ecr:CompleteLayerUpload`
- **App Runner** (if using auto-deploy): `apprunner:UpdateService`

Simplest approach: attach AWS managed policy `AmazonEC2ContainerRegistryPowerUser` to the IAM user, plus `AppRunnerFullAccess` if auto-deploying.

### Workflow Behavior

On push to `main`:
1. Docker image is built and tagged with both `:latest` and `:<commit-sha>`.
2. Image is pushed to ECR.
3. If `APP_RUNNER_SERVICE_ARN` is set, the workflow automatically updates the App Runner service with the new image (port 8080).

Monitor workflow runs in **Actions** tab of your GitHub repository.
#!/usr/bin/env bash
set -euo pipefail

# Usage:
# 1) Ensure Terraform has been applied in terraform/bootstrap so outputs exist
#    cd terraform/bootstrap && terraform apply
# 2) Install and authenticate GitHub CLI: `gh auth login`
# 3) Run this script from repo root: `./scripts/setup_github_secrets.sh`

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT/terraform/bootstrap"

# Check dependencies
if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform not found in PATH; install terraform and run this script after 'terraform apply'" >&2
  exit 1
fi
if ! command -v gh >/dev/null 2>&1; then
  echo "gh (GitHub CLI) not found in PATH; install it and run 'gh auth login' first" >&2
  exit 1
fi

echo "Reading Terraform outputs..."
ACCESS_KEY_ID=$(terraform output -raw gym_app_ci_access_key_id || true)
SECRET_ACCESS_KEY=$(terraform output -raw gym_app_ci_secret_access_key || true)
ACCOUNT_ID=$(terraform output -raw account_id || true)
REGION=$(terraform output -raw region || true)

if [ -z "${ACCESS_KEY_ID:-}" ] || [ -z "${SECRET_ACCESS_KEY:-}" ]; then
  echo "Terraform outputs for IAM not found. Ensure you've applied terraform in terraform/bootstrap and that the IAM module was created." >&2
  terraform output || true
  exit 1
fi

# Determine ECR repo name from Terraform outputs (if available)
BACKEND_ECR_URL=$(terraform output -raw backend_ecr_url 2>/dev/null || true)
if [ -n "${BACKEND_ECR_URL}" ]; then
  # Extract repo name from full ECR URL (e.g. 123456789012.dkr.ecr.us-east-1.amazonaws.com/gym-app-backend)
  ECR_REPO=$(basename "$BACKEND_ECR_URL")
else
  # Fallback: reasonable default; change if your repo name differs
  ECR_REPO="gym-app-backend"
fi

# Back to repo root for gh operations
cd "$REPO_ROOT"

echo "Setting GitHub secrets and variables for repository: $(git rev-parse --show-toplevel 2>/dev/null || echo $REPO_ROOT)"

# Secrets (sensitive)
echo "Creating secrets..."
gh secret set AWS_ACCESS_KEY_ID --body "$ACCESS_KEY_ID"
gh secret set AWS_SECRET_ACCESS_KEY --body "$SECRET_ACCESS_KEY"

# Optional: use env var APP_RUNNER_SERVICE_ARN if you want to set it via the environment
if [ -n "${APP_RUNNER_SERVICE_ARN:-}" ]; then
  echo "Setting APP_RUNNER_SERVICE_ARN from environment"
  gh secret set APP_RUNNER_SERVICE_ARN --body "$APP_RUNNER_SERVICE_ARN"
fi

# Non-sensitive variables
echo "Creating repository variables (non-sensitive)..."
gh variable set AWS_REGION --value "$REGION"
gh variable set AWS_ACCOUNT_ID --value "$ACCOUNT_ID"
gh variable set ECR_REPOSITORY --value "$ECR_REPO"

echo "All done."

echo "Verify in GitHub: Settings → Secrets and variables → Actions"

echo "You may now push to main to trigger CI or run the workflow manually."

**Deployment & GitHub Secrets Setup**

This file documents the minimal steps to run the `scripts/setup_github_secrets.sh` script that takes Terraform outputs from `terraform/bootstrap` and sets GitHub repository Secrets and Variables using the `gh` CLI.

- **Prerequisites**:
  - `terraform` installed and `terraform apply` already run in `terraform/bootstrap` (so outputs exist).
  - `gh` (GitHub CLI) installed and authenticated with an account that has repo admin permissions for this repository.
  - `jq` (optional) for inspecting JSON terraform outputs locally.
  - `git` remote `origin` pointing to the GitHub repo where you want to set secrets/variables.

- **Typical workflow (macOS / zsh)**:

  1. Apply Terraform in the bootstrap folder to create the CI IAM user and outputs:

```bash
cd terraform/bootstrap
terraform init
terraform apply -auto-approve
```

  2. Verify outputs (optional):

```bash
terraform output -json | jq .
# or inspect individual values
terraform output -raw gym_app_ci_access_key_id
```

  3. Install and authenticate `gh` (if you don't have it):

```bash
# install via Homebrew
brew install gh
# authenticate (interactive)
gh auth login
```

  4. Run the setup script from the repository root (it reads terraform outputs and sets secrets/variables):

```bash
cd /path/to/gym-app
chmod +x scripts/setup_github_secrets.sh
./scripts/setup_github_secrets.sh
```

  5. After the script runs, push a commit to `main` (or open a PR) to trigger the CI workflow which will build and push the Docker image to ECR.

- **Notes & troubleshooting**:
  - If `gh` complains about permissions, ensure the authenticated GitHub user has `repo` and `admin:org` (if org-level) access required to set repo secrets/variables.
  - If `terraform output` doesn't show the expected keys, re-run `terraform apply` in `terraform/bootstrap` and re-check outputs.
  - The script expects the Terraform outputs produced by `terraform/bootstrap` (e.g. `gym_app_ci_access_key_id`, `gym_app_ci_secret_access_key`). If you changed output names, edit the script accordingly.
  - Secrets set by the script include: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and (optionally) `APP_RUNNER_SERVICE_ARN`. Non-sensitive values are stored as GitHub Repository Variables: `AWS_REGION`, `AWS_ACCOUNT_ID`, `ECR_REPOSITORY`.

- **Security Configuration** (Generate SECRET_KEY):

  Before deploying to production, generate a secure SECRET_KEY for JWT authentication:

```bash
cd backend
python3 tools/generate_secret_key.py --format env

# Copy the output and add it to your terraform/terraform.tfvars file:
# environment_variables = {
#   SECRET_KEY = "your-generated-key-here"
# }
```

  **Why is this needed?** The SECRET_KEY is used to sign and verify JWT authentication tokens. Using the default key from the code is insecure for production environments.

  **Tool options**:
```bash
# Generate a key (default 32 bytes)
python3 tools/generate_secret_key.py

# Generate for .env file
python3 tools/generate_secret_key.py --format env

# Generate for Terraform
python3 tools/generate_secret_key.py --format terraform

# Generate multiple keys (for dev, staging, prod)
python3 tools/generate_secret_key.py --multiple 3
```

  See `backend/tools/README.md` for more details.

- **Next steps**:
  - After secrets and variables are set, push to `main` to run the `.github/workflows/ci-ecr-apprunner.yml` workflow, which will build and push the image to ECR and optionally update App Runner.
  - For App Runner SQLite testing, ensure the image is run with `ENVIRONMENT=development` and `DATABASE_URL=sqlite+aiosqlite:///./gym_app.db` and set App Runner instance scaling to a single instance (min=max=1).

If you'd like, I can also add a short snippet into `README.md` pointing to this `DEPLOYMENT.md`.
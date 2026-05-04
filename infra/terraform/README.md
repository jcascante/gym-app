# Terraform Infrastructure

This directory contains Terraform configurations for deploying the Gym App to AWS using App Runner.

## Directory Structure

```
terraform/
├── bootstrap/              # Bootstrap infrastructure (one-time setup)
│   ├── modules/
│   │   ├── ecr/           # ECR repositories
│   │   ├── iam/           # IAM users for CI/CD
│   │   └── vpc/           # VPC (optional, currently disabled)
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── modules/
│   └── app_runner/        # App Runner service module
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── main.tf                # Application infrastructure
├── variables.tf
├── outputs.tf
└── terraform.tfvars.example
```

## Prerequisites

1. **AWS Account**: You need an AWS account with appropriate permissions
2. **AWS CLI**: Install and configure AWS CLI with your credentials
   ```bash
   aws configure
   ```
3. **Terraform**: Install Terraform >= 1.0
   ```bash
   # macOS
   brew install terraform

   # Or download from https://www.terraform.io/downloads
   ```
4. **Docker**: Required for building and pushing images to ECR

## Deployment Steps

### Step 1: Bootstrap Infrastructure (One-Time Setup)

The bootstrap infrastructure creates foundational resources that other environments depend on:
- ECR repository for Docker images
- IAM user for GitHub Actions CI/CD
- S3 bucket and DynamoDB table for Terraform state (already exists)

```bash
cd terraform/bootstrap

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply

# Save the outputs (especially IAM credentials for GitHub Actions)
terraform output
```

**Important**: Save the `gym_app_ci_access_key_id` and `gym_app_ci_secret_access_key` outputs. You'll need these for GitHub Actions.

### Step 2: Build and Push Docker Image

Before deploying the App Runner service, you need to build and push a Docker image to ECR:

```bash
# Get ECR repository URL from bootstrap outputs
cd terraform/bootstrap
export ECR_REPO=$(terraform output -raw backend_ecr_url)
export AWS_REGION=$(terraform output -raw region)

# Navigate to project root
cd ../..

# Build the Docker image (builds both frontend and backend)
docker build -t ${ECR_REPO}:latest -f backend/Dockerfile .

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REPO}

# Push the image
docker push ${ECR_REPO}:latest

# Optional: Tag and push with version
# docker tag ${ECR_REPO}:latest ${ECR_REPO}:v1.0.0
# docker push ${ECR_REPO}:v1.0.0
```

### Step 3: Generate SECRET_KEY (Required for Production)

Before deploying, generate a secure SECRET_KEY for JWT authentication:

```bash
cd backend

# Generate a secure random key
python3 tools/generate_secret_key.py --format terraform

# Copy the output and add it to terraform/terraform.tfvars:
# environment_variables = {
#   SECRET_KEY = "your-generated-key-here"
# }
```

**Important**: The SECRET_KEY is used to sign and verify JWT tokens. Using the default key from the code is insecure for production. See `backend/tools/README.md` for more options.

### Step 4: Deploy App Runner Service

```bash
cd terraform

# Copy and customize the variables file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your desired configuration
# IMPORTANT: Add the SECRET_KEY you generated in Step 3

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply

# Get the service URL
terraform output app_runner_service_url
```

Your application should now be accessible at the App Runner service URL!

## Configuration

### Environment Variables

The application supports the following environment variables (configured in `terraform.tfvars`):

- `ENVIRONMENT`: Environment name (development, production)
- `DATABASE_URL`: Database connection URL
  - Development: `sqlite+aiosqlite:///./gym_app.db`
  - Production: Use AWS RDS PostgreSQL
- `RESET_DB_ON_START`: Reset database on container start (development only)
- `SECRET_KEY`: Secret key for JWT tokens (use AWS Secrets Manager in production)
- `CORS_ORIGINS`: Allowed CORS origins

### Instance Sizing

App Runner supports the following CPU and memory combinations:

| CPU (vCPU) | Memory Options (MB) |
|------------|---------------------|
| 256 (0.25) | 512, 1024           |
| 512 (0.5)  | 1024, 2048          |
| 1024 (1)   | 2048, 3072, 4096    |
| 2048 (2)   | 4096, 6144, 8192    |
| 4096 (4)   | 6144 to 12288       |

Default configuration: 1 vCPU (1024) + 2 GB memory (2048)

### Auto Scaling

Configure auto scaling in `terraform.tfvars`:

```hcl
min_instances   = 1    # Minimum instances
max_instances   = 10   # Maximum instances
max_concurrency = 100  # Requests per instance
```

App Runner automatically scales between min and max instances based on traffic.

## Managing Deployments

### Update Application Code

When `auto_deployments_enabled = true`, App Runner automatically deploys when you push a new image:

```bash
# Build and push new image
docker build -t ${ECR_REPO}:latest -f backend/Dockerfile .
docker push ${ECR_REPO}:latest

# App Runner automatically detects and deploys the new image
```

### Update Infrastructure

To update infrastructure configuration (CPU, memory, environment variables, etc.):

```bash
cd terraform

# Edit terraform.tfvars with your changes
vim terraform.tfvars

# Review changes
terraform plan

# Apply changes
terraform apply
```

### Rollback to Previous Version

To rollback to a previous image version:

```bash
cd terraform

# Update terraform.tfvars to use a specific tag
# image_tag = "v1.0.0"

terraform apply
```

## Monitoring and Logs

App Runner automatically sends logs to CloudWatch Logs. To view logs:

```bash
# Get service name
SERVICE_NAME=$(cd terraform && terraform output -raw app_runner_service_id)

# View logs in AWS Console
echo "https://console.aws.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#logsV2:log-groups/log-group//aws/apprunner/${SERVICE_NAME}"

# Or use AWS CLI
aws logs tail /aws/apprunner/${SERVICE_NAME} --follow
```

## Cost Optimization

App Runner pricing is based on:
1. **Compute**: Charged per vCPU-hour and GB-hour when instances are running
2. **Memory**: Charged per GB-hour
3. **Requests**: $0.40 per million requests

Tips for cost optimization:
- Set appropriate `min_instances` (1 for development, higher for production)
- Use smaller instance sizes if possible (e.g., 512 MB instead of 2 GB)
- Enable auto scaling to scale down during low traffic

## Production Considerations

### Database

**Important**: SQLite is NOT recommended for production. Use AWS RDS PostgreSQL:

1. Create an RDS PostgreSQL instance
2. Update `database_url` in `terraform.tfvars`:
   ```hcl
   database_url = "postgresql+asyncpg://username:password@your-rds-endpoint:5432/gym_app"
   ```
3. Set `reset_db_on_start = "false"`

### Secrets Management

For production, use AWS Secrets Manager or Parameter Store for sensitive values:

1. Store secrets in AWS Secrets Manager
2. Grant the App Runner instance role permission to read secrets
3. Update the application to read from Secrets Manager

### Custom Domain

To use a custom domain with App Runner:

1. In AWS Console, go to App Runner service
2. Click "Custom domains"
3. Add your domain and follow DNS configuration steps

### Security

- Never commit `terraform.tfvars` with production credentials
- Use AWS Secrets Manager for `SECRET_KEY` and other sensitive values
- Enable VPC connector if you need to access private resources (VPC, RDS)
- Review IAM roles and apply least privilege principle

## Troubleshooting

### Service fails to start

1. Check CloudWatch Logs for errors
2. Verify ECR image exists and is accessible
3. Check environment variables are correct
4. Verify IAM roles have correct permissions

### Health check failures

1. Verify health check path is accessible (`/` by default)
2. Check application logs in CloudWatch
3. Ensure the application is listening on port 80
4. Increase `health_check_timeout` if needed

### Image pull errors

1. Verify ECR repository permissions
2. Check the access role has `AmazonEC2ContainerRegistryReadOnly` policy
3. Ensure image tag exists in ECR

## Cleanup

To destroy all resources:

```bash
# Destroy application infrastructure
cd terraform
terraform destroy

# Destroy bootstrap infrastructure (WARNING: This deletes ECR repositories and images)
cd terraform/bootstrap
terraform destroy
```

**Warning**: Destroying bootstrap infrastructure will delete ECR repositories and all images. Make sure you have backups if needed.

## Additional Resources

- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [App Runner Pricing](https://aws.amazon.com/apprunner/pricing/)

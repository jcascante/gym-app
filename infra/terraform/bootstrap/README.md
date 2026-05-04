# Bootstrap - Account Setup

This directory contains Terraform configuration for one-time account-level setup. Run this **once** before deploying the application.

## What Gets Created

1. **Terraform State Backend**
   - S3 bucket for storing Terraform state
   - DynamoDB table for state locking
   - Versioning and encryption enabled

2. **ECR Repositories**
   - Container registries for Docker images
   - Lifecycle policies for image cleanup

3. **IAM Roles**
   - App Runner service roles
   - Common IAM policies

## Initial Setup

### 1. First Time Bootstrap

```bash
cd terraform/bootstrap

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your settings (optional, defaults work)
vim terraform.tfvars

# Initialize Terraform (local state for first run)
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

### 2. Migrate to Remote State (After First Apply)

After the initial `terraform apply` creates the S3 bucket and DynamoDB table:

1. Uncomment the `backend "s3"` block in `main.tf`
2. Update the bucket name if you changed the default
3. Run: `terraform init -migrate-state`
4. Confirm the migration when prompted

This moves your state from local to S3, enabling team collaboration and state locking.

## What's Next

After bootstrap is complete:
1. Note the ECR repository URLs from the output
2. Build and push your Docker images to ECR
3. Proceed to `terraform/app/` to deploy the application infrastructure

## Outputs

The bootstrap will output:
- S3 bucket name for Terraform state
- ECR repository URLs for pushing Docker images
- IAM role ARNs for App Runner

## Updating Bootstrap

To add new ECR repositories or update IAM roles:
```bash
# Edit terraform.tfvars or module configurations
# Then apply changes
terraform plan
terraform apply
```

## Destroying Bootstrap Resources

**Warning**: Only destroy bootstrap resources when completely decommissioning the project.

```bash
terraform destroy
```

This will delete:
- All container images in ECR
- Terraform state (make sure you have backups!)
- IAM roles

Make sure to destroy the application infrastructure (`terraform/app/`) first.

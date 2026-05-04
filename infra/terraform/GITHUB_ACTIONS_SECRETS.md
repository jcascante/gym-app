# GitHub Actions deployment variables and secrets for Gym App

# Set these in your GitHub repository settings:

## Secrets
AWS_DEPLOY_ROLE_ARN = <IAM role ARN for OIDC-based deploys>

## Repository Variables
ECS_CLUSTER_NAME = gym-app-production-cluster
ECS_SERVICE_NAME = gym-app-production-backend
LAMBDA_FUNCTION_NAME = gym-app-production-program-builder

# To get the exact values, run:
#   terraform output backend_ecs_cluster
#   terraform output backend_ecs_service
#   terraform output program_builder_function_name

# The IAM role for AWS_DEPLOY_ROLE_ARN should be created manually or via IaC with trust for GitHub OIDC provider.

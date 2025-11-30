# # VPC Outputs
# output "vpc_id" {
#   description = "ID of the VPC"
#   value       = module.vpc.vpc_id
# }

# output "private_subnet_ids" {
#   description = "IDs of private subnets"
#   value       = module.vpc.private_subnet_ids
# }

# output "vpc_endpoints_security_group_id" {
#   description = "ID of the security group for VPC endpoints"
#   value       = module.vpc.vpc_endpoints_security_group_id
# }

# ECR Outputs
output "ecr_repository_urls" {
  description = "URLs of the ECR repositories"
  value       = module.ecr.repository_urls
}

output "backend_ecr_url" {
  description = "ECR repository URL for backend"
  value       = module.ecr.repository_urls["backend"]
}

# General Info
output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}

# IAM Outputs (GitHub Actions CI/CD)
output "gym_app_ci_access_key_id" {
  description = "AWS Access Key ID for GitHub Actions (store in AWS_ACCESS_KEY_ID secret)"
  value       = module.iam.gym_app_ci_access_key_id
  sensitive   = false
}

output "gym_app_ci_secret_access_key" {
  description = "AWS Secret Access Key for GitHub Actions (store in AWS_SECRET_ACCESS_KEY secret)"
  value       = module.iam.gym_app_ci_secret_access_key
  sensitive   = true
}

output "gym_app_ci_user_arn" {
  description = "ARN of the gym-app-ci IAM user"
  value       = module.iam.gym_app_ci_user_arn
}

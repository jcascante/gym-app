# Application Infrastructure Outputs

# General Info
output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}

# ECR Repository
output "ecr_repository_url" {
  description = "ECR repository URL for the backend image"
  value       = data.aws_ecr_repository.backend.repository_url
}

# App Runner Service
output "app_runner_service_id" {
  description = "ID of the App Runner service"
  value       = module.app_runner.service_id
}

output "app_runner_service_arn" {
  description = "ARN of the App Runner service"
  value       = module.app_runner.service_arn
}

output "app_runner_service_url" {
  description = "URL of the App Runner service"
  value       = "https://${module.app_runner.service_url}"
}

output "app_runner_service_status" {
  description = "Current status of the App Runner service"
  value       = module.app_runner.service_status
}

output "app_runner_instance_role_arn" {
  description = "ARN of the App Runner instance IAM role"
  value       = module.app_runner.instance_role_arn
}

output "app_runner_access_role_arn" {
  description = "ARN of the App Runner access IAM role"
  value       = module.app_runner.access_role_arn
}

# Deployment Info
output "deployment_instructions" {
  description = "Instructions for deploying the application"
  value = <<-EOT

    To deploy the application:

    1. Build and push the Docker image:
       cd backend
       docker build -t ${data.aws_ecr_repository.backend.repository_url}:${var.image_tag} -f Dockerfile ..
       aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${data.aws_ecr_repository.backend.repository_url}
       docker push ${data.aws_ecr_repository.backend.repository_url}:${var.image_tag}

    2. The App Runner service will automatically deploy the new image (if auto_deployments_enabled = true)

    3. Access your application at: https://${module.app_runner.service_url}

    4. Monitor logs in CloudWatch Logs

  EOT
}

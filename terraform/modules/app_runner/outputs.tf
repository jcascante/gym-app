# App Runner Service Outputs

output "service_id" {
  description = "ID of the App Runner service"
  value       = aws_apprunner_service.this.service_id
}

output "service_arn" {
  description = "ARN of the App Runner service"
  value       = aws_apprunner_service.this.arn
}

output "service_url" {
  description = "URL of the App Runner service"
  value       = aws_apprunner_service.this.service_url
}

output "service_status" {
  description = "Status of the App Runner service"
  value       = aws_apprunner_service.this.status
}

output "instance_role_arn" {
  description = "ARN of the App Runner instance IAM role"
  value       = aws_iam_role.apprunner_instance_role.arn
}

output "access_role_arn" {
  description = "ARN of the App Runner access IAM role"
  value       = aws_iam_role.apprunner_access_role.arn
}

output "auto_scaling_configuration_arn" {
  description = "ARN of the App Runner auto scaling configuration"
  value       = aws_apprunner_auto_scaling_configuration_version.this.arn
}

# Output the access key and secret for GitHub secrets setup
output "gym_app_ci_access_key_id" {
  description = "AWS Access Key ID for GitHub Actions (store in AWS_ACCESS_KEY_ID secret)"
  value       = aws_iam_access_key.gym_app_ci.id
  sensitive   = false
}

output "gym_app_ci_secret_access_key" {
  description = "AWS Secret Access Key for GitHub Actions (store in AWS_SECRET_ACCESS_KEY secret)"
  value       = aws_iam_access_key.gym_app_ci.secret
  sensitive   = true
}

output "gym_app_ci_user_arn" {
  description = "ARN of the gym-app-ci IAM user"
  value       = aws_iam_user.gym_app_ci.arn
}

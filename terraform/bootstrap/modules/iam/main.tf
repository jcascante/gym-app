# IAM user for GitHub Actions CI/CD pipeline
# Permissions: ECR push, App Runner update

resource "aws_iam_user" "gym_app_ci" {
  name = "gym-app-ci"

  tags = {
    Name        = "gym-app-ci"
    Environment = "production"
    Purpose     = "GitHub Actions CI/CD"
  }
}

# Access key for the IAM user (used in GitHub Actions secrets)
resource "aws_iam_access_key" "gym_app_ci" {
  user = aws_iam_user.gym_app_ci.name
}

# Attach ECR push policy
resource "aws_iam_user_policy_attachment" "gym_app_ci_ecr" {
  user       = aws_iam_user.gym_app_ci.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
}

# Attach App Runner update policy (optional, for auto-deployment)
resource "aws_iam_user_policy_attachment" "gym_app_ci_apprunner" {
  user       = aws_iam_user.gym_app_ci.name
  policy_arn = "arn:aws:iam::aws:policy/AWSAppRunnerFullAccess"
                
}

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

# Lambda and S3 policy for program-builder deployment
resource "aws_iam_user_policy" "gym_app_ci_lambda_s3" {
  name = "gym-app-ci-lambda-s3"
  user = aws_iam_user.gym_app_ci.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::691650344087-terraform-state",
          "arn:aws:s3:::691650344087-terraform-state/gym-app/lambda/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:UpdateFunctionCode",
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration"
        ]
        Resource = "arn:aws:lambda:*:*:function:*"
      }
    ]
  })
}

# Frontend S3 and CloudFront policy for frontend deployment
resource "aws_iam_user_policy" "gym_app_ci_frontend" {
  name = "gym-app-ci-frontend"
  user = aws_iam_user.gym_app_ci.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::app.costabirra.com",
          "arn:aws:s3:::app.costabirra.com/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation"
        ]
        Resource = "arn:aws:cloudfront::*:distribution/*"
      }
    ]
  })
}

# ECS deployment policy for backend service updates
resource "aws_iam_user_policy" "gym_app_ci_ecs" {
  name = "gym-app-ci-ecs"
  user = aws_iam_user.gym_app_ci.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices"
        ]
        Resource = "arn:aws:ecs:*:*:service/*"
      }
    ]
  })
}

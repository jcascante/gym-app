# AWS App Runner Service Module

# IAM Role for App Runner Instance (runtime permissions)
resource "aws_iam_role" "apprunner_instance_role" {
  name = "${var.service_name}-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.service_name}-instance-role"
    Environment = var.environment
  }
}

# Attach policies for instance role (e.g., CloudWatch, Secrets Manager if needed)
resource "aws_iam_role_policy_attachment" "apprunner_instance_cloudwatch" {
  role       = aws_iam_role.apprunner_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# IAM Role for App Runner to access ECR (build/deployment permissions)
resource "aws_iam_role" "apprunner_access_role" {
  name = "${var.service_name}-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.service_name}-access-role"
    Environment = var.environment
  }
}

# Attach ECR read policy to access role
resource "aws_iam_role_policy_attachment" "apprunner_access_ecr" {
  role       = aws_iam_role.apprunner_access_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# App Runner Auto Scaling Configuration
resource "aws_apprunner_auto_scaling_configuration_version" "this" {
  auto_scaling_configuration_name = "${var.service_name}-autoscaling"

  max_concurrency = var.max_concurrency
  max_size        = var.max_size
  min_size        = var.min_size

  tags = {
    Name        = "${var.service_name}-autoscaling"
    Environment = var.environment
  }
}

# App Runner Service
resource "aws_apprunner_service" "this" {
  service_name = var.service_name

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access_role.arn
    }

    image_repository {
      image_identifier      = var.image_identifier
      image_repository_type = "ECR"

      image_configuration {
        port = var.port

        runtime_environment_variables = var.environment_variables

        # Optional: start command override
        # start_command = var.start_command
      }
    }

    auto_deployments_enabled = var.auto_deployments_enabled
  }

  instance_configuration {
    cpu               = var.cpu
    memory            = var.memory
    instance_role_arn = aws_iam_role.apprunner_instance_role.arn
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.this.arn

  health_check_configuration {
    protocol            = var.health_check_protocol
    path                = var.health_check_path
    interval            = var.health_check_interval
    timeout             = var.health_check_timeout
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
  }

  # Optional: Network configuration for VPC connector
  # network_configuration {
  #   egress_configuration {
  #     egress_type       = "VPC"
  #     vpc_connector_arn = var.vpc_connector_arn
  #   }
  # }

  tags = {
    Name        = var.service_name
    Environment = var.environment
  }
}

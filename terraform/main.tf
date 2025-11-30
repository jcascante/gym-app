terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for storing Terraform state
  # Update the bucket name and region to match your setup
  backend "s3" {
    bucket         = "691650344087-terraform-state"
    key            = "gym-app/application/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "691650344087-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Get ECR repository URL from bootstrap outputs
# You can either use a data source or pass it as a variable
data "aws_ecr_repository" "backend" {
  name = "ksknt-backend"
}

# App Runner Service
module "app_runner" {
  source = "./modules/app_runner"

  service_name = "${var.project_name}-${var.environment}"
  environment  = var.environment

  # ECR image identifier
  # Format: <repository_url>:<tag>
  # For initial deployment, you'll need to build and push an image first
  image_identifier = "${data.aws_ecr_repository.backend.repository_url}:${var.image_tag}"

  # Port exposed by the Docker container (from Dockerfile EXPOSE 80)
  port = var.app_port

  # Instance configuration
  cpu    = var.cpu
  memory = var.memory

  # Auto scaling configuration
  min_size        = var.min_instances
  max_size        = var.max_instances
  max_concurrency = var.max_concurrency

  # Enable auto deployments when new images are pushed to ECR
  auto_deployments_enabled = var.auto_deployments_enabled

  # Environment variables for the application
  environment_variables = merge(
    var.environment_variables,
    {
      ENVIRONMENT      = var.environment
      DATABASE_URL     = var.database_url
      RESET_DB_ON_START = var.reset_db_on_start
    }
  )

  # Health check configuration
  health_check_protocol            = var.health_check_protocol
  health_check_path                = var.health_check_path
  health_check_interval            = var.health_check_interval
  health_check_timeout             = var.health_check_timeout
  health_check_healthy_threshold   = var.health_check_healthy_threshold
  health_check_unhealthy_threshold = var.health_check_unhealthy_threshold
}

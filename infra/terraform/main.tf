terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }

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

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Reuse existing state bucket for Lambda deployment packages (prefix: gym-app/lambda/)
data "aws_s3_bucket" "state" {
  bucket = "691650344087-terraform-state"
}

data "aws_ecr_repository" "backend" {
  name = "gym-app-backend"
}

# ── Networking — existing default VPC (reused, not managed here) ─────────────

data "aws_vpc" "main" {
  id = "vpc-0b7eec76"
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

# ── IAM ─────────────────────────────────────────────────────────────────────

module "iam" {
  source = "./modules/iam"

  project_name         = var.project_name
  environment          = var.environment
  lambda_function_name = "gym-app-production-program-builder"
}

# ── Frontend — existing resources (reused, not managed here) ─────────────────

data "aws_s3_bucket" "frontend" {
  bucket = "app.movementtrainingclub.com"
}

# ACM cert already attached: arn:aws:acm:us-east-1:691650344087:certificate/9ba09513-c68c-40a7-af6f-68cc42f4d10c
data "aws_cloudfront_distribution" "frontend" {
  id = "E15DPRRJ6MVP5X"
}

data "aws_route53_zone" "frontend" {
  name = "movementtrainingclub.com."
}

# ── Route53: api.movementtrainingclub.com → backend ALB ─────────────
resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.frontend.zone_id
  name    = "api.movementtrainingclub.com"
  type    = "A"
  alias {
    name                   = module.backend_ecs.alb_dns_name
    zone_id                = module.backend_ecs.alb_zone_id
    evaluate_target_health = true
  }
}

# ── Lambda placeholder package ───────────────────────────────────────────────
# Uploaded once to the existing state bucket under gym-app/lambda/.
# CI/CD overwrites with the real package on every program-builder deploy.

data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/.placeholder.zip"

  source {
    content  = "def handler(event, context): return {'statusCode': 200, 'body': 'placeholder'}"
    filename = "handler.py"
  }
}

resource "aws_s3_object" "lambda_placeholder" {
  bucket = data.aws_s3_bucket.state.bucket
  key    = "gym-app/lambda/program-builder/placeholder.zip"
  source = data.archive_file.lambda_placeholder.output_path
  etag   = data.archive_file.lambda_placeholder.output_md5

  lifecycle { ignore_changes = [source, etag] }
}

# ── Program Builder Lambda ───────────────────────────────────────────────────

module "lambda_program_builder" {
  source = "./modules/lambda_program_builder"

  project_name       = var.project_name
  environment        = var.environment
  function_name      = "${var.project_name}-${var.environment}-program-builder"
  execution_role_arn = module.iam.lambda_execution_role_arn

  deployment_package_s3_bucket = data.aws_s3_bucket.state.bucket
  deployment_package_s3_key    = aws_s3_object.lambda_placeholder.key

  memory_mb   = 512
  timeout_sec = 30
}

# ── Backend API (ECS Fargate + ALB) ─────────────────────────────────────────

module "backend_ecs" {
  source = "./modules/backend_ecs"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = data.aws_vpc.main.id
  public_subnet_ids = data.aws_subnets.public.ids

  ecr_repository_url = data.aws_ecr_repository.backend.repository_url
  image_tag          = var.image_tag

  cpu           = var.backend_cpu
  memory        = var.backend_memory
  min_tasks     = var.backend_min_tasks
  max_tasks     = var.backend_max_tasks
  desired_tasks = var.backend_min_tasks

  task_execution_role_arn = module.iam.ecs_execution_role_arn
  task_role_arn           = module.iam.ecs_task_role_arn

  acm_certificate_arn = "arn:aws:acm:us-east-1:691650344087:certificate/9ba09513-c68c-40a7-af6f-68cc42f4d10c"

  environment_variables = {
    ENVIRONMENT                 = var.environment
    DATABASE_URL                = var.database_url
    SECRET_KEY                  = var.secret_key
    ENGINE_INVOCATION_MODE      = "lambda"
    ENGINE_LAMBDA_FUNCTION_NAME = module.lambda_program_builder.function_name
    ENGINE_LAMBDA_REGION        = var.aws_region
  }
}

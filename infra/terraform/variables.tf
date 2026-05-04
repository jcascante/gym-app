# General Configuration
variable "aws_region" {
  description = "AWS region for application resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "gym-app"
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
}

# Docker Image Configuration
variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

# Application Configuration
variable "app_port" {
  description = "Port that the application listens on (matches EXPOSE in Dockerfile)"
  type        = string
  default     = "80"
}

# Instance Configuration
variable "cpu" {
  description = "CPU units for the App Runner service (256, 512, 1024, 2048, 4096)"
  type        = string
  default     = "1024"
}

variable "memory" {
  description = "Memory for the App Runner service (512, 1024, 2048, 3072, 4096, 6144, 8192, 10240, 12288)"
  type        = string
  default     = "2048"
}

# Auto Scaling Configuration
variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "max_concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 100
}

variable "auto_deployments_enabled" {
  description = "Enable automatic deployments when new images are pushed to ECR"
  type        = bool
  default     = true
}

# Application Environment Variables
variable "database_url" {
  description = "Database connection URL"
  type        = string
  default     = "sqlite+aiosqlite:///./gym_app.db"
}

variable "reset_db_on_start" {
  description = "Whether to reset the database on container start (development only)"
  type        = string
  default     = "false"
}

variable "environment_variables" {
  description = "Additional environment variables for the application"
  type        = map(string)
  default     = {}
}

# Health Check Configuration
variable "health_check_protocol" {
  description = "Protocol for health check (HTTP or TCP)"
  type        = string
  default     = "HTTP"
}

variable "health_check_path" {
  description = "Path for HTTP health check"
  type        = string
  default     = "/"
}

variable "health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 10
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
}

variable "health_check_healthy_threshold" {
  description = "Number of consecutive successful health checks before marking healthy"
  type        = number
  default     = 1
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive failed health checks before marking unhealthy"
  type        = number
  default     = 5
}

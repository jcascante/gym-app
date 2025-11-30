# App Runner Service Variables

variable "service_name" {
  description = "Name of the App Runner service"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., production, staging, development)"
  type        = string
  default     = "production"
}

variable "image_identifier" {
  description = "ECR image identifier (repository_url:tag)"
  type        = string
}

variable "port" {
  description = "Port that the application listens on"
  type        = string
  default     = "80"
}

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

variable "auto_deployments_enabled" {
  description = "Enable automatic deployments when new images are pushed to ECR"
  type        = bool
  default     = true
}

variable "environment_variables" {
  description = "Environment variables for the application"
  type        = map(string)
  default     = {}
}

# Auto Scaling Configuration
variable "min_size" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "max_concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 100
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
  description = "Number of consecutive successful health checks"
  type        = number
  default     = 1
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive failed health checks"
  type        = number
  default     = 5
}

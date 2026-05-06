variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "gym-app"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "image_tag" {
  description = "Backend Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "backend_cpu" {
  type    = number
  default = 512
}

variable "backend_memory" {
  type    = number
  default = 1024
}

variable "backend_min_tasks" {
  type    = number
  default = 1
}

variable "backend_max_tasks" {
  type    = number
  default = 4
}

variable "database_url" {
  description = "PostgreSQL connection URL for the backend"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}



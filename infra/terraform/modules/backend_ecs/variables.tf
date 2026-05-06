variable "project_name" { type = string }
variable "environment"  { type = string }

variable "vpc_id"            { type = string }
variable "public_subnet_ids" { type = list(string) }

variable "ecr_repository_url" { type = string }

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "cpu" {
  type    = number
  default = 256
}

variable "memory" {
  type    = number
  default = 512
}

variable "min_tasks" {
  type    = number
  default = 1
}

variable "max_tasks" {
  type    = number
  default = 4
}

variable "desired_tasks" {
  type    = number
  default = 1
}

variable "task_execution_role_arn" { type = string }
variable "task_role_arn"           { type = string }

variable "container_port" {
  type    = number
  default = 80
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "acm_certificate_arn" {
  type    = string
  default = "arn:aws:acm:us-east-1:691650344087:certificate/9eed0ca3-3d14-4892-915c-d757b3408b4e"
}

variable "additional_certificate_arns" {
  type    = list(string)
  default = []
}

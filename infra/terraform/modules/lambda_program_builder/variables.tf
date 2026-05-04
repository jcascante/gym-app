variable "project_name"                  { type = string }
variable "environment"                   { type = string }
variable "function_name"                 { type = string }
variable "execution_role_arn"            { type = string }
variable "deployment_package_s3_bucket"  { type = string }
variable "deployment_package_s3_key"     { type = string }

variable "memory_mb" {
  type    = number
  default = 512
}

variable "timeout_sec" {
  type    = number
  default = 30
}

variable "runtime" {
  type    = string
  default = "python3.12"
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

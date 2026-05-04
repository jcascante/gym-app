variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "domain_name" {
  type        = string
  description = "Custom domain (e.g. app.example.com). Leave empty to use the CloudFront default."
  default     = ""
}

variable "acm_certificate_arn" {
  type        = string
  description = "ACM certificate ARN in us-east-1. Required when domain_name is set."
  default     = ""
}

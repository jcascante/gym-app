# # VPC
# resource "aws_vpc" "main" {
#   cidr_block           = var.vpc_cidr
#   enable_dns_hostnames = true
#   enable_dns_support   = true

#   tags = {
#     Name = "${var.project_name}-vpc"
#   }
# }

# # Data source for availability zones
# data "aws_availability_zones" "available" {
#   state = "available"
# }

# # Private Subnets (for Aurora and VPC-connected resources)
# resource "aws_subnet" "private" {
#   count             = var.availability_zones_count
#   vpc_id            = aws_vpc.main.id
#   cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
#   availability_zone = data.aws_availability_zones.available.names[count.index]

#   tags = {
#     Name = "${var.project_name}-private-${data.aws_availability_zones.available.names[count.index]}"
#     Type = "private"
#   }
# }

# # Private Route Table
# resource "aws_route_table" "private" {
#   vpc_id = aws_vpc.main.id

#   tags = {
#     Name = "${var.project_name}-private-rt"
#   }
# }

# # Private Route Table Associations
# resource "aws_route_table_association" "private" {
#   count          = var.availability_zones_count
#   subnet_id      = aws_subnet.private[count.index].id
#   route_table_id = aws_route_table.private.id
# }

# # Security Group for VPC Endpoints
# resource "aws_security_group" "vpc_endpoints" {
#   name        = "${var.project_name}-vpc-endpoints-sg"
#   description = "Security group for VPC endpoints"
#   vpc_id      = aws_vpc.main.id

#   ingress {
#     description = "HTTPS from VPC"
#     from_port   = 443
#     to_port     = 443
#     protocol    = "tcp"
#     cidr_blocks = [var.vpc_cidr]
#   }

#   egress {
#     description = "Allow all outbound"
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   tags = {
#     Name = "${var.project_name}-vpc-endpoints-sg"
#   }
# }

# # VPC Endpoint: S3 (Gateway Endpoint - Free)
# resource "aws_vpc_endpoint" "s3" {
#   vpc_id          = aws_vpc.main.id
#   service_name    = "com.amazonaws.${var.aws_region}.s3"
#   route_table_ids = [aws_route_table.private.id]

#   tags = {
#     Name = "${var.project_name}-s3-endpoint"
#   }
# }

# # VPC Endpoint: RDS Data API (for Aurora Serverless Data API access)
# resource "aws_vpc_endpoint" "rds_data" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.rds-data"
#   vpc_endpoint_type   = "Interface"
#   subnet_ids          = aws_subnet.private[*].id
#   security_group_ids  = [aws_security_group.vpc_endpoints.id]
#   private_dns_enabled = true

#   tags = {
#     Name = "${var.project_name}-rds-data-endpoint"
#   }
# }

# # VPC Endpoint: Secrets Manager (for database credentials)
# resource "aws_vpc_endpoint" "secretsmanager" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
#   vpc_endpoint_type   = "Interface"
#   subnet_ids          = aws_subnet.private[*].id
#   security_group_ids  = [aws_security_group.vpc_endpoints.id]
#   private_dns_enabled = true

#   tags = {
#     Name = "${var.project_name}-secretsmanager-endpoint"
#   }
# }

# # VPC Endpoint: ECR API (for pulling Docker images)
# resource "aws_vpc_endpoint" "ecr_api" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
#   vpc_endpoint_type   = "Interface"
#   subnet_ids          = aws_subnet.private[*].id
#   security_group_ids  = [aws_security_group.vpc_endpoints.id]
#   private_dns_enabled = true

#   tags = {
#     Name = "${var.project_name}-ecr-api-endpoint"
#   }
# }

# # VPC Endpoint: ECR Docker (for pulling Docker images)
# resource "aws_vpc_endpoint" "ecr_dkr" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
#   vpc_endpoint_type   = "Interface"
#   subnet_ids          = aws_subnet.private[*].id
#   security_group_ids  = [aws_security_group.vpc_endpoints.id]
#   private_dns_enabled = true

#   tags = {
#     Name = "${var.project_name}-ecr-dkr-endpoint"
#   }
# }

# # VPC Endpoint: CloudWatch Logs
# resource "aws_vpc_endpoint" "logs" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.logs"
#   vpc_endpoint_type   = "Interface"
#   subnet_ids          = aws_subnet.private[*].id
#   security_group_ids  = [aws_security_group.vpc_endpoints.id]
#   private_dns_enabled = true

#   tags = {
#     Name = "${var.project_name}-logs-endpoint"
#   }
# }

# # VPC Endpoint: STS (for IAM role assumption)
# resource "aws_vpc_endpoint" "sts" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.sts"
#   vpc_endpoint_type   = "Interface"
#   subnet_ids          = aws_subnet.private[*].id
#   security_group_ids  = [aws_security_group.vpc_endpoints.id]
#   private_dns_enabled = true

#   tags = {
#     Name = "${var.project_name}-sts-endpoint"
#   }
# }

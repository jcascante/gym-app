output "alb_dns_name" {
  value = aws_lb.backend.dns_name
}

output "alb_zone_id" {
  value = aws_lb.backend.zone_id
}

output "alb_arn" {
  value = aws_lb.backend.arn
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.backend.name
}

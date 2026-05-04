output "function_name" {
  value = aws_lambda_function.program_builder.function_name
}

output "function_arn" {
  value = aws_lambda_function.program_builder.arn
}

output "invoke_arn" {
  value = aws_lambda_function.program_builder.invoke_arn
}

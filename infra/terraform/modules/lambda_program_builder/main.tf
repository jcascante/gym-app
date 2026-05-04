resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 30
}

resource "aws_lambda_function" "program_builder" {
  function_name = var.function_name
  role          = var.execution_role_arn
  runtime       = var.runtime
  handler       = "lambda.handler.handler"
  timeout       = var.timeout_sec
  memory_size   = var.memory_mb

  s3_bucket = var.deployment_package_s3_bucket
  s3_key    = var.deployment_package_s3_key

  environment {
    variables = merge(
      var.environment_variables,
      {
        DATA_DIR        = "/var/task/data"
        DEFINITIONS_DIR = "/var/task/definitions"
        SCHEMAS_DIR     = "/var/task/schemas"
      }
    )
  }

  depends_on = [aws_cloudwatch_log_group.lambda]

  tags = {
    Name        = var.function_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda error rate too high"

  dimensions = { FunctionName = aws_lambda_function.program_builder.function_name }
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.function_name}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 60
  extended_statistic  = "p99"
  threshold           = 10000
  alarm_description   = "Lambda p99 duration > 10s"

  dimensions = { FunctionName = aws_lambda_function.program_builder.function_name }
}

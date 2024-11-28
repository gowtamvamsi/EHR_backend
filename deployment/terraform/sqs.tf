resource "aws_sqs_queue" "celery_queue_high_priority" {
  name                      = "ehs-high-priority-${var.environment}"
  delay_seconds             = 0
  max_message_size         = 262144
  message_retention_seconds = 345600
  receive_wait_time_seconds = 20
  visibility_timeout_seconds = 3600

  tags = {
    Environment = var.environment
    Project     = "EHS"
    Priority    = "high"
  }
}

resource "aws_sqs_queue" "celery_queue_default" {
  name                      = "ehs-default-${var.environment}"
  delay_seconds             = 0
  max_message_size         = 262144
  message_retention_seconds = 345600
  receive_wait_time_seconds = 20
  visibility_timeout_seconds = 3600

  tags = {
    Environment = var.environment
    Project     = "EHS"
    Priority    = "default"
  }
}

resource "aws_sqs_queue" "celery_queue_low_priority" {
  name                      = "ehs-low-priority-${var.environment}"
  delay_seconds             = 0
  max_message_size         = 262144
  message_retention_seconds = 345600
  receive_wait_time_seconds = 20
  visibility_timeout_seconds = 3600

  tags = {
    Environment = var.environment
    Project     = "EHS"
    Priority    = "low"
  }
}
resource "aws_ecs_cluster" "ehs_cluster" {
  name = "ehs-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = var.environment
    Project     = "EHS"
  }
}

# Celery Worker Service - High Priority
resource "aws_ecs_service" "celery_worker_high" {
  name            = "ehs-celery-high-${var.environment}"
  cluster         = aws_ecs_cluster.ehs_cluster.id
  task_definition = aws_ecs_task_definition.celery_worker_high.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.celery_sg.id]
  }

  tags = {
    Environment = var.environment
    Project     = "EHS"
    Component   = "celery-high"
  }
}

# Celery Worker Service - Default Priority
resource "aws_ecs_service" "celery_worker_default" {
  name            = "ehs-celery-default-${var.environment}"
  cluster         = aws_ecs_cluster.ehs_cluster.id
  task_definition = aws_ecs_task_definition.celery_worker_default.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.celery_sg.id]
  }

  tags = {
    Environment = var.environment
    Project     = "EHS"
    Component   = "celery-default"
  }
}

# Security Group for Celery Workers
resource "aws_security_group" "celery_sg" {
  name        = "ehs-celery-sg-${var.environment}"
  description = "Security group for EHS Celery workers"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment
    Project     = "EHS"
  }
}
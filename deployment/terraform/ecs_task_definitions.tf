resource "aws_ecs_task_definition" "django_migration" {
  family                   = "ehs-migration-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = "256"
  memory                  = "512"
  execution_role_arn      = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "django-migration"
      image = "${var.ecr_repository_url}:${var.image_tag}"
      command = ["/app/deployment/scripts/migrate.sh"]
      
      environment = [
        {
          name  = "DB_HOST"
          value = aws_db_instance.ehs_db.address
        },
        {
          name  = "DB_NAME"
          value = aws_db_instance.ehs_db.db_name
        },
        {
          name  = "DB_USER"
          value = aws_db_instance.ehs_db.username
        }
      ]
      
      secrets = [
        {
          name      = "DB_PASSWORD"
          valueFrom = aws_secretsmanager_secret.db_password.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/ehs-migration-${var.environment}"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "migration"
        }
      }
    }
  ])

  tags = {
    Environment = var.environment
    Project     = "EHS"
  }
}
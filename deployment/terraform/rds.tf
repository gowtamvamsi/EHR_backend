resource "aws_db_instance" "ehs_db" {
  identifier        = "ehs-db-${var.environment}"
  engine            = "postgres"
  engine_version    = "13.7"
  instance_class    = "db.t3.micro"  # Adjust based on needs
  allocated_storage = 20

  db_name  = "ehs_db"
  username = "ehs_admin"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  multi_az               = var.environment == "prod" ? true : false
  skip_final_snapshot    = var.environment != "prod"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  performance_insights_enabled = true
  
  tags = {
    Environment = var.environment
    Project     = "EHS"
  }
}

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "ehs-db-subnet-group-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Environment = var.environment
    Project     = "EHS"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "ehs-rds-sg-${var.environment}"
  description = "Security group for EHS RDS instance"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

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
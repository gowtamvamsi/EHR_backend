resource "aws_elasticache_cluster" "ehs_redis" {
  cluster_id           = "ehs-redis-${var.environment}"
  engine              = "redis"
  node_type           = "cache.t3.micro"  # Adjust based on needs
  num_cache_nodes     = 1
  parameter_group_family = "redis6.x"
  port                = 6379
  security_group_ids  = [aws_security_group.redis_sg.id]
  subnet_group_name   = aws_elasticache_subnet_group.redis_subnet_group.name

  tags = {
    Environment = var.environment
    Project     = "EHS"
  }
}

resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "ehs-redis-subnet-group-${var.environment}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_security_group" "redis_sg" {
  name        = "ehs-redis-sg-${var.environment}"
  description = "Security group for EHS Redis cluster"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
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
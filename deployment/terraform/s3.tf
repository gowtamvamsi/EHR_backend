resource "aws_s3_bucket" "ehs_storage" {
  bucket = "ehs-storage-${var.environment}-${var.aws_region}"

  tags = {
    Environment = var.environment
    Project     = "EHS"
  }
}

resource "aws_s3_bucket_versioning" "ehs_storage_versioning" {
  bucket = aws_s3_bucket.ehs_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ehs_storage_encryption" {
  bucket = aws_s3_bucket.ehs_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ehs_storage_public_access" {
  bucket = aws_s3_bucket.ehs_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "ehs_storage_cors" {
  bucket = aws_s3_bucket.ehs_storage.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = var.allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
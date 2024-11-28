output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.ehs_db.endpoint
  sensitive   = true
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.ehs_storage.id
}

output "s3_bucket_domain" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.ehs_storage.bucket_regional_domain_name
}
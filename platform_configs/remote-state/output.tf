# run `terraform output` to see values for backend
output "s3_bucket" {
  description = "Terraform state s3 bucket"
  value       = aws_s3_bucket.terraform_state_2.bucket
}

output "s3_bucket_key" {
  description = "Terraform state s3 bucket tfstate key"
  value       = "special-message-alarm/tfstate"
}

output "s3_bucket_region" {
  description = "Terraform state s3 bucket region"
  value       = aws_s3_bucket.terraform_state_2.region
}
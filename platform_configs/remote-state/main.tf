# Sets up terraform state resources for remote work
# See https://stackoverflow.com/questions/47913041/initial-setup-of-terraform-backend-using-terraform

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "terraform_state_2" {
  bucket = "terraform-state-117456"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state_2.id

  versioning_configuration {
    status = "Enabled"
  }
}

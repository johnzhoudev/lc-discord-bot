terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  backend "s3" {
    bucket       = "terraform-state-117290"
    key          = "lc-discord-bot/tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region = "us-east-1"
}

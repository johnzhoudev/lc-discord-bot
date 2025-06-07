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

resource "aws_ecr_repository" "my_app" {
  name = "lc-discord-bot"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecs_cluster" "lc_discord_bot_cluster" {
    name = "lc-discord-bot"
}

# resource "aws_ecs_task_definition" "lc_discord_bot" {
#     family = "lc-discord-bot"
#     requires_compatibilities = ["EC2"]


#     container_definitions = jsonencode([
#         {
#             # TODO

#         }
#     ])
# }

# IAM Policies
resource "aws_iam_role" "lc_discord_bot_task_role" {
    name = "lc_discord_bot_task"
    assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        "Condition": {
            "ArnLike": {
                "aws:SourceArn": "arn:aws:ecs:us-east-1:170221608339:*"
            },
            "StringEquals": {
                "aws:SourceAccount": "170221608339"
            }
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "lc_discord_bot_task_policy" {
    name = "lc_discord_bot_task_policy"
    role = aws_iam_role.lc_discord_bot_task_role.id

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
        {
            Action = [
                "ssm:GetParameter",
                "ssm:GetParameters",
            ]
            Effect   = "Allow"
            Resource = "arn:aws:ssm:us-east-1:170221608339:parameter/lc-discord-bot/BOT_TOKEN"
        },
        ]
    })
}


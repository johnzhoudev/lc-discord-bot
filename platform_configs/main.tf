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

resource "aws_ecr_repository" "lc_discord_bot" {
  name                 = "lc-discord-bot"
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

# This is a template ecs_task definition. Github actions will copy this task definition, modify it, and redeploy.
resource "aws_ecs_task_definition" "lc_discord_bot" {
  family                   = "lc-discord-bot"
  requires_compatibilities = ["EC2"]
  task_role_arn            = aws_iam_role.lc_discord_bot_task_role.arn
  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn
  network_mode = "bridge"

  container_definitions = jsonencode([
    {
      name = "lc-discord-bot"
      image = "${aws_ecr_repository.lc_discord_bot.repository_url}:latest"
      # TODO: Memory and cpu limits?
      # No need for port mappings since outbound only
      essential = true # If this stops, all other containers in the task stop too.
      memory = 128 # 128 mb

      logConfiguration = {
        logDriver = "awslogs"
        options = {
            awslogs-group = "${aws_cloudwatch_log_group.ecs_logs.name}"
            awslogs-region = "us-east-1",
            awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "lc_discord_bot_service" {
  name = "lc-discord-bot"
  cluster = aws_ecs_cluster.lc_discord_bot_cluster.arn
  task_definition = aws_ecs_task_definition.lc_discord_bot.arn
  desired_count = 1
  launch_type = "EC2"
}

# Logging, log groups
resource "aws_cloudwatch_log_group" "ecs_logs" {
    name = "/ecs/lc-discord-bot"
    retention_in_days = 7
}


# EC2 instances for the ECS Cluster

# Instance profile (binds ec2 instance to role)
resource "aws_iam_instance_profile" "ecs_instance_profile" {
  name = "ecsInstanceProfile"
  role = aws_iam_role.ecs_instance_role.name
}

resource "aws_default_vpc" "default" { 
}

# Security group allowing outbound connections only
resource "aws_security_group" "ecs_sg" {
  name        = "lc-discord-bot-security-group"
  description = "Allow all outbound"
  vpc_id      = aws_default_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Get ecs optimized ami 
data "aws_ssm_parameter" "ecs_ami" {
  name = "/aws/service/ecs/optimized-ami/amazon-linux-2/recommended/image_id"
}

# 4. EC2 instance with ECS agent and cluster name
resource "aws_instance" "ecs_instance" {
  ami           = "ami-0ec3e36ea5ad3df41" # 86x64 for us-east-1
  instance_type = "t3.nano"

  iam_instance_profile = aws_iam_instance_profile.ecs_instance_profile.name
  security_groups      = [aws_security_group.ecs_sg.name]
  subnet_id            = aws_default_subnet.default_us_east_1.id

  user_data = <<-EOF
              #!/bin/bash
              echo ECS_CLUSTER=${aws_ecs_cluster.lc_discord_bot_cluster.name} >> /etc/ecs/ecs.config
              EOF
}

# AWS Networking
# Use default AWS public subnet, but add a security group onto the service to disable incoming connections.
# Too much hassle to setup a whole private_subnet

resource "aws_default_subnet" "default_us_east_1" {
  availability_zone = "us-east-1a"
}

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
        "Condition" : {
          "ArnLike" : {
            "aws:SourceArn" : "arn:aws:ecs:us-east-1:170221608339:*"
          },
          "StringEquals" : {
            "aws:SourceAccount" : "170221608339"
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

# ECS Execution role policies
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# AWS Role for ec2 instances to operate
resource "aws_iam_role" "ecs_instance_role" {
  name = "ecsInstanceRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_instance_role_policy" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}
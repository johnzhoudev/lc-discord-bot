# IAM Policies

# IAM Role for task running in the container
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

# ECS Execution role (ECS Executor agent)
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
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# AWS Role for ec2 instances to operate in the ECS cluster
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
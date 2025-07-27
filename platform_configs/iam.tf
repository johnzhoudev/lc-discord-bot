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
            "aws:SourceArn" : "arn:aws:ecs:us-east-1:273354659414:*"
          },
          "StringEquals" : {
            "aws:SourceAccount" : "273354659414"
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
        Resource = "arn:aws:ssm:us-east-1:273354659414:parameter/lc-discord-bot/*"
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

# Github actions role
# https://medium.com/@thiagosalvatore/using-terraform-to-connect-github-actions-and-aws-with-oidc-0e3d27f00123

resource "aws_iam_openid_connect_provider" "github_oidc" {
  url = "https://token.actions.githubusercontent.com"
  client_id_list = [
    "sts.amazonaws.com",
  ]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]
}


resource "aws_iam_role" "github_oidc_role" {
  name = "github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = "sts:AssumeRoleWithWebIdentity",
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_oidc.arn
        },
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          },
          StringLike = {
            "token.actions.githubusercontent.com:sub" = var.github_oidc_sub
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "github_actions_policy" {
  name = "github_actions_policy"
  role = aws_iam_role.github_oidc_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = "ecr:GetAuthorizationToken",
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          # "ecr:BatchCheckLayerAvailability",
          # "ecr:InitiateLayerUpload",
          # "ecr:UploadLayerPart",
          # "ecr:CompleteLayerUpload",
          # "ecr:PutImage",
          # "ecr:DescribeRepositories",
          # "ecr:GetRepositoryPolicy"
          "ecr:*"
        ],
        Resource = "${aws_ecr_repository.lc_discord_bot.arn}"
      },
      {
        Effect = "Allow",
        Action = [
          # "ecs:UpdateService",
          # "ecs:DescribeServices",
          # "ecs:DescribeTaskDefinition"
          "ecs:*"
        ],
        Resource = "${aws_ecs_service.lc_discord_bot_service.id}"
      },
      {
        Effect = "Allow",
        Action = "iam:PassRole",
        Resource = "${aws_iam_role.ecs_task_execution_role.arn}"
      }
    ]
  })
}

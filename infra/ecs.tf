locals {
  budibase_container_name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-container"
  budibase_cluster_name   = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-cluster"
}

resource "aws_ecs_cluster" "budibase_cluster" {
  name = local.budibase_cluster_name

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  configuration {
    # ECS Exec encryption and logging set to 'Default' (also Monitoring).

    execute_command_configuration {
      logging = "OVERRIDE"

      log_configuration {
        cloud_watch_log_group_name = data.aws_cloudwatch_log_group.budibase_ecs_task.name
      }
    }

    # Provide AWS KMS keys for encryption of both managed and ephemeral storage.
    managed_storage_configuration {
      kms_key_id                           = aws_kms_key.fargate_managed_storage.id
      fargate_ephemeral_storage_kms_key_id = aws_kms_key.fargate_ephemeral_storage.arn
    }
  }

  depends_on = [data.aws_iam_policy_document.kms_key_for_fargate]
}

resource "aws_ecs_task_definition" "budibase_ecs_task" {
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  family                   = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-ecs-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"

  cpu    = 2048 # 2 vCPU (4GB)
  memory = 6144 # 6GB

  task_role_arn      = aws_iam_role.budibase_ecs_task.arn
  execution_role_arn = aws_iam_role.budibase_ecs_task_execution.arn

  volume {
    name = "budibase-ecs-task-storage"

    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.budibase_fargate_data.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.budibase_fargate_access_point.id
      }
    }
  }

  container_definitions = jsonencode([
    {
      name      = "${local.budibase_container_name}"
      essential = true
      image     = "${var.BUDIBASE_IMAGE_URL}"

      # Resource allocation limits:
      cpu    = 2048 # 2 vCPU
      memory = 6144 # 6GB

      portMappings = [
        {
          name          = "80-tcp"
          containerPort = 80
          appProtocol   = "http"
        },
        {
          name          = "443-tcp"
          containerPort = 443
        },
        {
          name          = "2222-tcp"
          containerPort = 2222
        },
        {
          name          = "4369-tcp"
          containerPort = 4369
        },
        {
          name          = "5984-tcp"
          containerPort = 5984
        },
        {
          name          = "9100-tcp"
          containerPort = 9100
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          "awslogs-group"         = data.aws_cloudwatch_log_group.budibase_ecs_task.name
          "awslogs-region"        = var.AWS_REGION
          "awslogs-stream-prefix" = "ecs"
        }
      }

      mountPoints = [
        {
          sourceVolume  = "budibase-ecs-task-storage"
          containerPath = "/data"
        }
      ]
    }
  ])
}

resource "aws_lb" "budibase_alb" {
  name = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-lb"

  load_balancer_type = "application"
  security_groups    = [aws_security_group.budibase_load_balancer.id]

  subnets = tolist([
    for key in var.SUBNETS_BY_ENV[var.ENVIRONMENT] :
    aws_subnet.public[key].id
  ])

  # enable_deletion_protection = var.ENVIRONMENT == "prod"
}

resource "aws_lb_target_group" "budibase_alb_target_group" {
  name        = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-lb-tg"
  target_type = "ip"
  vpc_id      = local.vpc_id
  protocol    = "HTTP"
  port        = 80

  deregistration_delay = 300
  # slow_start = 90 ?

  health_check {
    protocol = "HTTP"
    path     = "/"
    matcher  = "200-299,301-302"
  }
}

resource "aws_lb_listener" "budibase_alb_listener" {
  load_balancer_arn = aws_lb.budibase_alb.arn
  protocol          = "HTTP"
  port              = 80

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.budibase_alb_target_group.arn
  }
}

resource "aws_ecs_service" "budibase_ecs_service" {
  name            = "${var.PREFIX}-${var.ENVIRONMENT}-budibase-ecs-service"
  cluster         = aws_ecs_cluster.budibase_cluster.id
  task_definition = aws_ecs_task_definition.budibase_ecs_task.arn

  launch_type                   = "FARGATE"
  platform_version              = "LATEST"
  scheduling_strategy           = "REPLICA"
  desired_count                 = var.BUDIBASE_TASK_COUNT
  availability_zone_rebalancing = "ENABLED"
  #   - Health check grace period: 0 (disabled)
  enable_execute_command = true
  propagate_tags         = "TASK_DEFINITION"

  network_configuration {
    subnets = tolist([
      for key in var.SUBNETS_BY_ENV[var.ENVIRONMENT] :
      aws_subnet.private[key].id
    ])
    security_groups  = [aws_security_group.budibase_fargate.id]
    assign_public_ip = false
  }

  load_balancer {
    container_name   = local.budibase_container_name
    container_port   = 80
    target_group_arn = aws_lb_target_group.budibase_alb_target_group.arn
  }
}

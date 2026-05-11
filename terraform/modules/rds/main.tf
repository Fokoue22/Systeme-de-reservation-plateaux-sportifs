# RDS Module - Main Configuration

# Create DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.identifier}-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier}-subnet-group"
    }
  )
}

# Create RDS Instance
resource "aws_db_instance" "main" {
  identifier     = var.identifier
  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = var.storage_type
  storage_encrypted     = var.storage_encrypted

  db_name  = var.db_name
  username = var.username
  password = var.password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az               = var.multi_az
  publicly_accessible    = var.publicly_accessible
  backup_retention_period = var.backup_retention_days
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window
  skip_final_snapshot    = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.identifier}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  iam_database_authentication_enabled = var.enable_iam_database_authentication
  enabled_cloudwatch_logs_exports    = var.enable_cloudwatch_logs_exports
  deletion_protection    = var.deletion_protection

  tags = merge(
    var.tags,
    {
      Name = var.identifier
    }
  )
}

# Create Security Group for RDS
resource "aws_security_group" "rds" {
  name        = "${var.identifier}-sg"
  description = "Security group for RDS database"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier}-sg"
    }
  )
}

# Allow inbound traffic to RDS
resource "aws_security_group_rule" "rds_ingress" {
  type              = "ingress"
  from_port         = var.port
  to_port           = var.port
  protocol          = "tcp"
  cidr_blocks       = var.allowed_cidr_blocks
  security_group_id = aws_security_group.rds.id
}

# Create CloudWatch Log Group for RDS
resource "aws_cloudwatch_log_group" "rds" {
  count             = length(var.enable_cloudwatch_logs_exports) > 0 ? 1 : 0
  name              = "/aws/rds/${var.identifier}"
  retention_in_days = var.log_retention_days

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier}-logs"
    }
  )
}

# Create RDS Enhanced Monitoring Role (optional)
resource "aws_iam_role" "rds_monitoring" {
  count = var.enable_enhanced_monitoring ? 1 : 0
  name  = "${var.identifier}-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  count      = var.enable_enhanced_monitoring ? 1 : 0
  role       = aws_iam_role.rds_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Create RDS Parameter Group
resource "aws_db_parameter_group" "main" {
  family = "${var.engine}${split(".", var.engine_version)[0]}"
  name   = "${var.identifier}-params"

  dynamic "parameter" {
    for_each = var.parameters
    content {
      name  = parameter.key
      value = parameter.value
    }
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.identifier}-params"
    }
  )
}

# RDS Module - Root Configuration

module "rds" {
  source = "./modules/rds"

  identifier = local.rds_identifier

  vpc_id                 = module.vpc.vpc_id
  database_subnet_ids    = module.vpc.database_subnet_ids
  allowed_cidr_blocks    = var.private_subnet_cidrs

  engine         = local.rds_config.engine
  engine_version = local.rds_config.engine_version
  instance_class = local.rds_config.instance_class

  allocated_storage      = local.rds_config.allocated_storage
  max_allocated_storage  = local.rds_config.max_allocated_storage
  storage_type           = local.rds_config.storage_type
  storage_encrypted      = local.rds_config.storage_encrypted

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  multi_az                = local.rds_config.multi_az
  publicly_accessible     = false
  backup_retention_days   = local.rds_config.backup_retention_days
  backup_window           = local.rds_config.backup_window
  maintenance_window      = local.rds_config.maintenance_window
  skip_final_snapshot     = local.rds_config.skip_final_snapshot

  enable_cloudwatch_logs_exports      = ["postgresql"]
  enable_iam_database_authentication  = true
  deletion_protection                 = var.environment != "development"

  enable_enhanced_monitoring = true
  log_retention_days         = 7

  parameters = {
    "log_statement" = "all"
    "log_duration"  = "on"
  }

  tags = local.common_tags

  depends_on = [module.vpc]
}

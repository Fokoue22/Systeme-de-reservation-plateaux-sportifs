locals {
  # Common naming convention
  name_prefix = "${var.project_name}-${var.environment}"

  # Common tags applied to all resources
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  )

  # VPC Configuration
  vpc_config = {
    cidr_block           = var.vpc_cidr
    enable_dns_hostnames = true
    enable_dns_support   = true
  }

  # Subnet Configuration
  public_subnets = [
    for idx, cidr in var.public_subnet_cidrs : {
      cidr_block            = cidr
      availability_zone     = var.availability_zones[idx]
      map_public_ip_on_launch = true
    }
  ]

  private_subnets = [
    for idx, cidr in var.private_subnet_cidrs : {
      cidr_block        = cidr
      availability_zone = var.availability_zones[idx]
    }
  ]

  database_subnets = [
    for idx, cidr in var.database_subnet_cidrs : {
      cidr_block        = cidr
      availability_zone = var.availability_zones[idx]
    }
  ]

  # EKS Configuration
  eks_config = {
    cluster_version = var.eks_cluster_version
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  # EKS Node Group Configuration
  eks_node_group_config = {
    desired_size    = var.eks_node_group_desired_size
    min_size        = var.eks_node_group_min_size
    max_size        = var.eks_node_group_max_size
    instance_types  = var.eks_node_instance_types
    disk_size       = var.eks_node_disk_size
    capacity_type   = "ON_DEMAND"
  }

  # RDS Configuration
  rds_config = {
    engine               = "postgres"
    engine_version       = var.rds_engine_version
    instance_class       = var.rds_instance_class
    allocated_storage    = var.rds_allocated_storage
    max_allocated_storage = var.rds_max_allocated_storage
    storage_type         = "gp3"
    storage_encrypted    = true
    multi_az             = var.rds_multi_az
    backup_retention_days = var.rds_backup_retention_days
    backup_window        = "03:00-04:00"
    maintenance_window   = "mon:04:00-mon:05:00"
    skip_final_snapshot  = var.environment == "development" ? true : false
  }

  # ECR Configuration
  ecr_config = {
    image_tag_mutability = var.ecr_image_tag_mutability
    scan_on_push         = var.ecr_scan_on_push
  }

  # Security Group Rules
  eks_cluster_ingress_rules = [
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = [var.vpc_cidr]
      description = "Allow HTTPS from VPC"
    }
  ]

  eks_node_ingress_rules = [
    {
      from_port   = 0
      to_port     = 65535
      protocol    = "tcp"
      cidr_blocks = [var.vpc_cidr]
      description = "Allow all TCP from VPC"
    },
    {
      from_port   = 0
      to_port     = 65535
      protocol    = "udp"
      cidr_blocks = [var.vpc_cidr]
      description = "Allow all UDP from VPC"
    }
  ]

  rds_ingress_rules = [
    {
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      cidr_blocks = var.private_subnet_cidrs
      description = "Allow PostgreSQL from private subnets"
    }
  ]

  # Resource naming
  eks_cluster_name = "${local.name_prefix}-eks"
  rds_identifier   = "${local.name_prefix}-postgres"
  ecr_api_name     = "${local.name_prefix}-api"
  ecr_frontend_name = "${local.name_prefix}-frontend"

  # Kubernetes namespace
  kubernetes_namespace = "reservation"

  # Feature flags
  enable_nat_gateway = var.enable_nat_gateway
  enable_vpn_gateway = var.enable_vpn_gateway
  enable_flow_logs   = var.enable_flow_logs
  enable_monitoring  = var.enable_monitoring
}

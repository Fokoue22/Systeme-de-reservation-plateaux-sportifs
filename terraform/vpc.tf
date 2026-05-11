# VPC Module - Root Configuration

module "vpc" {
  source = "./modules/vpc"

  name_prefix = local.name_prefix
  vpc_cidr    = var.vpc_cidr

  availability_zones    = var.availability_zones
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs

  enable_dns_hostnames = local.vpc_config.enable_dns_hostnames
  enable_dns_support   = local.vpc_config.enable_dns_support
  enable_nat_gateway   = local.enable_nat_gateway
  enable_flow_logs     = local.enable_flow_logs

  tags = local.common_tags
}

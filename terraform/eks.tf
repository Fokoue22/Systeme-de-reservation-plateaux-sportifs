# EKS Module - Root Configuration

module "eks" {
  source = "./modules/eks"

  cluster_name    = local.eks_cluster_name
  cluster_version = local.eks_config.cluster_version

  vpc_id              = module.vpc.vpc_id
  vpc_cidr            = var.vpc_cidr
  public_subnet_ids   = module.vpc.public_subnet_ids
  private_subnet_ids  = module.vpc.private_subnet_ids

  desired_size   = local.eks_node_group_config.desired_size
  min_size       = local.eks_node_group_config.min_size
  max_size       = local.eks_node_group_config.max_size
  instance_types = local.eks_node_group_config.instance_types
  disk_size      = local.eks_node_group_config.disk_size
  capacity_type  = local.eks_node_group_config.capacity_type

  endpoint_private_access = local.eks_config.endpoint_private_access
  endpoint_public_access  = local.eks_config.endpoint_public_access

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  log_retention_days        = 7

  tags = local.common_tags

  depends_on = [module.vpc]
}

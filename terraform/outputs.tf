# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.vpc.private_subnet_ids
}

output "database_subnet_ids" {
  description = "IDs of database subnets"
  value       = module.vpc.database_subnet_ids
}

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = module.vpc.internet_gateway_id
}

output "nat_gateway_ids" {
  description = "NAT Gateway IDs"
  value       = module.vpc.nat_gateway_ids
}

# EKS Outputs
output "eks_cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_version" {
  description = "EKS cluster Kubernetes version"
  value       = module.eks.cluster_version
}

output "eks_cluster_certificate_authority" {
  description = "EKS cluster certificate authority data"
  value       = module.eks.cluster_certificate_authority
  sensitive   = true
}

output "eks_node_group_id" {
  description = "EKS node group ID"
  value       = module.eks.node_group_id
}

output "eks_node_group_status" {
  description = "EKS node group status"
  value       = module.eks.node_group_status
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "eks_cluster_role_arn" {
  description = "EKS cluster IAM role ARN"
  value       = module.eks.cluster_role_arn
}

output "eks_node_role_arn" {
  description = "EKS node IAM role ARN"
  value       = module.eks.node_role_arn
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.db_instance_endpoint
}

output "rds_address" {
  description = "RDS database address"
  value       = module.rds.db_instance_address
}

output "rds_port" {
  description = "RDS database port"
  value       = module.rds.db_instance_port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.db_name
}

output "rds_username" {
  description = "RDS master username"
  value       = module.rds.db_username
  sensitive   = true
}

output "rds_resource_id" {
  description = "RDS resource ID"
  value       = module.rds.db_instance_resource_id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = module.rds.security_group_id
}

# ECR Outputs
output "ecr_api_repository_url" {
  description = "ECR repository URL for API image"
  value       = module.ecr.api_repository_url
}

output "ecr_frontend_repository_url" {
  description = "ECR repository URL for Frontend image"
  value       = module.ecr.frontend_repository_url
}

output "ecr_registry_id" {
  description = "ECR registry ID"
  value       = module.ecr.api_registry_id
}

# Kubernetes Configuration
output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_id}"
}

output "kubernetes_cluster_name" {
  description = "Kubernetes cluster name"
  value       = module.eks.cluster_id
}

# Summary Output
output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    region              = var.aws_region
    environment         = var.environment
    vpc_cidr            = module.vpc.vpc_cidr
    vpc_id              = module.vpc.vpc_id
    eks_cluster_name    = module.eks.cluster_id
    eks_cluster_version = module.eks.cluster_version
    eks_endpoint        = module.eks.cluster_endpoint
    rds_endpoint        = module.rds.db_instance_endpoint
    rds_address         = module.rds.db_instance_address
    ecr_api_url         = module.ecr.api_repository_url
    ecr_frontend_url    = module.ecr.frontend_repository_url
  }
}

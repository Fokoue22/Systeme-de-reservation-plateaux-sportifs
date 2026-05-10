# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  description = "IDs of database subnets"
  value       = aws_subnet.database[*].id
}

# EKS Outputs
output "eks_cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.main.id
}

output "eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_version" {
  description = "EKS cluster Kubernetes version"
  value       = aws_eks_cluster.main.version
}

output "eks_cluster_certificate_authority" {
  description = "EKS cluster certificate authority data"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "eks_node_group_id" {
  description = "EKS node group ID"
  value       = aws_eks_node_group.main.id
}

output "eks_node_group_status" {
  description = "EKS node group status"
  value       = aws_eks_node_group.main.status
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.main.endpoint
}

output "rds_address" {
  description = "RDS database address"
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "RDS database port"
  value       = aws_db_instance.main.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "rds_username" {
  description = "RDS master username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "rds_resource_id" {
  description = "RDS resource ID"
  value       = aws_db_instance.main.resource_id
}

# ECR Outputs
output "ecr_api_repository_url" {
  description = "ECR repository URL for API image"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_frontend_repository_url" {
  description = "ECR repository URL for Frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecr_registry_id" {
  description = "ECR registry ID"
  value       = aws_ecr_repository.api.registry_id
}

# Security Group Outputs
output "eks_security_group_id" {
  description = "EKS cluster security group ID"
  value       = aws_security_group.eks_cluster.id
}

output "eks_node_security_group_id" {
  description = "EKS node security group ID"
  value       = aws_security_group.eks_nodes.id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

# IAM Outputs
output "eks_cluster_role_arn" {
  description = "EKS cluster IAM role ARN"
  value       = aws_iam_role.eks_cluster_role.arn
}

output "eks_node_role_arn" {
  description = "EKS node IAM role ARN"
  value       = aws_iam_role.eks_node_role.arn
}

# Kubernetes Configuration
output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}

output "kubernetes_cluster_name" {
  description = "Kubernetes cluster name"
  value       = aws_eks_cluster.main.name
}

# Summary Output
output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    region              = var.aws_region
    environment         = var.environment
    vpc_cidr            = aws_vpc.main.cidr_block
    eks_cluster_name    = aws_eks_cluster.main.name
    eks_cluster_version = aws_eks_cluster.main.version
    rds_endpoint        = aws_db_instance.main.endpoint
    ecr_api_url         = aws_ecr_repository.api.repository_url
    ecr_frontend_url    = aws_ecr_repository.frontend.repository_url
  }
}

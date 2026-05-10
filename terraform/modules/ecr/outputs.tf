output "api_repository_url" {
  description = "API ECR repository URL"
  value       = aws_ecr_repository.api.repository_url
}

output "api_repository_arn" {
  description = "API ECR repository ARN"
  value       = aws_ecr_repository.api.arn
}

output "api_repository_name" {
  description = "API ECR repository name"
  value       = aws_ecr_repository.api.name
}

output "api_registry_id" {
  description = "API ECR registry ID"
  value       = aws_ecr_repository.api.registry_id
}

output "frontend_repository_url" {
  description = "Frontend ECR repository URL"
  value       = aws_ecr_repository.frontend.repository_url
}

output "frontend_repository_arn" {
  description = "Frontend ECR repository ARN"
  value       = aws_ecr_repository.frontend.arn
}

output "frontend_repository_name" {
  description = "Frontend ECR repository name"
  value       = aws_ecr_repository.frontend.name
}

output "frontend_registry_id" {
  description = "Frontend ECR registry ID"
  value       = aws_ecr_repository.frontend.registry_id
}

output "ecr_push_pull_policy_arn" {
  description = "ECR push/pull policy ARN"
  value       = aws_iam_policy.ecr_push_pull.arn
}

output "github_actions_role_arn" {
  description = "GitHub Actions IAM role ARN"
  value       = try(aws_iam_role.github_actions[0].arn, null)
}

output "github_actions_role_name" {
  description = "GitHub Actions IAM role name"
  value       = try(aws_iam_role.github_actions[0].name, null)
}

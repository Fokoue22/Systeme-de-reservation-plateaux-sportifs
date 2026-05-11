# ECR Module - Root Configuration

module "ecr" {
  source = "./modules/ecr"

  name_prefix = local.name_prefix

  api_repository_name      = local.ecr_api_name
  frontend_repository_name = local.ecr_frontend_name

  image_tag_mutability = local.ecr_config.image_tag_mutability
  scan_on_push         = local.ecr_config.scan_on_push
  force_delete         = var.environment == "development" ? true : false

  encryption_type = "AES256"
  kms_key         = null

  create_github_actions_role = false
  github_repository          = ""
  aws_account_id             = var.aws_account_id

  tags = local.common_tags
}

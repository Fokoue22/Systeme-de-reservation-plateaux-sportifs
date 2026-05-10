# Production Environment

This directory contains the Terraform configuration for the production environment.

## Setup

1. Copy `terraform.tfvars.example` to `terraform.tfvars`:
```bash
cp terraform.tfvars.example terraform.tfvars
```

2. Update `terraform.tfvars` with your AWS account ID and desired configuration

3. Deploy:
```bash
terraform init
terraform plan
terraform apply
```

## Important Notes

- Always review the plan before applying
- Use remote state backend for production
- Enable deletion protection on critical resources
- Enable Multi-AZ for RDS in production
- Use larger instance types for better performance

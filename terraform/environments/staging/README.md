# Staging Environment

This directory contains the Terraform configuration for the staging environment.

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

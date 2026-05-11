# Terraform Infrastructure as Code

Complete Infrastructure as Code for the Sports Reservation System using Terraform.

## Quick Start

### 1. Install Terraform

#### Windows
```powershell
# Run the setup script
.\setup.ps1

# Or manually download from:
# https://www.terraform.io/downloads.html
```

#### Linux/macOS
```bash
# Run the setup script
chmod +x setup.sh
./setup.sh

# Or manually download from:
# https://www.terraform.io/downloads.html
```

### 2. Configure AWS Credentials

```bash
aws configure

# Or set environment variables:
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Verify:
aws sts get-caller-identity
```

### 3. Initialize Terraform

```bash
cd terraform
terraform init -upgrade
```

### 4. Validate Configuration

```bash
terraform validate
terraform fmt -check -recursive
```

### 5. Plan Infrastructure

```bash
# Development environment
terraform plan -var-file=environments/development/terraform.tfvars -out=tfplan

# Staging environment
terraform plan -var-file=environments/staging/terraform.tfvars -out=tfplan

# Production environment
terraform plan -var-file=environments/production/terraform.tfvars -out=tfplan
```

### 6. Apply Configuration

```bash
terraform apply tfplan
```

## Project Structure

```
terraform/
├── main.tf                    # Provider configuration
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── locals.tf                  # Local computed values
├── vpc.tf                      # VPC module instantiation
├── eks.tf                      # EKS module instantiation
├── rds.tf                      # RDS module instantiation
├── ecr.tf                      # ECR module instantiation
├── terraform.tfvars.example    # Example variables
├── Makefile                    # Make commands
├── validate.sh                 # Validation script
├── setup.ps1                   # Windows setup script
├── setup.sh                    # Linux/macOS setup script
├── README.md                   # This file
│
├── modules/
│   ├── vpc/                   # VPC module
│   ├── eks/                   # EKS module
│   ├── rds/                   # RDS module
│   └── ecr/                   # ECR module
│
└── environments/
    ├── development/           # Development environment
    ├── staging/               # Staging environment
    └── production/            # Production environment
```

## Modules

### VPC Module
Creates networking infrastructure:
- VPC with configurable CIDR
- Public, private, and database subnets
- Internet Gateway
- NAT Gateways
- Route tables
- VPC Flow Logs

### EKS Module
Creates Kubernetes infrastructure:
- EKS Cluster
- Node Groups
- IAM Roles and Policies
- Security Groups
- CloudWatch Logs

### RDS Module
Creates database infrastructure:
- PostgreSQL RDS Instance
- DB Subnet Group
- Security Group
- Parameter Group
- CloudWatch Logs
- Enhanced Monitoring

### ECR Module
Creates container registry:
- ECR Repositories (API and Frontend)
- Lifecycle Policies
- IAM Policies
- GitHub Actions Role (optional)

## Environments

### Development
- Smaller instance types (t3.medium)
- 2 EKS nodes (1 min, 5 max)
- Single-AZ RDS
- 7-day backup retention

### Staging
- Medium instance types
- 2-3 EKS nodes
- Optional Multi-AZ RDS
- 7-day backup retention

### Production
- Larger instance types
- 3+ EKS nodes
- Multi-AZ RDS
- 30-day backup retention
- Deletion protection enabled

## Common Commands

### Using Terraform Directly

```bash
# Initialize
terraform init -upgrade

# Validate
terraform validate

# Format
terraform fmt -recursive

# Plan
terraform plan -var-file=environments/development/terraform.tfvars

# Apply
terraform apply -var-file=environments/development/terraform.tfvars

# Destroy
terraform destroy -var-file=environments/development/terraform.tfvars

# Show outputs
terraform output -json

# Show state
terraform state list
```

### Using Makefile

```bash
# Initialize
make init ENVIRONMENT=development

# Validate
make validate

# Format
make fmt

# Plan
make plan ENVIRONMENT=development

# Apply
make apply ENVIRONMENT=development

# Destroy
make destroy ENVIRONMENT=development

# Test all
make test

# Show outputs
make output

# Show state
make state
```

### Using Validation Script

```bash
# Full validation
./validate.sh full development

# Initialize
./validate.sh init

# Validate
./validate.sh validate

# Format check
./validate.sh format

# Validate modules
./validate.sh modules

# Plan
./validate.sh plan development

# Show plan
./validate.sh show-plan
```

## Testing Specific Modules

```bash
# VPC only
terraform plan -var-file=environments/development/terraform.tfvars -target=module.vpc

# EKS only
terraform plan -var-file=environments/development/terraform.tfvars -target=module.eks

# RDS only
terraform plan -var-file=environments/development/terraform.tfvars -target=module.rds

# ECR only
terraform plan -var-file=environments/development/terraform.tfvars -target=module.ecr
```

## Variables

### Required Variables
- `aws_account_id` - AWS account ID

### Optional Variables (with defaults)
- `aws_region` - AWS region (default: us-east-1)
- `project_name` - Project name (default: reservation)
- `environment` - Environment (default: development)
- `vpc_cidr` - VPC CIDR block (default: 10.0.0.0/16)
- `eks_cluster_version` - Kubernetes version (default: 1.28)
- `rds_instance_class` - RDS instance type (default: db.t3.micro)

See `variables.tf` for complete list.

## Outputs

Key outputs include:
- VPC ID and CIDR
- EKS cluster endpoint and certificate
- RDS endpoint and credentials
- ECR repository URLs
- kubectl configuration command

## State Management

### Local State (Development)
```bash
# State stored in terraform.tfstate
# Not recommended for production
```

### Remote State (Production)
```bash
# Configure S3 backend in main.tf
# Uncomment the backend block and update values
```

## Security

- All sensitive data marked as sensitive in outputs
- Security groups with least privilege
- Encryption at rest for RDS
- IAM roles with specific permissions
- VPC Flow Logs for monitoring
- Non-root database users

## Troubleshooting

### Terraform not found
```bash
# Windows
.\setup.ps1

# Linux/macOS
chmod +x setup.sh
./setup.sh
```

### AWS credentials not configured
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

### Module not found
```bash
# Ensure you're in the terraform directory
cd terraform

# Reinitialize
terraform init -upgrade
```

### Plan fails
```bash
# Validate configuration
terraform validate

# Check variables
terraform validate -var-file=environments/development/terraform.tfvars

# Check AWS credentials
aws sts get-caller-identity
```

## Next Steps

1. **Install Terraform** - Run setup script or download manually
2. **Configure AWS** - Run `aws configure`
3. **Initialize** - Run `terraform init -upgrade`
4. **Validate** - Run `terraform validate`
5. **Plan** - Run `terraform plan -var-file=environments/development/terraform.tfvars`
6. **Review** - Check the plan output
7. **Apply** - Run `terraform apply` when ready

## Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Terraform logs: `TF_LOG=DEBUG terraform plan`
3. Check AWS credentials: `aws sts get-caller-identity`
4. Validate configuration: `terraform validate`

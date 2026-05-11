# Step 3: Terraform Basics - Project Structure

## Overview

This step establishes the Terraform project structure for Infrastructure as Code (IaC). We've created a modular, scalable, and maintainable Terraform configuration that can deploy the entire AWS infrastructure for the reservation system.

## Project Structure

```
terraform/
├── .gitignore                          # Terraform-specific gitignore
├── main.tf                             # Main configuration with providers
├── variables.tf                        # Input variables with validation
├── outputs.tf                          # Output values
├── locals.tf                           # Local values and computed variables
├── terraform.tfvars.example            # Example tfvars file
│
├── modules/                            # Reusable modules
│   ├── vpc/                           # VPC module
│   │   ├── main.tf                    # VPC resources
│   │   ├── variables.tf               # VPC variables
│   │   └── outputs.tf                 # VPC outputs
│   │
│   ├── eks/                           # EKS module
│   │   ├── main.tf                    # EKS resources
│   │   ├── variables.tf               # EKS variables
│   │   └── outputs.tf                 # EKS outputs
│   │
│   ├── rds/                           # RDS module
│   │   ├── main.tf                    # RDS resources
│   │   ├── variables.tf               # RDS variables
│   │   └── outputs.tf                 # RDS outputs
│   │
│   └── ecr/                           # ECR module
│       ├── main.tf                    # ECR resources
│       ├── variables.tf               # ECR variables
│       └── outputs.tf                 # ECR outputs
│
└── environments/                       # Environment-specific configs
    ├── development/                   # Development environment
    │   └── README.md
    ├── staging/                       # Staging environment
    │   └── README.md
    └── production/                    # Production environment
        └── README.md
```

## Core Files Explained

### 1. main.tf
**Purpose**: Defines Terraform version, required providers, and provider configuration

**Key Components**:
- Terraform version requirement (>= 1.0)
- AWS provider configuration with default tags
- Kubernetes provider for EKS cluster access
- Helm provider for Kubernetes package management

**Features**:
- Remote state backend configuration (commented out)
- Provider authentication setup
- Default tags for all resources

### 2. variables.tf
**Purpose**: Defines all input variables with validation rules

**Variable Categories**:
- **AWS Configuration**: Region, account ID
- **Project Configuration**: Name, environment
- **VPC Configuration**: CIDR blocks, subnets, availability zones
- **EKS Configuration**: Cluster version, node group sizing
- **RDS Configuration**: Database engine, instance class, storage
- **Database Credentials**: Username, password, database name
- **ECR Configuration**: Image tag mutability, scanning
- **Feature Flags**: NAT Gateway, VPN, Flow Logs, Monitoring

**Validation Examples**:
```hcl
validation {
  condition     = contains(["development", "staging", "production"], var.environment)
  error_message = "Environment must be development, staging, or production."
}
```

### 3. outputs.tf
**Purpose**: Exports important resource values for reference

**Output Categories**:
- VPC outputs (IDs, CIDR blocks, subnet IDs)
- EKS outputs (cluster endpoint, version, certificate authority)
- RDS outputs (endpoint, address, port, credentials)
- ECR outputs (repository URLs, registry IDs)
- Security group outputs
- IAM role outputs
- Kubernetes configuration commands

### 4. locals.tf
**Purpose**: Defines computed values and local variables

**Key Locals**:
- `name_prefix`: Consistent naming convention
- `common_tags`: Tags applied to all resources
- `vpc_config`: VPC configuration object
- `eks_config`: EKS configuration object
- `rds_config`: RDS configuration object
- `ecr_config`: ECR configuration object
- Security group rules
- Resource naming conventions

### 5. terraform.tfvars.example
**Purpose**: Template for environment-specific variables

**Usage**:
```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with your values
```

## Modules

### VPC Module
**Location**: `terraform/modules/vpc/`

**Resources Created**:
- VPC with configurable CIDR block
- Internet Gateway
- Public subnets (with auto-assign public IP)
- Private subnets
- Database subnets
- NAT Gateways (optional)
- Route tables and associations
- VPC Flow Logs (optional)

**Key Features**:
- Multi-AZ support
- Separate route tables for each subnet type
- Optional NAT Gateway for private subnet internet access
- VPC Flow Logs for network monitoring

### EKS Module
**Location**: `terraform/modules/eks/`

**Resources Created**:
- EKS Cluster
- EKS Node Group
- IAM roles and policies for cluster and nodes
- Security groups
- CloudWatch log groups

**Key Features**:
- Configurable Kubernetes version
- Auto-scaling node groups
- Multiple instance types support
- Cluster logging to CloudWatch
- Private and public endpoint options

### RDS Module
**Location**: `terraform/modules/rds/`

**Resources Created**:
- RDS Instance (PostgreSQL)
- DB Subnet Group
- Security Group
- Parameter Group
- CloudWatch Log Group
- Enhanced Monitoring Role (optional)

**Key Features**:
- Storage auto-scaling
- Multi-AZ support (optional)
- Automated backups
- Encryption at rest
- IAM database authentication
- Enhanced monitoring

### ECR Module
**Location**: `terraform/modules/ecr/`

**Resources Created**:
- ECR repositories (API and Frontend)
- Lifecycle policies (keep last 10 images)
- IAM policy for push/pull
- GitHub Actions IAM role (optional)

**Key Features**:
- Image scanning on push
- Image tag mutability
- Automatic cleanup of old images
- GitHub Actions integration support

## Environment Structure

### Development Environment
**Location**: `terraform/environments/development/`

**Characteristics**:
- Smaller instance types (t3.medium)
- Fewer replicas (2 nodes)
- Single-AZ RDS
- 7-day backup retention
- Lower storage allocation

### Staging Environment
**Location**: `terraform/environments/staging/`

**Characteristics**:
- Medium instance types
- 2-3 replicas
- Optional Multi-AZ RDS
- 7-day backup retention
- Medium storage allocation

### Production Environment
**Location**: `terraform/environments/production/`

**Characteristics**:
- Larger instance types
- 3+ replicas
- Multi-AZ RDS
- 30-day backup retention
- Larger storage allocation
- Deletion protection enabled

## File Descriptions

### Module Files

Each module contains:
- `main.tf` - Resource definitions
- `variables.tf` - Module input variables
- `outputs.tf` - Module output values

### Environment Files

Each environment directory contains:
- `README.md` - Environment-specific setup instructions
- `terraform.tfvars` - Environment-specific variable values (not in git)


## 2. Define Basic Infrastructure

### Root-Level Module Calls

We've created root-level configuration files that instantiate all modules:

#### vpc.tf
```hcl
module "vpc" {
  source = "./modules/vpc"
  
  name_prefix = local.name_prefix
  vpc_cidr    = var.vpc_cidr
  
  availability_zones    = var.availability_zones
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
  
  enable_nat_gateway = local.enable_nat_gateway
  enable_flow_logs   = local.enable_flow_logs
  
  tags = local.common_tags
}
```

#### eks.tf
```hcl
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = local.eks_cluster_name
  cluster_version = local.eks_config.cluster_version
  
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  private_subnet_ids  = module.vpc.private_subnet_ids
  
  desired_size   = local.eks_node_group_config.desired_size
  min_size       = local.eks_node_group_config.min_size
  max_size       = local.eks_node_group_config.max_size
  instance_types = local.eks_node_group_config.instance_types
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}
```

#### rds.tf
```hcl
module "rds" {
  source = "./modules/rds"
  
  identifier = local.rds_identifier
  
  vpc_id              = module.vpc.vpc_id
  database_subnet_ids = module.vpc.database_subnet_ids
  allowed_cidr_blocks = var.private_subnet_cidrs
  
  engine         = local.rds_config.engine
  engine_version = local.rds_config.engine_version
  instance_class = local.rds_config.instance_class
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  tags = local.common_tags
  
  depends_on = [module.vpc]
}
```

#### ecr.tf
```hcl
module "ecr" {
  source = "./modules/ecr"
  
  name_prefix = local.name_prefix
  
  api_repository_name      = local.ecr_api_name
  frontend_repository_name = local.ecr_frontend_name
  
  image_tag_mutability = local.ecr_config.image_tag_mutability
  scan_on_push         = local.ecr_config.scan_on_push
  
  aws_account_id = var.aws_account_id
  
  tags = local.common_tags
}
```

### Infrastructure Dependencies

The modules are organized with proper dependencies:

```
VPC (Foundation)
├── EKS (depends on VPC)
├── RDS (depends on VPC)
└── ECR (independent)
```

### Outputs Integration

All module outputs are exposed at the root level for easy access:

```hcl
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  value = module.rds.db_instance_endpoint
}

output "ecr_api_repository_url" {
  value = module.ecr.api_repository_url
}
```

## 3. Test Locally

### Prerequisites

**Required Tools:**
1. **Terraform** (>= 1.0)
   - Download: https://www.terraform.io/downloads.html
   - Verify: `terraform version`

2. **AWS CLI** (>= 2.0)
   - Download: https://aws.amazon.com/cli/
   - Verify: `aws --version`

3. **AWS Credentials**
   - Configure: `aws configure`
   - Verify: `aws sts get-caller-identity`

### Testing Workflow

#### Step 1: Initialize Terraform

```bash
cd terraform
terraform init -upgrade

# This will:
# - Download required providers
# - Create .terraform directory
# - Generate .terraform.lock.hcl
```

#### Step 2: Validate Configuration

```bash
# Validate syntax and structure
terraform validate

# Expected output:
# Success! The configuration is valid.
```

#### Step 3: Format Check

```bash
# Check if code is properly formatted
terraform fmt -check -recursive

# Auto-format if needed
terraform fmt -recursive
```

#### Step 4: Validate Modules

```bash
# Validate each module independently
for module in modules/*/; do
  (cd "$module" && terraform validate)
done
```

#### Step 5: Plan Infrastructure

```bash
# Create a plan for development environment
terraform plan \
  -var-file=environments/development/terraform.tfvars \
  -out=tfplan

# Review the plan
terraform show tfplan
```

#### Step 6: Review Plan Output

```bash
# Count resources to be created
terraform show tfplan | grep "^resource" | wc -l

# Show specific resource types
terraform show tfplan | grep "aws_eks_cluster"
terraform show tfplan | grep "aws_db_instance"
terraform show tfplan | grep "aws_ecr_repository"
```

### Using the Validation Script

```bash
chmod +x terraform/validate.sh

# Run full validation
./terraform/validate.sh full development

# Run specific validation
./terraform/validate.sh init
./terraform/validate.sh validate
./terraform/validate.sh format
./terraform/validate.sh modules
./terraform/validate.sh plan development
./terraform/validate.sh show-plan
```

### Using the Makefile

```bash
cd terraform

# Initialize
make init ENVIRONMENT=development

# Validate
make validate

# Format
make fmt

# Plan
make plan ENVIRONMENT=development

# Test all
make test

# Show outputs
make output

# Show state
make state
```

### Testing Different Environments

#### Development Environment

```bash
terraform plan \
  -var-file=environments/development/terraform.tfvars \
  -out=tfplan-dev

terraform show tfplan-dev
```

#### Staging Environment

```bash
terraform plan \
  -var-file=environments/staging/terraform.tfvars \
  -out=tfplan-staging

terraform show tfplan-staging
```

#### Production Environment

```bash
terraform plan \
  -var-file=environments/production/terraform.tfvars \
  -out=tfplan-prod

terraform show tfplan-prod
```

### Testing Specific Modules

#### Test VPC Only

```bash
terraform plan \
  -var-file=environments/development/terraform.tfvars \
  -target=module.vpc \
  -out=tfplan-vpc

terraform show tfplan-vpc
```

#### Test EKS Only

```bash
terraform plan \
  -var-file=environments/development/terraform.tfvars \
  -target=module.eks \
  -out=tfplan-eks

terraform show tfplan-eks
```

#### Test RDS Only

```bash
terraform plan \
  -var-file=environments/development/terraform.tfvars \
  -target=module.rds \
  -out=tfplan-rds

terraform show tfplan-rds
```

#### Test ECR Only

```bash
terraform plan \
  -var-file=environments/development/terraform.tfvars \
  -target=module.ecr \
  -out=tfplan-ecr

terraform show tfplan-ecr
```

### Common Issues and Solutions

#### Issue: "Provider not found"

**Error:**
```
Error: Failed to query available provider packages
```

**Solution:**
```bash
terraform init -upgrade
```

#### Issue: "Invalid variable"

**Error:**
```
Error: Unsupported argument
```

**Solution:**
1. Check variable names in `variables.tf`
2. Verify `terraform.tfvars` syntax
3. Run `terraform validate`

#### Issue: "Module not found"

**Error:**
```
Error: Module not found
```

**Solution:**
```bash
# Ensure module directories exist
ls -la modules/

# Verify module paths in root configuration
grep "source =" *.tf
```

#### Issue: "AWS credentials not found"

**Error:**
```
Error: error configuring Terraform AWS Provider: no valid credential sources for Terraform AWS Provider found
```

**Solution:**
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Verify credentials
aws sts get-caller-identity
```

### Cleanup

```bash
# Remove plan files
rm -f tfplan*

# Remove Terraform state (local only)
rm -f terraform.tfstate*

# Remove Terraform cache
rm -rf .terraform
rm -f .terraform.lock.hcl
```

## Next Steps

1. **Set up remote state** - Configure S3 backend for state management
2. **Enable state locking** - Use DynamoDB for locking
3. **Add monitoring modules** - CloudWatch, Prometheus, Grafana
4. **Create CI/CD integration** - GitHub Actions for Terraform
5. **Deploy to AWS** - Apply Terraform to create infrastructure

## Usage

### Initialize Terraform
```bash
cd terraform
terraform init
```

### Validate Configuration
```bash
terraform validate
```

### Format Code
```bash
terraform fmt -recursive
```

### Plan Deployment
```bash
terraform plan -var-file=environments/development/terraform.tfvars
```

### Apply Configuration
```bash
terraform apply -var-file=environments/development/terraform.tfvars
```

### Destroy Infrastructure
```bash
terraform destroy -var-file=environments/development/terraform.tfvars
```

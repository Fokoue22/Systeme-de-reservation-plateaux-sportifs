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

## Key Features

### 1. Modular Design
- Reusable modules for VPC, EKS, RDS, ECR
- Easy to extend and maintain
- Clear separation of concerns

### 2. Input Validation
- Variable validation rules
- Type checking
- Range validation for numeric values

### 3. Tagging Strategy
- Common tags applied to all resources
- Environment-specific tags
- Cost allocation tags

### 4. Security
- Non-root database users
- Encrypted storage
- Security groups with least privilege
- IAM roles with specific permissions
- VPC Flow Logs for monitoring

### 5. High Availability
- Multi-AZ support for RDS
- Multiple availability zones for subnets
- Auto-scaling for EKS nodes
- NAT Gateways for redundancy

### 6. Monitoring
- CloudWatch logs for EKS cluster
- CloudWatch logs for RDS
- VPC Flow Logs
- Enhanced RDS monitoring

## File Descriptions

### Root Level Files

| File | Purpose |
|------|---------|
| `main.tf` | Provider configuration and Terraform setup |
| `variables.tf` | Input variables with validation |
| `outputs.tf` | Output values for infrastructure |
| `locals.tf` | Local computed values |
| `terraform.tfvars.example` | Example variable values |
| `.gitignore` | Terraform-specific ignore patterns |

### Module Files

Each module contains:
- `main.tf` - Resource definitions
- `variables.tf` - Module input variables
- `outputs.tf` - Module output values

### Environment Files

Each environment directory contains:
- `README.md` - Environment-specific setup instructions
- `terraform.tfvars` - Environment-specific variable values (not in git)

## Commits Made

1. `feat: add .gitignore for Terraform directory`
2. `feat: add Terraform main configuration with providers`
3. `feat: add Terraform variables with validation rules`
4. `feat: add Terraform outputs for infrastructure resources`
5. `feat: add Terraform locals for configuration management`
6. `feat: add terraform.tfvars.example with default values`
7. `feat: add VPC module main configuration`
8. `feat: add VPC module variables`
9. `feat: add VPC module outputs`
10. `feat: add EKS module main configuration`
11. `feat: add EKS module variables`
12. `feat: add EKS module outputs`
13. `feat: add RDS module main configuration`
14. `feat: add RDS module variables`
15. `feat: add RDS module outputs`
16. `feat: add ECR module main configuration`
17. `feat: add ECR module variables`
18. `feat: add ECR module outputs`
19. `feat: add development environment README`
20. `feat: add staging environment README`
21. `feat: add production environment README`

## Next Steps

1. **Implement root-level module calls** - Create the main infrastructure configuration
2. **Set up remote state** - Configure S3 backend for state management
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

## Best Practices Implemented

✅ **Modular Structure** - Reusable modules for each component
✅ **Input Validation** - Variables validated at declaration
✅ **Consistent Naming** - Name prefix convention for all resources
✅ **Tagging Strategy** - Common tags for cost allocation and management
✅ **Security** - Encryption, security groups, IAM roles
✅ **Documentation** - Comments and README files
✅ **Environment Separation** - Dev, staging, production configs
✅ **State Management** - Remote state backend support
✅ **Scalability** - Easy to add new modules or resources
✅ **Monitoring** - CloudWatch integration

## Files Created

- ✅ `terraform/.gitignore`
- ✅ `terraform/main.tf`
- ✅ `terraform/variables.tf`
- ✅ `terraform/outputs.tf`
- ✅ `terraform/locals.tf`
- ✅ `terraform/terraform.tfvars.example`
- ✅ `terraform/modules/vpc/main.tf`
- ✅ `terraform/modules/vpc/variables.tf`
- ✅ `terraform/modules/vpc/outputs.tf`
- ✅ `terraform/modules/eks/main.tf`
- ✅ `terraform/modules/eks/variables.tf`
- ✅ `terraform/modules/eks/outputs.tf`
- ✅ `terraform/modules/rds/main.tf`
- ✅ `terraform/modules/rds/variables.tf`
- ✅ `terraform/modules/rds/outputs.tf`
- ✅ `terraform/modules/ecr/main.tf`
- ✅ `terraform/modules/ecr/variables.tf`
- ✅ `terraform/modules/ecr/outputs.tf`
- ✅ `terraform/environments/development/README.md`
- ✅ `terraform/environments/staging/README.md`
- ✅ `terraform/environments/production/README.md`

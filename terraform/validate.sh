#!/bin/bash

# Terraform Validation Script
# This script validates the Terraform configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if terraform is installed
check_terraform() {
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed"
        echo "Install from: https://www.terraform.io/downloads.html"
        exit 1
    fi
    
    TERRAFORM_VERSION=$(terraform version | head -1)
    log_info "Found: $TERRAFORM_VERSION"
}

# Initialize Terraform
init_terraform() {
    log_info "Initializing Terraform..."
    terraform init -upgrade
    log_info "Terraform initialized successfully"
}

# Validate configuration
validate_config() {
    log_info "Validating Terraform configuration..."
    terraform validate
    log_info "Configuration is valid"
}

# Format check
format_check() {
    log_info "Checking Terraform formatting..."
    terraform fmt -check -recursive
    log_info "Formatting is correct"
}

# Plan infrastructure
plan_infrastructure() {
    local environment=${1:-development}
    log_info "Planning infrastructure for $environment environment..."
    
    if [ ! -f "environments/$environment/terraform.tfvars" ]; then
        log_error "terraform.tfvars not found for $environment environment"
        log_info "Copy from example: cp environments/$environment/terraform.tfvars.example environments/$environment/terraform.tfvars"
        exit 1
    fi
    
    terraform plan -var-file=environments/$environment/terraform.tfvars -out=tfplan
    log_info "Plan saved to tfplan"
}

# Show plan
show_plan() {
    log_info "Showing Terraform plan..."
    terraform show tfplan
}

# Validate modules
validate_modules() {
    log_info "Validating modules..."
    
    for module in modules/*/; do
        module_name=$(basename "$module")
        log_info "Validating $module_name module..."
        (cd "$module" && terraform validate)
    done
    
    log_info "All modules validated successfully"
}

# Main execution
main() {
    local command=${1:-validate}
    local environment=${2:-development}
    
    log_info "Starting Terraform validation..."
    
    check_terraform
    
    case $command in
        init)
            init_terraform
            ;;
        validate)
            validate_config
            ;;
        format)
            format_check
            ;;
        modules)
            validate_modules
            ;;
        plan)
            init_terraform
            validate_config
            plan_infrastructure "$environment"
            ;;
        show-plan)
            show_plan
            ;;
        full)
            init_terraform
            validate_config
            format_check
            validate_modules
            plan_infrastructure "$environment"
            log_info "Full validation completed successfully!"
            ;;
        *)
            echo "Usage: $0 {init|validate|format|modules|plan|show-plan|full} [environment]"
            echo ""
            echo "Commands:"
            echo "  init       - Initialize Terraform"
            echo "  validate   - Validate configuration"
            echo "  format     - Check formatting"
            echo "  modules    - Validate all modules"
            echo "  plan       - Plan infrastructure"
            echo "  show-plan  - Show the plan"
            echo "  full       - Run all validations"
            echo ""
            echo "Examples:"
            echo "  $0 init"
            echo "  $0 validate"
            echo "  $0 plan development"
            echo "  $0 full production"
            exit 1
            ;;
    esac
    
    log_info "Validation completed successfully!"
}

# Run main function
main "$@"

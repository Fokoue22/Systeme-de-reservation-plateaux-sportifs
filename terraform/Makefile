.PHONY: help init validate fmt plan apply destroy clean test

# Variables
ENVIRONMENT ?= development
TF_VARS = -var-file=environments/$(ENVIRONMENT)/terraform.tfvars
TF_DIR = .

help:
	@echo "Terraform Management Commands"
	@echo "=============================="
	@echo ""
	@echo "Usage: make [target] ENVIRONMENT=<environment>"
	@echo ""
	@echo "Targets:"
	@echo "  init       - Initialize Terraform"
	@echo "  validate   - Validate Terraform configuration"
	@echo "  fmt        - Format Terraform code"
	@echo "  plan       - Plan infrastructure changes"
	@echo "  apply      - Apply infrastructure changes"
	@echo "  destroy    - Destroy infrastructure"
	@echo "  clean      - Clean Terraform files"
	@echo "  test       - Run all validation tests"
	@echo "  output     - Show Terraform outputs"
	@echo "  state      - Show Terraform state"
	@echo ""
	@echo "Examples:"
	@echo "  make init ENVIRONMENT=development"
	@echo "  make plan ENVIRONMENT=development"
	@echo "  make apply ENVIRONMENT=production"

init:
	@echo "Initializing Terraform for $(ENVIRONMENT) environment..."
	terraform init -upgrade

validate:
	@echo "Validating Terraform configuration..."
	terraform validate

fmt:
	@echo "Formatting Terraform code..."
	terraform fmt -recursive

plan:
	@echo "Planning infrastructure changes for $(ENVIRONMENT) environment..."
	terraform plan $(TF_VARS) -out=tfplan

apply:
	@echo "Applying infrastructure changes for $(ENVIRONMENT) environment..."
	@echo "WARNING: This will create/modify AWS resources!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		terraform apply tfplan; \
	else \
		echo "Apply cancelled"; \
	fi

destroy:
	@echo "Destroying infrastructure for $(ENVIRONMENT) environment..."
	@echo "WARNING: This will DELETE all AWS resources!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		terraform destroy $(TF_VARS); \
	else \
		echo "Destroy cancelled"; \
	fi

clean:
	@echo "Cleaning Terraform files..."
	rm -rf .terraform
	rm -f .terraform.lock.hcl
	rm -f tfplan
	rm -f terraform.tfstate*
	@echo "Clean complete"

test: validate fmt
	@echo "Running Terraform tests..."
	@echo "✓ Validation passed"
	@echo "✓ Formatting checked"

output:
	@echo "Terraform outputs for $(ENVIRONMENT) environment:"
	terraform output -json

state:
	@echo "Terraform state for $(ENVIRONMENT) environment:"
	terraform state list

lock:
	@echo "Creating .terraform.lock.hcl..."
	terraform init -upgrade

unlock:
	@echo "Removing .terraform.lock.hcl..."
	rm -f .terraform.lock.hcl

.DEFAULT_GOAL := help

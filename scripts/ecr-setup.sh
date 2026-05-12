#!/bin/bash

# ECR Setup Script
# Creates ECR repositories with proper configuration

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-671765845629}

echo "=========================================="
echo "ECR Repository Setup"
echo "=========================================="
echo "Region: $AWS_REGION"
echo "Account: $AWS_ACCOUNT_ID"
echo "=========================================="

# Create API Repository
echo ""
echo "Creating API repository..."
aws ecr create-repository \
  --repository-name reservation-api \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability IMMUTABLE \
  --tags Key=Environment,Value=development Key=Project,Value=reservation \
  2>/dev/null || echo "API repository already exists"

# Create Frontend Repository
echo "Creating Frontend repository..."
aws ecr create-repository \
  --repository-name reservation-frontend \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability IMMUTABLE \
  --tags Key=Environment,Value=development Key=Project,Value=reservation \
  2>/dev/null || echo "Frontend repository already exists"

# Set API Lifecycle Policy
echo ""
echo "Setting API repository lifecycle policy..."
cat > /tmp/api-lifecycle-policy.json << 'EOF'
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    },
    {
      "rulePriority": 2,
      "description": "Expire untagged images after 7 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF

aws ecr put-lifecycle-policy \
  --repository-name reservation-api \
  --lifecycle-policy-text file:///tmp/api-lifecycle-policy.json \
  --region $AWS_REGION

# Set Frontend Lifecycle Policy
echo "Setting Frontend repository lifecycle policy..."
cat > /tmp/frontend-lifecycle-policy.json << 'EOF'
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    },
    {
      "rulePriority": 2,
      "description": "Expire untagged images after 7 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF

aws ecr put-lifecycle-policy \
  --repository-name reservation-frontend \
  --lifecycle-policy-text file:///tmp/frontend-lifecycle-policy.json \
  --region $AWS_REGION

# Verify repositories
echo ""
echo "=========================================="
echo "Repositories Created:"
echo "=========================================="
aws ecr describe-repositories \
  --region $AWS_REGION \
  --query 'repositories[?contains(repositoryName, `reservation`)][repositoryName,repositoryUri]' \
  --output table

echo ""
echo "✓ ECR Setup Complete!"

#!/bin/bash

# ECR Cleanup Script
# Deletes ECR repositories and images

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
FORCE=${FORCE:-false}

echo "=========================================="
echo "ECR Cleanup"
echo "=========================================="
echo "Region: $AWS_REGION"
echo "Force Delete: $FORCE"
echo "=========================================="

# Function to delete repository
delete_repository() {
  local repo_name=$1
  
  echo ""
  echo "Deleting repository: $repo_name"
  
  if [ "$FORCE" = "true" ]; then
    aws ecr delete-repository \
      --repository-name $repo_name \
      --force \
      --region $AWS_REGION \
      2>/dev/null && echo "✓ Repository deleted: $repo_name" || echo "✗ Failed to delete: $repo_name"
  else
    # Delete images first
    echo "Deleting images in $repo_name..."
    local image_ids=$(aws ecr describe-images \
      --repository-name $repo_name \
      --region $AWS_REGION \
      --query 'imageDetails[*].imageId' \
      --output text 2>/dev/null)
    
    if [ -n "$image_ids" ]; then
      aws ecr batch-delete-image \
        --repository-name $repo_name \
        --image-ids $image_ids \
        --region $AWS_REGION \
        2>/dev/null && echo "✓ Images deleted from $repo_name"
    fi
    
    # Delete repository
    aws ecr delete-repository \
      --repository-name $repo_name \
      --region $AWS_REGION \
      2>/dev/null && echo "✓ Repository deleted: $repo_name" || echo "✗ Failed to delete: $repo_name"
  fi
}

# Delete repositories
delete_repository "reservation-api"
delete_repository "reservation-frontend"

# Verify deletion
echo ""
echo "=========================================="
echo "Remaining Repositories:"
echo "=========================================="
aws ecr describe-repositories \
  --region $AWS_REGION \
  --query 'repositories[?contains(repositoryName, `reservation`)].repositoryName' \
  --output text || echo "No repositories found"

echo ""
echo "✓ ECR Cleanup Complete!"

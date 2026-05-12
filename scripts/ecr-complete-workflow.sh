#!/bin/bash

# Complete ECR Workflow Script
# Handles login, build, and push in one command

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-671765845629}
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
IMAGE_TAG=${IMAGE_TAG:-latest}
VERSION=${VERSION:-v1.0.0}

echo "=========================================="
echo "ECR Complete Workflow"
echo "=========================================="
echo "Region: $AWS_REGION"
echo "Account: $AWS_ACCOUNT_ID"
echo "Registry: $ECR_REGISTRY"
echo "Image Tag: $IMAGE_TAG"
echo "Version: $VERSION"
echo "=========================================="

# Step 1: Login
echo ""
echo "Step 1: Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY
echo "✓ Login successful"

# Step 2: Build
echo ""
echo "Step 2: Building Docker images..."
docker build \
  -f Dockerfile.api \
  -t reservation-api:$IMAGE_TAG \
  -t $ECR_REGISTRY/reservation-api:$IMAGE_TAG \
  -t $ECR_REGISTRY/reservation-api:$VERSION \
  .
echo "✓ API image built"

docker build \
  -f Dockerfile.frontend \
  -t reservation-frontend:$IMAGE_TAG \
  -t $ECR_REGISTRY/reservation-frontend:$IMAGE_TAG \
  -t $ECR_REGISTRY/reservation-frontend:$VERSION \
  .
echo "✓ Frontend image built"

# Step 3: Push
echo ""
echo "Step 3: Pushing images to ECR..."
docker push $ECR_REGISTRY/reservation-api:$IMAGE_TAG
docker push $ECR_REGISTRY/reservation-api:$VERSION
echo "✓ API image pushed"

docker push $ECR_REGISTRY/reservation-frontend:$IMAGE_TAG
docker push $ECR_REGISTRY/reservation-frontend:$VERSION
echo "✓ Frontend image pushed"

# Step 4: Verify
echo ""
echo "Step 4: Verifying images in ECR..."
echo ""
echo "API Repository:"
aws ecr describe-images \
  --repository-name reservation-api \
  --region $AWS_REGION \
  --query 'imageDetails[*].[imageTags,imageSizeInBytes,imagePushedAt]' \
  --output table

echo ""
echo "Frontend Repository:"
aws ecr describe-images \
  --repository-name reservation-frontend \
  --region $AWS_REGION \
  --query 'imageDetails[*].[imageTags,imageSizeInBytes,imagePushedAt]' \
  --output table

echo ""
echo "=========================================="
echo "✓ ECR Workflow Complete!"
echo "=========================================="

#!/bin/bash

# Push Docker Images to ECR Script
# Pushes API and Frontend images to ECR repositories

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-671765845629}
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
IMAGE_TAG=${IMAGE_TAG:-latest}
VERSION=${VERSION:-v1.0.0}

echo "Pushing Docker images to ECR..."
echo "Registry: $ECR_REGISTRY"
echo "Image Tag: $IMAGE_TAG"
echo "Version: $VERSION"
echo ""

# Push API image
echo "Pushing API image..."
docker push $ECR_REGISTRY/reservation-api:$IMAGE_TAG
docker push $ECR_REGISTRY/reservation-api:$VERSION

# Push Frontend image
echo "Pushing Frontend image..."
docker push $ECR_REGISTRY/reservation-frontend:$IMAGE_TAG
docker push $ECR_REGISTRY/reservation-frontend:$VERSION

echo ""
echo "✓ Images pushed successfully"

# Verify
echo ""
echo "API Repository Images:"
aws ecr describe-images \
  --repository-name reservation-api \
  --region $AWS_REGION \
  --query 'imageDetails[*].[imageTags,imageSizeInBytes]' \
  --output table

echo ""
echo "Frontend Repository Images:"
aws ecr describe-images \
  --repository-name reservation-frontend \
  --region $AWS_REGION \
  --query 'imageDetails[*].[imageTags,imageSizeInBytes]' \
  --output table

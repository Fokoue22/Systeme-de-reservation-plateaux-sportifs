#!/bin/bash

# Build Docker Images Script
# Builds API and Frontend images with ECR tags

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-671765845629}
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
IMAGE_TAG=${IMAGE_TAG:-latest}
VERSION=${VERSION:-v1.0.0}

echo "Building Docker images..."
echo "Registry: $ECR_REGISTRY"
echo "Image Tag: $IMAGE_TAG"
echo "Version: $VERSION"
echo ""

# Build API image
echo "Building API image..."
docker build \
  -f Dockerfile.api \
  -t reservation-api:$IMAGE_TAG \
  -t $ECR_REGISTRY/reservation-api:$IMAGE_TAG \
  -t $ECR_REGISTRY/reservation-api:$VERSION \
  .

# Build Frontend image
echo "Building Frontend image..."
docker build \
  -f Dockerfile.frontend \
  -t reservation-frontend:$IMAGE_TAG \
  -t $ECR_REGISTRY/reservation-frontend:$IMAGE_TAG \
  -t $ECR_REGISTRY/reservation-frontend:$VERSION \
  .

echo ""
echo "✓ Images built successfully"
echo ""
docker images | grep reservation

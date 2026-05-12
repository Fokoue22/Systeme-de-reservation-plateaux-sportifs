# Step 4: Set Up Container Registry (ECR)

## Overview

This step focuses on setting up AWS Elastic Container Registry (ECR) for storing and managing Docker images. We'll create ECR repositories, configure authentication, build and push Docker images, and implement image lifecycle policies.

## 1. Create ECR Repositories

### Using AWS CLI

#### Create API Repository

```bash
aws ecr create-repository \
  --repository-name reservation-api \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability IMMUTABLE \
  --tags Key=Environment,Value=development Key=Project,Value=reservation
```

**Output:**
```json
{
  "repository": {
    "repositoryArn": "arn:aws:ecr:us-east-1:671765845629:repository/reservation-api",
    "registryId": "671765845629",
    "repositoryName": "reservation-api",
    "repositoryUri": "671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api",
    "createdAt": "2026-05-11T...",
    "imageTagMutability": "IMMUTABLE",
    "imageScanningConfiguration": {
      "scanOnPush": true
    }
  }
}
```

#### Create Frontend Repository

```bash
aws ecr create-repository \
  --repository-name reservation-frontend \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability IMMUTABLE \
  --tags Key=Environment,Value=development Key=Project,Value=reservation
```

### Verify Repositories

```bash
# List all repositories
aws ecr describe-repositories \
  --region us-east-1 \
  --query 'repositories[*].[repositoryName,repositoryUri]' \
  --output table
```

**Expected Output:**
```
|  repositoryName      |  repositoryUri                                                    |
|----------------------|-------------------------------------------------------------------|
|  reservation-api     |  671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api     |
|  reservation-frontend|  671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-frontend|
```

## 2. Configure Docker Authentication

### Login to ECR

```bash
# Get login token and authenticate Docker
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 671765845629.dkr.ecr.us-east-1.amazonaws.com
```

**Expected Output:**
```
Login Succeeded
```

### Create Authentication Script

Create `scripts/ecr-login.sh`:

```bash
#!/bin/bash

# ECR Login Script
# Authenticates Docker with AWS ECR

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-671765845629}

echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "✓ Successfully logged in to ECR"
```

Make it executable:
```bash
chmod +x scripts/ecr-login.sh
```

## 3. Build Docker Images

### Build API Image

```bash
# Build API image
docker build \
  -f Dockerfile.api \
  -t reservation-api:latest \
  -t 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api:latest \
  -t 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api:v1.0.0 \
  .

# Verify image
docker images | grep reservation-api
```

### Build Frontend Image

```bash
# Build frontend image
docker build \
  -f Dockerfile.frontend \
  -t reservation-frontend:latest \
  -t 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-frontend:latest \
  -t 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-frontend:v1.0.0 \
  .

# Verify image
docker images | grep reservation-frontend
```

### Create Build Script

Create `scripts/build-images.sh`:

```bash
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

echo "✓ Images built successfully"
docker images | grep reservation
```

Make it executable:
```bash
chmod +x scripts/build-images.sh
```

## 4. Push Images to ECR

### Push API Image

```bash
# Push API image
docker push 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api:latest
docker push 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api:v1.0.0

# Verify push
aws ecr describe-images \
  --repository-name reservation-api \
  --region us-east-1 \
  --query 'imageDetails[*].[imageTags,imageSizeInBytes,imagePushedAt]' \
  --output table
```

### Push Frontend Image

```bash
# Push frontend image
docker push 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-frontend:latest
docker push 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-frontend:v1.0.0

# Verify push
aws ecr describe-images \
  --repository-name reservation-frontend \
  --region us-east-1 \
  --query 'imageDetails[*].[imageTags,imageSizeInBytes,imagePushedAt]' \
  --output table
```

### Create Push Script

Create `scripts/push-images.sh`:

```bash
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

# Push API image
echo "Pushing API image..."
docker push $ECR_REGISTRY/reservation-api:$IMAGE_TAG
docker push $ECR_REGISTRY/reservation-api:$VERSION

# Push Frontend image
echo "Pushing Frontend image..."
docker push $ECR_REGISTRY/reservation-frontend:$IMAGE_TAG
docker push $ECR_REGISTRY/reservation-frontend:$VERSION

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
```

Make it executable:
```bash
chmod +x scripts/push-images.sh
```

## 5. Image Lifecycle Policies

### Set API Repository Lifecycle Policy

```bash
# Create lifecycle policy JSON
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

# Apply policy
aws ecr put-lifecycle-policy \
  --repository-name reservation-api \
  --lifecycle-policy-text file:///tmp/api-lifecycle-policy.json \
  --region us-east-1
```

### Set Frontend Repository Lifecycle Policy

```bash
# Create lifecycle policy JSON
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

# Apply policy
aws ecr put-lifecycle-policy \
  --repository-name reservation-frontend \
  --lifecycle-policy-text file:///tmp/frontend-lifecycle-policy.json \
  --region us-east-1
```

### Verify Lifecycle Policies

```bash
# Get API repository lifecycle policy
aws ecr get-lifecycle-policy \
  --repository-name reservation-api \
  --region us-east-1 \
  --query 'lifecyclePolicyText' \
  --output text | jq .

# Get Frontend repository lifecycle policy
aws ecr get-lifecycle-policy \
  --repository-name reservation-frontend \
  --region us-east-1 \
  --query 'lifecyclePolicyText' \
  --output text | jq .
```

## 6. Image Scanning

### Enable Image Scanning

Images are automatically scanned on push (configured during repository creation).

### View Scan Results

```bash
# Get scan findings for API images
aws ecr describe-image-scan-findings \
  --repository-name reservation-api \
  --image-id imageTag=latest \
  --region us-east-1 \
  --query 'imageScanFindings.[imageScanStatus.status,findingSeverityCounts]' \
  --output table

# Get scan findings for Frontend images
aws ecr describe-image-scan-findings \
  --repository-name reservation-frontend \
  --image-id imageTag=latest \
  --region us-east-1 \
  --query 'imageScanFindings.[imageScanStatus.status,findingSeverityCounts]' \
  --output table
```

## 7. Complete Workflow Script

Create `scripts/ecr-complete-workflow.sh`:

```bash
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
```

Make it executable:
```bash
chmod +x scripts/ecr-complete-workflow.sh
```

## 8. Usage Examples

### Quick Start

```bash
# Login to ECR
./scripts/ecr-login.sh

# Build images
./scripts/build-images.sh

# Push images
./scripts/push-images.sh
```

### Complete Workflow

```bash
# Run complete workflow
./scripts/ecr-complete-workflow.sh

# With custom version
IMAGE_TAG=v2.0.0 VERSION=v2.0.0 ./scripts/ecr-complete-workflow.sh
```

### Manual Steps

```bash
# 1. Login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 671765845629.dkr.ecr.us-east-1.amazonaws.com

# 2. Build
docker build -f Dockerfile.api -t 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api:latest .
docker build -f Dockerfile.frontend -t 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-frontend:latest .

# 3. Push
docker push 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api:latest
docker push 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-frontend:latest

# 4. Verify
aws ecr describe-images --repository-name reservation-api --region us-east-1
aws ecr describe-images --repository-name reservation-frontend --region us-east-1
```

## 9. Cleanup

### Delete Images

```bash
# Delete specific image tag
aws ecr batch-delete-image \
  --repository-name reservation-api \
  --image-ids imageTag=v1.0.0 \
  --region us-east-1

# Delete all images in repository
aws ecr batch-delete-image \
  --repository-name reservation-api \
  --image-ids $(aws ecr describe-images --repository-name reservation-api --query 'imageDetails[*].imageId' --output text | awk '{for(i=1;i<=NF;i++) print "imageTag="$i}') \
  --region us-east-1
```

### Delete Repositories

```bash
# Delete API repository (must be empty)
aws ecr delete-repository \
  --repository-name reservation-api \
  --region us-east-1

# Delete Frontend repository (must be empty)
aws ecr delete-repository \
  --repository-name reservation-frontend \
  --region us-east-1

# Force delete with images
aws ecr delete-repository \
  --repository-name reservation-api \
  --force \
  --region us-east-1

aws ecr delete-repository \
  --repository-name reservation-frontend \
  --force \
  --region us-east-1
```

## Key Concepts

### Image Tag Mutability
- **IMMUTABLE**: Once pushed, image tags cannot be overwritten
- **MUTABLE**: Image tags can be overwritten (default)
- **Best Practice**: Use IMMUTABLE for production

### Image Scanning
- Automatically scans images on push
- Detects vulnerabilities in image layers
- Integrates with AWS Security Hub

### Lifecycle Policies
- Automatically delete old images
- Reduce storage costs
- Keep repositories clean

### Repository Naming
- Use lowercase letters, numbers, hyphens, underscores
- Organize by project/environment: `project-environment-service`
- Example: `reservation-development-api`

## Next Steps

1. **Integrate with CI/CD** - Automate image builds and pushes
2. **Set up image signing** - Sign images for security
3. **Configure cross-account access** - Share images across AWS accounts
4. **Implement image retention policies** - Manage storage costs
5. **Deploy to EKS** - Pull images from ECR and deploy to Kubernetes


# ECR (Elastic Container Registry) Scripts

This directory contains scripts for managing Docker images in AWS ECR.

## Quick Start

### 1. Setup ECR Repositories

```bash
bash ecr-setup.sh
```

This creates:
- `reservation-api` repository
- `reservation-frontend` repository
- Lifecycle policies for both repositories
- Image scanning enabled

### 2. Complete Workflow (Login → Build → Push)

```bash
bash ecr-complete-workflow.sh
```

Or with custom version:
```bash
IMAGE_TAG=v2.0.0 VERSION=v2.0.0 bash ecr-complete-workflow.sh
```

### 3. Individual Steps

#### Login to ECR
```bash
bash ecr-login.sh
```

#### Build Images
```bash
bash build-images.sh
```

Or with custom tags:
```bash
IMAGE_TAG=v2.0.0 VERSION=v2.0.0 bash build-images.sh
```

#### Push Images
```bash
bash push-images.sh
```

Or with custom tags:
```bash
IMAGE_TAG=v2.0.0 VERSION=v2.0.0 bash push-images.sh
```

### 4. Cleanup

```bash
bash ecr-cleanup.sh
```

Or force delete:
```bash
FORCE=true bash ecr-cleanup.sh
```

## Using Makefile

From the scripts directory:

```bash
# Show help
make -f Makefile.ecr help

# Setup repositories
make -f Makefile.ecr setup

# Complete workflow
make -f Makefile.ecr workflow

# Verify images
make -f Makefile.ecr verify

# Cleanup
make -f Makefile.ecr cleanup
```

## Environment Variables

All scripts support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_ACCOUNT_ID` | `671765845629` | AWS account ID |
| `IMAGE_TAG` | `latest` | Docker image tag |
| `VERSION` | `v1.0.0` | Image version |
| `FORCE` | `false` | Force delete in cleanup |

### Example with Custom Variables

```bash
AWS_REGION=us-west-2 IMAGE_TAG=v2.0.0 bash ecr-complete-workflow.sh
```

## Scripts Description

### ecr-setup.sh
Creates ECR repositories with:
- Image scanning on push
- Immutable image tags
- Lifecycle policies (keep last 10 images, expire untagged after 7 days)
- Development environment tags

### ecr-login.sh
Authenticates Docker with AWS ECR using temporary credentials.

### build-images.sh
Builds Docker images for API and Frontend with ECR registry tags.

### push-images.sh
Pushes built images to ECR repositories and verifies the push.

### ecr-complete-workflow.sh
Combines all steps: login → build → push → verify

### ecr-cleanup.sh
Deletes images and repositories. Supports force delete option.

## Workflow Examples

### Development Workflow

```bash
# Initial setup
bash ecr-setup.sh

# Build and push new version
IMAGE_TAG=dev bash ecr-complete-workflow.sh

# Verify
aws ecr describe-images --repository-name reservation-api
```

### Release Workflow

```bash
# Build and push release version
IMAGE_TAG=v1.0.0 VERSION=v1.0.0 bash ecr-complete-workflow.sh

# Tag as latest
docker tag 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api:v1.0.0 \
           671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api:latest
docker push 671765845629.dkr.ecr.us-east-1.amazonaws.com/reservation-api:latest
```

### CI/CD Integration

```bash
#!/bin/bash
# In your CI/CD pipeline

set -e

# Setup
bash scripts/ecr-setup.sh

# Build and push
IMAGE_TAG=$CI_COMMIT_SHA VERSION=$CI_COMMIT_TAG bash scripts/ecr-complete-workflow.sh

# Verify
bash scripts/ecr-verify.sh
```

## Troubleshooting

### "Login Succeeded" but push fails

**Problem**: Docker login succeeded but push fails with authentication error.

**Solution**:
```bash
# Re-login
bash ecr-login.sh

# Verify credentials
aws sts get-caller-identity
```

### "Repository already exists"

**Problem**: Repository creation fails because it already exists.

**Solution**: This is expected and safe. The script continues with lifecycle policy setup.

### "Image not found"

**Problem**: Push fails with "image not found".

**Solution**:
```bash
# Verify image was built
docker images | grep reservation

# Rebuild if needed
bash build-images.sh
```

### "Access Denied"

**Problem**: AWS API calls fail with access denied.

**Solution**:
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check IAM permissions for ECR
aws iam get-user
```

## AWS CLI Commands Reference

### List Repositories
```bash
aws ecr describe-repositories --region us-east-1
```

### List Images in Repository
```bash
aws ecr describe-images --repository-name reservation-api --region us-east-1
```

### Get Repository URI
```bash
aws ecr describe-repositories \
  --repository-name reservation-api \
  --query 'repositories[0].repositoryUri' \
  --output text
```

### Get Image Details
```bash
aws ecr describe-images \
  --repository-name reservation-api \
  --image-ids imageTag=latest \
  --region us-east-1
```

### Delete Image
```bash
aws ecr batch-delete-image \
  --repository-name reservation-api \
  --image-ids imageTag=v1.0.0 \
  --region us-east-1
```

### Delete Repository
```bash
aws ecr delete-repository \
  --repository-name reservation-api \
  --force \
  --region us-east-1
```

## Best Practices

1. **Use Immutable Tags**: Prevents accidental overwrites
2. **Implement Lifecycle Policies**: Automatically clean up old images
3. **Enable Image Scanning**: Detect vulnerabilities
4. **Tag Consistently**: Use semantic versioning (v1.0.0)
5. **Use Latest Tag**: For development, use `latest` tag
6. **Monitor Repository Size**: Check storage costs
7. **Implement Access Control**: Use IAM policies
8. **Sign Images**: For production deployments

## Next Steps

1. **Integrate with CI/CD**: Automate image builds and pushes
2. **Deploy to EKS**: Pull images from ECR and deploy to Kubernetes
3. **Set up Image Signing**: Sign images for security
4. **Configure Cross-Account Access**: Share images across AWS accounts
5. **Implement Image Retention**: Manage storage costs


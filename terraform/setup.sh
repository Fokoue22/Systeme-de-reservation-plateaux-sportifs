#!/bin/bash

# Terraform Setup Script for Linux/macOS
# This script downloads and installs Terraform

set -e

TERRAFORM_VERSION="${1:-1.7.0}"
INSTALL_PATH="${2:-/usr/local/bin}"

echo "Terraform Setup Script"
echo "====================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    ARCH="amd64"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="darwin"
    # Check if Apple Silicon
    if [[ $(uname -m) == "arm64" ]]; then
        ARCH="arm64"
    else
        ARCH="amd64"
    fi
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS ($ARCH)"
echo ""

# Download URL
DOWNLOAD_URL="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_${OS}_${ARCH}.zip"
ZIP_PATH="/tmp/terraform_${TERRAFORM_VERSION}.zip"
EXTRACT_PATH="/tmp/terraform_${TERRAFORM_VERSION}"

echo "Downloading Terraform $TERRAFORM_VERSION..."
echo "URL: $DOWNLOAD_URL"
echo ""

# Download
if ! curl -fsSL -o "$ZIP_PATH" "$DOWNLOAD_URL"; then
    echo "✗ Failed to download Terraform"
    exit 1
fi

echo "✓ Downloaded successfully to $ZIP_PATH"
echo ""

# Extract
echo "Extracting Terraform..."

if ! unzip -q -o "$ZIP_PATH" -d "$EXTRACT_PATH"; then
    echo "✗ Failed to extract Terraform"
    exit 1
fi

echo "✓ Extracted successfully to $EXTRACT_PATH"
echo ""

# Check if terraform executable exists
if [ ! -f "$EXTRACT_PATH/terraform" ]; then
    echo "✗ Terraform executable not found"
    exit 1
fi

echo "✓ Terraform executable found"
echo ""

# Check if we need sudo
if [ ! -w "$INSTALL_PATH" ]; then
    echo "Installing to $INSTALL_PATH requires sudo"
    sudo cp "$EXTRACT_PATH/terraform" "$INSTALL_PATH/terraform"
    sudo chmod +x "$INSTALL_PATH/terraform"
else
    cp "$EXTRACT_PATH/terraform" "$INSTALL_PATH/terraform"
    chmod +x "$INSTALL_PATH/terraform"
fi

echo "✓ Terraform installed to $INSTALL_PATH/terraform"
echo ""

# Verify installation
echo "Verifying Terraform installation..."
terraform version

echo ""
echo "✓ Terraform installed successfully!"
echo ""
echo "Next steps:"
echo "1. cd terraform"
echo "2. terraform init -upgrade"
echo "3. terraform validate"
echo "4. terraform plan -var-file=environments/development/terraform.tfvars"
echo ""

# Cleanup
rm -f "$ZIP_PATH"
rm -rf "$EXTRACT_PATH"

echo "Setup complete!"

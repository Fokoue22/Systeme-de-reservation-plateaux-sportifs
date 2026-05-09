#!/bin/bash

# Kubernetes Cleanup Script
# This script removes all resources from the Kubernetes cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="reservation"

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

confirm() {
    local prompt="$1"
    local response
    
    read -p "$prompt (yes/no): " response
    
    if [[ "$response" == "yes" ]]; then
        return 0
    else
        return 1
    fi
}

cleanup_namespace() {
    log_info "Deleting namespace $NAMESPACE..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        kubectl delete namespace "$NAMESPACE" --wait=true
        log_info "Namespace $NAMESPACE deleted"
    else
        log_warn "Namespace $NAMESPACE does not exist"
    fi
}

cleanup_pvc() {
    log_info "Cleaning up PersistentVolumeClaims..."
    
    kubectl delete pvc --all -n "$NAMESPACE" 2>/dev/null || true
    log_info "PersistentVolumeClaims cleaned up"
}

cleanup_images() {
    log_info "Removing Docker images..."
    
    docker rmi reservation-api:latest 2>/dev/null || true
    docker rmi reservation-frontend:latest 2>/dev/null || true
    
    log_info "Docker images removed"
}

# Main execution
main() {
    log_warn "This will delete all resources in the $NAMESPACE namespace!"
    
    if ! confirm "Are you sure you want to continue?"; then
        log_info "Cleanup cancelled"
        exit 0
    fi
    
    log_info "Starting cleanup..."
    
    cleanup_namespace
    cleanup_pvc
    
    if confirm "Do you want to remove Docker images as well?"; then
        cleanup_images
    fi
    
    log_info "Cleanup completed!"
}

# Run main function
main "$@"

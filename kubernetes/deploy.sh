#!/bin/bash

# Kubernetes Deployment Script
# This script deploys the entire reservation system to Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="reservation"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
API_IMAGE="${API_IMAGE:-reservation-api:latest}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-reservation-frontend:latest}"

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

build_images() {
    log_info "Building Docker images..."
    
    docker build -f Dockerfile.api -t "$API_IMAGE" .
    docker build -f Dockerfile.frontend -t "$FRONTEND_IMAGE" .
    
    log_info "Docker images built successfully"
}

load_images_to_minikube() {
    if command -v minikube &> /dev/null; then
        log_info "Loading images to Minikube..."
        minikube image load "$API_IMAGE"
        minikube image load "$FRONTEND_IMAGE"
        log_info "Images loaded to Minikube"
    fi
}

create_namespace() {
    log_info "Creating namespace..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warn "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_info "Namespace $NAMESPACE created"
    fi
}

deploy_configmap() {
    log_info "Deploying ConfigMap..."
    kubectl apply -f kubernetes/configmap.yaml
    log_info "ConfigMap deployed"
}

deploy_secrets() {
    log_info "Deploying Secrets..."
    kubectl apply -f kubernetes/secrets.yaml
    log_info "Secrets deployed"
}

deploy_postgres() {
    log_info "Deploying PostgreSQL..."
    kubectl apply -f kubernetes/postgres/
    
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app=reservation,component=database \
        -n "$NAMESPACE" \
        --timeout=300s
    
    log_info "PostgreSQL deployed and ready"
}

deploy_api() {
    log_info "Deploying API..."
    kubectl apply -f kubernetes/api/
    
    log_info "Waiting for API to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app=reservation,component=api \
        -n "$NAMESPACE" \
        --timeout=300s
    
    log_info "API deployed and ready"
}

deploy_frontend() {
    log_info "Deploying Frontend..."
    kubectl apply -f kubernetes/frontend/
    
    log_info "Waiting for Frontend to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app=reservation,component=frontend \
        -n "$NAMESPACE" \
        --timeout=300s
    
    log_info "Frontend deployed and ready"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    echo ""
    echo "Pods:"
    kubectl get pods -n "$NAMESPACE"
    
    echo ""
    echo "Services:"
    kubectl get svc -n "$NAMESPACE"
    
    echo ""
    echo "Deployments:"
    kubectl get deployments -n "$NAMESPACE"
    
    echo ""
    echo "Ingress:"
    kubectl get ingress -n "$NAMESPACE"
}

print_access_info() {
    log_info "Deployment completed successfully!"
    
    echo ""
    echo "Access Information:"
    echo "==================="
    
    if command -v minikube &> /dev/null; then
        MINIKUBE_IP=$(minikube ip)
        echo "Minikube IP: $MINIKUBE_IP"
        echo "Frontend: http://$MINIKUBE_IP"
        echo "API: http://$MINIKUBE_IP:8000"
    else
        echo "Frontend: http://localhost (via port-forward)"
        echo "API: http://localhost:8000 (via port-forward)"
    fi
    
    echo ""
    echo "Port Forward Commands:"
    echo "====================="
    echo "Frontend: kubectl port-forward svc/frontend-service 8080:80 -n $NAMESPACE"
    echo "API: kubectl port-forward svc/api-service 8000:8000 -n $NAMESPACE"
    echo "PostgreSQL: kubectl port-forward svc/postgres-service 5432:5432 -n $NAMESPACE"
}

# Main execution
main() {
    log_info "Starting Kubernetes deployment..."
    
    check_prerequisites
    build_images
    load_images_to_minikube
    create_namespace
    deploy_configmap
    deploy_secrets
    deploy_postgres
    deploy_api
    deploy_frontend
    verify_deployment
    print_access_info
    
    log_info "Deployment completed!"
}

# Run main function
main "$@"

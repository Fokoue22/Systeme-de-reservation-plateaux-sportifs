# Kubernetes Setup Guide

## Prerequisites

### Option 1: Docker Desktop (Recommended for Windows)

1. **Enable Kubernetes in Docker Desktop**:
   - Open Docker Desktop
   - Go to Settings → Kubernetes
   - Check "Enable Kubernetes"
   - Click "Apply & Restart"
   - Wait for Kubernetes to start (5-10 minutes)

2. **Verify Installation**:
```bash
kubectl cluster-info
kubectl get nodes
```

### Option 2: Minikube (Alternative)

1. **Install Minikube**:
```bash
# Using Chocolatey (Windows)
choco install minikube

# Or download from: https://minikube.sigs.k8s.io/docs/start/
```

2. **Start Minikube**:
```bash
minikube start --cpus=4 --memory=8192 --driver=docker
```

3. **Verify Installation**:
```bash
minikube status
kubectl cluster-info
```

## Kubernetes Cluster Structure

```
┌─────────────────────────────────────────────────────────┐
│              Kubernetes Cluster                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │         reservation Namespace                     │   │
│  │                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Frontend Pod │  │  API Pod     │             │   │
│  │  │  (Nginx)     │  │  (FastAPI)   │             │   │
│  │  └──────────────┘  └──────────────┘             │   │
│  │         │                  │                     │   │
│  │         └──────────────────┘                     │   │
│  │                  │                               │   │
│  │         ┌────────▼────────┐                      │   │
│  │         │  PostgreSQL Pod  │                     │   │
│  │         │   (Database)     │                     │   │
│  │         └──────────────────┘                     │   │
│  │                                                   │   │
│  │  Services:                                        │   │
│  │  ├── frontend-service (ClusterIP)               │   │
│  │  ├── api-service (ClusterIP)                    │   │
│  │  ├── postgres-service (ClusterIP)               │   │
│  │  └── frontend-ingress (Ingress)                 │   │
│  │                                                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
kubernetes/
├── README.md                          # This file
├── namespace.yaml                     # Namespace definition
├── configmap.yaml                     # Configuration
├── secrets.yaml                       # Secrets (base64 encoded)
├── postgres/
│   ├── pvc.yaml                      # Persistent Volume Claim
│   ├── deployment.yaml               # PostgreSQL Deployment
│   └── service.yaml                  # PostgreSQL Service
├── api/
│   ├── deployment.yaml               # API Deployment
│   ├── service.yaml                  # API Service
│   ├── hpa.yaml                      # Horizontal Pod Autoscaler
│   └── pdb.yaml                      # Pod Disruption Budget
├── frontend/
│   ├── deployment.yaml               # Frontend Deployment
│   ├── service.yaml                  # Frontend Service
│   ├── ingress.yaml                  # Ingress Controller
│   └── hpa.yaml                      # Horizontal Pod Autoscaler
└── kustomization.yaml                # Kustomize configuration
```

## Quick Start

### 1. Build Docker Images

```bash
# Build API image
docker build -f Dockerfile.api -t reservation-api:latest .

# Build Frontend image
docker build -f Dockerfile.frontend -t reservation-frontend:latest .

# Tag for local Kubernetes (if using Minikube)
# minikube image load reservation-api:latest
# minikube image load reservation-frontend:latest
```

### 2. Create Namespace

```bash
kubectl apply -f kubernetes/namespace.yaml
```

### 3. Create ConfigMap and Secrets

```bash
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secrets.yaml
```

### 4. Deploy PostgreSQL

```bash
kubectl apply -f kubernetes/postgres/
```

### 5. Deploy API

```bash
kubectl apply -f kubernetes/api/
```

### 6. Deploy Frontend

```bash
kubectl apply -f kubernetes/frontend/
```

### 7. Verify Deployment

```bash
# Check all resources
kubectl get all -n reservation

# Check pods
kubectl get pods -n reservation

# Check services
kubectl get svc -n reservation

# Check ingress
kubectl get ingress -n reservation
```

## Accessing the Application

### Using Docker Desktop Kubernetes

```bash
# Get the frontend service
kubectl get svc frontend-service -n reservation

# Port forward to access locally
kubectl port-forward svc/frontend-service 8080:80 -n reservation

# Access at http://localhost:8080
```

### Using Minikube

```bash
# Get the Minikube IP
minikube ip

# Port forward
kubectl port-forward svc/frontend-service 8080:80 -n reservation

# Or use Minikube service command
minikube service frontend-service -n reservation
```

## Useful Commands

```bash
# View logs
kubectl logs -f deployment/api -n reservation
kubectl logs -f deployment/frontend -n reservation
kubectl logs -f deployment/postgres -n reservation

# Describe resources
kubectl describe pod <pod-name> -n reservation
kubectl describe deployment api -n reservation

# Execute commands in pod
kubectl exec -it <pod-name> -n reservation -- /bin/bash

# Port forward
kubectl port-forward svc/api-service 8000:8000 -n reservation
kubectl port-forward svc/frontend-service 8080:80 -n reservation

# Scale deployment
kubectl scale deployment api --replicas=3 -n reservation

# Delete resources
kubectl delete -f kubernetes/
kubectl delete namespace reservation

# Watch resources
kubectl get pods -n reservation -w
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n reservation

# Check logs
kubectl logs <pod-name> -n reservation

# Check events
kubectl get events -n reservation
```

### Image pull errors

```bash
# For Docker Desktop: images should be available automatically
# For Minikube: load images manually
minikube image load reservation-api:latest
minikube image load reservation-frontend:latest
```

### Database connection issues

```bash
# Check PostgreSQL pod
kubectl logs deployment/postgres -n reservation

# Connect to PostgreSQL
kubectl exec -it deployment/postgres -n reservation -- \
  psql -U reservation_user -d reservation_db
```

### Service not accessible

```bash
# Check service endpoints
kubectl get endpoints -n reservation

# Check service configuration
kubectl describe svc api-service -n reservation

# Test connectivity between pods
kubectl exec -it deployment/api -n reservation -- \
  curl http://postgres-service:5432
```

## Next Steps

1. Deploy to local Kubernetes
2. Test all services
3. Set up monitoring (Prometheus + Grafana)
4. Configure logging (ELK Stack)
5. Deploy to AWS EKS

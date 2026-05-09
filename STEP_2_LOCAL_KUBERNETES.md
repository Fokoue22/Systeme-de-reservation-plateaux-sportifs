# Step 2: Set Up Local Kubernetes

## Overview

This step sets up a complete Kubernetes cluster locally for testing and development. We'll deploy the separated services (Frontend, API, Database) to Kubernetes using manifests and scripts.

## Prerequisites

### Required Tools

1. **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
   - Version: 20.10+
   - Kubernetes enabled in Docker Desktop

2. **kubectl** (Kubernetes CLI)
   - Version: 1.24+
   - Installation: https://kubernetes.io/docs/tasks/tools/

3. **Minikube** (Optional, for Linux users)
   - Installation: https://minikube.sigs.k8s.io/docs/start/

### Verify Installation

```bash
# Check Docker
docker --version
docker ps

# Check kubectl
kubectl version --client
kubectl cluster-info

# Check Minikube (if using)
minikube status
```

## Architecture

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
│  │  │  Replicas: 2 │  │  Replicas: 2 │             │   │
│  │  └──────────────┘  └──────────────┘             │   │
│  │         │                  │                     │   │
│  │         └──────────────────┘                     │   │
│  │                  │                               │   │
│  │         ┌────────▼────────┐                      │   │
│  │         │  PostgreSQL Pod  │                     │   │
│  │         │   (Database)     │                     │   │
│  │         │  Replicas: 1     │                     │   │
│  │         └──────────────────┘                     │   │
│  │                                                   │   │
│  │  Services:                                        │   │
│  │  ├── frontend-service (ClusterIP:80)            │   │
│  │  ├── api-service (ClusterIP:8000)               │   │
│  │  ├── postgres-service (ClusterIP:5432)          │   │
│  │  └── frontend-ingress (Ingress)                 │   │
│  │                                                   │   │
│  │  Auto-scaling:                                    │   │
│  │  ├── API HPA (2-5 replicas)                     │   │
│  │  └── Frontend HPA (2-4 replicas)                │   │
│  │                                                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
kubernetes/
├── README.md                          # Setup guide
├── namespace.yaml                     # Namespace definition
├── configmap.yaml                     # Configuration
├── secrets.yaml                       # Secrets
├── kustomization.yaml                 # Kustomize config
├── deploy.sh                          # Deployment script
├── cleanup.sh                         # Cleanup script
├── postgres/
│   ├── pvc.yaml                      # Persistent Volume Claim
│   ├── deployment.yaml               # PostgreSQL Deployment
│   └── service.yaml                  # PostgreSQL Service
├── api/
│   ├── deployment.yaml               # API Deployment
│   ├── service.yaml                  # API Service
│   ├── hpa.yaml                      # Horizontal Pod Autoscaler
│   ├── pdb.yaml                      # Pod Disruption Budget
│   └── rbac.yaml                     # RBAC configuration
└── frontend/
    ├── deployment.yaml               # Frontend Deployment
    ├── service.yaml                  # Frontend Service
    ├── ingress.yaml                  # Ingress Controller
    └── hpa.yaml                      # Horizontal Pod Autoscaler
```

## Quick Start

### Step 1: Enable Kubernetes in Docker Desktop

**For Windows/Mac:**
1. Open Docker Desktop
2. Go to Settings → Kubernetes
3. Check "Enable Kubernetes"
4. Click "Apply & Restart"
5. Wait 5-10 minutes for Kubernetes to start

**Verify:**
```bash
kubectl cluster-info
kubectl get nodes
```

### Step 2: Build Docker Images

```bash
# Build API image
docker build -f Dockerfile.api -t reservation-api:latest .

# Build Frontend image
docker build -f Dockerfile.frontend -t reservation-frontend:latest .

# Verify images
docker images | grep reservation
```

### Step 3: Deploy to Kubernetes

**Option A: Using the deployment script (Recommended)**

```bash
# Make script executable (Linux/Mac)
chmod +x kubernetes/deploy.sh

# Run deployment
./kubernetes/deploy.sh

# Or on Windows PowerShell
bash kubernetes/deploy.sh
```

**Option B: Manual deployment**

```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Deploy configuration
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secrets.yaml

# Deploy PostgreSQL
kubectl apply -f kubernetes/postgres/

# Deploy API
kubectl apply -f kubernetes/api/

# Deploy Frontend
kubectl apply -f kubernetes/frontend/
```

**Option C: Using Kustomize**

```bash
# Deploy all resources
kubectl apply -k kubernetes/

# Or with specific overlays
kustomize build kubernetes/ | kubectl apply -f -
```

### Step 4: Verify Deployment

```bash
# Check all resources
kubectl get all -n reservation

# Check pods
kubectl get pods -n reservation -w

# Check services
kubectl get svc -n reservation

# Check ingress
kubectl get ingress -n reservation

# Check events
kubectl get events -n reservation
```

## Accessing the Application

### Port Forwarding

```bash
# Frontend (in one terminal)
kubectl port-forward svc/frontend-service 8080:80 -n reservation

# API (in another terminal)
kubectl port-forward svc/api-service 8000:8000 -n reservation

# PostgreSQL (optional)
kubectl port-forward svc/postgres-service 5432:5432 -n reservation
```

Then access:
- Frontend: http://localhost:8080
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Using Minikube Service

```bash
# Get Minikube IP
minikube ip

# Open service in browser
minikube service frontend-service -n reservation

# Or port forward
kubectl port-forward svc/frontend-service 8080:80 -n reservation
```

## Kubernetes Resources Explained

### Namespace
- **File**: `namespace.yaml`
- **Purpose**: Isolates resources for the reservation system
- **Benefits**: Resource quotas, RBAC, easier management

### ConfigMap
- **File**: `configmap.yaml`
- **Purpose**: Stores non-sensitive configuration
- **Contains**: Environment variables, Nginx config

### Secrets
- **File**: `secrets.yaml`
- **Purpose**: Stores sensitive data (passwords, keys)
- **Contains**: Database credentials, API keys

### PostgreSQL Deployment
- **Files**: `postgres/deployment.yaml`, `postgres/service.yaml`, `postgres/pvc.yaml`
- **Replicas**: 1 (stateful)
- **Storage**: 10Gi PersistentVolume
- **Health Checks**: Liveness and readiness probes

### API Deployment
- **Files**: `api/deployment.yaml`, `api/service.yaml`, `api/hpa.yaml`, `api/pdb.yaml`, `api/rbac.yaml`
- **Replicas**: 2-5 (auto-scaled)
- **Health Checks**: Liveness, readiness, startup probes
- **Auto-scaling**: CPU 70%, Memory 80%
- **Pod Disruption Budget**: Minimum 1 pod available

### Frontend Deployment
- **Files**: `frontend/deployment.yaml`, `frontend/service.yaml`, `frontend/ingress.yaml`, `frontend/hpa.yaml`
- **Replicas**: 2-4 (auto-scaled)
- **Health Checks**: Liveness and readiness probes
- **Auto-scaling**: CPU 75%, Memory 85%
- **Ingress**: External access via HTTP

## Useful Commands

### Viewing Resources

```bash
# List all resources
kubectl get all -n reservation

# List specific resource type
kubectl get pods -n reservation
kubectl get svc -n reservation
kubectl get deployments -n reservation
kubectl get ingress -n reservation

# Watch resources in real-time
kubectl get pods -n reservation -w

# Describe resource
kubectl describe pod <pod-name> -n reservation
kubectl describe deployment api -n reservation
```

### Viewing Logs

```bash
# View pod logs
kubectl logs <pod-name> -n reservation

# View logs from deployment
kubectl logs deployment/api -n reservation

# Follow logs in real-time
kubectl logs -f deployment/api -n reservation

# View logs from all pods in deployment
kubectl logs -l app=reservation,component=api -n reservation
```

### Executing Commands

```bash
# Execute command in pod
kubectl exec -it <pod-name> -n reservation -- /bin/bash

# Execute command in deployment
kubectl exec -it deployment/api -n reservation -- /bin/bash

# Connect to PostgreSQL
kubectl exec -it deployment/postgres -n reservation -- \
  psql -U reservation_user -d reservation_db
```

### Scaling

```bash
# Scale deployment
kubectl scale deployment api --replicas=3 -n reservation

# Check HPA status
kubectl get hpa -n reservation
kubectl describe hpa api-hpa -n reservation
```

### Port Forwarding

```bash
# Forward service port
kubectl port-forward svc/frontend-service 8080:80 -n reservation

# Forward pod port
kubectl port-forward pod/<pod-name> 8000:8000 -n reservation

# Forward with specific address
kubectl port-forward --address 0.0.0.0 svc/api-service 8000:8000 -n reservation
```

### Debugging

```bash
# Get pod events
kubectl describe pod <pod-name> -n reservation

# Get namespace events
kubectl get events -n reservation

# Check resource usage
kubectl top pods -n reservation
kubectl top nodes

# Get pod YAML
kubectl get pod <pod-name> -n reservation -o yaml

# Edit resource
kubectl edit deployment api -n reservation
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n reservation

# Check logs
kubectl logs <pod-name> -n reservation

# Check events
kubectl get events -n reservation --sort-by='.lastTimestamp'
```

### Image pull errors

```bash
# For Docker Desktop: images should be available automatically
# For Minikube: load images manually
minikube image load reservation-api:latest
minikube image load reservation-frontend:latest

# Verify images in Minikube
minikube image ls
```

### Database connection issues

```bash
# Check PostgreSQL pod
kubectl logs deployment/postgres -n reservation

# Connect to PostgreSQL
kubectl exec -it deployment/postgres -n reservation -- \
  psql -U reservation_user -d reservation_db

# Check database service
kubectl get svc postgres-service -n reservation
kubectl describe svc postgres-service -n reservation
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

### HPA not scaling

```bash
# Check HPA status
kubectl describe hpa api-hpa -n reservation

# Check metrics server
kubectl get deployment metrics-server -n kube-system

# View current metrics
kubectl top pods -n reservation
```

## Cleanup

### Remove all resources

```bash
# Using cleanup script
chmod +x kubernetes/cleanup.sh
./kubernetes/cleanup.sh

# Or manually
kubectl delete namespace reservation

# Or using Kustomize
kubectl delete -k kubernetes/
```

### Remove Docker images

```bash
docker rmi reservation-api:latest
docker rmi reservation-frontend:latest
```

## Next Steps

1. **Test the deployment**: Access the application via port forwarding
2. **Monitor resources**: Use `kubectl top` and `kubectl describe`
3. **Scale services**: Test HPA by generating load
4. **Set up monitoring**: Install Prometheus and Grafana
5. **Configure logging**: Set up ELK Stack
6. **Deploy to AWS EKS**: Use Terraform to create production cluster

## Files Created

- ✅ `kubernetes/README.md` - Setup guide
- ✅ `kubernetes/namespace.yaml` - Namespace
- ✅ `kubernetes/configmap.yaml` - Configuration
- ✅ `kubernetes/secrets.yaml` - Secrets
- ✅ `kubernetes/postgres/pvc.yaml` - Database storage
- ✅ `kubernetes/postgres/deployment.yaml` - Database deployment
- ✅ `kubernetes/postgres/service.yaml` - Database service
- ✅ `kubernetes/api/deployment.yaml` - API deployment
- ✅ `kubernetes/api/service.yaml` - API service
- ✅ `kubernetes/api/hpa.yaml` - API auto-scaling
- ✅ `kubernetes/api/pdb.yaml` - API availability
- ✅ `kubernetes/api/rbac.yaml` - API permissions
- ✅ `kubernetes/frontend/deployment.yaml` - Frontend deployment
- ✅ `kubernetes/frontend/service.yaml` - Frontend service
- ✅ `kubernetes/frontend/ingress.yaml` - Frontend ingress
- ✅ `kubernetes/frontend/hpa.yaml` - Frontend auto-scaling
- ✅ `kubernetes/deploy.sh` - Deployment script
- ✅ `kubernetes/cleanup.sh` - Cleanup script
- ✅ `kubernetes/kustomization.yaml` - Kustomize config

## Commits

1. `docs: add Kubernetes setup guide and cluster architecture`
2. `feat: add Kubernetes namespace definition`
3. `feat: add ConfigMap for application and Nginx configuration`
4. `feat: add Kubernetes Secrets for sensitive data`
5. `feat: add PostgreSQL PersistentVolumeClaim`
6. `feat: add PostgreSQL Deployment with health checks and resource limits`
7. `feat: add PostgreSQL Service for internal cluster communication`
8. `feat: add API Deployment with health probes and resource management`
9. `feat: add API Service for internal cluster communication`
10. `feat: add HorizontalPodAutoscaler for API auto-scaling`
11. `feat: add PodDisruptionBudget for API availability`
12. `feat: add RBAC for API service account`
13. `feat: add Frontend Deployment with Nginx configuration`
14. `feat: add Frontend Service for internal cluster communication`
15. `feat: add Ingress for external access to frontend`
16. `feat: add HorizontalPodAutoscaler for Frontend auto-scaling`
17. `feat: add deployment script for Kubernetes`
18. `feat: add cleanup script for Kubernetes resources`
19. `feat: add Kustomization for declarative resource management`

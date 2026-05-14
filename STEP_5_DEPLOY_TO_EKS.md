# Step 5: Deploy to EKS

## Overview

This step focuses on deploying the Reservation System to Amazon EKS (Elastic Kubernetes Service) using Helm charts. We'll create production-ready Helm charts for both the API and Frontend services with proper configuration, security, and scalability.

## Part 1: Create Helm Charts for Your Services

### Helm Chart Structure

```
.
├── Chart.yaml                  # Chart metadata
├── values.yaml               # Default values
├── values-dev.yaml          # Development values
├── values-prod.yaml         # Production values
├── README.md                 # This file
└── templates/
    ├── _helpers.tpl         # Template helpers
    ├── namespace.yaml       # Namespace
    ├── api-deployment.yaml  # API deployment
    ├── api-service.yaml     # API service
    ├── api-serviceaccount.yaml
    ├── api-hpa.yaml         # API autoscaler
    ├── frontend-deployment.yaml
    ├── frontend-service.yaml
    ├── frontend-serviceaccount.yaml
    ├── frontend-hpa.yaml    # Frontend autoscaler
    ├── ingress.yaml         # Ingress
    ├── networkpolicy.yaml   # Network policies
    └── rbac.yaml            # RBAC
```

### Chart.yaml

The main chart metadata file that defines:
- Chart name and version
- Application version
- Chart description
- Maintainer information
- Home and source URLs

**Key Fields:**
```yaml
apiVersion: v2                          # Helm 3 format
name: reservation-system               # Chart name
description: Reservation System Helm Chart
type: application                       # Application chart (not library)
version: 1.0.0                         # Chart version
appVersion: "1.0.0"                    # Application version
```

### values.yaml

Default configuration values for the Helm chart. Organized by service:

#### Global Configuration
```yaml
global:
  environment: development
  domain: reservation.local
  registry: 671765845629.dkr.ecr.us-east-1.amazonaws.com
  imagePullPolicy: IfNotPresent
```

#### API Service Configuration
```yaml
api:
  enabled: true
  name: reservation-api
  replicaCount: 2
  image:
    repository: reservation-api
    tag: latest
  service:
    type: ClusterIP
    port: 8000
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 5
    targetCPUUtilizationPercentage: 80
```

#### Frontend Service Configuration
```yaml
frontend:
  enabled: true
  name: reservation-frontend
  replicaCount: 2
  image:
    repository: reservation-frontend
    tag: latest
  service:
    type: ClusterIP
    port: 80
```

### Template Files

#### 1. Namespace Template (namespace.yaml)

Creates a dedicated Kubernetes namespace for the application:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: reservation-system
  labels:
    app: reservation-system
```

**Purpose**: Isolate application resources from other workloads

#### 2. API Deployment Template (api-deployment.yaml)

Defines the API service deployment with:
- Container specification
- Resource requests and limits
- Health probes (liveness, readiness, startup)
- Security context
- Volume mounts

**Key Features:**
- Non-root user execution (UID 1000)
- Read-only root filesystem
- Dropped Linux capabilities
- Temporary volume for runtime files

#### 3. API Service Template (api-service.yaml)

Exposes the API deployment:
- Service type: ClusterIP
- Port: 8000
- Selector: app=reservation-api

#### 4. API ServiceAccount (api-serviceaccount.yaml)

Creates a service account for RBAC:
- Used by API pods
- Bound to specific roles

#### 5. API HPA Template (api-hpa.yaml)

Horizontal Pod Autoscaler for API:
- Min replicas: 2
- Max replicas: 5
- CPU target: 80%
- Memory target: 80%

**Scaling Behavior:**
- Scale up: 100% increase per 30 seconds
- Scale down: 50% decrease per 60 seconds

#### 6. Frontend Deployment Template (frontend-deployment.yaml)

Similar to API deployment but for Nginx frontend:
- Non-root user (UID 101 - nginx user)
- Nginx-specific volumes (cache, run)
- Lighter resource requirements

#### 7. Frontend Service Template (frontend-service.yaml)

Exposes the Frontend deployment:
- Service type: ClusterIP
- Port: 80
- Selector: app=reservation-frontend

#### 8. Frontend ServiceAccount (frontend-serviceaccount.yaml)

Service account for Frontend pods

#### 9. Frontend HPA Template (frontend-hpa.yaml)

Horizontal Pod Autoscaler for Frontend:
- Min replicas: 2
- Max replicas: 5
- Same scaling behavior as API

#### 10. Ingress Template (ingress.yaml)

Exposes services externally:
- Nginx ingress controller
- TLS termination
- Path-based routing

**Routes:**
- `/` → Frontend (reservation.local)
- `/api` → API (api.reservation.local)

#### 11. NetworkPolicy Template (networkpolicy.yaml)

Implements network security:
- Default deny all traffic
- Allow API ← Frontend
- Allow Frontend ← Ingress
- Allow DNS egress

#### 12. RBAC Template (rbac.yaml)

Role-based access control:
- API role: read configmaps, read secrets
- Frontend role: read configmaps
- RoleBindings for both services

#### 13. Template Helpers (_helpers.tpl)

Reusable template functions:
- Chart name generation
- Full name generation
- Common labels
- Selector labels

## Configuration Examples

### Development Environment

```yaml
# values-dev.yaml
global:
  environment: development
  registry: 671765845629.dkr.ecr.us-east-1.amazonaws.com

api:
  replicaCount: 1
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 200m
      memory: 256Mi
  autoscaling:
    minReplicas: 1
    maxReplicas: 2

frontend:
  replicaCount: 1
  resources:
    requests:
      cpu: 25m
      memory: 32Mi
    limits:
      cpu: 100m
      memory: 128Mi
```

### Production Environment

```yaml
# values-prod.yaml
global:
  environment: production
  registry: 671765845629.dkr.ecr.us-east-1.amazonaws.com

api:
  replicaCount: 3
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi
  autoscaling:
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

frontend:
  replicaCount: 3
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
```

## Helm Chart Features

### 1. Templating

All templates use Helm templating syntax:
- `{{ .Values.api.name }}` - Access values
- `{{ .Release.Name }}` - Release name
- `{{ .Chart.Name }}` - Chart name
- `{{- if .Values.api.enabled }}` - Conditional rendering

### 2. Conditional Rendering

Services can be enabled/disabled:
```yaml
{{- if .Values.api.enabled }}
# API resources
{{- end }}
```

### 3. Resource Management

Requests and limits for CPU and memory:
```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 4. Health Checks

Three types of probes:
- **Liveness**: Restart if unhealthy
- **Readiness**: Remove from load balancer if not ready
- **Startup**: Wait for startup before other probes

### 5. Security

- Non-root user execution
- Read-only root filesystem
- Dropped Linux capabilities
- Network policies
- RBAC

### 6. Scalability

- Horizontal Pod Autoscaler
- Resource-based scaling
- Configurable min/max replicas

## Validation

### Lint the Chart

```bash
helm lint helm/
```

### Validate Templates

```bash
helm template reservation helm/
```

### Dry Run

```bash
helm install reservation helm/ --dry-run --debug
```

## Next Steps

1. **Part 2: Deploy to EKS** - Apply Helm charts to EKS cluster
2. **Part 3: Configure Ingress** - Set up ingress controller
3. **Part 4: Implement Monitoring** - Add Prometheus and Grafana
4. **Part 5: Setup CI/CD** - Automate deployments

## File Descriptions

### Core Files

| File | Purpose |
|------|---------|
| `Chart.yaml` | Chart metadata and version |
| `values.yaml` | Default configuration values |
| `templates/_helpers.tpl` | Reusable template functions |




# Reservation System Helm Chart

Production-ready Helm chart for deploying the Reservation System to Kubernetes.

## Quick Start

### Prerequisites

- Kubernetes 1.20+
- Helm 3.0+
- Docker images pushed to ECR

### Installation

#### Development Environment

```bash
helm install reservation . \
  -f values-dev.yaml \
  --namespace reservation-dev \
  --create-namespace
```

#### Production Environment

```bash
helm install reservation . \
  -f values-prod.yaml \
  --namespace reservation-prod \
  --create-namespace
```

### Verification

```bash
# Check deployment status
kubectl get deployments -n reservation-dev
kubectl get pods -n reservation-dev
kubectl get services -n reservation-dev

# Check ingress
kubectl get ingress -n reservation-dev

# View logs
kubectl logs -n reservation-dev -l app=reservation-api
kubectl logs -n reservation-dev -l app=reservation-frontend
```

## Configuration

### Global Settings

```yaml
global:
  environment: development
  domain: reservation.local
  registry: 671765845629.dkr.ecr.us-east-1.amazonaws.com
  imagePullPolicy: IfNotPresent
```

### API Configuration

```yaml
api:
  enabled: true
  replicaCount: 2
  image:
    repository: reservation-api
    tag: latest
  service:
    type: ClusterIP
    port: 8000
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
```

### Frontend Configuration

```yaml
frontend:
  enabled: true
  replicaCount: 2
  image:
    repository: reservation-frontend
    tag: latest
  service:
    type: ClusterIP
    port: 80
```

## Customization

### Override Values

```bash
helm install reservation . \
  -f values-dev.yaml \
  --set api.replicaCount=3 \
  --set frontend.replicaCount=2
```

### Create Custom Values File

```bash
cp values.yaml values-custom.yaml
# Edit values-custom.yaml
helm install reservation . -f values-custom.yaml
```

## Helm Commands

### Lint

```bash
helm lint .
```

### Template

```bash
helm template reservation .
helm template reservation . -f values-dev.yaml
```

### Dry Run

```bash
helm install reservation . --dry-run --debug
helm install reservation . -f values-dev.yaml --dry-run --debug
```

### Install

```bash
helm install reservation . -f values-dev.yaml
```

### Upgrade

```bash
helm upgrade reservation . -f values-dev.yaml
```

### Rollback

```bash
helm rollback reservation 1
```

### Uninstall

```bash
helm uninstall reservation
```

### List Releases

```bash
helm list
helm list -n reservation-dev
```

### Get Values

```bash
helm get values reservation
helm get values reservation -n reservation-dev
```

### Get Manifest

```bash
helm get manifest reservation
helm get manifest reservation -n reservation-dev
```

## Chart Structure

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


## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n reservation-dev

# Check logs
kubectl logs <pod-name> -n reservation-dev

# Check events
kubectl get events -n reservation-dev
```

### Service not accessible

```bash
# Check service
kubectl get svc -n reservation-dev

# Check endpoints
kubectl get endpoints -n reservation-dev

# Test connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
# Inside pod: wget http://reservation-api:8000
```

### Ingress not working

```bash
# Check ingress
kubectl get ingress -n reservation-dev

# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress logs
kubectl logs -n ingress-nginx <ingress-controller-pod>
```

### Autoscaler not scaling

```bash
# Check HPA status
kubectl get hpa -n reservation-dev

# Check HPA details
kubectl describe hpa reservation-api -n reservation-dev

# Check metrics
kubectl top pods -n reservation-dev
kubectl top nodes
```

## Environment-Specific Deployments

### Development

```bash
helm install reservation . \
  -f values-dev.yaml \
  --namespace reservation-dev \
  --create-namespace
```

**Characteristics:**
- 1 replica per service
- Lower resource requests
- Autoscaling: 1-2 replicas
- Network policies disabled
- Monitoring disabled

### Production

```bash
helm install reservation . \
  -f values-prod.yaml \
  --namespace reservation-prod \
  --create-namespace
```

**Characteristics:**
- 3 replicas per service
- Higher resource requests
- Autoscaling: 3-10 replicas
- Network policies enabled
- Monitoring enabled
- Pod anti-affinity
- TLS enabled

## Updating the Chart

### Update Image Tags

```bash
helm upgrade reservation . \
  -f values-dev.yaml \
  --set api.image.tag=v1.1.0 \
  --set frontend.image.tag=v1.1.0
```

### Update Replicas

```bash
helm upgrade reservation . \
  -f values-dev.yaml \
  --set api.replicaCount=3
```

### Update Resources

```bash
helm upgrade reservation . \
  -f values-dev.yaml \
  --set api.resources.requests.cpu=200m
```

## Rollback

```bash
# View release history
helm history reservation

# Rollback to previous release
helm rollback reservation

# Rollback to specific revision
helm rollback reservation 1
```

## Best Practices

1. **Use values files** - Keep configuration in version control
2. **Test with dry-run** - Always test before deploying
3. **Use namespaces** - Isolate environments
4. **Monitor deployments** - Check status after updates
5. **Keep backups** - Backup values and configurations
6. **Document changes** - Track what changed and why
7. **Use semantic versioning** - Version your charts properly
8. **Test in dev first** - Always test in development before production

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Kubernetes events: `kubectl get events`
3. Check pod logs: `kubectl logs <pod-name>`
4. Check Helm status: `helm status reservation`


# OpenShift Deployment Guide

This directory contains Kubernetes/OpenShift manifests for deploying OpsAgent.

## Files

- `deployment.yaml` - Main deployment with Service, Route, and ServiceAccount
- `configmap.yaml` - Configuration including full `config.yaml`
- `secrets.yaml.example` - Secret template (DO NOT commit actual secrets!)

## Prerequisites

1. **OpenShift CLI (`oc`)** installed and configured
2. **Container image** built and pushed to a registry
3. **Namespace/Project** created in OpenShift

## Quick Start

### 1. Build and Push Container Image

```bash
# Login to your container registry
podman login quay.io

# Build the image
podman build -f Containerfile -t quay.io/rbrhssa/ops-agents:latest .

# Push to registry
podman push quay.io/rbrhssa/ops-agents:latest
```

### 2. Create OpenShift Project

```bash
oc new-project ops-agent
```

### 3. Create Secrets

**Option A: From command line (recommended)**

```bash
oc create secret generic ops-agent-secrets \
  --from-literal=llm-api-key='your-api-key' \
  --from-literal=llm-base-url='https://your-llm-endpoint.com/v1' \
  -n ops-agent
```

**Option B: From file**

```bash
# Copy example and edit
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with your actual values
vim secrets.yaml

# Apply
oc apply -f secrets.yaml -n ops-agent

# IMPORTANT: Add secrets.yaml to .gitignore!
echo "deploy/secrets.yaml" >> ../.gitignore
```

### 4. Apply ConfigMap

```bash
oc apply -f configmap.yaml -n ops-agent
```

### 5. Deploy Application

The `deployment.yaml` is configured to use:

```yaml
spec:
  containers:
  - name: ops-agent
    image: quay.io/rbrhssa/ops-agents:latest
```

Apply the deployment:

```bash
oc apply -f deployment.yaml -n ops-agent
```

### 6. Verify Deployment

```bash
# Check pod status
oc get pods -n ops-agent

# Check logs
oc logs -f deployment/ops-agent -n ops-agent

# Get route URL
oc get route ops-agent -n ops-agent -o jsonpath='{.spec.host}'
```

## Configuration

### Environment Variables

The deployment uses environment variables to override `config.yaml`:

| Variable | Source | Description |
|----------|--------|-------------|
| `LLM_BASE_URL` | Secret | LLM endpoint URL |
| `LLM_API_KEY` | Secret | LLM API key |
| `LLM_DEFAULT_MODEL` | ConfigMap | Model name |
| `LLM_TEMPERATURE` | Env | Generation temperature (0.1 for tool calling) |
| `LLM_MAX_TOKENS` | Env | Max response tokens |
| `ANSIBLE_API_BASE_URL` | ConfigMap | Ansible API endpoint |

### Updating Configuration

**Update ConfigMap:**

```bash
# Edit configmap.yaml
vim configmap.yaml

# Apply changes
oc apply -f configmap.yaml -n ops-agent

# Restart pods to pick up changes
oc rollout restart deployment/ops-agent -n ops-agent
```

**Update Secrets:**

```bash
# Edit existing secret
oc edit secret ops-agent-secrets -n ops-agent

# Or delete and recreate
oc delete secret ops-agent-secrets -n ops-agent
oc create secret generic ops-agent-secrets \
  --from-literal=llm-api-key='new-key' \
  --from-literal=llm-base-url='https://new-endpoint.com/v1' \
  -n ops-agent

# Restart pods
oc rollout restart deployment/ops-agent -n ops-agent
```

## Scaling

```bash
# Scale to multiple replicas
oc scale deployment/ops-agent --replicas=3 -n ops-agent

# Auto-scaling (HPA)
oc autoscale deployment/ops-agent \
  --min=1 --max=5 \
  --cpu-percent=80 \
  -n ops-agent
```

## Monitoring

### View Logs

```bash
# Follow logs
oc logs -f deployment/ops-agent -n ops-agent

# Logs from specific pod
oc logs -f ops-agent-<pod-id> -n ops-agent

# Previous pod logs
oc logs --previous deployment/ops-agent -n ops-agent
```

### Access Application

```bash
# Get route URL
ROUTE_URL=$(oc get route ops-agent -n ops-agent -o jsonpath='{.spec.host}')
echo "OpsAgent URL: https://${ROUTE_URL}"

# Test health endpoint
curl https://${ROUTE_URL}/ok

# Access LangGraph Studio (if enabled)
open "https://smith.langchain.com/studio/?baseUrl=https://${ROUTE_URL}"
```

### Resource Usage

```bash
# Check resource usage
oc adm top pods -n ops-agent

# Describe pod for events
oc describe pod -l app=ops-agent -n ops-agent
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
oc get pods -n ops-agent

# Describe pod for events
oc describe pod -l app=ops-agent -n ops-agent

# Check logs
oc logs deployment/ops-agent -n ops-agent --tail=100
```

### Common Issues

**1. Image Pull Errors**

```bash
# Verify image exists
podman pull quay.io/your-org/ops-agent:latest

# Check image pull secret
oc get secrets -n ops-agent

# Create pull secret if needed
oc create secret docker-registry quay-pull-secret \
  --docker-server=quay.io \
  --docker-username=your-username \
  --docker-password=your-password \
  -n ops-agent

# Add to service account
oc secrets link ops-agent quay-pull-secret --for=pull -n ops-agent
```

**2. Permission Errors**

```bash
# Check security context constraints
oc get scc

# Grant SCC if needed (use with caution)
oc adm policy add-scc-to-user anyuid -z ops-agent -n ops-agent
```

**3. Configuration Errors**

```bash
# Verify ConfigMap
oc get configmap ops-agent-config -n ops-agent -o yaml

# Verify Secrets
oc get secret ops-agent-secrets -n ops-agent -o yaml

# Check environment variables in pod
oc exec deployment/ops-agent -n ops-agent -- env | grep LLM
```

## Production Recommendations

1. **Use a dedicated namespace**: `ops-agent-prod`
2. **Set resource limits**: Already configured in `deployment.yaml`
3. **Enable persistent storage** for data directory (if needed):
   ```yaml
   volumes:
   - name: data
     persistentVolumeClaim:
       claimName: ops-agent-data
   ```
4. **Configure monitoring**: Add Prometheus annotations
5. **Set up backup**: For persistent data
6. **Use NetworkPolicy**: Restrict traffic
7. **Enable RBAC**: Fine-grained access control

## CI/CD Integration

### Example GitHub Actions

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build image
      run: |
        podman build -f Containerfile -t quay.io/rbrhssa/ops-agents:${{ github.sha }} .
    
    - name: Push image
      run: |
        echo ${{ secrets.QUAY_PASSWORD }} | podman login -u rbrhssa --password-stdin quay.io
        podman push quay.io/rbrhssa/ops-agents:${{ github.sha }}
        podman tag quay.io/rbrhssa/ops-agents:${{ github.sha }} quay.io/rbrhssa/ops-agents:latest
        podman push quay.io/rbrhssa/ops-agents:latest
    
    - name: Deploy to OpenShift
      run: |
        oc login --token=${{ secrets.OCP_TOKEN }} --server=${{ secrets.OCP_SERVER }}
        oc set image deployment/ops-agent ops-agent=quay.io/rbrhssa/ops-agents:${{ github.sha }} -n ops-agent
```

## Cleanup

```bash
# Delete all resources
oc delete -f deployment.yaml -n ops-agent
oc delete -f configmap.yaml -n ops-agent
oc delete secret ops-agent-secrets -n ops-agent

# Delete project
oc delete project ops-agent
```

# Kubernetes Deployment Quick Start

This guide provides quick instructions for deploying the PV Chatbot services to Kubernetes.

## Prerequisites

- Kubernetes cluster (local or cloud)
- kubectl configured to access your cluster
- Docker for building images

## Quick Deployment

### 1. Build Docker Images

Build images for all services:

```bash
# Build frontend
cd iac/frontend
./build-image.sh v1.0.0

# Build backend orchestrator
cd ../backend-orchestrator
./build-image.sh v1.0.0

# Build rag service  
cd ../rag-service
./build-image.sh v1.0.0
```

### 2. Deploy to Kubernetes

Deploy all services at once:

```bash
cd iac/
./deploy-all.sh
```

Or deploy services individually:

```bash
# Create namespace
kubectl create namespace general-chatbot-app

# Deploy frontend
kubectl apply -f frontend/

# Deploy backend orchestrator
kubectl apply -f backend-orchestrator/

# Deploy rag service
kubectl apply -f rag-service/
```

### 3. Verify Deployment

Check that all pods are running:

```bash
kubectl get pods -n general-chatbot-app
kubectl get services -n general-chatbot-app
```

## Configuration

Update the following files with your actual values before deployment:

- `iac/backend-orchestrator/backend-orchestrator-secret.yaml` - API keys and database credentials
- `iac/rag-service/rag-service-secret.yaml` - API keys and database credentials
- `iac/frontend/frontend-configmap.yaml` - Backend service URLs and application settings
- ConfigMaps in each service directory for non-sensitive configuration

## Services

- **Frontend**: React/TypeScript web application on port 80
- **Backend Orchestrator**: Main API service on port 8000
- **RAG Service**: Knowledge retrieval service on port 8000

## Access

The frontend service is exposed as a ClusterIP service. To access it:

```bash
# Port forward to access locally
kubectl port-forward -n general-chatbot-app service/frontend-service 3000:80

# Or create an ingress/load balancer for external access
```

For detailed deployment instructions, see [docs/KUBERNETES_DEPLOYMENT.md](docs/KUBERNETES_DEPLOYMENT.md).

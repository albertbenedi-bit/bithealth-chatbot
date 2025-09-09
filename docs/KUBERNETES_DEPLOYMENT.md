# Kubernetes Deployment Guide

This guide covers deploying the healthcare chatbot system to Kubernetes with Poetry-based dependency management.

## Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Docker for building images
- Poetry installed locally for development

## Package Manager Recommendation: Poetry

We recommend **Poetry** as the Python package manager for this project because:

- **Deterministic builds**: poetry.lock ensures consistent dependency versions across environments
- **Better Docker layer caching**: Separate dependency installation step improves build performance
- **Virtual environment management**: Works seamlessly in containers
- **Development/production separation**: Easy to exclude dev dependencies in production builds
- **Dependency resolution**: Automatic conflict resolution and security updates

## Quick Start

### 1. Build Docker Images

```bash
# Build backend-orchestrator
cd backend_orchestrator
docker build -t backend-orchestrator:latest .

# Build rag-service
cd ../agents/rag-service
docker build -t rag-service:latest .
```

### 2. Set up Secrets

Create the required API key secrets:

```bash
# Create Gemini API key secret
kubectl create secret generic backend-orchestrator-secrets \
  --from-literal=GEMINI_API_KEY=your_gemini_api_key \
  --from-literal=ANTHROPIC_API_KEY=your_anthropic_api_key \
  -n general-chatbot-app

# Create RAG service secrets
kubectl create secret generic rag-service-secrets \
  --from-literal=GOOGLE_API_KEY=your_google_api_key \
  -n general-chatbot-app
```

### 3. Deploy to Kubernetes

```bash
cd iac
./deploy-all.sh
```

## Service Architecture

### Backend Orchestrator
- **Port**: 8000
- **Health Check**: `/health`
- **Dependencies**: PostgreSQL, Redis, Kafka
- **Replicas**: 2 (with HPA scaling 2-10)

### RAG Service
- **Port**: 8000
- **Health Check**: `/v1/health`
- **Dependencies**: PostgreSQL, Kafka
- **Replicas**: 2 (with HPA scaling 2-10)
- **Storage**: PVC for model caching (2Gi)

## Configuration Management

### ConfigMaps
- `backend-orchestrator-config`: Non-sensitive configuration
- `rag-service-config`: RAG-specific settings

### Secrets
- `backend-orchestrator-secrets`: API keys for LLM providers
- `rag-service-secrets`: Google API key

## Health Checks

Both services include comprehensive health checks:

- **Liveness Probe**: Ensures container is running
- **Readiness Probe**: Ensures service is ready to accept traffic
- **Startup Probe**: Handles slow startup times

## Resource Management

### Backend Orchestrator
- **Requests**: 200m CPU, 256Mi memory
- **Limits**: 400m CPU, 512Mi memory

### RAG Service
- **Requests**: 250m CPU, 512Mi memory
- **Limits**: 500m CPU, 1Gi memory
- **Storage**: 2Gi PVC for model cache

## Horizontal Pod Autoscaling

Both services auto-scale based on:
- CPU utilization (70% threshold)
- Memory utilization (80% threshold)
- Min replicas: 2
- Max replicas: 10

## Local Development

### Using Poetry

```bash
# Install dependencies
poetry install

# Run locally
poetry run uvicorn src.main:app --reload  # backend-orchestrator
poetry run uvicorn app.main:app --reload  # rag-service
```

### Using Docker Compose

```bash
docker-compose up -d
```

## Monitoring

### Health Check Endpoints

```bash
# Backend Orchestrator
curl http://localhost:8000/health

# RAG Service
curl http://localhost:8000/v1/health
```

### Kubernetes Status

```bash
# Check pod status
kubectl get pods -n general-chatbot-app

# Check service status
kubectl get svc -n general-chatbot-app

# View logs
kubectl logs -f deployment/backend-orchestrator -n general-chatbot-app
kubectl logs -f deployment/rag-service -n general-chatbot-app
```

## Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**: Check logs and ensure secrets are properly configured
2. **Service Unavailable**: Verify health check endpoints and dependencies
3. **Model Download Issues**: Ensure PVC is mounted and has sufficient space

### Debug Commands

```bash
# Describe pod for events
kubectl describe pod <pod-name> -n general-chatbot-app

# Check resource usage
kubectl top pods -n general-chatbot-app

# Port forward for local testing
kubectl port-forward svc/backend-orchestrator 8000:8000 -n general-chatbot-app
kubectl port-forward svc/rag-service 8001:8000 -n general-chatbot-app
```

## Security Considerations

- Services run as non-root users
- Secrets are base64 encoded and stored in Kubernetes secrets
- Network policies can be added for additional isolation
- Resource limits prevent resource exhaustion attacks

## Scaling Considerations

- Both services support horizontal scaling
- RAG service may need larger model cache volumes for multiple replicas
- Consider using ReadWriteMany storage for shared model cache if needed
- Monitor memory usage as ML models can be memory-intensive

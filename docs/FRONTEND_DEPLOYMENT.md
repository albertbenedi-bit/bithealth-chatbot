# Frontend Deployment Guide

This guide covers deploying the React/TypeScript frontend application to Kubernetes.

## Overview

The frontend is a React 18 + TypeScript single-page application (SPA) built with Vite. It serves as the user interface for the healthcare chatbot system and communicates with the backend services via REST APIs.

## Architecture

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with Radix UI components
- **Serving**: nginx in production
- **Port**: 80 (HTTP)

## Docker Configuration

### Multi-stage Build

The Dockerfile uses a multi-stage build approach:

1. **Builder Stage**: Node.js 18 Alpine for building the React application
2. **Runtime Stage**: nginx Alpine for serving static files

### Key Features

- **Security**: Runs as non-root user (appuser:1001)
- **Health Checks**: Custom nginx health endpoint at `/health`
- **SPA Routing**: nginx configured to handle client-side routing
- **Compression**: Gzip enabled for static assets
- **Caching**: Optimized cache headers for static assets

## Kubernetes Deployment

### Resources

- **CPU**: 50m request, 100m limit
- **Memory**: 64Mi request, 128Mi limit
- **Replicas**: 2 minimum, up to 10 with auto-scaling

### Configuration

Environment variables are injected at build time using Vite's `VITE_` prefix:

```yaml
# Frontend ConfigMap
VITE_BACKEND_ORCHESTRATOR_URL: "http://backend-orchestrator-service:8000"
VITE_AUTH_SERVICE_URL: "http://auth-service:8004"
VITE_APP_NAME: "PV Chatbot"
VITE_APP_VERSION: "1.0.0"
```

### Health Checks

- **Liveness Probe**: HTTP GET `/health` every 10s
- **Readiness Probe**: HTTP GET `/health` every 5s
- **Startup Probe**: Allows 30s for initial startup

## Build and Deployment

### 1. Build Docker Image

```bash
cd iac/frontend
./build-image.sh v1.0.0
```

### 2. Deploy to Kubernetes

```bash
kubectl apply -f iac/frontend/
```

### 3. Access the Application

```bash
# Port forward for local access
kubectl port-forward -n general-chatbot-app service/frontend-service 3000:80

# Open browser to http://localhost:3000
```

## Production Considerations

### External Access

For production deployments, configure an ingress controller:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  namespace: general-chatbot-app
spec:
  rules:
  - host: chatbot.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Load Balancer

Alternatively, use a LoadBalancer service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend-loadbalancer
  namespace: general-chatbot-app
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
```

### HTTPS/TLS

Configure TLS termination at the ingress level:

```yaml
spec:
  tls:
  - hosts:
    - chatbot.yourdomain.com
    secretName: frontend-tls
```

## Monitoring

### Health Checks

Test the health endpoint:

```bash
kubectl exec -it <frontend-pod> -n general-chatbot-app -- wget -O- http://localhost:80/health
```

### Logs

View application logs:

```bash
kubectl logs -f deployment/frontend -n general-chatbot-app
```

### Metrics

Monitor resource usage:

```bash
kubectl top pods -l app=frontend -n general-chatbot-app
```

## Troubleshooting

### Common Issues

**Pod not starting:**
```bash
kubectl describe pod <frontend-pod> -n general-chatbot-app
kubectl logs <frontend-pod> -n general-chatbot-app
```

**Application not loading:**
- Check if the build completed successfully
- Verify nginx configuration
- Test health endpoint

**API calls failing:**
- Verify backend service URLs in ConfigMap
- Check network connectivity between services
- Ensure backend services are running

### Debug Commands

```bash
# Check service endpoints
kubectl get endpoints frontend-service -n general-chatbot-app

# Test internal connectivity
kubectl exec -it <frontend-pod> -n general-chatbot-app -- wget -O- http://backend-orchestrator-service:8000/health

# View nginx configuration
kubectl exec -it <frontend-pod> -n general-chatbot-app -- cat /etc/nginx/nginx.conf
```

## Development

### Local Development

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `.env.local` for local development:

```env
VITE_BACKEND_ORCHESTRATOR_URL=http://localhost:8000
VITE_AUTH_SERVICE_URL=http://localhost:8004
VITE_APP_NAME=PV Chatbot (Dev)
```

### Building Locally

```bash
npm run build
npm run preview
```

## Security

- Runs as non-root user in container
- Security headers configured in nginx
- No sensitive data in frontend code
- Environment variables injected at build time
- Static file serving only (no server-side execution)

## Performance

- Gzip compression enabled
- Static asset caching configured
- Optimized Docker image layers
- Minimal resource requirements
- Horizontal pod autoscaling based on CPU/memory usage

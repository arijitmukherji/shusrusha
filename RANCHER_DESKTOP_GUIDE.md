# 🐄 Rancher Desktop Guide for Shusrusha

## Overview

Rancher Desktop provides a fantastic Docker alternative with full Docker API compatibility. Your Shusrusha app works seamlessly with Rancher Desktop!

**Confirmed Working**: Docker version 28.1.1-rd, build 4d7f01e ✅

## Prerequisites

1. **Rancher Desktop Installed**: Download from [rancherdesktop.io](https://rancherdesktop.io/)
2. **Container Runtime**: Choose either:
   - **dockerd (Recommended)**: Full Docker compatibility
   - **containerd**: Kubernetes-native with nerdctl

## Quick Start

### Method 1: Standard Docker Commands (Recommended)

Since you have Docker compatibility enabled, use standard commands:

```bash
# 1. Navigate to project
cd /Users/arijit/code/shusrusha

# 2. Build and run
docker-compose up --build -d

# 3. Access app
open http://localhost:8501
```

### Method 2: Using Build Scripts

Our cross-platform scripts automatically detect Rancher Desktop:

```bash
# macOS/Linux
./build-docker.sh

# Windows
build-docker.bat
```

## Rancher Desktop Configuration

### Container Runtime Selection

**In Rancher Desktop Settings:**

1. **Preferences** → **Container Engine**
2. Choose your runtime:
   - **dockerd**: Use `docker` and `docker-compose` commands
   - **containerd**: Use `nerdctl` and `nerdctl compose` commands

### Recommended Settings for Shusrusha

```yaml
# Preferences → Container Engine
containerEngine: dockerd

# Preferences → Kubernetes
kubernetes:
  enabled: false  # Not needed for this app

# Preferences → WSL Integration (Windows only)
wslIntegration:
  defaultDistribution: true
```

## Command Equivalents

| Docker Desktop | Rancher Desktop (dockerd) | Rancher Desktop (containerd) |
|----------------|---------------------------|------------------------------|
| `docker build` | `docker build` | `nerdctl build` |
| `docker run` | `docker run` | `nerdctl run` |
| `docker-compose up` | `docker-compose up` | `nerdctl compose up` |
| `docker ps` | `docker ps` | `nerdctl ps` |

## Troubleshooting

### Issue: "docker: command not found"

**Solution**: Ensure Rancher Desktop is running and PATH is configured:

```bash
# Check if docker is available
which docker

# If not found, restart Rancher Desktop or check settings
```

### Issue: Permission denied (Linux/macOS)

**Solution**: Add user to docker group:

```bash
sudo usermod -aG docker $USER
# Then restart terminal
```

### Issue: Port already in use

**Solution**: Stop existing containers:

```bash
# Check what's running
docker ps

# Stop Shusrusha containers
docker-compose down

# Or stop all containers
docker stop $(docker ps -q)
```

## Performance Optimization

### Resource Allocation

**In Rancher Desktop Settings:**

```yaml
# Preferences → Resources
memory: 4GB      # Minimum for OpenAI processing
cpus: 2          # Adjust based on your system
diskSize: 20GB   # Sufficient for containers and images
```

### Image Management

```bash
# Clean up unused images periodically
docker system prune -a

# View disk usage
docker system df
```

## Development Workflow

### 1. Code Changes

```bash
# After modifying code, rebuild:
docker-compose up --build

# Or rebuild specific service:
docker-compose build shusrusha-app
```

### 2. Environment Variables

```bash
# Create .env file for local development
echo "OPENAI_API_KEY=your_key_here" > .env

# Docker Compose automatically loads .env
docker-compose up
```

### 3. Debugging

```bash
# View logs
docker-compose logs -f

# Access container shell
docker exec -it shusrusha-app bash

# Check environment variables
docker exec shusrusha-app env | grep OPENAI
```

## Advanced: Kubernetes Integration

If you enable Kubernetes in Rancher Desktop:

### 1. Create Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shusrusha
spec:
  replicas: 1
  selector:
    matchLabels:
      app: shusrusha
  template:
    metadata:
      labels:
        app: shusrusha
    spec:
      containers:
      - name: shusrusha
        image: shusrusha:latest
        ports:
        - containerPort: 8501
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
---
apiVersion: v1
kind: Service
metadata:
  name: shusrusha-service
spec:
  selector:
    app: shusrusha
  ports:
  - port: 8501
    targetPort: 8501
  type: LoadBalancer
```

### 2. Deploy to Kubernetes

```bash
# Create secret for API key
kubectl create secret generic openai-secret \
  --from-literal=api-key=your_openai_api_key

# Deploy application
kubectl apply -f k8s-deployment.yaml

# Access via port forwarding
kubectl port-forward service/shusrusha-service 8501:8501
```

## Comparison: Rancher Desktop vs Docker Desktop

| Feature | Docker Desktop | Rancher Desktop |
|---------|----------------|-----------------|
| **License** | Subscription for commercial use | Free and open source |
| **Container Runtime** | dockerd | dockerd OR containerd |
| **Kubernetes** | Optional | Built-in |
| **Resource Usage** | Higher memory usage | More efficient |
| **API Compatibility** | 100% Docker API | 100% Docker API (dockerd mode) |
| **Performance** | Good | Excellent |
| **Shusrusha Compatibility** | ✅ Perfect | ✅ Perfect |

## Next Steps

1. **Production Deployment**: Use our cloud deployment guides
2. **CI/CD Integration**: Set up automated builds
3. **Monitoring**: Add health checks and logging
4. **Scaling**: Use Kubernetes for multi-replica deployments

## Support

- **Rancher Desktop Docs**: [docs.rancherdesktop.io](https://docs.rancherdesktop.io/)
- **Shusrusha Issues**: Create issue in this repository
- **Community**: Rancher Desktop Slack community

---

🎉 **You're all set!** Rancher Desktop provides an excellent Docker-compatible environment for Shusrusha development and deployment.

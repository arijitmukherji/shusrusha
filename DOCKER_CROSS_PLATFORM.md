# 🐳 Cross-Platform Docker Guide for Shusrusha

## 🎯 Overview

This Docker solution works seamlessly on **Windows**, **macOS**, and **Linux**, providing a consistent experience across all platforms.

## 🚀 Quick Start

### Docker Desktop Users
```bash
# Standard Docker commands work as expected
docker-compose up --build -d
```

### Rancher Desktop Users 🐄

**Important**: Rancher Desktop provides Docker-compatible commands, so all standard Docker operations work the same way!

#### Container Runtime Options:

**Option 1: dockerd (Recommended for compatibility)**
- Full Docker API compatibility
- Works with all Docker Compose files
- Use standard `docker` and `docker-compose` commands

**Option 2: containerd + nerdctl**
- Kubernetes-native containers
- Use `nerdctl compose` instead of `docker-compose`
- Slightly different syntax for some operations

#### Quick Setup with Rancher Desktop:
```bash
# 1. Verify Rancher Desktop is running
docker version  # or: nerdctl version

# 2. Use standard Docker commands
docker-compose up --build -d

# 3. Access application
open http://localhost:8501  # macOS
start http://localhost:8501  # Windows
```

### Option 1: One-Command Setup

**Windows:**
```cmd
build-docker.bat
# Choose option 6 for "Build and run immediately"
```

**macOS/Linux:**
```bash
chmod +x build-docker.sh
./build-docker.sh
# Choose option 7 for "Build and run immediately"
```

### Option 2: Docker Compose (Simplest)

```bash
# 1. Create .env file with your API key
echo "OPENAI_API_KEY=your-key-here" > .env

# 2. Start with Docker Compose
docker-compose up --build -d

# 3. Open browser
# Windows: start http://localhost:8501
# macOS: open http://localhost:8501
# Linux: xdg-open http://localhost:8501
```

## 📁 File Structure

Your Docker setup includes:

```
shusrusha/
├── 🐳 Dockerfile                 # Multi-platform container definition
├── 🐳 docker-compose.yml         # Orchestration configuration
├── 🔧 build-docker.sh            # macOS/Linux build script
├── 🔧 build-docker.bat           # Windows build script
├── 📄 .dockerignore              # Files to exclude from build
├── 📄 .env                       # Your API keys (you create this)
└── 📁 Platform-specific scripts:
    ├── run-docker-windows.bat    # Windows quick start
    └── run-docker-macos.sh       # macOS/Linux quick start
```

## 🛠️ Platform-Specific Instructions

### Windows Users

#### Prerequisites
1. **Install Docker Desktop** from https://www.docker.com/products/docker-desktop/
2. **Enable WSL 2** if prompted during installation
3. **Restart computer** after installation

#### Quick Start
```cmd
# 1. Double-click to run
build-docker.bat

# 2. Choose option 6 "Build and run immediately"

# 3. Access at http://localhost:8501
```

#### Manual Commands
```cmd
# Build image
docker build -t shusrusha .

# Run container
docker run -d --name shusrusha --env-file .env -p 8501:8501 shusrusha

# Stop container
docker stop shusrusha && docker rm shusrusha
```

### macOS Users

#### Prerequisites
1. **Install Docker Desktop** from https://www.docker.com/products/docker-desktop/
2. **Start Docker Desktop** from Applications

#### Quick Start
```bash
# 1. Make script executable and run
chmod +x build-docker.sh
./build-docker.sh

# 2. Choose option 7 "Build and run immediately"

# 3. Access at http://localhost:8501
```

#### Manual Commands
```bash
# Build image
docker build -t shusrusha .

# Run container
docker run -d --name shusrusha --env-file .env -p 8501:8501 shusrusha

# Stop container
docker stop shusrusha && docker rm shusrusha
```

### Linux Users

#### Prerequisites
```bash
# Install Docker (Ubuntu/Debian)
sudo apt update
sudo apt install docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Restart session or run
newgrp docker
```

#### Quick Start
```bash
# Same as macOS
chmod +x build-docker.sh
./build-docker.sh
```

## 🔧 Docker Compose Commands

### Basic Operations
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d

# View status
docker-compose ps
```

### Advanced Operations
```bash
# Run with specific compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale services (if needed)
docker-compose up -d --scale shusrusha=2

# Execute commands in running container
docker-compose exec shusrusha bash

# View resource usage
docker stats
```

## 📊 Image Variants

### Standard Image (Multi-platform)
- **Platforms**: linux/amd64, linux/arm64
- **Size**: ~800MB
- **Python**: 3.11-slim
- **Features**: Full functionality

### Development Image
```bash
# For development with live reload
docker-compose -f docker-compose.dev.yml up --build
```

### Production Image
```bash
# For production deployment
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🔍 Troubleshooting

### Common Issues

#### "Docker not found"
**Windows:**
- Install Docker Desktop
- Restart computer
- Check if Docker Desktop is running

**macOS:**
- Install Docker Desktop
- Start Docker Desktop from Applications
- Wait for Docker to start completely

**Linux:**
- Install docker.io package
- Start docker service: `sudo systemctl start docker`
- Add user to docker group

#### "Permission denied"
**Windows:**
- Run Command Prompt as Administrator
- Or restart Docker Desktop

**macOS/Linux:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### "Port already in use"
```bash
# Find what's using port 8501
# Windows:
netstat -ano | findstr :8501

# macOS/Linux:
lsof -i :8501

# Use different port
docker run -p 8502:8501 shusrusha
```

#### "Container won't start"
```bash
# Check logs
docker logs shusrusha

# Run interactively for debugging
docker run -it shusrusha /bin/bash

# Check container status
docker ps -a
```

#### "Out of space"
```bash
# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune

# Remove unused images
docker image prune -a
```

### Performance Optimization

#### Memory Issues
```yaml
# In docker-compose.yml, adjust limits:
deploy:
  resources:
    limits:
      memory: 1G  # Reduce if needed
      cpus: '1.0'
```

#### Build Speed
```bash
# Use build cache
docker build --cache-from shusrusha .

# Multi-stage builds (already implemented)
# Parallel builds with buildx
docker buildx build --platform linux/amd64,linux/arm64 .
```

## 🌐 Network Configuration

### Default Setup
- **Port**: 8501 (Streamlit default)
- **Network**: Bridge network
- **Access**: http://localhost:8501

### Custom Network
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  shusrusha:
    ports:
      - "80:8501"  # Use port 80
    environment:
      - STREAMLIT_SERVER_PORT=8501
```

### External Access
```bash
# Allow external connections
docker run -p 0.0.0.0:8501:8501 shusrusha

# Or use specific IP
docker run -p 192.168.1.100:8501:8501 shusrusha
```

## 💾 Data Persistence

### Volume Mounts
The Docker setup includes persistent volumes:

```yaml
volumes:
  - ./uploads:/app/uploads     # File uploads
  - ./output:/app/output       # Generated files
  - ./logs:/app/logs          # Application logs
  - app_temp:/app/temp        # Temporary files
```

### Backup Data
```bash
# Backup volumes
docker run --rm -v shusrusha_app_temp:/source -v $(pwd)/backup:/backup alpine tar czf /backup/temp-backup.tar.gz -C /source .

# Restore volumes
docker run --rm -v shusrusha_app_temp:/target -v $(pwd)/backup:/backup alpine tar xzf /backup/temp-backup.tar.gz -C /target
```

## 🔒 Security Considerations

### Environment Variables
```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use secrets in production
docker secret create openai_key openai_key.txt
```

### Container Security
- ✅ **Non-root user**: Container runs as user `shusrusha`
- ✅ **Minimal base image**: Using python:3.11-slim
- ✅ **No unnecessary packages**: Only required dependencies
- ✅ **Read-only mounts**: Sample images mounted read-only

### Network Security
```bash
# Restrict to localhost only
docker run -p 127.0.0.1:8501:8501 shusrusha

# Use custom networks
docker network create shusrusha-net --driver bridge
```

## 📈 Monitoring

### Health Checks
Built-in health check every 30 seconds:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1
```

### Logging
```bash
# View logs
docker-compose logs -f

# Log rotation (automatic in Docker)
# Logs are automatically rotated to prevent disk space issues
```

### Resource Monitoring
```bash
# Real-time stats
docker stats

# Historical stats
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
```

## 🚀 Production Deployment

### Using Production Compose
```bash
# Deploy with production settings
docker-compose -f docker-compose.prod.yml up -d

# With custom environment
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Cloud Deployment
The Docker image works on:
- **AWS ECS/EC2**
- **Google Cloud Run**
- **Azure Container Instances**
- **DigitalOcean Droplets**
- **Any Docker-compatible platform**

### Scaling
```bash
# Multiple instances
docker-compose up -d --scale shusrusha=3

# Load balancer (add to docker-compose.yml)
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  depends_on:
    - shusrusha
```

## 🎉 Success!

Once running, you'll have:
- ✅ **Cross-platform compatibility**: Works on Windows, macOS, Linux
- ✅ **Consistent environment**: Same experience everywhere
- ✅ **Easy deployment**: One command to start
- ✅ **Scalable architecture**: Ready for production
- ✅ **Secure setup**: Non-root container with health checks

Access your application at: **http://localhost:8501** 🎊

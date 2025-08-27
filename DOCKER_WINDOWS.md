# 🐳 Running Shusrusha with Docker on Windows

## Overview
Docker provides a consistent way to run Shusrusha on any Windows system without worrying about Python versions, dependencies, or environment setup.

## Prerequisites

### 1. Install Docker Desktop for Windows
1. Download from: https://www.docker.com/products/docker-desktop/
2. Install Docker Desktop
3. Restart your computer
4. Open Docker Desktop and wait for it to start

### 2. Verify Docker Installation
Open Command Prompt or PowerShell:
```cmd
docker --version
docker-compose --version
```

You should see version numbers if Docker is installed correctly.

## Method 1: Quick Start with Docker Compose (Recommended)

### Option A: Super Easy Setup
1. **Double-click**: `docker-quickstart.bat`
2. **Enter your OpenAI API key** when prompted
3. **Wait for browser to open** automatically
4. **Start using Shusrusha!**

### Option B: Manual Setup

#### 1. Prepare Your Environment
Create a `.env` file in the shusrusha directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

#### 2. Start the Application

**Command Prompt:**
```cmd
# Navigate to shusrusha directory
cd C:\path\to\shusrusha

# Start with Docker Compose
docker-compose up --build
```

**PowerShell:**
```powershell
# Navigate to shusrusha directory
Set-Location "C:\path\to\shusrusha"

# Start with Docker Compose
docker-compose up --build
```

#### 3. Access the Application
Open your browser and go to: http://localhost:8501

#### 4. Stop the Application
Press `Ctrl+C` in the terminal, then:
```cmd
docker-compose down
```

### Option C: Interactive Manager
Run `docker-windows.bat` for a full interactive menu with options to:
- Start/stop the application
- View logs
- Rebuild
- Clean up
- Open browser automatically

## Method 2: Manual Docker Build & Run

### 1. Build the Docker Image
```cmd
cd C:\path\to\shusrusha
docker build -t shusrusha:latest .
```

### 2. Run the Container
```cmd
docker run -d ^
  --name shusrusha ^
  -p 8501:8501 ^
  -v "%CD%\.env:/app/.env" ^
  -v "%CD%\images:/app/images" ^
  shusrusha:latest
```

### 3. View Logs
```cmd
docker logs shusrusha
```

### 4. Stop and Remove Container
```cmd
docker stop shusrusha
docker rm shusrusha
```

## Docker Compose Configurations

Shusrusha includes multiple Docker Compose configurations for different use cases:

### 1. `docker-compose.yml` - Standard Usage
- **Best for**: Regular users
- **Features**: Basic setup with health checks
- **Command**: `docker-compose up --build`

### 2. `docker-compose.dev.yml` - Development  
- **Best for**: Developers making code changes
- **Features**: Live reload, volume mounts for code editing
- **Command**: `docker-compose -f docker-compose.dev.yml up --build`

### 3. `docker-compose.prod.yml` - Production
- **Best for**: Production deployments
- **Features**: Nginx reverse proxy, SSL, resource limits
- **Command**: `docker-compose -f docker-compose.prod.yml up --build`

### Quick File Reference
- `docker-quickstart.bat` - One-click setup
- `docker-windows.bat` - Interactive manager
- `DOCKER_WINDOWS.md` - This guide
- `nginx.conf` - Production web server config

For development with file watching:

### 1. Create Development Compose File
Save as `docker-compose.dev.yml`:
```yaml
version: '3.8'
services:
  shusrusha-dev:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    volumes:
      - .:/app
      - /app/__pycache__
      - /app/.venv
    environment:
      - STREAMLIT_SERVER_RUNON_SAVE=true
      - STREAMLIT_SERVER_FILE_WATCHER_TYPE=poll
    env_file:
      - .env
    command: streamlit run app.py --server.address 0.0.0.0 --server.fileWatcherType poll
```

### 2. Run Development Version
```cmd
docker-compose -f docker-compose.dev.yml up --build
```

## Method 4: Pre-built Image from Registry

If the image is published to Docker Hub:

```cmd
# Pull and run pre-built image
docker run -d ^
  --name shusrusha ^
  -p 8501:8501 ^
  -e OPENAI_API_KEY=your_key_here ^
  arijitmukherji/shusrusha:latest
```

## Docker Commands Reference

### Building
```cmd
# Build image
docker build -t shusrusha .

# Build with no cache (clean build)
docker build --no-cache -t shusrusha .

# Build for specific platform
docker build --platform linux/amd64 -t shusrusha .
```

### Running
```cmd
# Run in background
docker run -d -p 8501:8501 shusrusha

# Run with environment file
docker run -d -p 8501:8501 --env-file .env shusrusha

# Run with volume mount for images
docker run -d -p 8501:8501 -v "%CD%\images:/app/images" shusrusha

# Run interactively (for debugging)
docker run -it shusrusha /bin/bash
```

### Management
```cmd
# List running containers
docker ps

# List all containers
docker ps -a

# View logs
docker logs shusrusha

# Follow logs in real-time
docker logs -f shusrusha

# Stop container
docker stop shusrusha

# Remove container
docker rm shusrusha

# Remove image
docker rmi shusrusha
```

## File Structure for Docker

Your shusrusha directory should look like:
```
shusrusha/
├── Dockerfile              # Main Docker configuration
├── docker-compose.yml      # Easy orchestration
├── docker-compose.dev.yml  # Development version
├── .env                    # Your API keys (create this)
├── .dockerignore           # Files to exclude
├── app.py                  # Main Streamlit app
├── requirements-app.txt    # Python dependencies
├── lib/                    # Utility modules
└── images/                 # Your medical documents
```

## Troubleshooting

### Docker Desktop Issues
```cmd
# Restart Docker Desktop
# Right-click Docker icon in system tray → Restart

# Check Docker status
docker info

# Test Docker installation
docker run hello-world
```

### Port Already in Use
```cmd
# Use different port
docker run -p 8502:8501 shusrusha

# Find what's using port 8501
netstat -ano | findstr :8501
```

### Permission Issues
```cmd
# Run Docker Desktop as Administrator
# Right-click Docker Desktop → Run as Administrator
```

### Build Failures
```cmd
# Clean up Docker system
docker system prune -a

# Remove all containers and images
docker container prune -f
docker image prune -a -f

# Rebuild from scratch
docker build --no-cache -t shusrusha .
```

### Container Won't Start
```cmd
# Check container logs
docker logs shusrusha

# Run interactively to debug
docker run -it shusrusha /bin/bash

# Check if port is accessible
curl http://localhost:8501
```

### Environment Variables Not Loading
```cmd
# Verify .env file exists and has correct format
type .env

# Run with explicit environment variable
docker run -e OPENAI_API_KEY=your_key shusrusha
```

## Performance Tips

### 1. Use Multi-stage Builds
The Dockerfile uses multi-stage builds to reduce image size.

### 2. Volume Mounts for Development
```cmd
# Mount source code for live editing
docker run -v "%CD%:/app" shusrusha
```

### 3. Resource Limits
```cmd
# Limit memory and CPU
docker run --memory=2g --cpus=1.5 shusrusha
```

### 4. Docker Compose for Production
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  shusrusha:
    build: .
    ports:
      - "80:8501"
    restart: unless-stopped
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_ENABLE_CORS=false
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.5'
```

## Security Considerations

### 1. Environment Variables
Never commit `.env` files with real API keys:
```gitignore
# Add to .gitignore
.env
*.env
```

### 2. Network Security
```cmd
# Run on localhost only
docker run -p 127.0.0.1:8501:8501 shusrusha

# Use Docker secrets in production
docker secret create openai_key openai_key.txt
```

### 3. User Permissions
The Dockerfile runs as non-root user for security.

## Production Deployment

### 1. Cloud Deployment
```cmd
# Deploy to cloud platforms
# Docker images work on: AWS, Azure, Google Cloud, DigitalOcean
```

### 2. Reverse Proxy
Use nginx or Traefik in front of the Streamlit app:
```yaml
# nginx proxy example
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
  
  shusrusha:
    build: .
    expose:
      - "8501"
```

### 3. SSL/HTTPS
Use Let's Encrypt or cloud provider SSL certificates.

## Backup and Updates

### 1. Backup Data
```cmd
# Backup processed files
docker cp shusrusha:/app/outputs ./backup/
```

### 2. Update Application
```cmd
# Pull latest code
git pull

# Rebuild and restart
docker-compose up --build -d
```

### 3. Database Persistence
If using databases, mount volumes:
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

## Conclusion

Docker provides the most reliable way to run Shusrusha on Windows because:
- ✅ **Consistent environment** across all systems
- ✅ **No Python installation** required on host
- ✅ **Easy updates** and rollbacks
- ✅ **Scalable** for multiple users
- ✅ **Production ready** deployment

Start with Method 1 (Docker Compose) for the easiest experience!

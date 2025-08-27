#!/bin/bash

# 🐄 Cross-Platform Docker Build Script for Shusrusha
# Compatible with Docker Desktop and Rancher Desktop
# Builds Docker images that work on Windows, macOS, and Linux

set -e

echo "🏥 Shusrusha Cross-Platform Docker Builder"
echo "==========================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="shusrusha"
IMAGE_TAG="latest"
REGISTRY_NAME=""  # Set this if you want to push to a registry
RUNTIME=""  # Will be auto-detected

# Platform detection
PLATFORM=$(uname -s)
ARCH=$(uname -m)

echo -e "${BLUE}Platform detected: $PLATFORM $ARCH${NC}"

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found! Please install Docker Desktop${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker found: $(docker --version)${NC}"

# Function to detect container runtime
detect_runtime() {
    if command -v docker &> /dev/null; then
        if docker version 2>/dev/null | grep -q "rd"; then
            echo -e "${GREEN}📦 Detected: Rancher Desktop with Docker compatibility${NC}"
            RUNTIME="rancher-docker"
        else
            echo -e "${GREEN}📦 Detected: Docker Desktop${NC}"
            RUNTIME="docker"
        fi
        DOCKER_CMD="docker"
        COMPOSE_CMD="docker-compose"
    elif command -v nerdctl &> /dev/null; then
        echo -e "${GREEN}📦 Detected: Rancher Desktop with containerd${NC}"
        RUNTIME="rancher-nerdctl"
        DOCKER_CMD="nerdctl"
        COMPOSE_CMD="nerdctl compose"
    else
        echo -e "${RED}❌ Error: No container runtime found!${NC}"
        echo "Please install Docker Desktop or Rancher Desktop"
        exit 1
    fi
    echo
}

# Detect runtime first
detect_runtime

# Function to clean up buildx issues
cleanup_buildx() {
    echo -e "${YELLOW}🧹 Cleaning up buildx builders...${NC}"
    
    # Remove existing builders
    $DOCKER_CMD buildx rm multiplatform-builder 2>/dev/null || true
    
    # Reset to default builder
    $DOCKER_CMD buildx use default 2>/dev/null || true
    
    echo -e "${GREEN}✅ Buildx cleanup completed${NC}"
}

# Function for quick local build (bypass buildx issues)
quick_local_build() {
    echo -e "${BLUE}🚀 Quick local build (single platform)...${NC}"
    
    $DOCKER_CMD build \
        --tag $IMAGE_NAME:$IMAGE_TAG \
        .
    
    echo -e "${GREEN}✅ Local build completed${NC}"
    return 0
}

# Check container daemon
if ! $DOCKER_CMD info &> /dev/null; then
    if [[ "$RUNTIME" == "rancher"* ]]; then
        echo -e "${RED}❌ Container daemon not running! Please start Rancher Desktop${NC}"
    else
        echo -e "${RED}❌ Docker daemon not running! Please start Docker Desktop${NC}"
    fi
    exit 1
fi

echo -e "${GREEN}✅ Container daemon running${NC}"

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    read -p "Enter your OpenAI API key: " openai_key
    echo "OPENAI_API_KEY=$openai_key" > .env
    echo -e "${GREEN}✅ Created .env file${NC}"
fi

echo

# Function to build multi-platform image
build_multiplatform() {
    echo -e "${BLUE}🔨 Building multi-platform Docker image...${NC}"
    
    # Check if buildx is available
    if $DOCKER_CMD buildx version &> /dev/null; then
        echo -e "${GREEN}✅ Buildx available for multi-platform builds${NC}"
        
        # Create builder instance if it doesn't exist
        if ! $DOCKER_CMD buildx inspect multiplatform-builder &> /dev/null; then
            echo -e "${BLUE}📦 Creating multi-platform builder...${NC}"
            $DOCKER_CMD buildx create --name multiplatform-builder --driver docker-container --use
            $DOCKER_CMD buildx inspect --bootstrap
        else
            echo -e "${GREEN}✅ Multi-platform builder exists${NC}"
            $DOCKER_CMD buildx use multiplatform-builder
        fi
        
        # Ask user what they want to do with multi-platform image
        echo -e "${YELLOW}🤔 Multi-platform build options:${NC}"
        echo "1. Build for current platform only (recommended for local use)"
        echo "2. Build multi-platform and push to registry"
        echo "3. Build multi-platform without loading (for CI/CD)"
        read -p "Choose option (1-3) [1]: " build_option
        build_option=${build_option:-1}
        
        case $build_option in
            1)
                echo -e "${BLUE}🏗️  Building for current platform...${NC}"
                $DOCKER_CMD buildx build \
                    --tag $IMAGE_NAME:$IMAGE_TAG \
                    --load \
                    .
                echo -e "${GREEN}✅ Single-platform build completed and loaded${NC}"
                ;;
            2)
                if [ -z "$REGISTRY_NAME" ]; then
                    read -p "Enter registry name (e.g., docker.io/username): " REGISTRY_NAME
                fi
                echo -e "${BLUE}🏗️  Building for linux/amd64 and linux/arm64, pushing to registry...${NC}"
                $DOCKER_CMD buildx build \
                    --platform linux/amd64,linux/arm64 \
                    --tag $REGISTRY_NAME/$IMAGE_NAME:$IMAGE_TAG \
                    --push \
                    .
                echo -e "${GREEN}✅ Multi-platform build completed and pushed${NC}"
                ;;
            3)
                echo -e "${BLUE}🏗️  Building for linux/amd64 and linux/arm64 (no load)...${NC}"
                $DOCKER_CMD buildx build \
                    --platform linux/amd64,linux/arm64 \
                    --tag $IMAGE_NAME:$IMAGE_TAG \
                    .
                echo -e "${GREEN}✅ Multi-platform build completed${NC}"
                echo -e "${YELLOW}⚠️  Image not loaded to local daemon (use option 1 for local use)${NC}"
                ;;
            *)
                echo -e "${RED}❌ Invalid option, falling back to single platform${NC}"
                build_single_platform
                ;;
        esac
    else
        echo -e "${YELLOW}⚠️  Docker Buildx not available, building for current platform only${NC}"
        build_single_platform
    fi
}

# Function to build for current platform only
build_single_platform() {
    echo -e "${BLUE}🔨 Building Docker image for current platform...${NC}"
    
    docker build \
        --tag $IMAGE_NAME:$IMAGE_TAG \
        --build-arg BUILDPLATFORM=$PLATFORM \
        --build-arg TARGETPLATFORM=$PLATFORM \
        .
    
    echo -e "${GREEN}✅ Single-platform build completed${NC}"
}

# Function to test the built image
test_image() {
    echo -e "${BLUE}🧪 Testing the built image...${NC}"
    
    # Stop any existing container
    docker stop shusrusha-test 2>/dev/null || true
    docker rm shusrusha-test 2>/dev/null || true
    
    # Run test container
    echo -e "${BLUE}🚀 Starting test container...${NC}"
    docker run -d \
        --name shusrusha-test \
        --env-file .env \
        -p 8502:8501 \
        $IMAGE_NAME:$IMAGE_TAG
    
    # Wait for container to start
    echo -e "${BLUE}⏳ Waiting for container to start...${NC}"
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:8502/_stcore/health &> /dev/null; then
        echo -e "${GREEN}✅ Container health check passed${NC}"
        echo -e "${GREEN}🌐 Test app available at: http://localhost:8502${NC}"
        
        read -p "Press Enter to stop test container..."
        docker stop shusrusha-test
        docker rm shusrusha-test
        
        echo -e "${GREEN}✅ Test completed successfully${NC}"
    else
        echo -e "${RED}❌ Container health check failed${NC}"
        echo -e "${YELLOW}📄 Container logs:${NC}"
        docker logs shusrusha-test
        
        docker stop shusrusha-test
        docker rm shusrusha-test
        exit 1
    fi
}

# Function to create platform-specific run scripts
create_run_scripts() {
    echo -e "${BLUE}📝 Creating platform-specific run scripts...${NC}"
    
    # Windows batch script
    cat > run-docker-windows.bat << 'EOF'
@echo off
echo 🏥 Starting Shusrusha Docker Container (Windows)
echo ================================================

REM Check if Docker is running
docker version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found or not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Stop existing container if running
docker stop shusrusha-app 2>nul
docker rm shusrusha-app 2>nul

REM Start container
echo 🚀 Starting Shusrusha container...
docker-compose up -d

if errorlevel 1 (
    echo ❌ Failed to start container
    pause
    exit /b 1
)

echo ✅ Container started successfully!
echo 🌐 Opening Shusrusha in browser...
timeout /t 5 /nobreak >nul
start http://localhost:8501

echo.
echo 📊 To view logs: docker-compose logs -f
echo 🛑 To stop: docker-compose down
echo.
pause
EOF

    # macOS/Linux shell script
    cat > run-docker-macos.sh << 'EOF'
#!/bin/bash

echo "🏥 Starting Shusrusha Docker Container (macOS/Linux)"
echo "==================================================="

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker not found or not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Stop existing container if running
docker stop shusrusha-app 2>/dev/null || true
docker rm shusrusha-app 2>/dev/null || true

# Start container
echo "🚀 Starting Shusrusha container..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Container started successfully!"
    echo "🌐 Opening Shusrusha in browser..."
    sleep 3
    
    # Try to open in browser (macOS)
    if command -v open &> /dev/null; then
        open http://localhost:8501
    # Try to open in browser (Linux)
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8501
    else
        echo "Please open http://localhost:8501 in your browser"
    fi
    
    echo
    echo "📊 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
    echo
else
    echo "❌ Failed to start container"
    exit 1
fi
EOF

    chmod +x run-docker-macos.sh
    
    echo -e "${GREEN}✅ Created run-docker-windows.bat${NC}"
    echo -e "${GREEN}✅ Created run-docker-macos.sh${NC}"
}

# Function to create Docker ignore file
create_dockerignore() {
    cat > .dockerignore << 'EOF'
# Git
.git
.gitignore

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
dist/
build/
*.egg-info/
temp/
logs/
*.log

# Large files that shouldn't be in container
*.mp4
*.avi
*.mov
*.zip
*.tar.gz
*.pdf

# Build artifacts
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
EOF

    echo -e "${GREEN}✅ Created .dockerignore${NC}"
}

# Main menu
show_menu() {
    echo
    echo -e "${BLUE}Choose an option:${NC}"
    echo "1. 🚀 Quick local build (recommended for local use)"
    echo "2. 🏗️  Build multi-platform image"
    echo "3. 🔨 Build for current platform only"
    echo "4. 🧪 Test built image"
    echo "5. 📝 Create run scripts"
    echo "6. 🧹 Clean up Docker artifacts"
    echo "7. 🔧 Fix buildx issues (cleanup builders)"
    echo "8. 📋 Show image info"
    echo "9. 🚀 Build and run immediately"
    echo "10. ❌ Exit"
    echo
    read -p "Enter your choice (1-10): " choice
}

# Cleanup function
cleanup_docker() {
    echo -e "${BLUE}🧹 Cleaning up Docker artifacts...${NC}"
    
    # Remove stopped containers
    echo "Removing stopped containers..."
    docker container prune -f
    
    # Remove unused images
    echo "Removing unused images..."
    docker image prune -f
    
    # Remove unused volumes
    echo "Removing unused volumes..."
    docker volume prune -f
    
    # Remove unused networks
    echo "Removing unused networks..."
    docker network prune -f
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Show image info
show_image_info() {
    echo -e "${BLUE}📋 Docker Image Information${NC}"
    echo "=========================="
    
    if docker image inspect $IMAGE_NAME:$IMAGE_TAG &> /dev/null; then
        echo -e "${GREEN}✅ Image exists: $IMAGE_NAME:$IMAGE_TAG${NC}"
        
        echo
        echo "Image details:"
        docker image inspect $IMAGE_NAME:$IMAGE_TAG --format "
Size: {{.Size}} bytes ({{div .Size 1048576}} MB)
Created: {{.Created}}
Architecture: {{.Architecture}}
OS: {{.Os}}
"
        
        echo "Image layers:"
        docker history $IMAGE_NAME:$IMAGE_TAG --format "table {{.CreatedBy}}\t{{.Size}}"
    else
        echo -e "${RED}❌ Image not found: $IMAGE_NAME:$IMAGE_TAG${NC}"
        echo "Run option 1 or 2 to build the image first."
    fi
}

# Build and run immediately
build_and_run() {
    echo -e "${BLUE}🚀 Building and running Shusrusha...${NC}"
    
    # Create necessary files
    create_dockerignore
    
    # Build the image
    if docker buildx version &> /dev/null; then
        build_multiplatform
    else
        build_single_platform
    fi
    
    # Start with docker-compose
    echo -e "${BLUE}🚀 Starting with docker-compose...${NC}"
    docker-compose up -d
    
    echo -e "${GREEN}✅ Shusrusha is starting up!${NC}"
    echo -e "${GREEN}🌐 Available at: http://localhost:8501${NC}"
    echo
    echo -e "${BLUE}📊 To view logs: docker-compose logs -f${NC}"
    echo -e "${BLUE}🛑 To stop: docker-compose down${NC}"
}

# Main script logic
create_dockerignore

while true; do
    show_menu
    
    case $choice in
        1)
            quick_local_build
            ;;
        2)
            build_multiplatform
            ;;
        3)
            build_single_platform
            ;;
        4)
            test_image
            ;;
        5)
            create_run_scripts
            ;;
        6)
            cleanup_docker
            ;;
        7)
            cleanup_buildx
            ;;
        8)
            show_image_info
            ;;
        9)
            build_and_run
            break
            ;;
        10)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            ;;
    esac
done

#!/bin/bash

# 🔧 Quick Fix for Docker Buildx Issues
# Resolves "docker exporter does not currently support exporting manifest lists" error

set -e

echo "🔧 Docker Buildx Quick Fix"
echo "=========================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Step 1: Cleaning up problematic buildx builders...${NC}"

# Remove any existing problematic builders
docker buildx rm multiplatform-builder 2>/dev/null || true
docker buildx rm --all-inactive 2>/dev/null || true

echo -e "${GREEN}✅ Removed problematic builders${NC}"

echo -e "${BLUE}🔄 Step 2: Resetting to default builder...${NC}"

# Reset to default builder
docker buildx use default

echo -e "${GREEN}✅ Reset to default builder${NC}"

echo -e "${BLUE}🚀 Step 3: Building Shusrusha with simple Docker build...${NC}"

# Simple docker build for local use
docker build -t shusrusha:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo
    echo -e "${YELLOW}🎉 Your Shusrusha image is ready!${NC}"
    echo
    echo "Next steps:"
    echo -e "${BLUE}🚀 Run with docker-compose:${NC}"
    echo "   docker-compose up -d"
    echo
    echo -e "${BLUE}🌐 Access at:${NC}"
    echo "   http://localhost:8501"
    echo
    echo -e "${BLUE}📊 View logs:${NC}"
    echo "   docker-compose logs -f"
    echo
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

#!/bin/bash

# Quick Docker Setup Validation for Shusrusha
# Verifies that all components are ready for cross-platform deployment

echo "🔍 Shusrusha Docker Setup Validation"
echo "===================================="
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECKS_PASSED=0
TOTAL_CHECKS=0

check() {
    local name="$1"
    local command="$2"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    printf "%-30s" "$name:"
    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✅ PASS${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL${NC}"
    fi
}

echo "🐳 Docker Environment"
echo "--------------------"
check "Docker installed" "docker --version"
check "Docker daemon running" "docker info"
check "Docker Compose available" "docker-compose --version"

echo
echo "📁 Required Files"
echo "----------------"
check "Dockerfile exists" "test -f Dockerfile"
check "docker-compose.yml exists" "test -f docker-compose.yml"
check "app.py exists" "test -f app.py"
check "requirements-app.txt exists" "test -f requirements-app.txt"
check "lib directory exists" "test -d lib"

echo
echo "🔧 Build Scripts"
echo "---------------"
check "build-docker.sh exists" "test -f build-docker.sh"
check "build-docker.sh executable" "test -x build-docker.sh"
check "build-docker.bat exists" "test -f build-docker.bat"

echo
echo "📄 Configuration Files"
echo "---------------------"
check ".env file exists" "test -f .env"
check ".streamlit directory exists" "test -d .streamlit"
check "OpenAI key in .env" "grep -q 'OPENAI_API_KEY' .env"

echo
echo "🎯 Docker Build Test"
echo "-------------------"

# Test Docker build (dry run)
printf "%-30s" "Dockerfile syntax:"
if docker build --dry-run . &> /dev/null; then
    echo -e "${GREEN}✅ PASS${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

printf "%-30s" "Compose file syntax:"
if docker-compose config &> /dev/null; then
    echo -e "${GREEN}✅ PASS${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo
echo "📊 Results"
echo "--------"
echo "Checks passed: $CHECKS_PASSED/$TOTAL_CHECKS"

if [ $CHECKS_PASSED -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}🎉 All checks passed! Your Docker setup is ready.${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Run: ./build-docker.sh (macOS/Linux) or build-docker.bat (Windows)"
    echo "2. Choose option 7 for 'Build and run immediately'"
    echo "3. Access your app at http://localhost:8501"
    echo
elif [ $CHECKS_PASSED -gt $((TOTAL_CHECKS * 3 / 4)) ]; then
    echo -e "${YELLOW}⚠️  Most checks passed, but some issues need attention.${NC}"
    echo
    echo -e "${BLUE}Common fixes:${NC}"
    echo "- Create .env file with: OPENAI_API_KEY=your_key_here"
    echo "- Start Docker Desktop if daemon not running"
    echo "- Run: chmod +x build-docker.sh"
else
    echo -e "${RED}❌ Several issues found. Please address them before proceeding.${NC}"
    echo
    echo -e "${BLUE}Essential requirements:${NC}"
    echo "- Docker Desktop installed and running"
    echo "- .env file with valid OPENAI_API_KEY"
    echo "- All required project files present"
fi

echo

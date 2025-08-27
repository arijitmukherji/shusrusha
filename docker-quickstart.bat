@echo off
echo.
echo ========================================
echo   🐳 Shusrusha Docker Quick Setup
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found!
    echo.
    echo Please install Docker Desktop for Windows:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo ✅ Docker is ready
echo.

REM Check for .env file
if not exist ".env" (
    echo 📝 Creating environment file...
    echo.
    set /p OPENAI_KEY="Enter your OpenAI API key: "
    echo OPENAI_API_KEY=!OPENAI_KEY!> .env
    echo ✅ Created .env file
    echo.
)

echo 🚀 Starting Shusrusha...
echo.

REM Start with Docker Compose
docker-compose up --build -d

if errorlevel 1 (
    echo ❌ Failed to start Shusrusha
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo ✅ Shusrusha is starting up!
echo.
echo 🌐 Opening in browser in 30 seconds...
echo    URL: http://localhost:8501
echo.
echo 📊 To view logs: docker-compose logs -f
echo 🛑 To stop: docker-compose down
echo.

REM Wait for startup
timeout /t 30 /nobreak

REM Open browser
start http://localhost:8501

echo.
echo Press any key to exit this setup script...
pause >nul

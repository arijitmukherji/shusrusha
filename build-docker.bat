@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   🏥 Shusrusha Docker Builder (Windows)
echo ========================================
echo.

REM Configuration
set IMAGE_NAME=shusrusha
set IMAGE_TAG=latest

REM Check Docker installation
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found! Please install Docker Desktop
    echo Download from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo ✅ Docker found
docker --version

REM Check Docker daemon
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker daemon not running! Please start Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker daemon running

REM Check for .env file
if not exist ".env" (
    echo ⚠️  No .env file found
    set /p OPENAI_KEY="Enter your OpenAI API key: "
    echo OPENAI_API_KEY=!OPENAI_KEY!> .env
    echo ✅ Created .env file
)

echo.

:menu
echo Choose an option:
echo.
echo 1. 🔨 Build Docker image
echo 2. 🧪 Test built image
echo 3. 📝 Create run scripts
echo 4. 🧹 Clean up Docker
echo 5. 📋 Show image info
echo 6. 🚀 Build and run immediately
echo 7. ❌ Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto build
if "%choice%"=="2" goto test
if "%choice%"=="3" goto scripts
if "%choice%"=="4" goto cleanup
if "%choice%"=="5" goto info
if "%choice%"=="6" goto buildrun
if "%choice%"=="7" goto exit
echo Invalid choice. Please try again.
goto menu

:build
echo.
echo 🔨 Building Docker image...
call :create_dockerignore

docker build -t %IMAGE_NAME%:%IMAGE_TAG% .
if errorlevel 1 (
    echo ❌ Build failed
    pause
    goto menu
)

echo ✅ Build completed successfully
pause
goto menu

:test
echo.
echo 🧪 Testing the built image...

REM Stop existing test container
docker stop shusrusha-test >nul 2>&1
docker rm shusrusha-test >nul 2>&1

echo 🚀 Starting test container...
docker run -d --name shusrusha-test --env-file .env -p 8502:8501 %IMAGE_NAME%:%IMAGE_TAG%

if errorlevel 1 (
    echo ❌ Failed to start test container
    pause
    goto menu
)

echo ⏳ Waiting for container to start...
timeout /t 10 /nobreak >nul

REM Test health endpoint (simplified for Windows)
curl -f http://localhost:8502/_stcore/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Container health check failed
    echo 📄 Container logs:
    docker logs shusrusha-test
    docker stop shusrusha-test >nul 2>&1
    docker rm shusrusha-test >nul 2>&1
    pause
    goto menu
)

echo ✅ Container health check passed
echo 🌐 Test app available at: http://localhost:8502
echo.
pause

REM Cleanup test container
docker stop shusrusha-test >nul 2>&1
docker rm shusrusha-test >nul 2>&1
echo ✅ Test completed successfully
pause
goto menu

:scripts
echo.
echo 📝 Creating run scripts...

REM Create Windows run script
(
echo @echo off
echo echo 🏥 Starting Shusrusha Docker Container
echo echo ============================================
echo.
echo docker version ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo ❌ Docker not found or not running!
echo     echo Please start Docker Desktop and try again.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo ✅ Docker is running
echo.
echo REM Stop existing container
echo docker stop shusrusha-app 2^>nul
echo docker rm shusrusha-app 2^>nul
echo.
echo echo 🚀 Starting Shusrusha container...
echo docker-compose up -d
echo.
echo if errorlevel 1 ^(
echo     echo ❌ Failed to start container
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo ✅ Container started successfully!
echo echo 🌐 Opening Shusrusha in browser...
echo timeout /t 5 /nobreak ^>nul
echo start http://localhost:8501
echo.
echo echo 📊 To view logs: docker-compose logs -f
echo echo 🛑 To stop: docker-compose down
echo pause
) > run-docker.bat

echo ✅ Created run-docker.bat
pause
goto menu

:cleanup
echo.
echo 🧹 Cleaning up Docker artifacts...

echo Removing stopped containers...
docker container prune -f

echo Removing unused images...
docker image prune -f

echo Removing unused volumes...
docker volume prune -f

echo Removing unused networks...
docker network prune -f

echo ✅ Cleanup completed
pause
goto menu

:info
echo.
echo 📋 Docker Image Information
echo ============================

docker image inspect %IMAGE_NAME%:%IMAGE_TAG% >nul 2>&1
if errorlevel 1 (
    echo ❌ Image not found: %IMAGE_NAME%:%IMAGE_TAG%
    echo Run option 1 to build the image first.
    pause
    goto menu
)

echo ✅ Image exists: %IMAGE_NAME%:%IMAGE_TAG%
echo.
echo Image details:
docker image inspect %IMAGE_NAME%:%IMAGE_TAG% --format "Size: {{.Size}} bytes"
docker image inspect %IMAGE_NAME%:%IMAGE_TAG% --format "Created: {{.Created}}"
docker image inspect %IMAGE_NAME%:%IMAGE_TAG% --format "Architecture: {{.Architecture}}"
docker image inspect %IMAGE_NAME%:%IMAGE_TAG% --format "OS: {{.Os}}"

pause
goto menu

:buildrun
echo.
echo 🚀 Building and running Shusrusha...

call :create_dockerignore

echo 🔨 Building Docker image...
docker build -t %IMAGE_NAME%:%IMAGE_TAG% .
if errorlevel 1 (
    echo ❌ Build failed
    pause
    goto menu
)

echo 🚀 Starting with docker-compose...
docker-compose up -d
if errorlevel 1 (
    echo ❌ Failed to start container
    pause
    goto menu
)

echo ✅ Shusrusha is starting up!
echo 🌐 Available at: http://localhost:8501
echo.
echo 📊 To view logs: docker-compose logs -f
echo 🛑 To stop: docker-compose down
echo.
echo Opening in browser in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:8501
pause
goto menu

:create_dockerignore
if not exist ".dockerignore" (
    (
        echo # Git
        echo .git
        echo .gitignore
        echo.
        echo # Docker
        echo Dockerfile*
        echo docker-compose*
        echo .dockerignore
        echo.
        echo # Python
        echo __pycache__
        echo *.pyc
        echo *.pyo
        echo *.pyd
        echo .Python
        echo env
        echo .env
        echo .venv
        echo venv/
        echo.
        echo # IDEs
        echo .vscode/
        echo .idea/
        echo.
        echo # OS
        echo .DS_Store
        echo Thumbs.db
        echo.
        echo # Build artifacts
        echo dist/
        echo build/
        echo *.egg-info/
        echo temp/
        echo logs/
        echo *.log
    ) > .dockerignore
)
goto :eof

:exit
echo.
echo 👋 Goodbye!
exit /b 0

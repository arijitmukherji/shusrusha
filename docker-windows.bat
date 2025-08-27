@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   🐳 Shusrusha Docker Manager
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found! Please install Docker Desktop from:
    echo    https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo ✅ Docker found
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running! Please start Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker is running
echo.

REM Check for .env file
if not exist ".env" (
    echo ⚠️  No .env file found!
    echo    Please create a .env file with your OpenAI API key:
    echo    OPENAI_API_KEY=your_key_here
    echo.
    set /p OPENAI_KEY="Enter your OpenAI API key (or press Enter to skip): "
    if not "!OPENAI_KEY!"=="" (
        echo OPENAI_API_KEY=!OPENAI_KEY!> .env
        echo ✅ Created .env file
    )
    echo.
)

:menu
echo Choose an option:
echo.
echo 1. 🚀 Start Shusrusha (build and run)
echo 2. 🛑 Stop Shusrusha
echo 3. 📊 View logs
echo 4. 🔧 Rebuild (clean build)
echo 5. 📋 Show container status
echo 6. 🧹 Clean up (remove containers/images)
echo 7. 🌐 Open in browser
echo 8. ❌ Exit
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto logs
if "%choice%"=="4" goto rebuild
if "%choice%"=="5" goto status
if "%choice%"=="6" goto cleanup
if "%choice%"=="7" goto browser
if "%choice%"=="8" goto exit
echo Invalid choice. Please try again.
goto menu

:start
echo.
echo 🚀 Starting Shusrusha with Docker Compose...
docker-compose up --build -d
if errorlevel 1 (
    echo ❌ Failed to start. Check the error above.
    pause
    goto menu
)
echo.
echo ✅ Shusrusha is starting up!
echo    🌐 URL: http://localhost:8501
echo    📊 Logs: Choose option 3 to view logs
echo    ⏱️  Please wait 30-60 seconds for startup
echo.
pause
goto menu

:stop
echo.
echo 🛑 Stopping Shusrusha...
docker-compose down
echo ✅ Shusrusha stopped
echo.
pause
goto menu

:logs
echo.
echo 📊 Showing logs (Press Ctrl+C to stop following logs)...
echo.
docker-compose logs -f
echo.
pause
goto menu

:rebuild
echo.
echo 🔧 Rebuilding Shusrusha (clean build)...
docker-compose down
docker system prune -f
docker-compose up --build -d
if errorlevel 1 (
    echo ❌ Rebuild failed. Check the error above.
    pause
    goto menu
)
echo ✅ Rebuild complete!
echo.
pause
goto menu

:status
echo.
echo 📋 Container Status:
echo.
docker ps -a --filter "name=shusrusha"
echo.
echo Docker Images:
docker images | findstr shusrusha
echo.
echo Resource Usage:
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | findstr shusrusha
echo.
pause
goto menu

:cleanup
echo.
echo ⚠️  This will remove all Shusrusha containers and images!
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto menu

echo.
echo 🧹 Cleaning up...
docker-compose down
docker container prune -f
docker image prune -f
docker rmi shusrusha-shusrusha 2>nul
echo ✅ Cleanup complete
echo.
pause
goto menu

:browser
echo.
echo 🌐 Opening Shusrusha in browser...
start http://localhost:8501
echo.
echo If the page doesn't load:
echo 1. Make sure Shusrusha is running (option 1)
echo 2. Wait a minute for startup to complete
echo 3. Check logs for errors (option 3)
echo.
pause
goto menu

:exit
echo.
echo 👋 Goodbye!
exit /b 0

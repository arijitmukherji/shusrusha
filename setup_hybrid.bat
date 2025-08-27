@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   🏥 Shusrusha Hybrid Deployment Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip not found! Please install pip
    pause
    exit /b 1
)

echo ✅ pip found

REM Install dependencies
echo.
echo 📦 Installing local API server dependencies...
pip install -r requirements-local-api.txt

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Check for .env file
if not exist ".env" (
    echo.
    echo ⚠️  No .env file found. Creating one now...
    echo.
    
    set /p OPENAI_KEY="Enter your OpenAI API key: "
    set /p API_SECRET="Enter a secret key for API authentication (or press Enter for default): "
    
    if "!API_SECRET!"=="" (
        set API_SECRET=hybrid-%RANDOM%%RANDOM%
    )
    
    (
        echo # OpenAI API Configuration
        echo OPENAI_API_KEY=!OPENAI_KEY!
        echo.
        echo # Local API Server Configuration
        echo LOCAL_API_SECRET=!API_SECRET!
        echo.
        echo # Optional: Customize rate limits
        echo RATE_LIMIT_DOCS_HOUR=10
        echo RATE_LIMIT_DOCS_DAY=50
        echo MAX_FILE_SIZE_MB=10
    ) > .env
    
    echo ✅ Created .env file with your configuration
) else (
    echo ✅ .env file already exists
)

REM Check for ngrok
echo.
echo 🔍 Checking for ngrok...
ngrok version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  ngrok not found. 
    echo.
    echo You can:
    echo 1. Install ngrok from https://ngrok.com/
    echo 2. Or manually run: python local_api_server.py
    echo 3. Then set up port forwarding on your router
    echo.
    echo 🚀 Starting local API server manually...
    echo Press Ctrl+C to stop the server
    echo.
    python local_api_server.py
    goto :end
)

echo ✅ ngrok found
ngrok version

echo.
echo 🚀 Starting local API server...

REM Start API server in background
start /B python local_api_server.py > local_api.log 2>&1

REM Wait for server to start
timeout /t 5 /nobreak > nul

echo ✅ Local API server started
echo 📄 Logs saved to: local_api.log

echo.
echo 🌐 Starting ngrok tunnel...

REM Start ngrok in background
start /B ngrok http 5000

REM Wait for ngrok to start
timeout /t 5 /nobreak > nul

REM Try to get ngrok URL (simplified for Windows)
echo.
echo 🔧 Getting ngrok tunnel URL...
echo Please check http://localhost:4040 for your ngrok tunnel URL

echo.
echo 🎉 Setup Complete!
echo ==================
echo.
echo Your local API server is running at:
echo   Local:  http://localhost:5000
echo   Public: Check http://localhost:4040 for ngrok URL
echo.
echo 🌐 Cloud App Setup:
echo 1. Deploy app_hybrid_cloud.py to Streamlit Cloud
echo 2. Add these secrets to your Streamlit Cloud app:
echo    LOCAL_API_URL = "your_ngrok_https_url"
echo    LOCAL_API_SECRET = "your_secret_from_env_file"
echo.
echo 📊 To monitor:
echo    - API logs: type local_api.log
echo    - ngrok dashboard: http://localhost:4040
echo.
echo 🛑 To stop: Close this window or press Ctrl+C
echo.

pause

:end

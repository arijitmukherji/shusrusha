@echo off
echo.
echo ========================================
echo   🏥 Starting Shusrusha Web App
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ from python.org
    echo    Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ app.py not found! Please run this from the shusrusha directory
    pause
    exit /b 1
)

echo ✅ App files found
echo.

REM Check if dependencies are installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing dependencies...
    pip install -r requirements-app.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

echo ✅ Dependencies ready
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

echo 🚀 Starting Shusrusha web application...
echo    Opening in your default browser...
echo    URL: http://localhost:8501
echo.
echo    Press Ctrl+C to stop the server
echo.

REM Start Streamlit
streamlit run app.py

echo.
echo 👋 Shusrusha stopped. Press any key to exit.
pause >nul

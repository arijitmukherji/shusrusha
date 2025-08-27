@echo off
REM Shusrusha Medical Document Processor - Windows Run Script

echo 🏥 Starting Shusrusha Medical Document Processor...

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Start the application
echo 🚀 Launching web application...
echo 📱 The app will open in your browser at: http://localhost:8501
echo 🛑 Press Ctrl+C to stop the application
echo.

streamlit run app.py

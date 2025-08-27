@echo off
REM Shusrusha Medical Document Processor - Windows Setup Script

echo 🏥 Setting up Shusrusha Medical Document Processor...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3 is required but not installed.
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements-app.txt

REM Check if .env file exists
if not exist ".env" (
    echo ⚙️ Creating .env file...
    echo # Add your OpenAI API key here > .env
    echo OPENAI_API_KEY=your_openai_api_key_here >> .env
    echo ❗ Please edit .env file and add your OpenAI API key
) else (
    echo ✅ .env file already exists
)

echo.
echo 🎉 Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file and add your OpenAI API key
echo 2. Run: run.bat
echo.
echo Or manually:
echo 1. .venv\Scripts\activate.bat
echo 2. streamlit run app.py

pause

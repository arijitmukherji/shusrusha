@echo off
REM Windows Batch Script to Build Shusrusha Executable
REM Run this on a Windows 10/11 machine

echo ========================================
echo    Shusrusha Windows Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8-3.11 from https://python.org
    pause
    exit /b 1
)

echo Python detected:
python --version

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo.
echo Step 1: Installing build dependencies...
pip install pyinstaller>=5.13.0
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Step 2: Installing application dependencies...
pip install -r requirements-app.txt
if errorlevel 1 (
    echo ERROR: Failed to install application dependencies
    echo Make sure requirements-app.txt exists
    pause
    exit /b 1
)

echo.
echo Step 3: Building Windows executable...
python build_windows_enhanced.py
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo           BUILD COMPLETED!
echo ========================================
echo.
echo Your executable is ready in: dist\windows\
echo.
echo Files created:
echo   - Shusrusha.exe        (Main application)
echo   - README.txt           (User instructions)  
echo   - config_template.txt  (API key setup)
echo.
echo To distribute:
echo   1. Copy the entire dist\windows\ folder
echo   2. Users follow README.txt for setup
echo   3. Users double-click Shusrusha.exe to run
echo.
pause

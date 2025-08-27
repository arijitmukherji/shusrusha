#!/usr/bin/env python3
"""
Create a portable Windows package for Shusrusha
"""

import os
import shutil
import zipfile
from pathlib import Path
import json

def create_portable_package():
    """Create a portable Windows package"""
    
    print("📦 Creating portable Windows package for Shusrusha...")
    print("=" * 60)
    
    # Create package directory
    package_dir = Path("dist/shusrusha-portable")
    package_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Package directory: {package_dir}")
    
    # Files to copy
    files_to_copy = [
        "app.py",
        "langgraph_app.py", 
        "requirements-app.txt",
        "setup.bat",
        "run.bat",
        "README-APP.md",
        "WINDOWS_PACKAGING.md",
    ]
    
    directories_to_copy = [
        "lib",
        "images",  # Include sample images if they exist
    ]
    
    # Copy files
    print("📋 Copying application files...")
    for file_path in files_to_copy:
        src = Path(file_path)
        if src.exists():
            shutil.copy2(src, package_dir / src.name)
            print(f"  ✅ {file_path}")
        else:
            print(f"  ⚠️  {file_path} (not found, skipping)")
    
    # Copy directories
    print("📁 Copying directories...")
    for dir_path in directories_to_copy:
        src = Path(dir_path)
        if src.exists() and src.is_dir():
            shutil.copytree(src, package_dir / src.name, dirs_exist_ok=True)
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ⚠️  {dir_path}/ (not found, skipping)")
    
    # Create enhanced startup script
    print("🚀 Creating startup script...")
    startup_script = package_dir / "start_shusrusha.bat"
    with open(startup_script, 'w', encoding='utf-8') as f:
        f.write('''@echo off
chcp 65001 >nul
title Shusrusha Medical Document Processor

echo.
echo 🏥 Shusrusha Medical Document Processor
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is required but not installed.
    echo.
    echo 📥 Please install Python 3.8 or higher from:
    echo    https://python.org/downloads/
    echo.
    echo 💡 During installation, make sure to check:
    echo    "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo.
    echo 📦 Setting up virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\\Scripts\\activate.bat

REM Install/update dependencies
echo 📥 Installing dependencies...
pip install --upgrade pip
pip install -r requirements-app.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Check for .env file
if not exist ".env" (
    echo.
    echo ⚙️ Creating configuration file...
    echo # Shusrusha Configuration > .env
    echo # Add your OpenAI API key below: >> .env
    echo OPENAI_API_KEY=your_openai_api_key_here >> .env
    echo.
    echo ❗ IMPORTANT: Configuration Setup Required
    echo.
    echo 1. Open the ".env" file in this folder
    echo 2. Replace "your_openai_api_key_here" with your actual OpenAI API key
    echo 3. Save the file and run this script again
    echo.
    echo 🔑 Get your API key from: https://platform.openai.com/api-keys
    echo.
    pause
    exit /b 1
)

REM Check if API key is properly set
findstr /C:"your_openai_api_key_here" .env >nul
if %errorlevel% equ 0 (
    echo.
    echo ⚠️ API key not configured properly
    echo.
    echo Please edit the ".env" file and add your OpenAI API key
    echo Replace "your_openai_api_key_here" with your actual key
    echo.
    pause
    exit /b 1
)

findstr /C:"OPENAI_API_KEY=sk-" .env >nul
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ OpenAI API key may not be set correctly
    echo Make sure your .env file contains:
    echo OPENAI_API_KEY=sk-your_actual_key_here
    echo.
)

REM Start the application
echo.
echo 🚀 Launching Shusrusha...
echo.
echo 📱 The application will open in your web browser at:
echo    http://localhost:8501
echo.
echo 🛑 To stop the application, press Ctrl+C in this window
echo.
echo =====================================
echo.

streamlit run app.py

REM If we get here, the app has stopped
echo.
echo 🏥 Shusrusha has stopped.
echo Thank you for using Shusrusha Medical Document Processor!
echo.
pause
''')
    
    # Create user guide
    print("📖 Creating user guide...")
    user_guide = package_dir / "USER_GUIDE.txt"
    with open(user_guide, 'w', encoding='utf-8') as f:
        f.write('''🏥 SHUSRUSHA MEDICAL DOCUMENT PROCESSOR - USER GUIDE
=====================================================

QUICK START:
1. Double-click "start_shusrusha.bat"
2. Follow the setup prompts
3. Add your OpenAI API key when requested
4. The app will open in your web browser

SYSTEM REQUIREMENTS:
- Windows 10 or newer
- Internet connection
- OpenAI API key (get from https://platform.openai.com/api-keys)

FIRST TIME SETUP:
1. Run start_shusrusha.bat
2. Python will be installed if needed
3. Dependencies will be installed automatically
4. Edit the .env file with your API key
5. Run start_shusrusha.bat again

USING THE APPLICATION:
1. Upload discharge summary images
2. Configure processing options
3. Click "Start Processing"
4. Download your results

FILES IN THIS PACKAGE:
- start_shusrusha.bat: Main launcher
- app.py: Application code
- requirements-app.txt: Python dependencies
- .env: Configuration file (created on first run)
- lib/: Application libraries

TROUBLESHOOTING:
- If antivirus software blocks the app, add folder to exceptions
- If Python errors occur, reinstall Python from python.org
- Make sure "Add Python to PATH" is checked during Python installation
- For support, check README-APP.md

PRIVACY & SECURITY:
- All processing happens locally on your computer
- Images are temporarily stored and automatically deleted
- Only text is sent to OpenAI API for processing
- Your API key is stored locally in the .env file

© 2025 Shusrusha Medical Document Processor
''')
    
    # Create package info
    package_info = {
        "name": "Shusrusha Medical Document Processor",
        "version": "1.0.0",
        "description": "AI-powered medical document processing",
        "platform": "Windows Portable",
        "created": "2025-08-26",
        "files": len(files_to_copy),
        "requirements": "Python 3.8+, OpenAI API key"
    }
    
    with open(package_dir / "package_info.json", 'w') as f:
        json.dump(package_info, f, indent=2)
    
    # Create ZIP package
    print("🗜️ Creating ZIP archive...")
    zip_path = Path("dist/shusrusha-portable-windows.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir.parent)
                zipf.write(file_path, arcname)
                
    # Get package size
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    
    print("\n✅ Portable package created successfully!")
    print(f"📦 ZIP file: {zip_path} ({zip_size_mb:.1f} MB)")
    print(f"📁 Folder: {package_dir}")
    print("\n🚀 Distribution Instructions:")
    print("1. Send the ZIP file to Windows users")
    print("2. They extract it and run 'start_shusrusha.bat'")
    print("3. Follow the setup prompts")
    print("4. Add OpenAI API key when requested")

if __name__ == "__main__":
    create_portable_package()

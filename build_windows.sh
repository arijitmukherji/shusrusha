#!/bin/bash
# Cross-platform build script for Windows executable
# Can be run on macOS/Linux to create Windows executable

echo "========================================="
echo "   Shusrusha Windows Build (Cross-Platform)"
echo "========================================="
echo

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ ERROR: Python is not installed"
    echo "Please install Python 3.8-3.11"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
else
    PYTHON_CMD=python
    PIP_CMD=pip
fi

echo "✅ Python detected: $($PYTHON_CMD --version)"

# Check if pip is available
if ! command -v $PIP_CMD &> /dev/null; then
    echo "❌ ERROR: pip is not available"
    exit 1
fi

echo "✅ Pip detected: $($PIP_CMD --version)"

echo
echo "📦 Step 1: Installing build dependencies..."
$PIP_CMD install pyinstaller>=5.13.0
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to install PyInstaller"
    exit 1
fi

echo
echo "📦 Step 2: Installing application dependencies..."
$PIP_CMD install -r requirements-app.txt
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to install application dependencies"
    echo "Make sure requirements-app.txt exists"
    exit 1
fi

echo
echo "🔨 Step 3: Building Windows executable..."
$PYTHON_CMD build_windows_enhanced.py
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Build failed"
    exit 1
fi

echo
echo "========================================="
echo "           ✅ BUILD COMPLETED!"
echo "========================================="
echo
echo "📦 Your executable is ready in: dist/windows/"
echo
echo "📁 Files created:"
echo "   - Shusrusha.exe        (Main application)"
echo "   - README.txt           (User instructions)"  
echo "   - config_template.txt  (API key setup)"
echo
echo "🚀 To distribute:"
echo "   1. Copy the entire dist/windows/ folder"
echo "   2. Users follow README.txt for setup"
echo "   3. Users double-click Shusrusha.exe to run"
echo
echo "⚠️  Note: This was built on $(uname -s)"
echo "   Test on actual Windows 10/11 before distributing"
echo

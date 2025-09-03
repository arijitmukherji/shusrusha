#!/bin/bash
# Quick packaging script for Windows distribution

echo "📦 Packaging Shusrusha for Windows..."

# Create a clean distribution directory
mkdir -p dist/shusrusha-windows

# Copy essential files
cp dist/Shusrusha.exe dist/shusrusha-windows/
cp dist/README.txt dist/shusrusha-windows/
cp dist/env_template.txt dist/shusrusha-windows/

# Create a simple batch file for Windows users
cat > dist/shusrusha-windows/start.bat << 'EOF'
@echo off
echo Starting Shusrusha Medical Document Processor...
echo.
echo Make sure you have:
echo 1. Created .env file with your OpenAI API key
echo 2. Internet connection is available
echo.
echo The app will open in your web browser...
echo.
Shusrusha.exe
pause
EOF

echo "✅ Windows distribution ready in: dist/shusrusha-windows/"
echo "📁 Contents:"
ls -la dist/shusrusha-windows/

echo ""
echo "🚀 Distribution Instructions:"
echo "1. Copy the entire 'shusrusha-windows' folder to a Windows machine"
echo "2. Copy env_template.txt to .env and add OpenAI API key"
echo "3. Run start.bat or double-click Shusrusha.exe"
echo "4. The app will open in the web browser"

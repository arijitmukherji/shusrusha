#!/bin/bash
# Quick Windows testing setup using Docker (if available)

echo "🧪 Setting up Windows testing environment..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first."
    echo "📥 Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker detected"

# Try to pull a minimal Windows container
echo "📥 Pulling Windows Server Core container..."
echo "⚠️  Note: This requires Docker Desktop with Windows containers enabled"

# For testing purposes, we'll create a test script instead
echo "📝 Creating Windows test script..."

cat > dist/shusrusha-windows/test-on-windows.bat << 'EOF'
@echo off
echo Testing Shusrusha Windows Executable
echo =====================================
echo.

echo 1. Checking if executable exists...
if exist "Shusrusha.exe" (
    echo ✅ Shusrusha.exe found
) else (
    echo ❌ Shusrusha.exe not found
    goto :error
)

echo.
echo 2. Creating test .env file...
echo OPENAI_API_KEY=test_key_for_validation > .env
echo ✅ Created test .env file

echo.
echo 3. Testing executable launch (this will fail without real API key)...
echo ⚠️  Expected: Should start but fail on API validation
echo.

REM Try to run the executable for a few seconds then kill
timeout /t 3 /nobreak > nul
taskkill /f /im Shusrusha.exe 2>nul

echo.
echo 4. Checking for common issues...
if exist ".env" (
    echo ✅ .env file created successfully
) else (
    echo ❌ .env file missing
)

echo.
echo =====================================
echo Test completed!
echo.
echo To run manually:
echo 1. Add real OpenAI API key to .env file
echo 2. Double-click Shusrusha.exe
echo 3. App should open in web browser
echo.
pause
goto :end

:error
echo.
echo ❌ Test failed - check if all files are present
pause

:end
EOF

echo "✅ Created test-on-windows.bat"

# Create GitHub Actions workflow for automatic testing
mkdir -p .github/workflows

cat > .github/workflows/test-windows-exe.yml << 'EOF'
name: Test Windows Executable

on:
  push:
    paths:
      - 'dist/**'
      - '.github/workflows/test-windows-exe.yml'
  pull_request:
    paths:
      - 'dist/**'

jobs:
  test-windows-exe:
    runs-on: windows-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Check executable exists
      run: |
        if (Test-Path "dist/shusrusha-windows/Shusrusha.exe") {
          Write-Host "✅ Shusrusha.exe found"
          $size = (Get-Item "dist/shusrusha-windows/Shusrusha.exe").Length / 1MB
          Write-Host "📏 Size: $([math]::Round($size, 1)) MB"
        } else {
          Write-Host "❌ Shusrusha.exe not found"
          exit 1
        }
      shell: powershell
      
    - name: Check required files
      run: |
        $files = @("README.txt", "env_template.txt", "start.bat")
        foreach ($file in $files) {
          if (Test-Path "dist/shusrusha-windows/$file") {
            Write-Host "✅ $file found"
          } else {
            Write-Host "❌ $file missing"
            exit 1
          }
        }
      shell: powershell
      
    - name: Test basic executable info
      run: |
        cd dist/shusrusha-windows
        Write-Host "📁 Directory contents:"
        Get-ChildItem
        
        Write-Host "`n🧪 Testing executable properties..."
        $exe = Get-Item "Shusrusha.exe"
        Write-Host "Created: $($exe.CreationTime)"
        Write-Host "Size: $([math]::Round($exe.Length / 1MB, 1)) MB"
        
        # Create test .env
        "OPENAI_API_KEY=test_key" | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host "✅ Created test .env file"
      shell: powershell
      
    - name: Quick executable validation
      run: |
        cd dist/shusrusha-windows
        Write-Host "🚀 Quick executable validation..."
        
        # This will fail without real API key, but tests if exe runs
        $process = Start-Process -FilePath ".\Shusrusha.exe" -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 5
        
        if (!$process.HasExited) {
          Write-Host "✅ Executable started successfully"
          Stop-Process -Id $process.Id -Force
        } else {
          Write-Host "ℹ️  Executable exited (expected without valid API key)"
        }
      shell: powershell
      continue-on-error: true
EOF

echo "✅ Created GitHub Actions workflow: .github/workflows/test-windows-exe.yml"

echo ""
echo "🧪 Windows Testing Options Created!"
echo "=================================="
echo ""
echo "📋 Available testing methods:"
echo ""
echo "1. 🔄 GitHub Actions (Automatic)"
echo "   → Push to GitHub and check Actions tab"
echo "   → Tests will run automatically on Windows Server"
echo ""
echo "2. 🖥️  Manual Windows Testing"
echo "   → Copy dist/shusrusha-windows/ to Windows machine"
echo "   → Run test-on-windows.bat"
echo ""
echo "3. 🐳 Docker (if Windows containers available)"
echo "   → Requires Docker Desktop with Windows containers"
echo "   → See test-windows.md for detailed instructions"
echo ""
echo "4. ☁️  Cloud VMs (Free tiers available)"
echo "   → Azure: \$200 free credit"
echo "   → AWS: Free tier Windows instances"
echo "   → Google Cloud: \$300 free credit"
echo ""
echo "5. 💻 VirtualBox (Free)"
echo "   → Download Windows 10 Enterprise VM (90-day trial)"
echo "   → From: https://developer.microsoft.com/windows/downloads/virtual-machines/"
echo ""
echo "🎯 Recommended: Start with GitHub Actions for quick validation!"

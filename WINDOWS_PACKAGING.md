# 🏥 Shusrusha Windows Packaging Guide

This document provides multiple methods to package and distribute the Shusrusha medical document processor for Windows users.

## ⚠️ Important Cross-Platform Note

**Architecture Compatibility**: Executables must be built on the target platform for best compatibility:
- **Windows executables**: Should be built on Windows (x86_64)
- **macOS executables**: Built on macOS (ARM64 or Intel)
- **Linux executables**: Built on Linux (x86_64)

The build scripts in this repository can run on any platform, but the resulting executables may not work across different operating systems and architectures.

## 🎯 Packaging Methods Overview

| Method | Complexity | Size | User Experience | Best For |
|--------|------------|------|-----------------|----------|
| **PyInstaller Executable** | Low | ~50MB | Single-click run | End users |
| **Portable Package** | Medium | ~100MB | Extract & run | Power users |
| **Docker Container** | High | ~500MB | Cross-platform | Developers |
| **Python Installation** | High | Varies | Manual setup | Technical users |

---

## 🚀 Method 1: PyInstaller (Recommended)

Creates a single executable file that includes Python and all dependencies.

### Setup PyInstaller

```bash
# Install PyInstaller
pip install pyinstaller

# Create the executable
pyinstaller --onefile --add-data "app.py;." --add-data "lib;lib" --add-data "requirements-app.txt;." --name "Shusrusha" app.py
```

### Advanced PyInstaller Script

Create `build_windows.py`:

```python
import PyInstaller.__main__
import os

# Build configuration
PyInstaller.__main__.run([
    'app.py',
    '--onefile',
    '--windowed',  # Hide console window
    '--name=Shusrusha',
    '--icon=icon.ico',  # Add if you have an icon
    '--add-data=lib;lib',
    '--add-data=requirements-app.txt;.',
    '--hidden-import=streamlit',
    '--hidden-import=langgraph_app',
    '--hidden-import=PIL',
    '--collect-all=streamlit',
    '--collect-all=altair',
    '--distpath=dist/windows',
    '--workpath=build/windows',
])
```

---

## 🖥️ Method 2: Auto-py-to-exe (GUI Tool)

User-friendly GUI for PyInstaller.

### Installation

```bash
pip install auto-py-to-exe
```

### Usage

1. Run `auto-py-to-exe`
2. Configure settings:
   - **Script Location**: Select `app.py`
   - **Onefile**: Yes
   - **Console Window**: No (for cleaner experience)
   - **Additional Files**: Add `lib` folder and `requirements-app.txt`
3. Click "Convert .py to .exe"

---

## 🐳 Method 3: Docker Container

Cross-platform containerized solution.

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
```

### Build and Run

```bash
# Build the Docker image
docker build -t shusrusha .

# Run the container
docker run -p 8501:8501 -e OPENAI_API_KEY=your_key_here shusrusha
```

---

## 📦 Method 4: Portable Python Package

Create a portable package with Python included.

### Create `package_portable.py`

```python
import os
import shutil
import zipfile
from pathlib import Path

def create_portable_package():
    """Create a portable Windows package"""
    
    # Create package directory
    package_dir = Path("dist/shusrusha-portable")
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy application files
    files_to_copy = [
        "app.py",
        "langgraph_app.py",
        "requirements-app.txt",
        "setup.bat",
        "run.bat",
        "README-APP.md",
        "lib/",
    ]
    
    for file_path in files_to_copy:
        src = Path(file_path)
        if src.is_file():
            shutil.copy2(src, package_dir / src.name)
        elif src.is_dir():
            shutil.copytree(src, package_dir / src.name, dirs_exist_ok=True)
    
    # Create startup script
    startup_script = package_dir / "start_shusrusha.bat"
    with open(startup_script, 'w') as f:
        f.write('''@echo off
echo 🏥 Starting Shusrusha Medical Document Processor...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist ".venv" (
    echo 📦 Setting up virtual environment...
    python -m venv .venv
    call .venv\\Scripts\\activate.bat
    pip install -r requirements-app.txt
) else (
    call .venv\\Scripts\\activate.bat
)

REM Check for .env file
if not exist ".env" (
    echo ⚙️ Creating .env file...
    echo OPENAI_API_KEY=your_openai_api_key_here > .env
    echo.
    echo ❗ IMPORTANT: Please edit .env file and add your OpenAI API key
    echo Then run this script again.
    pause
    exit /b 1
)

REM Start the application
echo 🚀 Launching Shusrusha...
echo 📱 The app will open at: http://localhost:8501
echo 🛑 Press Ctrl+C to stop
echo.
streamlit run app.py
''')
    
    # Create ZIP package
    zip_path = Path("dist/shusrusha-portable-windows.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir.parent)
                zipf.write(file_path, arcname)
    
    print(f"✅ Portable package created: {zip_path}")
    print(f"📁 Package folder: {package_dir}")

if __name__ == "__main__":
    create_portable_package()
```

---

## 🎯 Recommended Approach

For most users, I recommend **Method 1 (PyInstaller)** because:

1. ✅ **Single file** - Easy to distribute
2. ✅ **No Python installation required**
3. ✅ **Professional appearance**
4. ✅ **Includes all dependencies**

### Quick Start Commands

```bash
# Install PyInstaller
pip install pyinstaller

# Create the Windows executable
pyinstaller --onefile --windowed --name="Shusrusha" --add-data="lib;lib" app.py

# The executable will be in dist/Shusrusha.exe
```

The resulting `Shusrusha.exe` file can be distributed to any Windows computer and will run without requiring Python installation!

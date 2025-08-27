# 🚀 Quick Windows Deployment Guide

## Option 1: Single Executable (Recommended)

### For Developers:
```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
python build_windows.py

# Or use the build system
python build_all.py
```

### For End Users:
1. Download `Shusrusha.exe`
2. Double-click to run
3. App opens at http://localhost:8501
4. Add OpenAI API key in the sidebar

## Option 2: Portable Package

### For Developers:
```bash
# Create portable package
python package_portable.py
```

### For End Users:
1. Download and extract `shusrusha-portable-windows.zip`
2. Run `start_shusrusha.bat`
3. Follow setup prompts
4. Edit `.env` file with API key

## Option 3: Docker (Cross-platform)

### Build and Run:
```bash
# Build container
docker build -t shusrusha .

# Run with API key
docker run -p 8501:8501 -e OPENAI_API_KEY=your_key_here shusrusha

# Or use docker-compose
docker-compose up
```

## Quick Commands

### Build Everything:
```bash
python build_all.py
```

### Just PyInstaller:
```bash
python build_windows.py
```

### Just Portable:
```bash
python package_portable.py
```

## Requirements
- Python 3.8+
- OpenAI API key
- Internet connection

## Support
- Windows 10+
- 2GB RAM minimum
- 100MB disk space

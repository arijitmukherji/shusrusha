# Building Shusrusha on Windows

## Prerequisites
1. Install Python 3.8+ from https://python.org/downloads/
2. Install Git from https://git-scm.com/download/win
3. Download this project as ZIP or clone with Git

## Steps to Build on Windows

### 1. Setup Environment
```cmd
# Open Command Prompt or PowerShell as Administrator
cd path\to\shusrusha
python -m pip install --upgrade pip
pip install -r requirements-app.txt
pip install pyinstaller
```

### 2. Set Environment Variable
Create a `.env` file in the project directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Build the Executable
```cmd
python build_windows_native.py
```

### 4. Test the Build
```cmd
cd dist\windows
Shusrusha.exe
```

## Troubleshooting Windows Issues

### Common Problems:

#### 1. "MSVCP140.dll missing"
**Solution**: Install Microsoft Visual C++ Redistributable
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Install and restart computer

#### 2. "Python not found"
**Solution**: Reinstall Python with "Add to PATH" checked
- Download Python installer
- Check "Add Python to PATH" during installation
- Restart Command Prompt

#### 3. "ModuleNotFoundError"
**Solution**: Install missing packages
```cmd
pip install -r requirements-app.txt
```

#### 4. "OpenAI API Error"
**Solution**: Check your API key
- Verify `.env` file exists with correct API key
- Test API key at https://platform.openai.com/

#### 5. "Permission Denied"
**Solution**: Run as Administrator
- Right-click Command Prompt → "Run as Administrator"
- Or disable Windows Defender temporarily during build

#### 6. "Long Path Issues"
**Solution**: Enable long paths in Windows
```cmd
# Run as Administrator
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1
```

### Build Optimization
For smaller executable size:
```cmd
# Edit build_windows_native.py and uncomment:
# '--exclude-module', 'matplotlib',
# '--exclude-module', 'scipy',
# '--exclude-module', 'numpy',
```

### Testing Your Build
1. Copy the `dist\windows\Shusrusha.exe` to a different Windows computer
2. Double-click to run the application
3. Test with a sample medical document image

## Distribution
Once built on Windows, you can:
1. **Share the executable**: Just send `Shusrusha.exe` 
2. **Create installer**: Use tools like NSIS or Inno Setup
3. **Package as ZIP**: Include all dependencies in a folder

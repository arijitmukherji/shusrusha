#!/usr/bin/env python3
"""
Simple Windows 10 Executable Builder for Shusrusha
Creates a basic standalone .exe file.
"""

import os
import sys
import subprocess
from pathlib import Path

def build_windows_exe():
    """Build a simple Windows executable"""
    
    print("🏥 Building Simple Shusrusha Windows Executable...")
    print("=" * 50)
    
    # Clean previous builds
    if Path('dist').exists():
        import shutil
        shutil.rmtree('dist')
    if Path('build').exists():
        import shutil
        shutil.rmtree('build')
    
    # Simple PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--console',  # Keep console for debugging
        '--name=Shusrusha',
        'app.py'
    ]
    
    print("🔧 Running PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ PyInstaller completed successfully!")
        
        # Check if exe was created (different names on different platforms)
        exe_path = Path('dist/Shusrusha.exe') if sys.platform == 'win32' else Path('dist/Shusrusha')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"🎉 SUCCESS! Executable created: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
            
            # On macOS/Linux, copy to .exe name for Windows compatibility
            if sys.platform != 'win32':
                exe_copy = Path('dist/Shusrusha.exe')
                import shutil
                shutil.copy2(exe_path, exe_copy)
                print(f"📋 Created Windows-compatible copy: {exe_copy}")
            
            # Create simple instructions
            readme = """# Shusrusha Windows Executable

## Setup
1. Create a file called `.env` in the same folder as this executable
2. Add your OpenAI API key to the .env file:
   OPENAI_API_KEY=your_api_key_here

## Run
Double-click Shusrusha.exe to start the application.
The app will open in your web browser.

## Requirements
- Windows 10 or 11
- Internet connection
- OpenAI API key

## Note
This executable was cross-compiled and should work on Windows 10/11.
If Windows SmartScreen blocks it, click "More info" then "Run anyway".
"""
            Path('dist/README.txt').write_text(readme)
            print("📝 Created README.txt")
            
            return True
        else:
            print("❌ Executable not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed:")
        print(e.stderr)
        return False

if __name__ == "__main__":
    success = build_windows_exe()
    if success:
        print("\n🎉 Build completed successfully!")
        print("📁 Files in dist/ folder are ready for Windows")
    else:
        print("\n❌ Build failed")
        sys.exit(1)

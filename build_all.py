#!/usr/bin/env python3
"""
Master build script for creating Windows distributions of Shusrusha
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def check_requirements():
    """Check if required tools are available"""
    print("🔍 Checking requirements...")
    
    # Check Python
    try:
        python_version = subprocess.check_output([sys.executable, '--version'], text=True).strip()
        print(f"✅ {python_version}")
    except:
        print("❌ Python not found")
        return False
    
    # Check if we can import required modules
    required_modules = ['streamlit', 'openai', 'requests', 'beautifulsoup4', 'python-dotenv']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module.replace('-', '_'))
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"⚠️ Missing modules: {missing_modules}")
        print("Install with: pip install -r requirements-app.txt")
    else:
        print("✅ All required modules available")
    
    return len(missing_modules) == 0

def run_command(cmd, description, shell=True):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}...")
    try:
        if isinstance(cmd, list):
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, shell=shell, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False, e.stderr

def build_pyinstaller():
    """Build with PyInstaller"""
    print("\n🔧 Installing PyInstaller...")
    success, _ = run_command([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], "PyInstaller installation")
    if not success:
        return False
    
    # Run the build script
    success, _ = run_command([sys.executable, 'build_windows.py'], "PyInstaller build")
    return success

def build_portable():
    """Build portable package"""
    print("\n📦 Creating portable package...")
    try:
        success, _ = run_command([sys.executable, 'package_portable.py'], "Portable package creation")
        return success
    except Exception as e:
        print(f"❌ Portable build failed: {e}")
        return False

def install_auto_py_to_exe():
    """Install and launch auto-py-to-exe"""
    print("\n🖥️ Installing auto-py-to-exe...")
    success, _ = run_command([sys.executable, '-m', 'pip', 'install', 'auto-py-to-exe'], "auto-py-to-exe installation")
    
    if success:
        print("\n🚀 Launching auto-py-to-exe GUI...")
        print("Configure the following settings:")
        print("- Script Location: app.py")
        print("- Onefile: Yes")
        print("- Console Window: No")
        print("- Additional Files: lib folder")
        print("- Icon: icon.ico (if available)")
        
        try:
            subprocess.run([sys.executable, '-m', 'auto_py_to_exe'], check=False)
        except:
            print("You can also run: python -m auto_py_to_exe")
    
    return success

def main():
    """Interactive build system for Shusrusha Windows packages"""
    
    print("🏥 Shusrusha Windows Build System")
    print("=" * 50)
    
    # Check platform
    current_platform = platform.system()
    print(f"🖥️  Current platform: {current_platform}")
    
    if current_platform != "Windows":
        print("⚠️  WARNING: Building on non-Windows platform!")
        print("   Executables built here may not work properly on Windows.")
        print("   For best results, run this on a Windows machine.")
        print()
    
    print("Choose a packaging method:")
    print()
    print("1. 🚀 PyInstaller Executable (~50MB)")
    print("   Single .exe file with everything included")
    print("   ✅ Best for end users")
    print()
    print("2. � Portable Package (~100MB)")  
    print("   ZIP file with Python + dependencies")
    print("   ✅ Best for power users")
    print()
    print("3. 🐳 Docker Container (~500MB)")
    print("   Cross-platform containerized app")
    print("   ✅ Best for developers")
    print()
    print("4. � Show system info")
    print("   Display build environment details")
    print()
    print("0. ❌ Exit")
    print()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Enhanced Windows 10 Executable Builder for Shusrusha
Creates a standalone .exe file that works on Windows 10/11 without Python installation.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import json

def check_dependencies():
    """Check if all required packages are installed."""
    import subprocess
    import sys
    
    # Check pyinstaller as command
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                      capture_output=True, check=True)
        print("✅ PyInstaller detected")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found")
        return False
    
    # Check Python packages
    required_packages = [
        ('beautifulsoup4', 'bs4'),
        ('python-dotenv', 'dotenv'), 
        ('pillow', 'PIL'),
        ('streamlit', 'streamlit'),
        ('openai', 'openai'),
        ('requests', 'requests'),
        ('langgraph', 'langgraph')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} detected")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} missing")
    
    if missing_packages:
        print(f"💡 Install missing packages with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def create_config_template():
    """Create a configuration template for users"""
    config_content = '''# Shusrusha Configuration
# Copy this file to the same directory as Shusrusha.exe and rename to .env

# Required: OpenAI API Key for medical document processing
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Advanced Settings
# OPENAI_BASE_URL=https://api.openai.com/v1
# MAX_RETRIES=3
# TIMEOUT_SECONDS=60

# Instructions:
# 1. Get your OpenAI API key from https://platform.openai.com/api-keys
# 2. Replace "your_openai_api_key_here" with your actual API key
# 3. Save this file as ".env" (including the dot) in the same folder as Shusrusha.exe
# 4. Double-click Shusrusha.exe to run the application
'''
    
    Path('dist/windows/config_template.txt').write_text(config_content, encoding='utf-8')
    print("✅ Created config_template.txt for users")

def create_readme():
    """Create README for Windows distribution"""
    readme_content = '''# Shusrusha - Medical Document Processor

## Quick Start Guide

### 1. Setup (First Time Only)
1. Copy `config_template.txt` and rename it to `.env`
2. Edit `.env` file and add your OpenAI API key
3. Double-click `Shusrusha.exe` to start the application

### 2. Using the Application
- The app will open in your default web browser
- Upload medical document images (JPEG, PNG formats)
- Click "Process Documents" to extract information
- Download results as HTML files

### 3. System Requirements
- Windows 10 or Windows 11
- Internet connection for OpenAI API calls
- At least 2GB free RAM
- 500MB free disk space

### 4. Troubleshooting
- **App doesn't start**: Check Windows Defender/antivirus settings
- **API errors**: Verify your OpenAI API key in the .env file
- **Slow performance**: Ensure stable internet connection

### 5. Support
- For technical issues, check the console window for error messages
- Ensure your OpenAI account has sufficient credits
- The app creates logs in the same directory

## Security Note
This executable may trigger Windows SmartScreen on first run. 
Click "More info" then "Run anyway" if prompted.

---
Built with ❤️ for medical professionals in India
'''
    
    Path('dist/windows/README.txt').write_text(readme_content, encoding='utf-8')
    print("✅ Created README.txt for users")

def main():
    """Build enhanced Windows 10 executable"""
    
    print("🏥 Building Shusrusha for Windows 10/11...")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Please install missing dependencies first")
        sys.exit(1)
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if required files exist
    required_files = ['app.py', 'langgraph_app.py', 'lib/graph_utils.py']
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        sys.exit(1)
    
    # Clean previous builds
    if Path('dist/windows').exists():
        print("🧹 Cleaning previous build...")
        shutil.rmtree('dist/windows')
    if Path('build/windows').exists():
        shutil.rmtree('build/windows')
    
    print("✅ All required files found")
    
    # Enhanced PyInstaller configuration for Windows 10
    # Use proper separator based on current platform (: for macOS/Linux, ; for Windows)
    import platform
    sep = ';' if platform.system() == 'Windows' else ':'
    
    build_args = [
        sys.executable, '-m', 'PyInstaller',
        'app.py',
        '--onefile',
        '--console',  # Keep console for easier debugging
        '--name=Shusrusha',
        '--distpath=dist/windows',
        '--workpath=build/windows',
        '--specpath=build/windows',
        
        # Add data files (only include files that exist)
        f'--add-data=langgraph_app.py{sep}.',
        f'--add-data=lib/__init__.py{sep}lib',
        f'--add-data=lib/graph_utils.py{sep}lib',
        
        # Comprehensive hidden imports
        '--hidden-import=streamlit',
        '--hidden-import=langgraph_app', 
        '--hidden-import=lib.graph_utils',
        '--hidden-import=openai',
        '--hidden-import=requests',
        '--hidden-import=bs4',
        '--hidden-import=dotenv',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=subprocess',
        '--hidden-import=webbrowser',
        '--hidden-import=json',
        '--hidden-import=typing',
        '--hidden-import=pathlib',
        '--hidden-import=concurrent.futures',
        '--hidden-import=threading',
        '--hidden-import=time',
        '--hidden-import=random',
        '--hidden-import=re',
        '--hidden-import=urllib.parse',
        '--hidden-import=base64',
        '--hidden-import=os',
        '--hidden-import=sys',
        
        # Streamlit specific
        '--collect-all=streamlit',
        '--collect-all=altair',
        '--collect-all=plotly',
        
        # Windows specific optimizations
        '--optimize=2',
        '--strip',
        '--noupx',  # Disable UPX compression for better Windows compatibility
        
        # Clean build
        '--clean',
        '--noconfirm',
        
        # Additional Windows compatibility
        '--exclude-module=_tkinter',  # Exclude if not needed to reduce size
    ]
    
    # Add icon if available
    icon_path = Path('icon.ico')
    if icon_path.exists():
        build_args.append(f'--icon={icon_path}')
        print("✅ Using custom icon")
    else:
        print("💡 No icon.ico found - using default")
    
    print("🔧 Building executable with PyInstaller...")
    print(f"🎯 Target: Windows 10/11 (64-bit)")
    print(f"📁 Output: dist/windows/Shusrusha.exe")
    
    try:
        # Run PyInstaller using subprocess
        print(f"🔧 Running: {' '.join(build_args[:5])}...")  # Show first few args
        result = subprocess.run(build_args, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ PyInstaller failed with error:")
            print(result.stderr)
            return False
            
        print("✅ PyInstaller completed successfully")
        
        # Check if build was successful
        exe_path = Path('dist/windows/Shusrusha.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            
            # Create user documentation
            create_config_template()
            create_readme()
            
            print(f"\n🎉 SUCCESS! Windows executable created!")
            print(f"📱 Executable: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
            print(f"\n📦 Distribution Package Contents:")
            print(f"   ├── Shusrusha.exe          (Main application)")
            print(f"   ├── config_template.txt    (API key setup guide)")
            print(f"   └── README.txt             (User instructions)")
            
            print(f"\n🚀 Distribution Instructions:")
            print(f"   1. Copy entire 'dist/windows/' folder to target machine")
            print(f"   2. User follows README.txt to setup API key")
            print(f"   3. Double-click Shusrusha.exe to run")
            print(f"   4. App opens in web browser automatically")
            
            print(f"\n✅ Windows 10/11 Compatibility:")
            print(f"   • No Python installation required")
            print(f"   • Self-contained executable")
            print(f"   • Automatic browser launch")
            print(f"   • File dialogs for image selection")
            print(f"   • Download links for results")
            
            print(f"\n⚠️  Security Notes:")
            print(f"   • Windows may show SmartScreen warning (normal for new apps)")
            print(f"   • Antivirus may scan on first run (expected)")
            print(f"   • Users need valid OpenAI API key")
            
        else:
            print("❌ Build failed - executable not found")
            print("🔍 Checking build output...")
            dist_path = Path('dist/windows')
            if dist_path.exists():
                print("Files created:")
                for f in dist_path.iterdir():
                    print(f"  📄 {f.name}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Build failed with error: {e}")
        print(f"\n🔧 Troubleshooting Steps:")
        print(f"   1. Ensure all dependencies installed: pip install -r requirements-app.txt pyinstaller")
        print(f"   2. Check Python version compatibility (3.8-3.11 recommended)")
        print(f"   3. Try running from clean virtual environment")
        print(f"   4. Check console output above for specific errors")
        sys.exit(1)

if __name__ == "__main__":
    main()

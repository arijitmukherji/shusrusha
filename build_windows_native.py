#!/usr/bin/env python3
"""
PyInstaller build script for Shusrusha Windows executable
This script should be run on a Windows machine to create a native Windows executable.
"""

import PyInstaller.__main__
import os
import sys
from pathlib import Path

def main():
    """Build Shusrusha as a Windows executable on Windows"""
    
    print("🏥 Building Shusrusha for Windows (Native Build)...")
    print("=" * 60)
    
    # Check if running on Windows
    if os.name != 'nt':
        print("⚠️ This script should be run on Windows for best results!")
        print("The executable created on non-Windows systems may not work on Windows.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Build cancelled.")
            sys.exit(0)
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if required files exist
    required_files = ['app.py', 'langgraph_app.py', 'lib/graph_utils.py']
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        sys.exit(1)
    
    print("✅ All required files found")
    
    # PyInstaller configuration for Windows
    build_args = [
        'app.py',
        '--onefile',
        '--windowed',  # Hide console for Windows GUI apps
        '--name=Shusrusha',
        '--distpath=dist/windows',
        '--workpath=build/windows',
        '--specpath=build/windows',
        
        # Add data files (Windows uses semicolon separator)
        f'--add-data=lib;lib',
        f'--add-data=langgraph_app.py;.',
        
        # Hidden imports for modules that PyInstaller might miss
        '--hidden-import=streamlit',
        '--hidden-import=langgraph_app',
        '--hidden-import=lib.graph_utils',
        '--hidden-import=openai',
        '--hidden-import=requests',
        '--hidden-import=bs4',  # beautifulsoup4 import name
        '--hidden-import=dotenv',  # python-dotenv import name
        '--hidden-import=PIL',
        '--hidden-import=tkinter',
        '--hidden-import=subprocess',
        '--hidden-import=webbrowser',
        '--hidden-import=json',
        '--hidden-import=typing',
        '--hidden-import=pathlib',
        
        # Collect streamlit's complex dependencies
        '--collect-all=streamlit',
        
        # Optimization
        '--optimize=2',
        '--strip',  # Remove debug symbols for smaller size
        
        # Clean build
        '--clean',
    ]
    
    # Add icon if available
    icon_path = Path('icon.ico')
    if icon_path.exists():
        build_args.append(f'--icon={icon_path}')
        print("✅ Using custom icon")
    
    print("🔧 Starting PyInstaller build...")
    print(f"📁 Output directory: dist/windows/")
    print(f"🎯 Target platform: Windows")
    
    try:
        # Run PyInstaller
        PyInstaller.__main__.run(build_args)
        
        # Check if build was successful
        exe_path = Path('dist/windows/Shusrusha.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✅ Build completed successfully!")
            print(f"📱 Executable: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
            print(f"\n🚀 Distribution Instructions:")
            print(f"   1. Copy 'Shusrusha.exe' to the target Windows machine")
            print(f"   2. Users can double-click to run (no installation needed)")
            print(f"   3. First run may take longer as Windows scans the file")
            print(f"\n💡 Tips:")
            print(f"   - Test on Windows 10/11 before distributing")
            print(f"   - Antivirus may flag unknown executables initially")
            print(f"   - Users need OPENAI_API_KEY environment variable or .env file")
        else:
            print("❌ Build failed - executable not found")
            # List what was actually created
            dist_path = Path('dist/windows')
            if dist_path.exists():
                print("Files created:")
                for f in dist_path.iterdir():
                    print(f"  {f.name}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Build failed with error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   - Ensure all dependencies are installed: pip install -r requirements-app.txt")
        print("   - Try running with --debug flag for more information")
        print("   - Check PyInstaller compatibility with your Python version")
        sys.exit(1)

if __name__ == "__main__":
    main()

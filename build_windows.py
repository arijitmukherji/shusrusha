#!/usr/bin/env python3
"""
PyInstaller build script for Shusrusha Windows executable
"""

import PyInstaller.__main__
import os
import sys
from pathlib import Path

def main():
    """Build Shusrusha as a Windows executable"""
    
    print("🏥 Building Shusrusha for Windows with PyInstaller...")
    print("=" * 60)
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Determine the correct separator for add-data based on OS
    # PyInstaller uses : on Unix-like systems and ; on Windows
    separator = ':' if os.name != 'nt' else ';'
    
    # Check if required files exist
    required_files = ['app.py', 'langgraph_app.py', 'lib/graph_utils.py']
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        sys.exit(1)
    
    print("✅ All required files found")
    
    # PyInstaller configuration
    build_args = [
        'app.py',
        '--onefile',
        '--name=Shusrusha',
        '--distpath=dist/windows',
        '--workpath=build/windows',
        '--specpath=build/windows',
        
        # Add data files - use absolute paths to avoid issues
        f'--add-data={script_dir}/lib{separator}lib',
        f'--add-data={script_dir}/langgraph_app.py{separator}.',
        
        # Hidden imports for modules that PyInstaller might miss
        '--hidden-import=streamlit',
        '--hidden-import=langgraph_app',
        '--hidden-import=lib.graph_utils',
        '--hidden-import=openai',
        '--hidden-import=requests',
        '--hidden-import=beautifulsoup4',
        '--hidden-import=python-dotenv',
        '--hidden-import=PIL',
        '--hidden-import=tkinter',
        '--hidden-import=subprocess',
        '--hidden-import=webbrowser',
        
        # Optimization
        '--optimize=2',
        
        # Console options - keep console visible for debugging
        '--console',
    ]
    
    # Add icon if available
    icon_path = Path('icon.ico')
    if icon_path.exists():
        build_args.append(f'--icon={icon_path}')
        print("✅ Using custom icon")
    
    print("🔧 Starting PyInstaller build...")
    print(f"📁 Output directory: dist/windows/")
    
    try:
        # Run PyInstaller
        PyInstaller.__main__.run(build_args)
        
        # Check if build was successful
        exe_name = 'Shusrusha.exe' if os.name == 'nt' else 'Shusrusha'
        exe_path = Path(f'dist/windows/{exe_name}')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✅ Build completed successfully!")
            print(f"📱 Executable: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
            print(f"\n🚀 You can now distribute '{exe_name}' to Windows users")
            if os.name == 'nt':
                print(f"💡 Users just need to double-click the .exe file to run the app")
            else:
                print(f"💡 This binary was built on macOS - test on Windows before distributing")
                print(f"💡 Windows users will run this as an executable file")
        else:
            print("❌ Build failed - executable not found")
            print(f"Expected: {exe_path}")
            # List what was actually created
            dist_path = Path('dist/windows')
            if dist_path.exists():
                print("Files created:")
                for f in dist_path.iterdir():
                    print(f"  {f.name}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Build failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def main():
    import shutil
    # Ensure we execute in the project directory
    os.chdir(Path(__file__).parent)
    
    print("Building one-directory distribution (fast startup for dev)...")
    temp_dist = Path("dist/amiga-reader-dir-temp")
    target_dist = Path("dist/amiga-reader-dir")
    
    # 1. Run PyInstaller in onedir mode with the desired executable name
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller", 
        "--onedir", 
        "--name", "amiga-reader", 
        "--distpath", str(temp_dist),
        "--clean", 
        "--paths", "src", 
        "src/amiga_reader/amiga_reader.py"
    ])
    
    # 2. Rename/Move the folder to the target 'dist/amiga-reader-dir' and clean up temp
    if target_dist.exists():
        shutil.rmtree(target_dist)
    shutil.move(temp_dist / "amiga-reader", target_dist)
    shutil.rmtree(temp_dist)
    
    print("\nBuilding one-file standalone executable...")
    # 3. Run PyInstaller in onefile mode
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller", 
        "--onefile", 
        "--name", "amiga-reader", 
        "--clean", 
        "--paths", "src", 
        "src/amiga_reader/amiga_reader.py"
    ])
    
    print("\n✓ Build complete!")
    print("  - Fast Startup Dev Folder:        dist/amiga-reader-dir/amiga-reader")
    print("  - Standalone One-File Executable:  dist/amiga-reader")

if __name__ == "__main__":
    main()
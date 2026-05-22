#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def main():
    # Ensure we execute in the project directory
    os.chdir(Path(__file__).parent)
    
    print("Building one-file executable with PyInstaller...")
    
    # Run PyInstaller
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "--onefile", "--name", "amiga-reader", "--clean", "--paths", "src", "src/amiga_reader/amiga_reader.py"])
    
    print("\n✓ Build complete! Check the 'dist' directory for your executable.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
TrackIT Verification & Setup Script
Checks system requirements and initializes the project
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verify Python 3.8+"""
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_pip():
    """Verify pip is available"""
    try:
        result = subprocess.run(['pip', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("✗ pip not found")
    return False

def init_project():
    """Run project initialization"""
    print("\nInitializing project structure...")
    try:
        from init_project import create_project_structure
        create_project_structure()
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def install_dependencies():
    """Install Python packages"""
    print("\nInstalling dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                      check=True, capture_output=True)
        print("✓ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Installation failed: {e}")
        return False

def main():
    """Main setup routine"""
    print("="*60)
    print("TrackIT - Asset & Inventory Management System")
    print("System Setup & Verification")
    print("="*60)
    
    checks = [
        ("Python version", check_python_version),
        ("pip availability", check_pip),
        ("Project structure", init_project),
    ]
    
    for name, check_func in checks:
        print(f"\n[{name}]")
        if not check_func():
            print(f"\n✗ Setup failed at: {name}")
            return False
    
    print("\n" + "="*60)
    print("✓ All checks passed!")
    print("="*60)
    print("\nNext steps:")
    print("  1. pip install -r requirements.txt  (or run this script's install)")
    print("  2. python db_seed.py")
    print("  3. python run.py")
    print("\nOpen http://localhost:5000 in your browser")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

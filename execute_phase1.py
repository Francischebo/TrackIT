#!/usr/bin/env python3
"""
TrackIT Execution Guide
Run this after Phase 1 to verify everything works
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report status"""
    print(f"\n{'='*60}")
    print(f"[{description}]")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"✓ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - FAILED")
        print(f"Error: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ Command not found: {cmd[0]}")
        return False

def main():
    """Execute Phase 1 verification steps"""
    
    print("="*60)
    print("TrackIT - Phase 1 Execution Guide")
    print("="*60)
    
    root = Path(__file__).parent
    os.chdir(root)
    
    steps = [
        (
            [sys.executable, "init_project.py"],
            "Initialize Project Structure"
        ),
        (
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            "Install Dependencies"
        ),
        (
            [sys.executable, "db_seed.py"],
            "Seed Database with Test Data"
        ),
    ]
    
    print("\nThis guide will:")
    print("1. Initialize the project structure")
    print("2. Install Python dependencies")
    print("3. Create and seed the database")
    print("\nAfter completion, run:")
    print("  python run.py")
    print("Then open http://localhost:5000")
    
    all_success = True
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            all_success = False
            print(f"\n✗ Stopping at: {desc}")
            print("Please fix the error above and try again")
            return False
    
    print(f"\n{'='*60}")
    print("✓ ALL STEPS COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}")
    
    print("\nYour TrackIT application is ready!")
    print("\nNext Steps:")
    print("1. Start the development server:")
    print("   python run.py")
    print("\n2. Open your browser:")
    print("   http://localhost:5000")
    print("\n3. Login with test credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\nOr read QUICK_REFERENCE.md for complete test credentials")
    print("\nPress Ctrl+C to stop the server when done")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

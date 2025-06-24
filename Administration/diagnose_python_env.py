#!/usr/bin/env python3
"""
Diagnose Python environment issues
"""

import sys
import subprocess
import os
from pathlib import Path

print("=== Python Environment Diagnostic ===\n")

# 1. Python info
print("1. Python Information:")
print(f"   Python executable: {sys.executable}")
print(f"   Python version: {sys.version}")
print(f"   Python prefix: {sys.prefix}")

# 2. Pip info
print("\n2. Pip Information:")
try:
    pip_version = subprocess.check_output([sys.executable, '-m', 'pip', '--version'], text=True)
    print(f"   Pip version: {pip_version.strip()}")
except Exception as e:
    print(f"   ✗ Error getting pip version: {e}")

# 3. Check installed packages
print("\n3. Checking installed packages:")
try:
    installed_packages = subprocess.check_output([sys.executable, '-m', 'pip', 'list'], text=True)
    
    # Check for our specific packages
    packages_to_check = ['python-dotenv', 'dotenv', 'flask', 'alpaca-trade-api']
    for package in packages_to_check:
        if package.lower() in installed_packages.lower():
            # Get specific line
            for line in installed_packages.split('\n'):
                if package.lower() in line.lower():
                    print(f"   ✓ Found: {line.strip()}")
                    break
        else:
            print(f"   ✗ Not found: {package}")
            
except Exception as e:
    print(f"   ✗ Error listing packages: {e}")

# 4. Python path
print("\n4. Python Path (sys.path):")
for i, path in enumerate(sys.path[:5]):  # Show first 5 paths
    print(f"   [{i}] {path}")
if len(sys.path) > 5:
    print(f"   ... and {len(sys.path) - 5} more paths")

# 5. Site packages location
print("\n5. Site packages location:")
try:
    import site
    site_packages = site.getsitepackages()
    for sp in site_packages:
        print(f"   - {sp}")
        # Check if dotenv exists there
        dotenv_path = Path(sp) / 'dotenv'
        if dotenv_path.exists():
            print(f"     ✓ dotenv found here!")
except Exception as e:
    print(f"   ✗ Error getting site packages: {e}")

# 6. Virtual environment check
print("\n6. Virtual Environment Check:")
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("   ✓ Running in a virtual environment")
    print(f"   Base prefix: {getattr(sys, 'base_prefix', 'N/A')}")
else:
    print("   ✗ NOT running in a virtual environment")
    
# Check for venv
if 'VIRTUAL_ENV' in os.environ:
    print(f"   VIRTUAL_ENV: {os.environ['VIRTUAL_ENV']}")

# 7. Try different install methods
print("\n7. Installation Commands to Try:")
print("   Option 1 (recommended):")
print(f"   {sys.executable} -m pip install python-dotenv")
print("\n   Option 2 (if Option 1 fails):")
print(f"   {sys.executable} -m pip install --user python-dotenv")
print("\n   Option 3 (force reinstall):")
print(f"   {sys.executable} -m pip install --force-reinstall python-dotenv")

# 8. Test import in subprocess
print("\n8. Testing import in subprocess:")
test_code = "from dotenv import load_dotenv; print('SUCCESS: dotenv imported')"
try:
    result = subprocess.run(
        [sys.executable, '-c', test_code],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"   ✓ {result.stdout.strip()}")
    else:
        print(f"   ✗ Import failed: {result.stderr.strip()}")
except Exception as e:
    print(f"   ✗ Test failed: {e}")

print("\n" + "="*50)
print("RECOMMENDATION:")
print("="*50)
print("Run this command to install python-dotenv:")
print(f"\n   {sys.executable} -m pip install python-dotenv\n")
print("If that doesn't work, try:")
print(f"\n   {sys.executable} -m pip install --user python-dotenv\n")

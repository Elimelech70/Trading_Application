#!/usr/bin/env python3
"""
Robust requirement installer for Trading Application
Handles common pip issues in Codespaces
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and return success status"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    print("🔧 Installing Trading Application Requirements\n")
    
    # Step 1: Upgrade pip and core tools
    print("Step 1: Upgrading pip and setuptools...")
    if not run_command(f"{sys.executable} -m pip install --upgrade pip setuptools wheel"):
        print("❌ Failed to upgrade pip/setuptools")
        return 1
    
    # Step 2: Install requirements one by one to identify issues
    requirements = [
        "flask==3.0.0",
        "requests==2.31.0",
        "pandas==2.1.4",
        "numpy==1.26.2",
        "scikit-learn==1.3.2",
        "yfinance==0.2.33",
        "psutil==5.9.6",
        "python-dateutil==2.8.2",
        "pytz==2023.3",
        "beautifulsoup4==4.12.2",
        "lxml==4.9.3"
    ]
    
    print("\nStep 2: Installing packages...")
    failed = []
    
    for req in requirements:
        print(f"\nInstalling {req}...")
        if not run_command(f"{sys.executable} -m pip install {req}"):
            failed.append(req)
            print(f"⚠️  Failed to install {req}")
        else:
            print(f"✅ {req} installed")
    
    # Step 3: Try to install Alpaca separately (often causes issues)
    print("\nStep 3: Attempting Alpaca installation...")
    if not run_command(f"{sys.executable} -m pip install alpaca-py==0.21.1"):
        print("⚠️  Alpaca installation failed - you can run without it")
        print("   Paper trading will use mock trades instead")
    else:
        print("✅ Alpaca installed successfully")
    
    # Summary
    print("\n" + "="*50)
    print("📊 Installation Summary:")
    print(f"✅ Successful: {len(requirements) - len(failed)} packages")
    
    if failed:
        print(f"❌ Failed: {len(failed)} packages")
        for pkg in failed:
            print(f"   - {pkg}")
        print("\nYour trading system can still run, but some features may be limited.")
    else:
        print("\n🎉 All packages installed successfully!")
    
    print("\n🚀 Next step: python setup_codespace.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
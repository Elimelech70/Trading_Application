#!/usr/bin/env python3
"""
Name of Service: Test Alpaca Import
Filename: test_alpaca_import.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Test if alpaca-trade-api is properly installed
  - Checks if module can be imported
  - Shows version information
  - Tests basic functionality

DESCRIPTION:
Quick test to see if alpaca-trade-api is installed and working
in the current environment.
"""

import sys
import subprocess

def test_alpaca_import():
    """Test if alpaca-trade-api can be imported"""
    
    print("=" * 60)
    print("TESTING ALPACA-TRADE-API INSTALLATION")
    print("=" * 60)
    
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    print("\n1. CHECKING IF MODULE IS INSTALLED:")
    print("-" * 40)
    
    try:
        import alpaca_trade_api as tradeapi
        print("✓ alpaca-trade-api is installed!")
        
        # Get version
        if hasattr(tradeapi, '__version__'):
            print(f"  Version: {tradeapi.__version__}")
        
        # Check what's available
        print(f"  Module location: {tradeapi.__file__}")
        print(f"  REST class available: {hasattr(tradeapi, 'REST')}")
        
    except ImportError as e:
        print(f"✗ alpaca-trade-api is NOT installed!")
        print(f"  Error: {e}")
        
        print("\n2. CHECKING PIP LIST:")
        print("-" * 40)
        
        # Check if it's in pip list
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True)
            if 'alpaca' in result.stdout.lower():
                print("Found alpaca-related packages:")
                for line in result.stdout.split('\n'):
                    if 'alpaca' in line.lower():
                        print(f"  {line}")
            else:
                print("No alpaca packages found in pip list")
        except Exception as e:
            print(f"Error checking pip: {e}")
        
        print("\n3. INSTALLING ALPACA-TRADE-API:")
        print("-" * 40)
        print("To install, run:")
        print(f"  {sys.executable} -m pip install alpaca-trade-api")
        
        install = input("\nInstall now? (y/n): ")
        if install.lower() == 'y':
            print("\nInstalling...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'alpaca-trade-api'])
                print("✓ Installation complete!")
                
                # Test import again
                import alpaca_trade_api
                print("✓ Module imported successfully after installation!")
                
            except Exception as e:
                print(f"✗ Installation failed: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    import os
    test_alpaca_import()

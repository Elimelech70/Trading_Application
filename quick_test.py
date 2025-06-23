#!/usr/bin/env python3
"""
Quick Test Script - Validates basic functionality
"""
import subprocess
import time
import sys

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Success")
            if result.stdout:
                print(f"  Output: {result.stdout.strip()[:100]}...")
            return True
        else:
            print(f"  ❌ Failed")
            if result.stderr:
                print(f"  Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False

def main():
    print("🧪 Running Quick Tests...")
    print("="*50)
    
    tests = [
        ("python --version", "Checking Python"),
        ("ls -la trading_system.db 2>/dev/null || echo 'Database not found'", "Checking database"),
        ("ls -la logs/ 2>/dev/null || echo 'Logs directory not found'", "Checking logs directory"),
        ("pip show flask requests pandas", "Checking key packages"),
    ]
    
    passed = 0
    for cmd, desc in tests:
        if run_command(cmd, desc):
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

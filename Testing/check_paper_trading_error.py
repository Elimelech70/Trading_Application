#!/usr/bin/env python3
"""
Name of Service: Check Paper Trading Error
Filename: check_paper_trading_error.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Diagnose paper trading startup error
  - Checks for syntax errors
  - Shows recent error logs
  - Tests if service can be imported

DESCRIPTION:
Diagnoses why paper trading service won't start after modification.
"""

import subprocess
import sys
import os

def check_paper_trading_error():
    """Check why paper trading won't start"""
    
    print("=" * 60)
    print("DIAGNOSING PAPER TRADING ERROR")
    print("=" * 60)
    
    # 1. Try to import the file to check for syntax errors
    print("\n1. CHECKING FOR SYNTAX ERRORS:")
    print("-" * 40)
    
    paper_trading_path = '../paper_trading.py' if os.path.exists('../paper_trading.py') else 'paper_trading.py'
    
    # Check syntax
    result = subprocess.run([sys.executable, '-m', 'py_compile', paper_trading_path], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("✗ SYNTAX ERROR FOUND!")
        print(result.stderr)
    else:
        print("✓ No syntax errors detected")
    
    # 2. Try to run it and capture error
    print("\n2. TRYING TO START SERVICE:")
    print("-" * 40)
    
    result = subprocess.run([sys.executable, paper_trading_path], 
                          capture_output=True, text=True, timeout=5)
    
    if result.returncode != 0:
        print("✗ Service failed to start")
        print("\nError output:")
        print(result.stderr)
        if result.stdout:
            print("\nStandard output:")
            print(result.stdout)
    
    # 3. Check the recent modification
    print("\n3. CHECKING RECENT MODIFICATION:")
    print("-" * 40)
    
    with open(paper_trading_path, 'r') as f:
        lines = f.readlines()
    
    # Find the modified section
    for i, line in enumerate(lines):
        if 'Handle both' in line or 'signal_value' in line:
            print(f"Found modification at line {i+1}:")
            # Show surrounding lines
            for j in range(max(0, i-2), min(len(lines), i+5)):
                print(f"Line {j+1}: {lines[j].rstrip()}")
            break
    
    # 4. Check if there's a backup
    print("\n4. CHECKING FOR BACKUP:")
    print("-" * 40)
    
    import glob
    backups = glob.glob(f'{paper_trading_path}.backup_*')
    if backups:
        latest_backup = max(backups)
        print(f"✓ Found backup: {latest_backup}")
        print("\nTo restore from backup, run:")
        print(f"cp {latest_backup} {paper_trading_path}")
    else:
        print("✗ No backup found")
    
    # 5. Show the fix
    print("\n5. QUICK FIX:")
    print("-" * 40)
    print("\nThe issue is likely indentation. The fix should be:")
    print("""
        # Original line 151 area should look like:
        for signal in signals:
            # Handle both 'signal' and 'signal_type' for backward compatibility
            signal_value = signal.get('signal') or signal.get('signal_type')
            if signal_value not in ['BUY', 'SELL']:
                continue
""")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        check_paper_trading_error()
    except Exception as e:
        print(f"Error running diagnostic: {e}")

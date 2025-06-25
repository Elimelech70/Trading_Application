#!/usr/bin/env python3
"""
Name of Service: Fix Paper Trading Indentation Error
Filename: fix_indentation_error.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Fix indentation error in paper_trading.py
  - Fixes the try block indentation
  - Maintains backward compatibility
  - Preserves the signal/signal_type handling

DESCRIPTION:
Fixes the IndentationError in paper_trading.py caused by improper
indentation after the try statement.
"""

import os
import shutil
from datetime import datetime

def fix_indentation():
    """Fix the indentation error in paper_trading.py"""
    
    print("=" * 60)
    print("FIXING PAPER TRADING INDENTATION ERROR")
    print("=" * 60)
    
    paper_trading_path = '../paper_trading.py' if os.path.exists('../paper_trading.py') else 'paper_trading.py'
    
    # Read the file
    with open(paper_trading_path, 'r') as f:
        lines = f.readlines()
    
    # Fix the indentation around line 150-154
    # We need to properly indent everything after the try: statement
    
    fixed_lines = []
    for i, line in enumerate(lines):
        if i == 151:  # Line 152 in 1-based counting
            # This line needs to be indented inside the try block
            fixed_lines.append('                ' + line.lstrip())  # Add proper indentation
        elif i == 152:  # Line 153
            # The signal_value line needs to be inside try block
            fixed_lines.append('                ' + line.lstrip())
        elif i == 153:  # Line 154 - the if statement
            # This should also be inside the try block
            fixed_lines.append('                ' + line.lstrip())
        else:
            fixed_lines.append(line)
    
    # Create a new backup before fixing
    backup_path = f'{paper_trading_path}.backup_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy(paper_trading_path, backup_path)
    print(f"✓ Created new backup: {backup_path}")
    
    # Write the fixed file
    with open(paper_trading_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print("✓ Fixed indentation error")
    
    # Verify the fix
    print("\nVerifying the fix...")
    import subprocess
    import sys
    
    result = subprocess.run([sys.executable, '-m', 'py_compile', paper_trading_path], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ No syntax errors - fix successful!")
        print("\nYou can now start paper_trading.py")
    else:
        print("✗ Still has errors:")
        print(result.stderr)
        print("\nYou may need to restore from backup:")
        print(f"cp ../paper_trading.py.backup_20250625_100034 ../paper_trading.py")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    fix_indentation()

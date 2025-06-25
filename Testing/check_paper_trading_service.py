#!/usr/bin/env python3
"""
Name of Service: Check Paper Trading Service Code
Filename: check_paper_trading_service.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Analyze paper_trading.py for issues
  - Checks if dotenv is imported and used
  - Finds simulation fallback code
  - Identifies credential loading issues

DESCRIPTION:
This script analyzes the paper_trading.py file to find why it's
not using the working Alpaca credentials and falling back to simulation.
"""

import os
import re

def check_paper_trading_code():
    """Analyze paper_trading.py for credential loading issues"""
    
    print("=" * 60)
    print("PAPER TRADING SERVICE CODE ANALYSIS")
    print("=" * 60)
    
    # Find paper_trading.py
    paper_trading_path = None
    if os.path.exists('../paper_trading.py'):
        paper_trading_path = '../paper_trading.py'
    elif os.path.exists('./paper_trading.py'):
        paper_trading_path = './paper_trading.py'
    else:
        print("✗ Cannot find paper_trading.py")
        return
    
    print(f"Analyzing: {paper_trading_path}")
    print("=" * 60)
    
    with open(paper_trading_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 1. Check for dotenv import
    print("\n1. CHECKING FOR DOTENV USAGE:")
    print("-" * 40)
    
    has_dotenv_import = False
    has_load_dotenv = False
    dotenv_line = None
    
    for i, line in enumerate(lines):
        if 'from dotenv import' in line or 'import dotenv' in line:
            has_dotenv_import = True
            print(f"✓ Found dotenv import at line {i+1}: {line.strip()}")
        if 'load_dotenv' in line:
            has_load_dotenv = True
            dotenv_line = i + 1
            print(f"✓ Found load_dotenv() at line {i+1}: {line.strip()}")
    
    if not has_dotenv_import:
        print("✗ No dotenv import found!")
        print("  Add: from dotenv import load_dotenv")
    if not has_load_dotenv:
        print("✗ No load_dotenv() call found!")
        print("  Add: load_dotenv() in __init__ method")
    
    # 2. Check how credentials are loaded
    print("\n2. CHECKING CREDENTIAL LOADING:")
    print("-" * 40)
    
    for i, line in enumerate(lines):
        if 'ALPACA_PAPER_API_KEY' in line:
            print(f"Line {i+1}: {line.strip()}")
            # Check if it's using os.environ.get
            if 'os.environ.get' in line:
                print("  ✓ Using os.environ.get()")
            elif 'os.getenv' in line:
                print("  ✓ Using os.getenv()")
            else:
                print("  ⚠️  Check how this is being loaded")
    
    # 3. Find simulation mode code
    print("\n3. CHECKING FOR SIMULATION MODE:")
    print("-" * 40)
    
    simulation_found = False
    for i, line in enumerate(lines):
        if 'simulation' in line.lower() or 'simulate' in line.lower():
            if not simulation_found:
                print("Found simulation code:")
                simulation_found = True
            print(f"Line {i+1}: {line.strip()[:80]}...")
    
    # 4. Find try/except blocks around Alpaca
    print("\n4. CHECKING ERROR HANDLING:")
    print("-" * 40)
    
    in_try_block = False
    try_line = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith('try:'):
            in_try_block = True
            try_line = i
        elif line.strip().startswith('except') and in_try_block:
            # Check if this is near Alpaca code
            block_text = '\n'.join(lines[try_line:i+5])
            if 'alpaca' in block_text.lower() or 'api' in block_text.lower():
                print(f"\nFound try/except around Alpaca code (lines {try_line+1}-{i+1}):")
                print("  This might be catching errors and falling back to simulation")
                for j in range(try_line, min(i+3, len(lines))):
                    print(f"  Line {j+1}: {lines[j].rstrip()}")
            in_try_block = False
    
    # 5. Check __init__ method
    print("\n5. CHECKING __init__ METHOD:")
    print("-" * 40)
    
    in_init = False
    for i, line in enumerate(lines):
        if 'def __init__' in line:
            in_init = True
            print(f"Found __init__ at line {i+1}")
            # Look for next 20 lines
            for j in range(i, min(i+20, len(lines))):
                if 'load_dotenv' in lines[j]:
                    print(f"  ✓ load_dotenv() called at line {j+1}")
                    break
                if 'def ' in lines[j] and j > i:
                    break
            else:
                if has_dotenv_import and not has_load_dotenv:
                    print("  ✗ load_dotenv() not called in __init__")
            break
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    if not has_dotenv_import or not has_load_dotenv:
        print("\n1. Add dotenv support to paper_trading.py:")
        print("   At the top of the file:")
        print("   from dotenv import load_dotenv")
        print("\n   In the __init__ method:")
        print("   load_dotenv()  # Add this before loading credentials")
    
    print("\n2. Check that credentials are loaded BEFORE Alpaca initialization")
    print("\n3. Add logging to see what credentials are being loaded:")
    print("   self.logger.info(f'API Key: {api_key[:10]}...')")
    print("   self.logger.info(f'Has API Secret: {bool(api_secret)}')")
    
    print("\n4. Remove or fix try/except blocks that hide Alpaca errors")
    print("   Instead of silently falling back to simulation, log the error")
    
    print("=" * 60)


if __name__ == "__main__":
    check_paper_trading_code()

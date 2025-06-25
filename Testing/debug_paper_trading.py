#!/usr/bin/env python3
"""
Name of Service: Debug Paper Trading Credentials
Filename: debug_paper_trading.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Debug credential loading in paper trading
  - Checks if both API key and secret are loaded
  - Tests the actual connection
  - Shows the exact error

DESCRIPTION:
This script checks exactly what's happening with credential loading
in the paper trading service and why it's falling back to simulation.
"""

import os
import sys

# Add parent directory to path
if os.path.exists('../trading_system.db'):
    sys.path.insert(0, os.path.abspath('..'))

def debug_paper_trading():
    """Debug the paper trading credential issue"""
    
    print("=" * 60)
    print("DEBUG PAPER TRADING CREDENTIALS")
    print("=" * 60)
    
    # 1. First check if we can find api_secret in the file
    print("\n1. CHECKING PAPER_TRADING.PY FOR API_SECRET:")
    print("-" * 40)
    
    paper_trading_path = '../paper_trading.py' if os.path.exists('../paper_trading.py') else 'paper_trading.py'
    
    with open(paper_trading_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Look for api_secret
    api_secret_found = False
    for i, line in enumerate(lines):
        if 'api_secret' in line and 'self.' in line:
            print(f"Line {i+1}: {line.strip()}")
            api_secret_found = True
    
    if not api_secret_found:
        print("✗ No self.api_secret assignment found!")
        print("  This is the problem - api_secret is never loaded")
    
    # 2. Check what the __init__ method looks like
    print("\n2. CHECKING __init__ METHOD:")
    print("-" * 40)
    
    in_init = False
    init_lines = []
    for i, line in enumerate(lines):
        if 'def __init__' in line:
            in_init = True
        elif in_init and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            break
        
        if in_init:
            init_lines.append(f"Line {i+1}: {line.rstrip()}")
    
    # Show relevant lines
    for line in init_lines[:20]:  # First 20 lines of __init__
        if any(keyword in line for keyword in ['api', 'key', 'secret', 'environ', 'ALPACA']):
            print(line)
    
    # 3. Test loading credentials directly
    print("\n3. TESTING CREDENTIAL LOADING:")
    print("-" * 40)
    
    # Load .env
    from dotenv import load_dotenv
    load_dotenv('../.env' if os.path.exists('../.env') else '.env')
    
    api_key = os.environ.get('ALPACA_PAPER_API_KEY', '')
    api_secret = os.environ.get('ALPACA_PAPER_API_SECRET', '')
    
    print(f"API Key from environment: {api_key[:10]}... (length: {len(api_key)})")
    print(f"API Secret from environment: {'*' * 10 if api_secret else 'NOT FOUND'} (length: {len(api_secret)})")
    
    # 4. Try to replicate what paper_trading.py does
    print("\n4. REPLICATING PAPER TRADING CONNECTION:")
    print("-" * 40)
    
    try:
        import alpaca_trade_api as tradeapi
        
        base_url = 'https://paper-api.alpaca.markets'
        
        print(f"Creating Alpaca REST client...")
        print(f"Base URL: {base_url}")
        
        api = tradeapi.REST(
            api_key,
            api_secret,
            base_url,
            api_version='v2'
        )
        
        print("Testing connection...")
        account = api.get_account()
        
        print("✓ SUCCESS! Connected to Alpaca")
        print(f"Account status: {account.status}")
        
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")
        
        if "401" in str(e):
            print("\nAuthentication failed!")
            print("This happens when:")
            print("1. API key is wrong")
            print("2. API secret is wrong or missing")
            print("3. Using live keys on paper endpoint")
    
    # 5. Check the exact error in setup_alpaca_api
    print("\n5. SETUP_ALPACA_API METHOD:")
    print("-" * 40)
    
    # Find setup_alpaca_api method
    in_setup = False
    for i, line in enumerate(lines):
        if 'def setup_alpaca_api' in line:
            in_setup = True
            print(f"Found at line {i+1}")
            # Show next 30 lines
            for j in range(i, min(i+30, len(lines))):
                if 'self.api_key' in lines[j] or 'self.api_secret' in lines[j]:
                    print(f"Line {j+1}: {lines[j].strip()}")
            break
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("=" * 60)
    
    if not api_secret_found:
        print("\n✗ PROBLEM FOUND: self.api_secret is not being loaded!")
        print("  The service loads api_key but not api_secret")
        print("  This causes Alpaca authentication to fail")
        print("\nFIX: Add this line after self.api_key assignment:")
        print("  self.api_secret = os.environ.get('ALPACA_PAPER_API_SECRET', '')")
    else:
        print("\napi_secret appears to be loaded")
        print("Check the logs for the actual error when connecting to Alpaca")
    
    print("=" * 60)


if __name__ == "__main__":
    debug_paper_trading()

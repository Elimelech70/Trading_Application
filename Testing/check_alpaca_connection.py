#!/usr/bin/env python3
"""
Name of Service: Check Alpaca Connection Script
Filename: check_alpaca_connection.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Direct Alpaca connection verification
  - Tests Alpaca API connection directly
  - Verifies credentials are working
  - Shows real account data vs simulation

DESCRIPTION:
This script directly tests the Alpaca Paper Trading API connection
to determine why the service shows connected but returns simulation data.
"""

import os
import sys
from dotenv import load_dotenv

# Handle running from Testing folder
if os.path.exists('../trading_system.db'):
    # Load .env from parent directory
    load_dotenv('../.env')
else:
    load_dotenv()

def check_alpaca_direct():
    """Test Alpaca connection directly"""
    
    print("=" * 60)
    print("DIRECT ALPACA CONNECTION TEST")
    print("=" * 60)
    
    # Check for credentials
    api_key = os.environ.get('ALPACA_PAPER_API_KEY')
    api_secret = os.environ.get('ALPACA_PAPER_API_SECRET')
    
    print("1. CREDENTIAL CHECK")
    print("-" * 40)
    
    if not api_key or not api_secret:
        print("✗ Alpaca credentials not found in environment")
        print("  Attempting to load from .env file...")
        
        # Try loading manually
        env_path = '../.env' if os.path.exists('../.env') else '.env'
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if 'ALPACA_PAPER_API_KEY=' in line:
                        api_key = line.split('=', 1)[1].strip()
                    elif 'ALPACA_PAPER_API_SECRET=' in line:
                        api_secret = line.split('=', 1)[1].strip()
    
    if api_key and api_secret:
        print(f"✓ API Key found: {api_key[:10]}...")
        print(f"✓ API Secret found: ***")
        
        # Check if it's a paper key
        if api_key.startswith('PK'):
            print("✓ Key format looks correct (starts with PK)")
        else:
            print("⚠️  Key doesn't start with PK - might not be paper trading key")
    else:
        print("✗ Could not find credentials")
        return
    
    print("\n2. TESTING DIRECT ALPACA CONNECTION")
    print("-" * 40)
    
    try:
        import alpaca_trade_api as tradeapi
        print("✓ alpaca-trade-api package imported")
        
        # Create API connection
        print("\nConnecting to Alpaca Paper Trading...")
        api = tradeapi.REST(
            api_key,
            api_secret,
            base_url='https://paper-api.alpaca.markets',
            api_version='v2'
        )
        
        # Get account info
        print("Fetching account information...")
        account = api.get_account()
        
        print("\n✓ SUCCESSFULLY CONNECTED TO ALPACA!")
        print(f"\nAccount Details:")
        print(f"  Account Number: {account.account_number}")
        print(f"  Status: {account.status}")
        print(f"  Currency: {account.currency}")
        print(f"  Buying Power: ${account.buying_power}")
        print(f"  Cash: ${account.cash}")
        print(f"  Portfolio Value: ${account.portfolio_value}")
        print(f"  Day Trading Buying Power: ${account.daytrading_buying_power}")
        print(f"  Pattern Day Trader: {account.pattern_day_trader}")
        
        # Get positions
        print("\n3. CHECKING POSITIONS")
        print("-" * 40)
        positions = api.list_positions()
        print(f"Current positions: {len(positions)}")
        for pos in positions:
            print(f"  - {pos.symbol}: {pos.qty} shares @ ${pos.avg_entry_price}")
        
        # Get recent orders
        print("\n4. CHECKING RECENT ORDERS")
        print("-" * 40)
        orders = api.list_orders(status='all', limit=5)
        print(f"Recent orders: {len(orders)}")
        for order in orders:
            print(f"  - {order.symbol} {order.side} {order.qty} shares")
            print(f"    Status: {order.status}")
            print(f"    Order ID: {order.id}")
            print(f"    Submitted: {order.submitted_at}")
        
    except ImportError:
        print("✗ alpaca-trade-api not installed")
        print("  Run: pip install alpaca-trade-api")
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}")
        print(f"  Error: {str(e)}")
        
        if "401" in str(e):
            print("\n  Authentication failed - check your API credentials")
        elif "paper-api.alpaca.markets" in str(e):
            print("\n  Network error - check internet connection")
    
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    
    print("\nIf connection succeeded but Paper Trading Service shows simulation:")
    print("1. The service may not be loading the .env file properly")
    print("2. The service may be catching Alpaca errors and falling back to simulation")
    print("3. Check if paper_trading.py has the correct path to .env")
    
    print("\nNext steps:")
    print("1. Check paper_trading.py imports dotenv and loads .env")
    print("2. Look for try/except blocks that might hide Alpaca errors")
    print("3. Check if ALPACA_PAPER_API_KEY is being read correctly in the service")


if __name__ == "__main__":
    # First try to install alpaca-trade-api if not present
    try:
        import alpaca_trade_api
    except ImportError:
        print("Installing alpaca-trade-api...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "alpaca-trade-api"])
    
    check_alpaca_direct()

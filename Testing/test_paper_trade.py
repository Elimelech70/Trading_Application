#!/usr/bin/env python3
"""
Name of Service: Test Paper Trade Script
Filename: test_paper_trade.py
Version: 1.0.0
Last Updated: 2025-01-27
REVISION HISTORY:
v1.0.0 (2025-01-27) - Initial test script for paper trading verification
  - Executes a single test trade (1 share of AAPL)
  - Verifies service health and account status
  - Checks for Alpaca Order ID to confirm real execution
  - Provides detailed troubleshooting guidance
  - Supports running from Testing folder or main directory

DESCRIPTION:
This script manually triggers a test trade through the paper trading service
to verify that Alpaca Paper Trading API integration is working correctly.
It attempts to buy 1 share of AAPL and reports whether the trade was executed
on Alpaca (with order ID) or simulated locally.
"""

import requests
import json
import os
import sys
from datetime import datetime

# Handle running from Testing folder
if os.path.exists('../trading_system.db'):
    sys.path.insert(0, os.path.abspath('..'))

def test_paper_trade():
    """Test paper trading with a small order"""
    
    print("=" * 60)
    print("PAPER TRADING TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Running from: {os.getcwd()}")
    print("=" * 60)
    
    # Define test trade
    test_signal = {
        "symbol": "AAPL",  # Apple stock as test
        "signal_type": "BUY",
        "confidence": 0.75,
        "quantity": 1,  # Just 1 share for testing
        "reason": "Manual test trade to verify Alpaca integration"
    }
    
    print(f"\nTest Trade Details:")
    print(f"  Symbol: {test_signal['symbol']}")
    print(f"  Action: {test_signal['signal_type']}")
    print(f"  Quantity: {test_signal['quantity']} share")
    print(f"  Confidence: {test_signal['confidence']}")
    print(f"  Reason: {test_signal['reason']}")
    
    try:
        # First check if service is running
        print("\n1. CHECKING PAPER TRADING SERVICE")
        print("-" * 40)
        health_response = requests.get('http://localhost:5005/health', timeout=5)
        
        if health_response.status_code != 200:
            print("✗ Paper Trading Service is not running!")
            print("  Please start the service first:")
            print("  python paper_trading.py")
            return
            
        health_data = health_response.json()
        print(f"✓ Service Status: {health_data.get('status')}")
        print(f"  Alpaca Connected: {health_data.get('alpaca_connected', False)}")
        print(f"  Mode: {health_data.get('mode', 'Unknown')}")
        
        # Check account status
        print("\n2. CHECKING ACCOUNT STATUS")
        print("-" * 40)
        account_response = requests.get('http://localhost:5005/account', timeout=5)
        
        if account_response.status_code == 200:
            account = account_response.json()
            print(f"✓ Account Status: {account.get('status')}")
            print(f"  Buying Power: ${account.get('buying_power', 0)}")
            print(f"  Portfolio Value: ${account.get('portfolio_value', 0)}")
            
            buying_power = float(account.get('buying_power', 0))
            if buying_power < 100:
                print("⚠️  Warning: Low buying power!")
                
            # Check if this is real account data
            if account.get('account_number'):
                print(f"  Account Number: {account['account_number'][:4]}****")
                print("  ✓ Connected to Alpaca Paper Trading")
            else:
                print("  ⚠️  No account number - May be in simulation mode")
        else:
            print("✗ Could not retrieve account information")
            print("  Service may be in simulation mode")
            
        # Execute test trade
        print("\n3. EXECUTING TEST TRADE")
        print("-" * 40)
        print("Sending trade signal to paper trading service...")
        
        trade_response = requests.post(
            'http://localhost:5005/execute_trades',
            json={"signals": [test_signal]},
            timeout=30
        )
        
        print(f"Response Status: {trade_response.status_code}")
        
        if trade_response.status_code == 200:
            result = trade_response.json()
            print(f"\n✓ Trade Response Received:")
            print(json.dumps(result, indent=2))
            
            # Analyze the response
            print("\n4. TRADE EXECUTION ANALYSIS")
            print("-" * 40)
            
            trades_executed = result.get('trades_executed', 0)
            print(f"Trades Executed: {trades_executed}")
            
            if trades_executed > 0:
                print("\n✓ SUCCESS: Trade was executed!")
                
                # Check for Alpaca order ID
                alpaca_order_found = False
                if result.get('execution_details'):
                    for detail in result['execution_details']:
                        if detail.get('alpaca_order_id'):
                            print(f"\n  ✓ ALPACA ORDER ID: {detail['alpaca_order_id']}")
                            print("  ✓ CONFIRMED: Real paper trade executed on Alpaca!")
                            alpaca_order_found = True
                            
                            # Additional details if available
                            if detail.get('status'):
                                print(f"  Order Status: {detail['status']}")
                            if detail.get('filled_qty'):
                                print(f"  Filled Quantity: {detail['filled_qty']}")
                            if detail.get('filled_price'):
                                print(f"  Filled Price: ${detail['filled_price']}")
                        else:
                            print("\n  ⚠️  No Alpaca Order ID found")
                            print("  Trade was SIMULATED locally (not sent to Alpaca)")
                            
                if not alpaca_order_found and 'execution_details' not in result:
                    print("\n  ⚠️  No execution details provided")
                    print("  Trade may have been simulated")
            else:
                print("\n✗ No trades were executed")
                print("  Check the logs for error details")
                
                if result.get('message'):
                    print(f"  Message: {result['message']}")
                if result.get('errors'):
                    print(f"  Errors: {result['errors']}")
        else:
            print(f"\n✗ Trade execution failed (Status: {trade_response.status_code})")
            try:
                error_data = trade_response.json()
                print(f"  Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"  Response: {trade_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to Paper Trading Service")
        print("  Make sure the service is running on port 5005:")
        print("  python paper_trading.py")
    except requests.exceptions.Timeout:
        print("\n✗ Request timed out")
        print("  The service may be busy or not responding")
    except Exception as e:
        print(f"\n✗ Unexpected error: {type(e).__name__}")
        print(f"  Details: {str(e)}")
        
    print("\n" + "=" * 60)
    print("TROUBLESHOOTING GUIDE")
    print("=" * 60)
    
    print("\nIf trade was SIMULATED (no Alpaca Order ID):")
    print("1. Check Alpaca credentials are set correctly:")
    print("   - ALPACA_PAPER_API_KEY environment variable")
    print("   - ALPACA_PAPER_API_SECRET environment variable")
    print("   - Or in .env file in main project directory")
    print("\n2. Verify credentials are for PAPER trading (not live)")
    print("   - Paper API keys usually start with 'PK'")
    print("   - Use paper-api.alpaca.markets endpoint")
    print("\n3. Check logs/paper_trading_service.log for errors:")
    print("   - Authentication failures")
    print("   - Network connection issues")
    print("   - API rate limit errors")
    
    print("\nTo get Alpaca Paper Trading credentials:")
    print("1. Sign up at https://alpaca.markets (free)")
    print("2. Go to your dashboard → Paper Trading")
    print("3. View API Keys → Generate New Key")
    print("4. Run: python setup_alpaca_credentials.py")
    
    print("\nIf trade was SUCCESSFUL (has Alpaca Order ID):")
    print("✓ Your paper trading is working correctly!")
    print("✓ Trades are being executed on Alpaca Paper Trading")
    print("✓ You can monitor them at https://app.alpaca.markets")
    
    print("=" * 60)


if __name__ == "__main__":
    test_paper_trade()

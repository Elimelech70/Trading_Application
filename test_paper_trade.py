#!/usr/bin/env python3
"""
Test Paper Trade Script
Manually triggers a test trade through the paper trading service
"""

import requests
import json
from datetime import datetime

def test_paper_trade():
    """Test paper trading with a small order"""
    
    print("=" * 60)
    print("PAPER TRADING TEST")
    print("=" * 60)
    
    # Define test trade
    test_signal = {
        "symbol": "AAPL",  # Apple stock as test
        "signal_type": "BUY",
        "confidence": 0.75,
        "quantity": 1,  # Just 1 share for testing
        "reason": "Manual test trade to verify Alpaca integration"
    }
    
    print(f"Test Trade Details:")
    print(f"  Symbol: {test_signal['symbol']}")
    print(f"  Action: {test_signal['signal_type']}")
    print(f"  Quantity: {test_signal['quantity']} share")
    print(f"  Confidence: {test_signal['confidence']}")
    
    try:
        # First check if service is running
        print("\n1. Checking Paper Trading Service...")
        health_response = requests.get('http://localhost:5005/health', timeout=5)
        
        if health_response.status_code != 200:
            print("✗ Paper Trading Service is not running!")
            print("  Please start the service first.")
            return
            
        health_data = health_response.json()
        print(f"✓ Service Status: {health_data.get('status')}")
        print(f"  Alpaca Connected: {health_data.get('alpaca_connected', False)}")
        
        # Check account status
        print("\n2. Checking Account Status...")
        account_response = requests.get('http://localhost:5005/account', timeout=5)
        
        if account_response.status_code == 200:
            account = account_response.json()
            print(f"✓ Account Status: {account.get('status')}")
            print(f"  Buying Power: ${account.get('buying_power', 0)}")
            
            if float(account.get('buying_power', 0)) < 100:
                print("⚠️  Warning: Low buying power!")
        else:
            print("✗ Could not retrieve account information")
            
        # Execute test trade
        print("\n3. Executing Test Trade...")
        print("   Sending trade signal to paper trading service...")
        
        trade_response = requests.post(
            'http://localhost:5005/execute_trades',
            json={"signals": [test_signal]},
            timeout=30
        )
        
        if trade_response.status_code == 200:
            result = trade_response.json()
            print(f"\n✓ Trade Response Received:")
            print(json.dumps(result, indent=2))
            
            # Check if trade was actually executed
            if result.get('trades_executed', 0) > 0:
                print(f"\n✓ SUCCESS: Trade was executed!")
                
                # Check for Alpaca order ID
                if result.get('execution_details'):
                    for detail in result['execution_details']:
                        if detail.get('alpaca_order_id'):
                            print(f"  Alpaca Order ID: {detail['alpaca_order_id']}")
                            print("  ✓ CONFIRMED: Real paper trade on Alpaca!")
                        else:
                            print("  ⚠️  No Alpaca Order ID - Trade was simulated")
            else:
                print(f"\n✗ No trades were executed")
                print(f"  Check logs for details")
        else:
            print(f"\n✗ Trade execution failed (Status: {trade_response.status_code})")
            print(f"  Response: {trade_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to Paper Trading Service")
        print("  Make sure the service is running on port 5005")
    except Exception as e:
        print(f"\n✗ Error during test: {str(e)}")
        
    print("\n" + "=" * 60)
    
    # Provide guidance
    print("\nTROUBLESHOOTING GUIDE:")
    print("-" * 40)
    print("If trade was simulated (no Alpaca Order ID):")
    print("1. Check if ALPACA_PAPER_API_KEY and ALPACA_PAPER_API_SECRET are set")
    print("2. Verify credentials are for Paper Trading (not live trading)")
    print("3. Check paper_trading_service.log for connection errors")
    print("\nTo get Alpaca Paper Trading credentials:")
    print("1. Sign up at https://alpaca.markets (free)")
    print("2. Go to your dashboard → Paper Trading")
    print("3. View API Keys → Generate New Key")
    print("4. Add to .env file or set as environment variables")
    print("=" * 60)


if __name__ == "__main__":
    test_paper_trade()

#!/usr/bin/env python3
"""
Name of Service: Test Correct Signal Format
Filename: test_correct_signal.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Test with correct signal field name
  - Uses 'signal' instead of 'signal_type'
  - Includes all required fields
  - Should execute successfully

DESCRIPTION:
Tests paper trading with the correct field name 'signal'
instead of 'signal_type' to match what the code expects.
"""

import requests
import json
import time

def test_correct_signal():
    """Test with the correct signal format"""
    
    print("=" * 60)
    print("TESTING WITH CORRECT SIGNAL FORMAT")
    print("=" * 60)
    
    # Correct signal format - using 'signal' not 'signal_type'
    test_payload = {
        "signals": [{
            "symbol": "AAPL",
            "signal": "BUY",  # ← CORRECT FIELD NAME
            "quantity": 1,
            "confidence": 0.8,
            "reason": "Test trade with correct field name",
            "current_price": 180.0  # Adding current price as it's required
        }]
    }
    
    print("Sending signal with correct field names:")
    print(json.dumps(test_payload, indent=2))
    
    try:
        response = requests.post(
            "http://localhost:5005/execute_trades",
            json=test_payload,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\nResponse:")
            print(json.dumps(result, indent=2))
            
            if isinstance(result, list) and len(result) > 0:
                print("\n✓ SUCCESS! Trade was executed!")
                
                # Check for Alpaca order ID
                for trade in result:
                    if trade.get('alpaca_order_id'):
                        print(f"\n✓ ALPACA ORDER ID: {trade['alpaca_order_id']}")
                        print("✓ CONFIRMED: Real paper trade on Alpaca!")
                    else:
                        print("\n⚠️  No Alpaca order ID in response")
            elif isinstance(result, list) and len(result) == 0:
                print("\n✗ Empty array returned - trade was not executed")
                print("Check if all required fields are present")
        else:
            print(f"\nError: {response.text}")
            
    except Exception as e:
        print(f"\nError: {e}")
    
    # Test with multiple signals
    print("\n\n" + "=" * 60)
    print("TESTING MULTIPLE SIGNALS:")
    print("=" * 60)
    
    multi_payload = {
        "signals": [
            {
                "symbol": "AAPL",
                "signal": "BUY",
                "quantity": 1,
                "confidence": 0.9,
                "reason": "Strong buy signal",
                "current_price": 180.0
            },
            {
                "symbol": "MSFT", 
                "signal": "BUY",
                "quantity": 2,
                "confidence": 0.75,
                "reason": "Moderate buy signal",
                "current_price": 380.0
            }
        ]
    }
    
    print("Sending multiple signals...")
    
    try:
        response = requests.post(
            "http://localhost:5005/execute_trades",
            json=multi_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nExecuted {len(result)} trades")
            
            for i, trade in enumerate(result):
                print(f"\nTrade {i+1}:")
                print(f"  Symbol: {trade.get('symbol')}")
                print(f"  Order ID: {trade.get('alpaca_order_id', 'None')}")
                
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print("\nThe issue was using 'signal_type' instead of 'signal'")
    print("The code expects these exact field names:")
    print("  - signal (not signal_type)")
    print("  - symbol")
    print("  - quantity") 
    print("  - confidence")
    print("  - reason")
    print("  - current_price")
    print("=" * 60)


if __name__ == "__main__":
    test_correct_signal()

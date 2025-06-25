#!/usr/bin/env python3
"""
Name of Service: Test Service State
Filename: test_service_state.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Test paper trading service state
  - Calls multiple endpoints to check consistency
  - Shows if Alpaca is really connected
  - Helps identify the disconnect

DESCRIPTION:
Tests the paper trading service to understand why it shows
as connected in logs but returns simulation data via API.
"""

import requests
import json
import time

def test_service_state():
    """Test the actual state of the paper trading service"""
    
    print("=" * 60)
    print("PAPER TRADING SERVICE STATE TEST")
    print("=" * 60)
    print("Testing all endpoints to check service state...")
    print("=" * 60)
    
    base_url = "http://localhost:5005"
    
    # 1. Test health endpoint
    print("\n1. HEALTH ENDPOINT (/health):")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Check specific fields
            if 'alpaca_connected' in data:
                print(f"\n✓ Alpaca Connected: {data['alpaca_connected']}")
        else:
            print(f"Error: Status {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. Test account endpoint
    print("\n\n2. ACCOUNT ENDPOINT (/account):")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/account", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Analyze the response
            if 'mode' in data:
                print(f"\n⚠️  Mode: {data['mode']}")
            if 'account_number' in data:
                print(f"✓ Account Number: {data.get('account_number', 'None')}")
            else:
                print("✗ No account number (indicates simulation)")
                
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Test positions endpoint
    print("\n\n3. POSITIONS ENDPOINT (/positions):")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/positions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"Positions: {len(data)}")
            if data:
                print("First position:", json.dumps(data[0], indent=2))
        else:
            print(f"Error: Status {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. Try to execute a minimal test trade
    print("\n\n4. TEST TRADE EXECUTION:")
    print("-" * 40)
    
    test_signal = {
        "symbol": "SPY",
        "signal_type": "BUY", 
        "quantity": 1,
        "confidence": 0.8,
        "reason": "Service state test"
    }
    
    print(f"Sending test signal: {test_signal['symbol']} {test_signal['signal_type']} {test_signal['quantity']}")
    
    try:
        response = requests.post(
            f"{base_url}/execute_trades",
            json={"signals": [test_signal]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\nResponse:")
            print(json.dumps(data, indent=2))
            
            # Check for Alpaca order ID
            if 'execution_details' in data:
                for detail in data['execution_details']:
                    if 'alpaca_order_id' in detail and detail['alpaca_order_id']:
                        print(f"\n✓ ALPACA ORDER ID: {detail['alpaca_order_id']}")
                        print("✓ Real paper trading confirmed!")
                    else:
                        print("\n✗ No Alpaca order ID - trade was simulated")
        else:
            print(f"Error: Status {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n\n" + "=" * 60)
    print("ANALYSIS:")
    print("=" * 60)
    
    print("\nIf health shows alpaca_connected=True but account shows simulation,")
    print("the issue is in the get_account_info() method logic.")
    print("\nThe service IS connected but the account endpoint has a bug.")
    print("=" * 60)


if __name__ == "__main__":
    test_service_state()

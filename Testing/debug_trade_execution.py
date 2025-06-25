#!/usr/bin/env python3
"""
Name of Service: Debug Trade Execution
Filename: debug_trade_execution.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Debug why trades aren't executing
  - Checks execute_trades endpoint logic
  - Identifies why empty array is returned
  - Tests with different payloads

DESCRIPTION:
The paper trading service is connected to Alpaca but trades
aren't being executed. This script finds out why.
"""

import requests
import json
import os

def debug_trade_execution():
    """Debug why trades aren't being executed"""
    
    print("=" * 60)
    print("TRADE EXECUTION DEBUGGING")
    print("=" * 60)
    
    # 1. Check the execute_trades method in code
    print("\n1. CHECKING EXECUTE_TRADES METHOD:")
    print("-" * 40)
    
    paper_trading_path = '../paper_trading.py' if os.path.exists('../paper_trading.py') else 'paper_trading.py'
    
    with open(paper_trading_path, 'r') as f:
        lines = f.readlines()
    
    # Find execute_trades method
    in_method = False
    method_lines = []
    route_found = False
    
    # First find the route
    for i, line in enumerate(lines):
        if '@app.route' in line and '/execute_trades' in line:
            print(f"Found route at line {i+1}: {line.strip()}")
            route_found = True
        elif route_found and 'def ' in line:
            print(f"Handler function at line {i+1}: {line.strip()}")
            # Look at the handler logic
            for j in range(i, min(i+20, len(lines))):
                if 'return' in lines[j] or 'jsonify' in lines[j]:
                    print(f"Line {j+1}: {lines[j].strip()}")
                    if '[]' in lines[j]:
                        print("  ⚠️  PROBLEM: Returning empty array!")
            break
    
    # Also find the actual execute_trades method
    for i, line in enumerate(lines):
        if 'def execute_trades' in line or 'def _execute_trades' in line:
            print(f"\nFound execute_trades method at line {i+1}")
            # Show first 20 lines
            for j in range(i, min(i+20, len(lines))):
                method_lines.append((j+1, lines[j].rstrip()))
    
    if method_lines:
        print("\nMethod preview:")
        for line_num, line in method_lines[:10]:
            print(f"Line {line_num}: {line}")
    
    # 2. Test different request formats
    print("\n\n2. TESTING DIFFERENT REQUEST FORMATS:")
    print("-" * 40)
    
    base_url = "http://localhost:5005"
    
    # Test 1: Current format
    print("\nTest 1: Standard format with 'signals' key")
    test_payload = {
        "signals": [{
            "symbol": "AAPL",
            "signal_type": "BUY",
            "quantity": 1,
            "confidence": 0.8,
            "reason": "Debug test"
        }]
    }
    
    try:
        response = requests.post(f"{base_url}/execute_trades", json=test_payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) == 0:
                print("⚠️  Empty list returned - no trades executed")
            elif isinstance(data, dict):
                print(f"Response type: dict")
                print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Without 'signals' wrapper
    print("\n\nTest 2: Direct array format")
    test_payload2 = [{
        "symbol": "MSFT",
        "signal_type": "BUY",
        "quantity": 1,
        "confidence": 0.8,
        "reason": "Debug test 2"
    }]
    
    try:
        response = requests.post(f"{base_url}/execute_trades", json=test_payload2, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Single signal
    print("\n\nTest 3: Single signal object")
    test_payload3 = {
        "symbol": "TSLA",
        "signal_type": "BUY",
        "quantity": 1,
        "confidence": 0.8,
        "reason": "Debug test 3"
    }
    
    try:
        response = requests.post(f"{base_url}/execute_trades", json=test_payload3, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Check logs for errors
    print("\n\n3. CHECKING RECENT LOG ENTRIES:")
    print("-" * 40)
    
    log_path = '../logs/paper_trading_service.log'
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            lines = f.readlines()
            
        # Look for recent execute_trades entries
        recent_executes = []
        for line in lines[-50:]:  # Last 50 lines
            if 'execute' in line.lower() or 'trade' in line.lower():
                recent_executes.append(line.strip())
        
        if recent_executes:
            print("Recent trade-related log entries:")
            for entry in recent_executes[-5:]:
                print(f"  {entry}")
        else:
            print("No recent trade execution logs found")
    
    # 4. Analysis
    print("\n\n" + "=" * 60)
    print("POSSIBLE ISSUES:")
    print("=" * 60)
    
    print("\n1. The /execute_trades endpoint might be:")
    print("   - Expecting a different request format")
    print("   - Not extracting signals from the request properly")
    print("   - Immediately returning [] without processing")
    
    print("\n2. The execute_trades method might be:")
    print("   - Not being called by the endpoint")
    print("   - Filtering out all signals")
    print("   - Having an early return statement")
    
    print("\n3. Check if the endpoint handler:")
    print("   - Gets the JSON data correctly")
    print("   - Passes it to the execute_trades method")
    print("   - Returns the actual result")
    
    print("\nNEXT STEPS:")
    print("1. Add logging in the endpoint handler")
    print("2. Check if signals are being extracted from request")
    print("3. Verify the execute_trades method is called")
    
    print("=" * 60)


if __name__ == "__main__":
    debug_trade_execution()

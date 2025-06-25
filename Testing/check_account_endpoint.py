#!/usr/bin/env python3
"""
Name of Service: Check Account Endpoint Issue
Filename: check_account_endpoint.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Debug why /account returns simulation data
  - Checks the get_account_info method
  - Tests the endpoint directly
  - Identifies the logic issue

DESCRIPTION:
The service connects to Alpaca successfully but the /account
endpoint returns simulation data. This script finds out why.
"""

import os
import requests

def check_account_endpoint():
    """Debug the account endpoint issue"""
    
    print("=" * 60)
    print("ACCOUNT ENDPOINT DEBUGGING")
    print("=" * 60)
    
    # 1. First check the code
    print("\n1. CHECKING GET_ACCOUNT_INFO METHOD:")
    print("-" * 40)
    
    paper_trading_path = '../paper_trading.py' if os.path.exists('../paper_trading.py') else 'paper_trading.py'
    
    with open(paper_trading_path, 'r') as f:
        lines = f.readlines()
    
    # Find get_account_info method
    in_method = False
    method_lines = []
    
    for i, line in enumerate(lines):
        if 'def get_account_info' in line or 'def _get_account_info' in line:
            in_method = True
            print(f"Found method at line {i+1}")
        elif in_method and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            break
        
        if in_method:
            method_lines.append((i+1, line.rstrip()))
    
    # Show the method
    if method_lines:
        print("\nMethod code:")
        for line_num, line in method_lines[:30]:  # Show up to 30 lines
            print(f"Line {line_num}: {line}")
            
            # Highlight problematic patterns
            if 'self.alpaca_api is None' in line:
                print("  ⚠️  PROBLEM: Checking if alpaca_api is None")
            if 'return' in line and 'simulation' in line:
                print("  ⚠️  PROBLEM: Returning simulation data")
    
    # 2. Test the actual endpoint
    print("\n\n2. TESTING /account ENDPOINT:")
    print("-" * 40)
    
    try:
        response = requests.get('http://localhost:5005/account', timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nResponse data:")
            for key, value in data.items():
                print(f"  {key}: {value}")
                
            # Check for simulation indicators
            if data.get('mode') == 'simulation':
                print("\n⚠️  CONFIRMED: Endpoint returns simulation mode")
            if data.get('status') == 'simulated':
                print("⚠️  CONFIRMED: Status is 'simulated'")
            if data.get('buying_power') == 100000:
                print("⚠️  CONFIRMED: Default simulation buying power")
                
    except Exception as e:
        print(f"Error calling endpoint: {e}")
    
    # 3. Test health endpoint for comparison
    print("\n\n3. TESTING /health ENDPOINT FOR COMPARISON:")
    print("-" * 40)
    
    try:
        response = requests.get('http://localhost:5005/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("Health endpoint data:")
            for key, value in data.items():
                print(f"  {key}: {value}")
                
            if data.get('alpaca_connected'):
                print("\n✓ Health endpoint shows Alpaca is connected!")
                
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. Find the issue
    print("\n\n" + "=" * 60)
    print("ANALYSIS:")
    print("=" * 60)
    
    print("\nThe issue is likely that get_account_info() has code like:")
    print("  if self.alpaca_api is None:")
    print("      return simulation_data")
    print("\nBut self.alpaca_api might be None even after successful connection")
    print("due to an error in setup or a logic issue.")
    
    print("\nPOSSIBLE FIXES:")
    print("1. Check if self.alpaca_api is being set correctly after connection")
    print("2. Remove the simulation fallback in get_account_info()")
    print("3. Add logging to see the value of self.alpaca_api")
    
    # Look for where alpaca_api is set
    print("\n\n5. CHECKING WHERE self.alpaca_api IS SET:")
    print("-" * 40)
    
    for i, line in enumerate(lines):
        if 'self.alpaca_api =' in line and 'None' not in line:
            print(f"Line {i+1}: {line.strip()}")
            # Check next few lines for error handling
            for j in range(i+1, min(i+5, len(lines))):
                if 'except' in lines[j] or 'self.alpaca_api = None' in lines[j]:
                    print(f"  Line {j+1}: {lines[j].strip()}")
                    print("  ⚠️  alpaca_api might be set to None on error")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_account_endpoint()

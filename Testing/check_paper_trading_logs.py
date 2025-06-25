#!/usr/bin/env python3
"""
Name of Service: Check Paper Trading Logs
Filename: check_paper_trading_logs.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Check paper trading logs for errors
  - Finds Alpaca connection errors
  - Shows credential loading messages
  - Identifies why it's falling back to simulation

DESCRIPTION:
This script analyzes the paper trading service log to find
the actual error that's causing the Alpaca connection to fail.
"""

import os
import re
from datetime import datetime

def check_logs():
    """Check paper trading logs for Alpaca errors"""
    
    print("=" * 60)
    print("PAPER TRADING LOG ANALYSIS")
    print("=" * 60)
    
    log_path = '../logs/paper_trading_service.log' if os.path.exists('../logs/paper_trading_service.log') else './logs/paper_trading_service.log'
    
    if not os.path.exists(log_path):
        print(f"✗ Log file not found at: {log_path}")
        return
    
    print(f"Analyzing: {log_path}")
    print("=" * 60)
    
    # Read the log file
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    # Patterns to look for
    patterns = {
        'credential_loaded': r'credentials loaded from environment',
        'credential_not_found': r'credentials not found',
        'error_alpaca': r'Error.*Alpaca.*API',
        'connected': r'Connected to Alpaca',
        'simulation': r'simulation mode',
        'api_error': r'401|403|authentication|unauthorized',
        'import_error': r'ImportError|ModuleNotFoundError',
        'setup_alpaca': r'setup.*alpaca',
        'alpaca_available': r'ALPACA_AVAILABLE'
    }
    
    # Collect relevant lines
    relevant_lines = []
    
    print("\n1. RECENT ALPACA-RELATED LOG ENTRIES:")
    print("-" * 40)
    
    # Look at last 200 lines
    for i, line in enumerate(lines[-200:]):
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                # Get the timestamp if available
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)
                    relevant_lines.append((timestamp, pattern_name, line.strip()))
                else:
                    relevant_lines.append(('No timestamp', pattern_name, line.strip()))
                break
    
    # Sort by timestamp (most recent first)
    relevant_lines.sort(reverse=True)
    
    # Show the most recent relevant entries
    shown = 0
    for timestamp, pattern_type, line in relevant_lines[:20]:
        print(f"\n[{timestamp}] {pattern_type.upper()}:")
        print(f"  {line[:150]}{'...' if len(line) > 150 else ''}")
        shown += 1
    
    if shown == 0:
        print("No Alpaca-related entries found in recent logs")
    
    # 2. Look for specific error patterns
    print("\n\n2. CHECKING FOR SPECIFIC ERRORS:")
    print("-" * 40)
    
    # Check for import errors
    import_errors = [line for line in lines if 'alpaca' in line.lower() and ('import' in line.lower() or 'module' in line.lower())]
    if import_errors:
        print("\nImport-related errors found:")
        for error in import_errors[-3:]:
            print(f"  {error.strip()}")
    
    # Check for authentication errors
    auth_errors = [line for line in lines if any(word in line.lower() for word in ['401', '403', 'unauthorized', 'authentication'])]
    if auth_errors:
        print("\nAuthentication errors found:")
        for error in auth_errors[-3:]:
            print(f"  {error.strip()}")
    
    # Check for setup errors
    setup_errors = [line for line in lines if 'error setting up alpaca' in line.lower()]
    if setup_errors:
        print("\nSetup errors found:")
        for error in setup_errors[-3:]:
            print(f"  {error.strip()}")
    
    # 3. Check service startup
    print("\n\n3. SERVICE STARTUP SEQUENCE:")
    print("-" * 40)
    
    startup_lines = []
    for i, line in enumerate(lines):
        if any(phrase in line.lower() for phrase in ['starting paper trading', 'paper trading service', 'initialized']):
            # Get next 10 lines after startup
            for j in range(i, min(i+10, len(lines))):
                startup_lines.append(lines[j].strip())
    
    if startup_lines:
        print("Recent startup sequence:")
        for line in startup_lines[-10:]:
            print(f"  {line[:120]}{'...' if len(line) > 120 else ''}")
    
    # 4. Summary
    print("\n\n" + "=" * 60)
    print("ANALYSIS SUMMARY:")
    print("=" * 60)
    
    # Count occurrences
    simulation_count = sum(1 for line in lines if 'simulation mode' in line.lower())
    connected_count = sum(1 for line in lines if 'connected to alpaca' in line.lower())
    error_count = sum(1 for line in lines if 'error' in line.lower() and 'alpaca' in line.lower())
    
    print(f"\nLog statistics:")
    print(f"  - Times entered simulation mode: {simulation_count}")
    print(f"  - Times connected to Alpaca: {connected_count}")
    print(f"  - Alpaca-related errors: {error_count}")
    
    print("\nMost likely issues:")
    if import_errors:
        print("  ✗ Module import problems detected")
    if auth_errors:
        print("  ✗ Authentication failures detected")
    if setup_errors:
        print("  ✗ Setup errors detected")
    if simulation_count > connected_count:
        print("  ✗ Service consistently falling back to simulation")
    
    print("\nRecommendations:")
    print("1. Check if alpaca-trade-api is installed in the service environment")
    print("2. Verify the service can access the .env file")
    print("3. Add more detailed error logging in setup_alpaca_api()")
    print("=" * 60)


if __name__ == "__main__":
    check_logs()

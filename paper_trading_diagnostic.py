#!/usr/bin/env python3
"""
DIAGNOSTIC VERSION - Paper Trading Service
This version includes extensive print statements to help identify where failures occur
"""

import sys
import traceback

print("=== PAPER TRADING SERVICE DIAGNOSTIC START ===")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")

# Test imports one by one
print("\n1. Testing imports...")

try:
    import os
    print("✓ os imported")
except Exception as e:
    print(f"✗ Failed to import os: {e}")
    sys.exit(1)

try:
    from pathlib import Path
    print("✓ pathlib imported")
except Exception as e:
    print(f"✗ Failed to import pathlib: {e}")

try:
    from dotenv import load_dotenv
    print("✓ dotenv imported")
except Exception as e:
    print(f"✗ Failed to import dotenv: {e}")
    print("  Install with: pip install python-dotenv")

try:
    import requests
    print("✓ requests imported")
except Exception as e:
    print(f"✗ Failed to import requests: {e}")
    print("  Install with: pip install requests")

try:
    import logging
    print("✓ logging imported")
except Exception as e:
    print(f"✗ Failed to import logging: {e}")

try:
    import sqlite3
    print("✓ sqlite3 imported")
except Exception as e:
    print(f"✗ Failed to import sqlite3: {e}")

try:
    import json
    print("✓ json imported")
except Exception as e:
    print(f"✗ Failed to import json: {e}")

try:
    from datetime import datetime
    print("✓ datetime imported")
except Exception as e:
    print(f"✗ Failed to import datetime: {e}")

try:
    from flask import Flask, request, jsonify
    print("✓ flask imported")
except Exception as e:
    print(f"✗ Failed to import flask: {e}")
    print("  Install with: pip install flask")

try:
    from typing import Dict, List, Optional
    print("✓ typing imported")
except Exception as e:
    print(f"✗ Failed to import typing: {e}")

# Check current directory
print(f"\n2. Current directory: {os.getcwd()}")
print(f"   Script location: {os.path.abspath(__file__)}")

# Check for .env file
env_path = Path('.env')
print(f"\n3. Checking for .env file...")
if env_path.exists():
    print(f"✓ .env file found at: {env_path.absolute()}")
else:
    print(f"✗ .env file not found")

# Load environment variables
try:
    load_dotenv()
    print("✓ dotenv loaded")
except Exception as e:
    print(f"✗ Failed to load dotenv: {e}")

# Check environment variables
print("\n4. Checking environment variables...")
api_key = os.environ.get('ALPACA_PAPER_API_KEY', '')
api_secret = os.environ.get('ALPACA_PAPER_API_SECRET', '')
print(f"   ALPACA_PAPER_API_KEY: {'Set' if api_key else 'Not set'}")
print(f"   ALPACA_PAPER_API_SECRET: {'Set' if api_secret else 'Not set'}")

# Try to import Alpaca
print("\n5. Testing Alpaca import...")
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
    print("✓ alpaca_trade_api imported successfully")
except ImportError as e:
    ALPACA_AVAILABLE = False
    print(f"✗ alpaca_trade_api not available: {e}")
    print("  Install with: pip install alpaca-trade-api")

# Check database
print("\n6. Checking database...")
db_path = './trading_system.db'
if Path(db_path).exists():
    print(f"✓ Database found at: {Path(db_path).absolute()}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        if cursor.fetchone():
            print("✓ 'trades' table exists in database")
        else:
            print("✗ 'trades' table NOT found in database")
        conn.close()
    except Exception as e:
        print(f"✗ Error checking database: {e}")
else:
    print(f"✗ Database not found at: {Path(db_path).absolute()}")

# Check logs directory
print("\n7. Checking logs directory...")
logs_dir = Path('./logs')
if logs_dir.exists():
    print(f"✓ Logs directory exists: {logs_dir.absolute()}")
    # Check permissions
    try:
        test_file = logs_dir / 'test_write.tmp'
        test_file.write_text('test')
        test_file.unlink()
        print("✓ Can write to logs directory")
    except Exception as e:
        print(f"✗ Cannot write to logs directory: {e}")
else:
    print(f"✗ Logs directory does not exist")
    try:
        logs_dir.mkdir(parents=True)
        print("✓ Created logs directory")
    except Exception as e:
        print(f"✗ Failed to create logs directory: {e}")

# Test logging setup
print("\n8. Testing logging setup...")
try:
    # Basic logging setup
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('PaperTradingTest')
    logger.info("Test log message")
    print("✓ Basic logging works")
    
    # Try file handler
    try:
        handler = logging.FileHandler('./logs/paper_trading_diagnostic.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.info("Test file log message")
        print("✓ File logging works")
    except Exception as e:
        print(f"✗ File logging failed: {e}")
        
except Exception as e:
    print(f"✗ Logging setup failed: {e}")
    traceback.print_exc()

# Test Flask app creation
print("\n9. Testing Flask app creation...")
try:
    app = Flask(__name__)
    print("✓ Flask app created")
    
    @app.route('/test', methods=['GET'])
    def test():
        return {'status': 'ok'}
    
    print("✓ Test route added")
except Exception as e:
    print(f"✗ Flask app creation failed: {e}")
    traceback.print_exc()

# Try to create service instance
print("\n10. Testing PaperTradingService creation...")
try:
    # Import the actual service
    from paper_trading import PaperTradingService
    print("✓ PaperTradingService imported")
    
    # Try to create instance
    service = PaperTradingService()
    print("✓ PaperTradingService instance created")
    
except Exception as e:
    print(f"✗ Failed to create PaperTradingService: {e}")
    print("\nFull traceback:")
    traceback.print_exc()

print("\n=== DIAGNOSTIC COMPLETE ===")
print("\nSummary:")
print("- If you see errors above, fix them before running the service")
print("- Common issues:")
print("  1. Missing dependencies (install with pip)")
print("  2. Database not initialized")
print("  3. Logs directory permissions")
print("  4. Import errors in paper_trading.py")

# If we get here, try to show what would happen when running
print("\n11. What happens when we try to run the service...")
try:
    if 'service' in locals():
        print("Would start service on port 5005...")
        # Don't actually run it in diagnostic mode
    else:
        print("Service instance not created, cannot proceed")
except Exception as e:
    print(f"Error checking service: {e}")

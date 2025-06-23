#!/usr/bin/env python3
"""
Complete setup for Paper Trading Service
Installs dependencies and creates necessary files
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{description}...")
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Success")
            if result.stdout:
                print(result.stdout.strip())
            return True
        else:
            print(f"✗ Failed")
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

print("=== Paper Trading Service Setup ===")
print(f"Python: {sys.executable}")

# 1. Install python-dotenv
print("\n1. Installing python-dotenv...")
success = run_command(
    [sys.executable, '-m', 'pip', 'install', 'python-dotenv'],
    "Installing python-dotenv"
)

if not success:
    print("Trying user install...")
    run_command(
        [sys.executable, '-m', 'pip', 'install', '--user', 'python-dotenv'],
        "Installing python-dotenv (user)"
    )

# 2. Install alpaca-trade-api
print("\n2. Installing alpaca-trade-api...")
run_command(
    [sys.executable, '-m', 'pip', 'install', 'alpaca-trade-api'],
    "Installing alpaca-trade-api"
)

# 3. Verify installations
print("\n3. Verifying installations...")
try:
    import dotenv
    print("✓ python-dotenv is installed")
except ImportError:
    print("✗ python-dotenv is NOT installed")

try:
    import alpaca_trade_api
    print("✓ alpaca-trade-api is installed")
except ImportError:
    print("✗ alpaca-trade-api is NOT installed")

# 4. Create .env file
print("\n4. Setting up .env file...")
env_path = Path('.env')
if not env_path.exists():
    env_content = """# Paper Trading API Configuration
# Get your API keys from: https://alpaca.markets/

# Alpaca Paper Trading API Keys
ALPACA_PAPER_API_KEY=your_paper_api_key_here
ALPACA_PAPER_API_SECRET=your_paper_api_secret_here

# Base URL (use paper trading URL)
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Optional: Other service configurations
COORDINATION_SERVICE_URL=http://localhost:5000
LOG_LEVEL=INFO
"""
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✓ Created .env template file")
    print("⚠️  Remember to edit .env and add your Alpaca API keys!")
else:
    print("✓ .env file already exists")

# 5. Check/create trades table
print("\n5. Setting up database...")
db_path = Path('./trading_system.db')
if db_path.exists():
    print("✓ Database found")
    import sqlite3
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if trades table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        if not cursor.fetchone():
            print("Creating trades table...")
            cursor.execute("""
                CREATE TABLE trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10) NOT NULL,
                    signal_type VARCHAR(10) NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    confidence REAL,
                    trade_reason TEXT,
                    alpaca_order_id VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'pending',
                    profit_loss REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX idx_trades_symbol ON trades(symbol)")
            cursor.execute("CREATE INDEX idx_trades_status ON trades(status)")
            cursor.execute("CREATE INDEX idx_trades_created ON trades(created_at)")
            
            conn.commit()
            print("✓ Created trades table with indexes")
        else:
            print("✓ trades table already exists")
            
        conn.close()
    except Exception as e:
        print(f"✗ Database error: {e}")
else:
    print("✗ Database not found")
    print("  Run database_migration.py to create it")

# 6. Test paper trading import
print("\n6. Testing Paper Trading Service import...")
try:
    from paper_trading import PaperTradingService
    print("✓ Paper Trading Service can be imported!")
    print("\n✅ Setup complete! You can now run:")
    print("   python paper_trading.py")
except Exception as e:
    print(f"✗ Import failed: {e}")
    print("\nTrying the no-dotenv version...")
    try:
        # Test if we can at least run without dotenv
        import flask
        print("✓ Flask is available")
        print("\nYou can try running:")
        print("   python paper_trading_no_dotenv.py")
    except:
        print("✗ Flask is not available")

print("\n" + "="*50)
print("Summary:")
print("="*50)
print("1. If setup was successful, run: python paper_trading.py")
print("2. If dotenv issues persist, use: python paper_trading_no_dotenv.py") 
print("3. To run in simulation mode, just don't add API keys to .env")
print("\nFor Alpaca API keys:")
print("- Sign up at https://alpaca.markets/")
print("- Use PAPER trading keys (not live trading)")
print("- Add them to the .env file")

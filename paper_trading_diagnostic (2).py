#!/usr/bin/env python3
"""
Paper Trading Diagnostic Tool
Checks the status of paper trading and Alpaca API connection
"""

import requests
import sqlite3
import json
import os
from datetime import datetime, timedelta

class PaperTradingDiagnostic:
    def __init__(self):
        self.db_path = './trading_system.db'
        self.paper_trading_port = 5005
        
    def run_diagnostics(self):
        """Run complete paper trading diagnostics"""
        print("=" * 60)
        print("PAPER TRADING DIAGNOSTIC REPORT")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. Check service health
        self.check_service_health()
        
        # 2. Check Alpaca API connection
        self.check_alpaca_connection()
        
        # 3. Check database for trades
        self.check_database_trades()
        
        # 4. Check for Alpaca credentials
        self.check_alpaca_credentials()
        
        # 5. Check recent trading signals
        self.check_trading_signals()
        
        # 6. Check for any errors in trades
        self.check_trade_errors()
        
    def check_service_health(self):
        """Check if paper trading service is running"""
        print("\n1. SERVICE HEALTH CHECK")
        print("-" * 40)
        
        try:
            response = requests.get(f'http://localhost:{self.paper_trading_port}/health', timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Paper Trading Service: HEALTHY")
                print(f"  - Status: {data.get('status', 'Unknown')}")
                print(f"  - Alpaca Connected: {data.get('alpaca_connected', False)}")
                print(f"  - Mode: {data.get('mode', 'Unknown')}")
            else:
                print(f"✗ Paper Trading Service: UNHEALTHY (Status: {response.status_code})")
        except Exception as e:
            print(f"✗ Paper Trading Service: OFFLINE")
            print(f"  Error: {str(e)}")
    
    def check_alpaca_connection(self):
        """Check Alpaca API connection status"""
        print("\n2. ALPACA API CONNECTION")
        print("-" * 40)
        
        try:
            # Check account endpoint
            response = requests.get(f'http://localhost:{self.paper_trading_port}/account', timeout=5)
            if response.status_code == 200:
                account = response.json()
                print(f"✓ Alpaca Account Connected")
                print(f"  - Account Status: {account.get('status', 'Unknown')}")
                print(f"  - Buying Power: ${account.get('buying_power', 0)}")
                print(f"  - Portfolio Value: ${account.get('portfolio_value', 0)}")
                print(f"  - Cash: ${account.get('cash', 0)}")
                
                # Check if this is real data or simulation
                if account.get('account_number'):
                    print(f"  - Account Number: {account['account_number'][:4]}****")
                    print(f"  - MODE: REAL PAPER TRADING")
                else:
                    print(f"  - MODE: SIMULATION (No Alpaca connection)")
            else:
                print(f"✗ Cannot retrieve account info (Status: {response.status_code})")
                
            # Check positions
            response = requests.get(f'http://localhost:{self.paper_trading_port}/positions', timeout=5)
            if response.status_code == 200:
                positions = response.json()
                print(f"\n  Current Positions: {len(positions)}")
                for pos in positions[:5]:  # Show first 5
                    print(f"    - {pos.get('symbol')}: {pos.get('qty')} shares @ ${pos.get('avg_entry_price', 0)}")
                    
        except Exception as e:
            print(f"✗ Cannot connect to Paper Trading Service")
            print(f"  Error: {str(e)}")
    
    def check_database_trades(self):
        """Check trades in database"""
        print("\n3. DATABASE TRADES ANALYSIS")
        print("-" * 40)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check trades table
            cursor.execute("SELECT COUNT(*) FROM trades")
            total_trades = cursor.fetchone()[0]
            print(f"Total trades in database: {total_trades}")
            
            # Check recent trades
            cursor.execute("""
                SELECT trade_id, symbol, side, quantity, status, 
                       alpaca_order_id, created_at 
                FROM trades 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            recent_trades = cursor.fetchall()
            if recent_trades:
                print("\nRecent trades:")
                for trade in recent_trades:
                    print(f"  - {trade[1]} {trade[2]} {trade[3]} shares")
                    print(f"    Status: {trade[4]}")
                    print(f"    Alpaca Order ID: {trade[5] or 'NONE (Simulation)'}")
                    print(f"    Time: {trade[6]}")
            else:
                print("No trades found in database")
                
            # Check for trades with Alpaca order IDs
            cursor.execute("""
                SELECT COUNT(*) FROM trades 
                WHERE alpaca_order_id IS NOT NULL 
                AND alpaca_order_id != ''
            """)
            alpaca_trades = cursor.fetchone()[0]
            print(f"\nTrades with Alpaca Order IDs: {alpaca_trades}")
            
            if alpaca_trades == 0 and total_trades > 0:
                print("⚠️  WARNING: Trades exist but none have Alpaca Order IDs")
                print("   This suggests trades are being simulated, not executed on Alpaca")
                
        except Exception as e:
            print(f"Error checking database: {str(e)}")
        finally:
            conn.close()
    
    def check_alpaca_credentials(self):
        """Check if Alpaca credentials are configured"""
        print("\n4. ALPACA CREDENTIALS CHECK")
        print("-" * 40)
        
        # Check environment variables
        api_key = os.environ.get('ALPACA_PAPER_API_KEY')
        api_secret = os.environ.get('ALPACA_PAPER_API_SECRET')
        
        if api_key and api_secret:
            print(f"✓ Alpaca API Key: Set ({api_key[:10]}...)")
            print(f"✓ Alpaca API Secret: Set")
        else:
            print("✗ Alpaca credentials not found in environment")
            
        # Check .env file
        if os.path.exists('.env'):
            print("\n.env file found - checking for Alpaca credentials...")
            with open('.env', 'r') as f:
                env_content = f.read()
                if 'ALPACA_PAPER_API_KEY' in env_content:
                    print("✓ Alpaca credentials found in .env file")
                else:
                    print("✗ Alpaca credentials not found in .env file")
        else:
            print("\n✗ No .env file found")
            
        print("\nTo enable real paper trading, you need:")
        print("1. Create a free Alpaca account at https://alpaca.markets")
        print("2. Get your Paper Trading API credentials")
        print("3. Set environment variables or create .env file with:")
        print("   ALPACA_PAPER_API_KEY=your_api_key")
        print("   ALPACA_PAPER_API_SECRET=your_api_secret")
    
    def check_trading_signals(self):
        """Check recent trading signals"""
        print("\n5. TRADING SIGNALS ANALYSIS")
        print("-" * 40)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if trading_signals table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='trading_signals'
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    SELECT COUNT(*) FROM trading_signals 
                    WHERE created_at > datetime('now', '-1 day')
                """)
                recent_signals = cursor.fetchone()[0]
                print(f"Trading signals (last 24h): {recent_signals}")
                
                # Show recent signals
                cursor.execute("""
                    SELECT symbol, signal_type, confidence, created_at 
                    FROM trading_signals 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                
                signals = cursor.fetchall()
                if signals:
                    print("\nRecent signals:")
                    for signal in signals:
                        print(f"  - {signal[0]}: {signal[1]} (confidence: {signal[2]:.2f})")
                        print(f"    Time: {signal[3]}")
            else:
                print("✗ trading_signals table not found")
                
        except Exception as e:
            print(f"Error checking signals: {str(e)}")
        finally:
            conn.close()
    
    def check_trade_errors(self):
        """Check for any trade execution errors"""
        print("\n6. TRADE EXECUTION ERRORS")
        print("-" * 40)
        
        # Check paper trading log
        log_path = './logs/paper_trading_service.log'
        if os.path.exists(log_path):
            print(f"Checking {log_path} for errors...")
            
            error_count = 0
            alpaca_errors = []
            recent_trades = []
            
            with open(log_path, 'r') as f:
                lines = f.readlines()[-100:]  # Last 100 lines
                
                for line in lines:
                    if 'ERROR' in line:
                        error_count += 1
                        if 'alpaca' in line.lower() or 'api' in line.lower():
                            alpaca_errors.append(line.strip())
                    if 'Executing trade' in line or 'Trade executed' in line:
                        recent_trades.append(line.strip())
            
            print(f"Errors found (last 100 lines): {error_count}")
            
            if alpaca_errors:
                print("\nAlpaca-related errors:")
                for error in alpaca_errors[-5:]:  # Last 5
                    print(f"  - {error}")
                    
            if recent_trades:
                print(f"\nRecent trade attempts: {len(recent_trades)}")
                for trade in recent_trades[-3:]:  # Last 3
                    print(f"  - {trade}")
            else:
                print("\n⚠️  No trade execution attempts found in recent logs")
        else:
            print("✗ Paper trading log file not found")
            
        print("\n" + "=" * 60)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    diagnostic = PaperTradingDiagnostic()
    diagnostic.run_diagnostics()

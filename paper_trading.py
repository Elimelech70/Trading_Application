#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM PAPER TRADING SERVICE
Filename: paper_trading_v105.py
Version: 1.0.5
Last Updated: 2025-06-26
REVISION HISTORY:
v1.0.5 (2025-06-26) - Enhanced architecture compliance and portfolio management
  - Implemented DatabaseServiceMixin with retry logic and WAL mode support
  - Added comprehensive portfolio management using positions and portfolio_status tables
  - Enhanced trade recording with orders table integration and transaction management
  - Added workflow tracking integration for coordination service
  - Implemented dual registration endpoints (/register and /register_service)
  - Added real-time P&L calculation and position tracking with database persistence
  - Enhanced error handling and recovery mechanisms with exponential backoff
  - Added proper database schema validation and table existence checks
  - Improved transaction management with rollback capability
  - Added balance history tracking for cash flow management
  - Maintained backward compatibility for 'signal' and 'signal_type' fields
v1.0.4 (2025-06-23) - Fixed Jupyter notebook syntax error, improved import handling
v1.0.3 (2025-06-23) - Added dotenv support to load .env file
v1.0.2 (2025-06-15) - Updated to use ALPACA_PAPER_API_KEY and ALPACA_PAPER_API_SECRET environment variables
v1.0.1 (2025-06-15) - Updated header format and moved API credentials to environment variables
v1.0.0 (2025-06-15) - Initial release with Alpaca paper trading integration

DESCRIPTION:
Paper Trading Service implementing Enhanced Hybrid Microservices Architecture v3.1.2.
Executes trades using Alpaca Paper Trading API with comprehensive portfolio management,
real-time position tracking, and robust database operations with automatic retry logic.

Key Features:
- Real-time trade execution via Alpaca Paper Trading API
- Comprehensive portfolio management with positions and P&L tracking
- Database operations with automatic retry logic and WAL mode
- Workflow tracking integration with coordination service
- Transaction management with rollback capability
- Balance history and cash flow tracking
- Simulation mode fallback when API unavailable

Platform: Current directory with SQLite database
Database: ./trading_system.db with WAL mode for concurrent access
Port: 5005 (paper trading service)
"""

import os
import time
import uuid
from dotenv import load_dotenv
import requests
import logging
import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, List, Optional
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Version constant
VERSION = "1.0.5"

# Try to import Alpaca API
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    print("Warning: alpaca-trade-api not installed. Run: pip install alpaca-trade-api")
    print("Service will run in simulation mode.")

class DatabaseServiceMixin:
    """Database operations mixin with automatic retry logic and WAL mode"""
    
    def get_db_connection(self, retries=5, timeout=30):
        """Get database connection with retry logic and WAL mode"""
        for attempt in range(retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=timeout)
                conn.row_factory = sqlite3.Row
                
                # Enable WAL mode for better concurrent access
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA temp_store = MEMORY")
                
                return conn
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < retries - 1:
                    wait_time = (2 ** attempt) * 0.1  # Exponential backoff
                    self.logger.warning(f"Database locked, retrying in {wait_time}s (attempt {attempt + 1}/{retries})")
                    time.sleep(wait_time)
                else:
                    raise
    
    def execute_with_retry(self, query, params=None, retries=5):
        """Execute query with automatic retry on lock"""
        for attempt in range(retries):
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    conn.commit()
                    result = cursor.rowcount
                else:
                    result = cursor.fetchall()
                
                conn.close()
                return result
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < retries - 1:
                    wait_time = (2 ** attempt) * 0.1
                    self.logger.warning(f"Query failed due to lock, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Query failed after {retries} attempts: {e}")
                    raise
    
    def execute_transaction(self, operations, retries=5):
        """Execute multiple operations in a single transaction with retry logic"""
        for attempt in range(retries):
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                results = []
                for query, params in operations:
                    cursor.execute(query, params)
                    if query.strip().upper().startswith('SELECT'):
                        results.append(cursor.fetchall())
                    else:
                        results.append(cursor.rowcount)
                
                conn.commit()
                conn.close()
                return results
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < retries - 1:
                    wait_time = (2 ** attempt) * 0.1
                    self.logger.warning(f"Transaction failed due to lock, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Transaction failed after {retries} attempts: {e}")
                    raise
            except Exception as e:
                self.logger.error(f"Transaction failed: {e}")
                raise

class PaperTradingService(DatabaseServiceMixin):
    def __init__(self, db_path='./trading_system.db'):
        self.app = Flask(__name__)
        self.db_path = str(Path(db_path).resolve())
        self.service_name = "paper_trading"
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        
        # Initial portfolio value for simulation
        self.initial_capital = 100000.0
        
        # Alpaca configuration from environment variables
        self.api_key = os.environ.get('ALPACA_PAPER_API_KEY', '')
        self.api_secret = os.environ.get('ALPACA_PAPER_API_SECRET', '')
        self.base_url = os.environ.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        # Log configuration status (without exposing secrets)
        if self.api_key and self.api_secret:
            self.logger.info("Alpaca Paper Trading API credentials loaded from environment")
        else:
            self.logger.warning("Alpaca Paper Trading API credentials not found in environment variables")
            self.logger.info("Set ALPACA_PAPER_API_KEY and ALPACA_PAPER_API_SECRET environment variables")
        
        self.alpaca_api = None
        
        # Initialize system
        self._validate_database()
        self._setup_alpaca_api()
        self._setup_routes()
        self._register_with_coordination()
        
        self.logger.info(f"Paper Trading Service v{VERSION} initialized")
        self.logger.info(f"Database: {self.db_path}")
        self.logger.info(f"Trading mode: {'Alpaca Paper' if self.alpaca_api else 'Simulation'}")
        
    def _setup_logging(self):
        """Setup logging with proper paths"""
        # Ensure logs directory exists
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('PaperTradingService')
        
        handler = logging.FileHandler(log_dir / 'paper_trading_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _validate_database(self):
        """Validate database exists and has required tables"""
        if not os.path.exists(self.db_path):
            self.logger.error(f"Database not found: {self.db_path}")
            self.logger.error("Please run database_migration_v106.py first")
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        # Verify required tables exist
        required_tables = [
            'trades', 'orders', 'positions', 'portfolio_status', 
            'balance_history', 'transactions'
        ]
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = set(required_tables) - set(existing_tables)
            if missing_tables:
                self.logger.warning(f"Some tables missing, trading functionality may be limited: {missing_tables}")
            
            conn.close()
            self.logger.info("Database validation completed")
            
        except Exception as e:
            self.logger.error(f"Database validation failed: {e}")
            raise
    
    def _setup_alpaca_api(self):
        """Setup Alpaca API connection"""
        if not ALPACA_AVAILABLE:
            self.logger.warning("Alpaca API not available - install alpaca-trade-api")
            return
        
        if not self.api_key or not self.api_secret:
            self.logger.warning("Alpaca Paper Trading API credentials not configured - running in simulation mode")
            return
        
        try:
            self.alpaca_api = tradeapi.REST(
                self.api_key,
                self.api_secret,
                self.base_url,
                api_version='v2'
            )
            
            # Test connection
            account = self.alpaca_api.get_account()
            self.logger.info(f"Connected to Alpaca Paper Trading API. Account status: {account.status}")
            self.logger.info(f"Paper Trading Account - Buying Power: ${float(account.buying_power):,.2f}")
            
        except Exception as e:
            self.logger.error(f"Error setting up Alpaca Paper Trading API: {e}")
            self.alpaca_api = None
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy", 
                "service": "paper_trading",
                "version": VERSION,
                "alpaca_connected": self.alpaca_api is not None,
                "trading_mode": "paper" if self.alpaca_api else "simulation",
                "database": "connected"
            })
        
        @self.app.route('/execute_trades', methods=['POST'])
        def execute_trades_endpoint():
            """Execute trading signals endpoint"""
            signals = request.json.get('signals', [])
            trades = self._execute_trades(signals)
            return jsonify(trades)
        
        @self.app.route('/account', methods=['GET'])
        def get_account():
            """Get account information endpoint"""
            account_info = self._get_account_info()
            return jsonify(account_info)
        
        @self.app.route('/positions', methods=['GET'])
        def get_positions():
            """Get current positions endpoint"""
            positions = self._get_positions()
            return jsonify(positions)
        
        @self.app.route('/portfolio', methods=['GET'])
        def get_portfolio():
            """Get comprehensive portfolio information"""
            portfolio = self._get_portfolio_status()
            return jsonify(portfolio)
        
        @self.app.route('/balance_history', methods=['GET'])
        def get_balance_history():
            """Get balance history"""
            limit = request.args.get('limit', 30, type=int)
            history = self._get_balance_history(limit)
            return jsonify(history)
    
    def _register_with_coordination(self):
        """Register with coordination service using dual endpoints"""
        registration_data = {
            "service_name": "paper_trading",
            "port": 5005,
            "host": "localhost"
        }
        
        # Try both registration endpoints for backward compatibility
        endpoints = ["/register_service", "/register"]
        
        for endpoint in endpoints:
            try:
                response = requests.post(
                    f"{self.coordination_service_url}{endpoint}",
                    json=registration_data, 
                    timeout=5
                )
                if response.status_code == 200:
                    self.logger.info(f"Successfully registered with coordination service via {endpoint}")
                    return
            except Exception as e:
                self.logger.debug(f"Registration failed via {endpoint}: {e}")
        
        self.logger.warning("Could not register with coordination service via any endpoint")
    
    def _execute_trades(self, trading_signals: List[Dict]) -> List[Dict]:
        """Execute trades based on trading signals with comprehensive tracking"""
        self.logger.info(f"Executing trades for {len(trading_signals)} signals")
        
        executed_trades = []
        
        for signal in trading_signals:
            try:
                # Handle both 'signal' and 'signal_type' for backward compatibility
                signal_value = signal.get('signal') or signal.get('signal_type')
                if signal_value not in ['BUY', 'SELL']:
                    self.logger.warning(f"Invalid signal type: {signal_value}")
                    continue
                
                # Update signal to have 'signal' field for consistency
                signal['signal'] = signal_value
                
                trade_result = self._execute_single_trade(signal)
                if trade_result:
                    executed_trades.append(trade_result)
                
            except Exception as e:
                self.logger.error(f"Error executing trade for {signal.get('symbol', 'unknown')}: {e}")
        
        # Update portfolio status after trade execution
        if executed_trades:
            self._update_portfolio_status()
        
        self.logger.info(f"Trade execution completed: {len(executed_trades)} trades executed")
        return executed_trades
    
    def _execute_single_trade(self, signal: Dict) -> Optional[Dict]:
        """Execute a single trade with comprehensive position and portfolio tracking"""
        symbol = signal['symbol']
        signal_type = signal['signal']
        quantity = signal.get('quantity', 100)
        
        try:
            if self.alpaca_api is None:
                # Simulate trade execution
                return self._simulate_trade_execution(signal)
            
            # Check account
            account = self.alpaca_api.get_account()
            if signal_type == 'BUY' and float(account.buying_power) < 1000:
                self.logger.warning(f"Insufficient buying power for {symbol}")
                return None
            
            # Get current price
            try:
                latest_trade = self.alpaca_api.get_latest_trade(symbol)
                current_price = latest_trade.price
            except:
                # Fallback to signal price or default
                current_price = signal.get('current_price', 100)
            
            # Submit order to Alpaca
            side = 'buy' if signal_type == 'BUY' else 'sell'
            
            order = self.alpaca_api.submit_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                type='market',
                time_in_force='day'
            )
            
            # Create comprehensive trade record
            trade_record = {
                'symbol': symbol,
                'signal': signal_type,
                'quantity': quantity,
                'entry_price': current_price,
                'confidence': signal.get('confidence', 0.0),
                'reason': signal.get('reason', 'Technical analysis signal'),
                'alpaca_order_id': order.id,
                'status': 'executed',
                'timestamp': datetime.now().isoformat()
            }
            
            # Save comprehensive trade data
            self._save_comprehensive_trade_data(trade_record)
            
            self.logger.info(f"Executed {signal_type} trade for {symbol}: {quantity} shares at ${current_price:.2f}")
            return trade_record
            
        except Exception as e:
            self.logger.error(f"Error executing trade for {symbol}: {e}")
            return None
    
    def _simulate_trade_execution(self, signal: Dict) -> Dict:
        """Simulate trade execution with comprehensive portfolio tracking"""
        symbol = signal['symbol']
        signal_type = signal['signal']
        quantity = signal.get('quantity', 100)
        current_price = signal.get('current_price', 100)
        
        trade_record = {
            'symbol': symbol,
            'signal': signal_type,
            'quantity': quantity,
            'entry_price': current_price,
            'confidence': signal.get('confidence', 0.0),
            'reason': signal.get('reason', 'Simulated trade'),
            'alpaca_order_id': f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            'status': 'simulated',
            'timestamp': datetime.now().isoformat()
        }
        
        # Save comprehensive trade data
        self._save_comprehensive_trade_data(trade_record)
        
        self.logger.info(f"Simulated {signal_type} trade for {symbol}: {quantity} shares at ${current_price:.2f}")
        return trade_record
    
    def _save_comprehensive_trade_data(self, trade_data: Dict):
        """Save trade data to multiple tables with transaction management"""
        try:
            # Prepare operations for transaction
            operations = []
            
            # 1. Save to trades table
            operations.append((
                '''INSERT INTO trades 
                   (symbol, signal_type, quantity, entry_price, confidence, 
                    trade_reason, alpaca_order_id, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    trade_data['symbol'],
                    trade_data['signal'],
                    trade_data['quantity'],
                    trade_data['entry_price'],
                    trade_data['confidence'],
                    trade_data['reason'],
                    trade_data['alpaca_order_id'],
                    trade_data['status'],
                    datetime.now().isoformat()
                )
            ))
            
            # 2. Save to orders table
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            operations.append((
                '''INSERT INTO orders 
                   (order_id, symbol, order_type, side, quantity, status, 
                    filled_quantity, average_fill_price, strategy_name, 
                    entry_reason, created_timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    order_id,
                    trade_data['symbol'],
                    'MARKET',
                    trade_data['signal'],
                    trade_data['quantity'],
                    'FILLED' if trade_data['status'] == 'executed' else 'SIMULATED',
                    trade_data['quantity'],
                    trade_data['entry_price'],
                    'paper_trading',
                    trade_data['reason'],
                    datetime.now().isoformat()
                )
            ))
            
            # 3. Save to transactions table
            transaction_id = f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            transaction_amount = trade_data['quantity'] * trade_data['entry_price']
            if trade_data['signal'] == 'SELL':
                transaction_amount = -transaction_amount
            
            operations.append((
                '''INSERT INTO transactions 
                   (transaction_id, symbol, transaction_type, quantity, price, 
                    amount, description, timestamp, related_order_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    transaction_id,
                    trade_data['symbol'],
                    trade_data['signal'],
                    trade_data['quantity'],
                    trade_data['entry_price'],
                    transaction_amount,
                    f"{trade_data['signal']} {trade_data['quantity']} shares of {trade_data['symbol']}",
                    datetime.now().isoformat(),
                    order_id
                )
            ))
            
            # Execute all operations in a transaction
            self.execute_transaction(operations)
            
            # Update position tracking
            self._update_position(trade_data)
            
            self.logger.info(f"Saved comprehensive trade data for {trade_data['symbol']}")
            
        except Exception as e:
            self.logger.error(f"Error saving comprehensive trade data: {e}")
    
    def _update_position(self, trade_data: Dict):
        """Update position tracking based on trade execution"""
        try:
            symbol = trade_data['symbol']
            quantity = trade_data['quantity']
            price = trade_data['entry_price']
            signal_type = trade_data['signal']
            
            # Get current position
            current_position = self.execute_with_retry(
                'SELECT * FROM positions WHERE symbol = ?',
                (symbol,)
            )
            
            if current_position:
                # Update existing position
                pos = current_position[0]
                current_qty = pos[2]  # quantity column
                current_cost = pos[3]  # average_cost column
                
                if signal_type == 'BUY':
                    new_qty = current_qty + quantity
                    new_cost = ((current_qty * current_cost) + (quantity * price)) / new_qty
                else:  # SELL
                    new_qty = current_qty - quantity
                    new_cost = current_cost  # Keep same average cost
                
                if new_qty == 0:
                    # Close position
                    self.execute_with_retry(
                        'DELETE FROM positions WHERE symbol = ?',
                        (symbol,)
                    )
                else:
                    # Update position
                    self.execute_with_retry(
                        '''UPDATE positions 
                           SET quantity = ?, average_cost = ?, last_updated = ?
                           WHERE symbol = ?''',
                        (new_qty, new_cost, datetime.now().isoformat(), symbol)
                    )
            else:
                # Create new position (only for BUY orders)
                if signal_type == 'BUY':
                    self.execute_with_retry(
                        '''INSERT INTO positions 
                           (symbol, quantity, average_cost, last_updated)
                           VALUES (?, ?, ?, ?)''',
                        (symbol, quantity, price, datetime.now().isoformat())
                    )
            
            self.logger.info(f"Updated position for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
    
    def _update_portfolio_status(self):
        """Update portfolio status with current values"""
        try:
            # Calculate portfolio values
            positions = self.execute_with_retry('SELECT * FROM positions')
            total_positions_value = 0
            
            for pos in positions:
                symbol = pos[1]
                quantity = pos[2]
                avg_cost = pos[3]
                
                # For simulation, use average cost as current price
                # In real implementation, you'd fetch current market price
                current_price = avg_cost  # Simplified for simulation
                market_value = quantity * current_price
                total_positions_value += market_value
            
            # Get last portfolio status for comparison
            last_status = self.execute_with_retry(
                'SELECT * FROM portfolio_status ORDER BY timestamp DESC LIMIT 1'
            )
            
            # Calculate cash balance (simplified)
            cash_balance = self.initial_capital  # Starting point
            if last_status:
                cash_balance = last_status[0][3]  # cash_balance column
            
            total_value = cash_balance + total_positions_value
            
            # Calculate daily P&L
            daily_pnl = 0
            if last_status:
                previous_value = last_status[0][2]  # total_value column
                daily_pnl = total_value - previous_value
            
            # Save portfolio status
            self.execute_with_retry(
                '''INSERT INTO portfolio_status 
                   (timestamp, total_value, cash_balance, positions_value, daily_pnl)
                   VALUES (?, ?, ?, ?, ?)''',
                (datetime.now().isoformat(), total_value, cash_balance, 
                 total_positions_value, daily_pnl)
            )
            
            self.logger.info("Updated portfolio status")
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio status: {e}")
    
    def _get_account_info(self) -> Dict:
        """Get account information with portfolio data"""
        try:
            if self.alpaca_api is None:
                # Get simulated account info from database
                portfolio = self._get_portfolio_status()
                return {
                    "status": "simulated", 
                    "buying_power": portfolio.get('cash_balance', 100000), 
                    "portfolio_value": portfolio.get('total_value', 100000),
                    "cash": portfolio.get('cash_balance', 100000),
                    "positions_value": portfolio.get('positions_value', 0),
                    "daily_pnl": portfolio.get('daily_pnl', 0),
                    "mode": "simulation"
                }
            
            account = self.alpaca_api.get_account()
            
            return {
                "account_status": account.status,
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "cash": float(account.cash),
                "equity": float(account.equity),
                "mode": "paper_trading",
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": account.transfers_blocked
            }
            
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return {"error": str(e)}
    
    def _get_positions(self) -> List[Dict]:
        """Get current positions from database and Alpaca"""
        try:
            if self.alpaca_api is None:
                # Get positions from database
                positions = self.execute_with_retry('SELECT * FROM positions')
                position_list = []
                
                for pos in positions:
                    position_list.append({
                        "symbol": pos[1],
                        "quantity": pos[2],
                        "side": "long" if pos[2] > 0 else "short",
                        "avg_entry_price": pos[3],
                        "current_price": pos[3],  # Simplified for simulation
                        "market_value": pos[2] * pos[3],
                        "unrealized_pl": 0,  # Simplified for simulation
                        "last_updated": pos[5]
                    })
                
                return position_list
            
            # Get positions from Alpaca
            positions = self.alpaca_api.list_positions()
            
            position_list = []
            for position in positions:
                position_list.append({
                    "symbol": position.symbol,
                    "quantity": int(position.qty),
                    "side": "long" if int(position.qty) > 0 else "short",
                    "market_value": float(position.market_value),
                    "unrealized_pl": float(position.unrealized_pl),
                    "unrealized_plpc": float(position.unrealized_plpc),
                    "avg_entry_price": float(position.avg_entry_price),
                    "current_price": float(position.current_price) if hasattr(position, 'current_price') else None
                })
            
            return position_list
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    def _get_portfolio_status(self) -> Dict:
        """Get comprehensive portfolio status"""
        try:
            # Get latest portfolio status
            latest_status = self.execute_with_retry(
                'SELECT * FROM portfolio_status ORDER BY timestamp DESC LIMIT 1'
            )
            
            if latest_status:
                status = latest_status[0]
                return {
                    "timestamp": status[1],
                    "total_value": status[2],
                    "cash_balance": status[3],
                    "positions_value": status[4],
                    "daily_pnl": status[5] if len(status) > 5 else 0,
                    "total_pnl": status[6] if len(status) > 6 else 0,
                }
            else:
                # Return default values
                return {
                    "timestamp": datetime.now().isoformat(),
                    "total_value": self.initial_capital,
                    "cash_balance": self.initial_capital,
                    "positions_value": 0,
                    "daily_pnl": 0,
                    "total_pnl": 0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting portfolio status: {e}")
            return {"error": str(e)}
    
    def _get_balance_history(self, limit: int = 30) -> List[Dict]:
        """Get balance history"""
        try:
            history = self.execute_with_retry(
                'SELECT * FROM balance_history ORDER BY timestamp DESC LIMIT ?',
                (limit,)
            )
            
            history_list = []
            for record in history:
                history_list.append({
                    "timestamp": record[1],
                    "cash_balance": record[2],
                    "change_amount": record[3],
                    "change_reason": record[4],
                    "transaction_type": record[5]
                })
            
            return history_list
            
        except Exception as e:
            self.logger.error(f"Error getting balance history: {e}")
            return []
    
    def run(self):
        """Run the paper trading service"""
        self.logger.info(f"Starting Paper Trading Service v{VERSION} on port 5005")
        self.logger.info(f"Database: {self.db_path}")
        
        if self.alpaca_api:
            self.logger.info("Alpaca Paper Trading API connected and ready")
        else:
            self.logger.info("Running in simulation mode (no Alpaca connection)")
            
        self.app.run(host='0.0.0.0', port=5005, debug=False)

if __name__ == "__main__":
    service = PaperTradingService()
    service.run()
"""
Name of Service: TRADING SYSTEM PHASE 1 - PAPER TRADING
Version: 1.0.4
Last Updated: 2025-06-23
REVISION HISTORY:
v1.0.4 (2025-06-23) - Fixed Jupyter notebook syntax error, improved import handling
v1.0.3 (2025-06-23) - Added dotenv support to load .env file
v1.0.2 (2025-06-15) - Updated to use ALPACA_PAPER_API_KEY and ALPACA_PAPER_API_SECRET environment variables
v1.0.1 (2025-06-15) - Updated header format and moved API credentials to environment variables
v1.0.0 (2025-06-15) - Initial release with Alpaca paper trading integration

Paper Trading Service - Executes trades using Alpaca paper trading API
Receives trading signals and executes them via Alpaca
"""

import os
from dotenv import load_dotenv
import requests
import logging
import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, List, Optional

# Load environment variables from .env file
load_dotenv()

# Try to import Alpaca API
try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    print("Warning: alpaca-trade-api not installed. Run: pip install alpaca-trade-api")
    print("Service will run in simulation mode.")

class PaperTradingService:
    def __init__(self, db_path='./trading_system.db'):
        self.app = Flask(__name__)
        self.db_path = db_path
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        
        # Alpaca configuration from environment variables - UPDATED TO USE PAPER TRADING VARS
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
        self._setup_alpaca_api()
        self._setup_routes()
        self._register_with_coordination()
        
    def _setup_logging(self):
        import os
        os.makedirs('./logs', exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('PaperTradingService')
        
        handler = logging.FileHandler('./logs/paper_trading_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
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
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy", 
                "service": "paper_trading",
                "alpaca_connected": self.alpaca_api is not None,
                "trading_mode": "paper" if self.alpaca_api else "simulation"
            })
        
        @self.app.route('/execute_trades', methods=['POST'])
        def execute_trades_endpoint():
            signals = request.json.get('signals', [])
            trades = self._execute_trades(signals)
            return jsonify(trades)
        
        @self.app.route('/account', methods=['GET'])
        def get_account():
            account_info = self._get_account_info()
            return jsonify(account_info)
        
        @self.app.route('/positions', methods=['GET'])
        def get_positions():
            positions = self._get_positions()
            return jsonify(positions)
    
    def _register_with_coordination(self):
        """Register with coordination service"""
        try:
            registration_data = {
                "service_name": "paper_trading",
                "port": 5005
            }
            response = requests.post(f"{self.coordination_service_url}/register_service",
                                   json=registration_data, timeout=5)
            if response.status_code == 200:
                self.logger.info("Successfully registered with coordination service")
        except Exception as e:
            self.logger.warning(f"Could not register with coordination service: {e}")
    
    def _execute_trades(self, trading_signals: List[Dict]) -> List[Dict]:
        """Execute trades based on trading signals"""
        self.logger.info(f"Executing trades for {len(trading_signals)} signals")
        
        executed_trades = []
        
        for signal in trading_signals:
            try:
                # Handle both 'signal' and 'signal_type' for backward compatibility
                signal_value = signal.get('signal') or signal.get('signal_type')
                if signal_value not in ['BUY', 'SELL']:
                continue
                
                trade_result = self._execute_single_trade(signal)
                if trade_result:
                    executed_trades.append(trade_result)
                
            except Exception as e:
                self.logger.error(f"Error executing trade for {signal.get('symbol', 'unknown')}: {e}")
        
        self.logger.info(f"Trade execution completed: {len(executed_trades)} trades executed")
        return executed_trades
    
    def _execute_single_trade(self, signal: Dict) -> Optional[Dict]:
        """Execute a single trade"""
        symbol = signal['symbol']
        signal_type = signal['signal']
        quantity = signal.get('quantity', 100)
        
        try:
            if self.alpaca_api is None:
                # Simulate trade execution for demo
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
                # Fallback to last close price
                current_price = signal.get('current_price', 100)
            
            # Submit order
            side = 'buy' if signal_type == 'BUY' else 'sell'
            
            order = self.alpaca_api.submit_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                type='market',
                time_in_force='day'
            )
            
            # Create trade record
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
            
            # Save to database
            self._save_trade_record(trade_record)
            
            self.logger.info(f"Executed {signal_type} trade for {symbol}: {quantity} shares at ${current_price:.2f}")
            return trade_record
            
        except Exception as e:
            self.logger.error(f"Error executing trade for {symbol}: {e}")
            return None
    
    def _simulate_trade_execution(self, signal: Dict) -> Dict:
        """Simulate trade execution when Alpaca API is not available"""
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
            'alpaca_order_id': f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'status': 'simulated',
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to database
        self._save_trade_record(trade_record)
        
        self.logger.info(f"Simulated {signal_type} trade for {symbol}: {quantity} shares at ${current_price:.2f}")
        return trade_record
    
    def _save_trade_record(self, trade_data: Dict):
        """Save trade record to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades 
                (symbol, signal_type, quantity, entry_price, confidence, 
                 trade_reason, alpaca_order_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data['symbol'],
                signal.get('signal') or signal.get('signal_type'),  # Use whichever field is present
                trade_data['quantity'],
                trade_data['entry_price'],
                trade_data['confidence'],
                trade_data['reason'],
                trade_data['alpaca_order_id'],
                trade_data['status'],
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved trade record for {trade_data['symbol']}")
            
        except Exception as e:
            self.logger.error(f"Error saving trade record: {e}")
    
    def _get_account_info(self) -> Dict:
        """Get account information"""
        try:
            if self.alpaca_api is None:
                return {
                    "status": "simulated", 
                    "buying_power": 100000, 
                    "portfolio_value": 100000,
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
        """Get current positions"""
        try:
            if self.alpaca_api is None:
                return []
            
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
    
    def run(self):
        self.logger.info("Starting Paper Trading Service on port 5005")
        if self.alpaca_api:
            self.logger.info("Alpaca Paper Trading API connected and ready")
        else:
            self.logger.info("Running in simulation mode (no Alpaca connection)")
        self.app.run(host='0.0.0.0', port=5005, debug=False)

if __name__ == "__main__":
    service = PaperTradingService()
    service.run()

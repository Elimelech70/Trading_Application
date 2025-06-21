# ================================================================
# 2. security_scanner.py (Port 5001) - FIXED VERSION
# ================================================================

"""
Name of Service: TRADING SYSTEM SECURITY SCANNER - FIXED VERSION
Version: 1.0.4
Last Updated: 2025-06-17
REVISION HISTORY:
v1.0.4 (2025-06-17) - Fixed websockets dependency issue with yfinance fallback
v1.0.3 (2025-06-17) - Added error handling for yfinance import issues
v1.0.2 (2025-06-15) - Enhanced integration with news service
v1.0.1 (2025-06-15) - Initial version
v1.0.0 (2025-06-15) - Original implementation

Security Scanner Service - Scans market for securities meeting criteria
Integrates with news service for sentiment analysis
Fixed to handle yfinance websockets dependency issues gracefully
"""

import requests
import logging
import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, List, Optional

# Handle yfinance import with fallback for websockets issues
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    print("✅ yfinance imported successfully")
except ImportError as e:
    print(f"⚠️ yfinance import failed: {e}")
    YFINANCE_AVAILABLE = False
except Exception as e:
    print(f"⚠️ yfinance import error: {e}")
    YFINANCE_AVAILABLE = False

class SecurityScannerService:
    def __init__(self, db_path='/content/trading_system.db'):
        self.app = Flask(__name__)
        self.db_path = db_path
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        self.news_service_url = "http://localhost:5008"
        
        # Trading criteria
        self.criteria = {
            "min_price": 2.0,
            "max_price": 20.0,
            "min_volume_ratio": 5.0,
            "min_price_change_pct": 10.0
        }
        
        self._setup_routes()
        self._register_with_coordination()
        
    def _setup_logging(self):
        import os
        os.makedirs('/content/logs', exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('SecurityScannerService')
        
        handler = logging.FileHandler('/content/logs/security_scanner.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy", 
                "service": "security_scanner",
                "yfinance_available": YFINANCE_AVAILABLE,
                "data_source": "yfinance" if YFINANCE_AVAILABLE else "simulated"
            })
        
        @self.app.route('/scan_securities', methods=['GET'])
        def scan_securities_endpoint():
            securities = self._scan_securities()
            return jsonify(securities)
        
        @self.app.route('/criteria', methods=['GET', 'POST'])
        def manage_criteria():
            if request.method == 'GET':
                return jsonify(self.criteria)
            else:
                self.criteria.update(request.json)
                self.logger.info(f"Updated criteria: {self.criteria}")
                return jsonify({"message": "Criteria updated"})
    
    def _register_with_coordination(self):
        """Register with coordination service"""
        try:
            registration_data = {
                "service_name": "security_scanner",
                "port": 5001
            }
            response = requests.post(f"{self.coordination_service_url}/register_service", 
                                   json=registration_data, timeout=5)
            if response.status_code == 200:
                self.logger.info("Successfully registered with coordination service")
        except Exception as e:
            self.logger.warning(f"Could not register with coordination service: {e}")
    
    def _scan_securities(self) -> List[Dict]:
        """Main security scanning logic"""
        self.logger.info("Starting securities scan")
        
        selected_securities = []
        watchlist = self._get_watchlist()
        
        for symbol in watchlist:
            try:
                if YFINANCE_AVAILABLE:
                    security_data = self._analyze_security_yfinance(symbol)
                else:
                    security_data = self._analyze_security_simulated(symbol)
                
                if security_data and self._meets_criteria(security_data):
                    # Get news sentiment
                    news_data = self._get_news_sentiment(symbol)
                    security_data.update(news_data)
                    
                    # Save to database
                    self._save_selected_security(security_data)
                    
                    selected_securities.append(security_data)
                    self.logger.info(f"Selected {symbol}: {security_data['selection_reason']}")
                
            except Exception as e:
                self.logger.error(f"Error analyzing {symbol}: {e}")
        
        self.logger.info(f"Scan completed: {len(selected_securities)} securities selected")
        return selected_securities
    
    def _get_watchlist(self) -> List[str]:
        """Get list of symbols to analyze"""
        return ['AAPL', 'TSLA', 'AMD', 'NVDA', 'MSFT', 'GOOGL', 'META', 'AMZN', 
                'SPY', 'QQQ', 'PLTR', 'GME', 'AMC', 'BB', 'NOK', 'SOXL', 'TQQQ']
    
    def _analyze_security_yfinance(self, symbol: str) -> Optional[Dict]:
        """Analyze individual security using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Use simpler method that doesn't require websockets
            try:
                hist = ticker.history(period="5d")
                info = ticker.info
            except Exception as e:
                self.logger.warning(f"yfinance error for {symbol}, using fallback: {e}")
                return self._analyze_security_simulated(symbol)
            
            if len(hist) < 2:
                return None
            
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].mean()
            
            price_change_pct = ((current_price - prev_price) / prev_price) * 100
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            return {
                'symbol': symbol,
                'price': float(current_price),
                'volume': int(current_volume),
                'volume_ratio': float(volume_ratio),
                'price_change_pct': float(price_change_pct),
                'market_cap': info.get('marketCap', 0),
                'selection_reason': f"Price change: {price_change_pct:.2f}%, Volume ratio: {volume_ratio:.2f}x",
                'data_source': 'yfinance'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol} with yfinance: {e}")
            return self._analyze_security_simulated(symbol)
    
    def _analyze_security_simulated(self, symbol: str) -> Optional[Dict]:
        """Analyze security using simulated data when yfinance is unavailable"""
        import random
        import time
        
        # Use symbol hash for consistent "random" data per symbol
        random.seed(hash(symbol) + int(time.time() / 86400))  # Changes daily
        
        # Generate realistic simulated data
        base_price = random.uniform(5, 500)
        price_change_pct = random.uniform(-20, 20)
        volume_ratio = random.uniform(0.5, 8.0)
        
        current_price = base_price * (1 + price_change_pct / 100)
        
        return {
            'symbol': symbol,
            'price': round(current_price, 2),
            'volume': random.randint(100000, 5000000),
            'volume_ratio': round(volume_ratio, 2),
            'price_change_pct': round(price_change_pct, 2),
            'market_cap': random.randint(1000000000, 100000000000),
            'selection_reason': f"Simulated: Price change: {price_change_pct:.2f}%, Volume ratio: {volume_ratio:.2f}x",
            'data_source': 'simulated'
        }
    
    def _meets_criteria(self, security: Dict) -> bool:
        """Check if security meets trading criteria"""
        criteria_met = (
            self.criteria["min_price"] <= security["price"] <= self.criteria["max_price"] and
            security["volume_ratio"] >= self.criteria["min_volume_ratio"] and
            abs(security["price_change_pct"]) >= self.criteria["min_price_change_pct"]
        )
        
        return criteria_met
    
    def _get_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment from news service"""
        try:
            response = requests.get(f"{self.news_service_url}/news_sentiment/{symbol}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Could not get news sentiment for {symbol}")
                return {"sentiment_score": 0.0, "sentiment_label": "neutral"}
        except Exception as e:
            self.logger.warning(f"Error getting news sentiment for {symbol}: {e}")
            return {"sentiment_score": 0.0, "sentiment_label": "neutral"}
    
    def _save_selected_security(self, security_data: Dict):
        """Save selected security to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO selected_securities 
                (symbol, selection_date, selection_criteria, market_cap, average_volume, 
                 sector, industry, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                security_data['symbol'],
                datetime.now().date().isoformat(),
                security_data['selection_reason'],
                security_data.get('market_cap', 0),
                security_data.get('volume', 0),
                'Technology',  # Default sector
                'Software',    # Default industry
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved selected security: {security_data['symbol']}")
            
        except Exception as e:
            self.logger.error(f"Error saving security {security_data['symbol']}: {e}")
    
    def run(self):
        mode = "with yfinance" if YFINANCE_AVAILABLE else "in simulation mode"
        self.logger.info(f"Starting Security Scanner Service on port 5001 {mode}")
        self.app.run(host='0.0.0.0', port=5001, debug=False)

if __name__ == "__main__":
    service = SecurityScannerService()
    service.run()
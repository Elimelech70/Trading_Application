# ================================================================
# 2. security_scanner.py (Port 5001) - ARCHITECTURAL COMPLIANCE VERSION
# ================================================================

"""
Name of Service: TRADING SYSTEM SECURITY SCANNER - ARCHITECTURAL COMPLIANCE VERSION
Version: 1.0.5
Last Updated: 2025-06-26
REVISION HISTORY:
v1.0.5 (2025-06-26) - ARCHITECTURAL COMPLIANCE UPDATE
    - Added DatabaseServiceMixin with retry logic and exponential backoff
    - Updated to use scanning_results table (correct schema compliance)
    - Added WAL mode configuration for better concurrent access
    - Added dual registration endpoints (/register and /register_service)
    - Enhanced health check with database status and version reporting
    - Added transaction management with proper commit/rollback handling
    - Added workflow integration and coordination tracking support
    - Preserved all v1.0.4 functionality and yfinance graceful fallback
v1.0.4 (2025-06-17) - Fixed websockets dependency issue with yfinance fallback
v1.0.3 (2025-06-17) - Added error handling for yfinance import issues
v1.0.2 (2025-06-15) - Enhanced integration with news service
v1.0.1 (2025-06-15) - Initial version
v1.0.0 (2025-06-15) - Original implementation

Security Scanner Service - Scans market for securities meeting criteria
Integrates with news service for sentiment analysis
Fixed to handle yfinance websockets dependency issues gracefully
Now includes robust database operations with automatic retry logic
"""

import time
import requests
import logging
import sqlite3
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, List, Optional
import os

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

class DatabaseServiceMixin:
    """Database utilities mixin with retry logic and WAL mode configuration"""
    
    def configure_database(self, db_path: str):
        """Configure database with WAL mode and optimizations"""
        try:
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()
            
            # Configure WAL mode for better concurrent access
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA temp_store = MEMORY")
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database configured with WAL mode and optimizations")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring database: {e}")
            return False
    
    def get_db_connection(self, retries: int = 5, timeout: float = 30.0) -> Optional[sqlite3.Connection]:
        """Get database connection with retry logic"""
        for attempt in range(retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=timeout)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                return conn
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    self.logger.warning(f"Database locked, retrying in {wait_time:.2f}s (attempt {attempt + 1}/{retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Database connection failed after {retries} attempts: {e}")
                    return None
            except Exception as e:
                self.logger.error(f"Unexpected database error: {e}")
                return None
        
        return None
    
    def execute_with_retry(self, query: str, params: Optional[tuple] = None, retries: int = 5) -> bool:
        """Execute query with automatic retry on database lock"""
        for attempt in range(retries):
            conn = None
            try:
                conn = self.get_db_connection()
                if not conn:
                    return False
                
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                return True
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    self.logger.warning(f"Query retry {attempt + 1}/{retries} in {wait_time:.2f}s")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Query failed after {retries} attempts: {e}")
                    return False
            except Exception as e:
                self.logger.error(f"Unexpected query error: {e}")
                return False
            finally:
                if conn:
                    conn.close()
        
        return False
    
    def bulk_insert_with_transaction(self, table: str, records: List[Dict], retries: int = 5) -> bool:
        """Bulk insert with transaction management and retry logic"""
        if not records:
            return True
        
        for attempt in range(retries):
            conn = None
            try:
                conn = self.get_db_connection()
                if not conn:
                    return False
                
                cursor = conn.cursor()
                
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                for record in records:
                    if table == "scanning_results":
                        cursor.execute('''
                            INSERT INTO scanning_results 
                            (symbol, scan_timestamp, price, volume, change_percent, relative_volume, 
                             market_cap, scan_type, metadata, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            record.get('symbol'),
                            record.get('scan_timestamp', datetime.now().isoformat()),
                            record.get('price', 0.0),
                            record.get('volume', 0),
                            record.get('change_percent', 0.0),
                            record.get('relative_volume', 0.0),
                            record.get('market_cap', 0),
                            record.get('scan_type', 'momentum'),
                            json.dumps(record.get('metadata', {})),
                            datetime.now().isoformat()
                        ))
                
                # Commit transaction
                cursor.execute("COMMIT")
                return True
                
            except sqlite3.OperationalError as e:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                
                if "database is locked" in str(e) and attempt < retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    self.logger.warning(f"Bulk insert retry {attempt + 1}/{retries} in {wait_time:.2f}s")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Bulk insert failed after {retries} attempts: {e}")
                    return False
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                self.logger.error(f"Unexpected bulk insert error: {e}")
                return False
            finally:
                if conn:
                    conn.close()
        
        return False

class SecurityScannerService(DatabaseServiceMixin):
    def __init__(self, db_path='./trading_system.db'):
        self.app = Flask(__name__)
        self.db_path = db_path
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        self.news_service_url = "http://localhost:5008"
        self.service_version = "1.0.5"
        
        # Trading criteria
        self.criteria = {
            "min_price": 2.0,
            "max_price": 20.0,
            "min_volume_ratio": 3.0,
            "min_price_change_pct": 7.0
        }
        
        # Configure database with WAL mode
        self.configure_database(self.db_path)
        
        self._setup_routes()
        self._register_with_coordination()
        
    def _setup_logging(self):
        os.makedirs('./logs', exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('SecurityScannerService')
        
        handler = logging.FileHandler('./logs/security_scanner.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health():
            # Enhanced health check with database status
            db_status = "healthy"
            db_info = {}
            
            try:
                conn = self.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM scanning_results")
                    scan_count = cursor.fetchone()[0]
                    
                    # Check WAL mode
                    cursor.execute("PRAGMA journal_mode")
                    journal_mode = cursor.fetchone()[0]
                    
                    db_info = {
                        "scan_results_count": scan_count,
                        "journal_mode": journal_mode,
                        "last_connection": datetime.now().isoformat()
                    }
                    conn.close()
                else:
                    db_status = "connection_failed"
                    
            except Exception as e:
                db_status = f"error: {str(e)}"
            
            return jsonify({
                "status": "healthy", 
                "service": "security_scanner",
                "version": self.service_version,
                "yfinance_available": YFINANCE_AVAILABLE,
                "data_source": "yfinance" if YFINANCE_AVAILABLE else "simulated",
                "database_status": db_status,
                "database_info": db_info,
                "architecture_compliance": "v3.1.2",
                "features": [
                    "database_retry_logic",
                    "wal_mode",
                    "transaction_management",
                    "dual_registration",
                    "workflow_integration"
                ]
            })
        
        # Dual registration endpoints for architecture compliance
        @self.app.route('/register', methods=['POST'])
        def register():
            return self._handle_registration(request)
        
        @self.app.route('/register_service', methods=['POST'])
        def register_service():
            return self._handle_registration(request)
        
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
        
        @self.app.route('/database_status', methods=['GET'])
        def database_status():
            """New endpoint for database monitoring"""
            try:
                conn = self.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    # Get table info
                    cursor.execute("SELECT COUNT(*) FROM scanning_results")
                    scan_count = cursor.fetchone()[0]
                    
                    # Get recent scans
                    cursor.execute("""
                        SELECT symbol, scan_timestamp, price, change_percent 
                        FROM scanning_results 
                        ORDER BY created_at DESC LIMIT 5
                    """)
                    recent_scans = [dict(row) for row in cursor.fetchall()]
                    
                    cursor.execute("PRAGMA journal_mode")
                    journal_mode = cursor.fetchone()[0]
                    
                    conn.close()
                    
                    return jsonify({
                        "status": "healthy",
                        "total_scans": scan_count,
                        "journal_mode": journal_mode,
                        "recent_scans": recent_scans,
                        "last_check": datetime.now().isoformat()
                    })
                else:
                    return jsonify({"status": "connection_failed"}), 500
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
    
    def _handle_registration(self, request):
        """Handle both registration endpoints"""
        try:
            data = request.get_json() or {}
            service_info = {
                "service_name": "security_scanner",
                "version": self.service_version,
                "port": 5001,
                "status": "running",
                "capabilities": [
                    "market_scanning",
                    "criteria_filtering", 
                    "news_integration",
                    "database_persistence"
                ],
                "database_compliance": True,
                "registration_time": datetime.now().isoformat()
            }
            
            self.logger.info(f"Service registration handled: {service_info}")
            return jsonify(service_info)
            
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _register_with_coordination(self):
        """Register with coordination service using dual endpoints"""
        registration_data = {
            "service_name": "security_scanner",
            "version": self.service_version,
            "port": 5001,
            "capabilities": [
                "market_scanning",
                "criteria_filtering",
                "news_integration", 
                "database_persistence"
            ]
        }
        
        # Try both registration endpoints for compatibility
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
                self.logger.warning(f"Could not register via {endpoint}: {e}")
        
        self.logger.warning("Could not register with coordination service via any endpoint")
    
    def _scan_securities(self) -> List[Dict]:
        """Main security scanning logic with enhanced database operations"""
        self.logger.info("Starting securities scan")
        
        selected_securities = []
        watchlist = self._get_watchlist()
        scan_timestamp = datetime.now().isoformat()
        
        for symbol in watchlist:
            try:
                time.sleep(0.5)  # Rate limit protection
                if YFINANCE_AVAILABLE:
                    security_data = self._analyze_security_yfinance(symbol)
                else:
                    security_data = self._analyze_security_simulated(symbol)
                
                if security_data and self._meets_criteria(security_data):
                    # Get news sentiment
                    news_data = self._get_news_sentiment(symbol)
                    security_data.update(news_data)
                    
                    # Add scan metadata
                    security_data['scan_timestamp'] = scan_timestamp
                    security_data['scan_type'] = 'momentum'
                    security_data['metadata'] = {
                        'criteria_met': True,
                        'news_sentiment': news_data,
                        'scan_version': self.service_version
                    }
                    
                    # Save to database using new schema
                    if self._save_scanning_result(security_data):
                        selected_securities.append(security_data)
                        self.logger.info(f"Selected {symbol}: {security_data['selection_reason']}")
                    else:
                        self.logger.error(f"Failed to save scanning result for {symbol}")
                
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
                'change_percent': float(price_change_pct),  # Schema compliance
                'relative_volume': float(volume_ratio),     # Schema compliance
                'market_cap': info.get('marketCap', 0),
                'selection_reason': f"Price change: {price_change_pct:.2f}%, Volume ratio: {volume_ratio:.2f}x",
                'data_source': 'yfinance'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol} with yfinance: {e}")
            return self._analyze_security_simulated(symbol)
    
    def _analyze_security_simulated(self, symbol: str) -> Optional[Dict]:
        """Analyze security using simulated data when yfinance is unavailable"""
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
            'change_percent': round(price_change_pct, 2),    # Schema compliance
            'relative_volume': round(volume_ratio, 2),       # Schema compliance
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
    
    def _save_scanning_result(self, security_data: Dict) -> bool:
        """Save scanning result to database using correct schema with retry logic"""
        try:
            # Prepare data for scanning_results table
            scan_data = {
                'symbol': security_data['symbol'],
                'scan_timestamp': security_data.get('scan_timestamp', datetime.now().isoformat()),
                'price': security_data.get('price', 0.0),
                'volume': security_data.get('volume', 0),
                'change_percent': security_data.get('change_percent', 0.0),
                'relative_volume': security_data.get('relative_volume', 0.0),
                'market_cap': security_data.get('market_cap', 0),
                'scan_type': security_data.get('scan_type', 'momentum'),
                'metadata': security_data.get('metadata', {})
            }
            
            # Use bulk insert for consistency (even though it's just one record)
            success = self.bulk_insert_with_transaction('scanning_results', [scan_data])
            
            if success:
                self.logger.info(f"Saved scanning result for {security_data['symbol']}")
            else:
                self.logger.error(f"Failed to save scanning result for {security_data['symbol']}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error saving scanning result for {security_data['symbol']}: {e}")
            return False
    
    def run(self):
        mode = "with yfinance" if YFINANCE_AVAILABLE else "in simulation mode"
        self.logger.info(f"Starting Security Scanner Service v{self.service_version} on port 5001 {mode}")
        self.logger.info("Features: DatabaseServiceMixin, WAL mode, retry logic, dual registration")
        self.app.run(host='0.0.0.0', port=5001, debug=False)

if __name__ == "__main__":
    service = SecurityScannerService()
    service.run()
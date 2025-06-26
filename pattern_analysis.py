# ================================================================
# 3. pattern_analysis.py (Port 5002) - COMPLETE ARCHITECTURAL COMPLIANCE VERSION
# ================================================================
"""
Name of Service: TRADING SYSTEM PATTERN ANALYSIS - COMPLETE ARCHITECTURAL COMPLIANCE VERSION
Version: 1.0.6
Last Updated: 2025-06-26
REVISION HISTORY:
v1.0.6 (2025-06-26) - COMPLETE ARCHITECTURAL COMPLIANCE UPDATE
    - Added DatabaseServiceMixin with retry logic and exponential backoff
    - Enhanced pattern storage with proper pattern_analysis table schema compliance
    - Added WAL mode configuration for better concurrent access
    - Added dual registration endpoints (/register and /register_service)
    - Enhanced health check with database status, pattern statistics, and version reporting
    - Added transaction management with proper commit/rollback handling
    - Added workflow integration and coordination tracking support
    - Enhanced pattern metadata storage with individual pattern records
    - Added comprehensive monitoring endpoints for pattern analysis tracking
    - Preserved all v1.0.5 functionality including JSON serialization fixes and manual pattern detection
v1.0.5 (2025-06-17) - CRITICAL FIX: JSON serialization error with boolean values
v1.0.4 (2025-06-17) - Fixed websockets dependency issue with yfinance graceful import
v1.0.3 (2025-06-15) - Removed TA-Lib dependency, using only manual pattern detection
v1.0.2 (2025-06-15) - Fixed version with TA-Lib fallback
v1.0.1 (2025-06-15) - Initial version
v1.0.0 (2025-06-15) - Original implementation

Pattern Analysis Service - Analyzes technical patterns using manual calculation methods
CRITICAL BUG FIX: Fixed JSON serialization error when saving patterns with boolean values
Now includes robust database operations with automatic retry logic and proper schema compliance
"""

import numpy as np
import pandas as pd
import requests
import logging
import sqlite3
import json
import random
import time
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
    
    def bulk_insert_patterns(self, pattern_data: List[Dict], retries: int = 5) -> bool:
        """Bulk insert patterns with transaction management"""
        if not pattern_data:
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
                
                for pattern in pattern_data:
                    cursor.execute('''
                        INSERT INTO pattern_analysis 
                        (symbol, pattern_type, pattern_name, confidence, entry_price, stop_loss, 
                         target_price, timeframe, detection_timestamp, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pattern.get('symbol'),
                        pattern.get('pattern_type', 'candlestick'),
                        pattern.get('pattern_name'),
                        pattern.get('confidence', 0.0),
                        pattern.get('entry_price', 0.0),
                        pattern.get('stop_loss', 0.0),
                        pattern.get('target_price', 0.0),
                        pattern.get('timeframe', '1d'),
                        pattern.get('detection_timestamp', datetime.now().isoformat()),
                        json.dumps(pattern.get('metadata', {})),
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
                    self.logger.warning(f"Bulk pattern insert retry {attempt + 1}/{retries} in {wait_time:.2f}s")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Bulk pattern insert failed after {retries} attempts: {e}")
                    return False
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                self.logger.error(f"Unexpected bulk pattern insert error: {e}")
                return False
            finally:
                if conn:
                    conn.close()
        
        return False

class PatternAnalysisService(DatabaseServiceMixin):
    def __init__(self, db_path='./trading_system.db'):
        self.app = Flask(__name__)
        self.db_path = db_path
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        self.pattern_recognition_url = "http://localhost:5006"
        self.service_version = "1.0.6"
        
        # Configure database with WAL mode
        self.configure_database(self.db_path)
        
        self._setup_routes()
        self._register_with_coordination()
        
    def _setup_logging(self):
        os.makedirs('./logs', exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('PatternAnalysisService')
        
        handler = logging.FileHandler('./logs/pattern_analysis_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health():
            # Enhanced health check with database and pattern statistics
            db_status = "healthy"
            db_info = {}
            pattern_stats = {}
            
            try:
                conn = self.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    # Get pattern counts
                    cursor.execute("SELECT COUNT(*) FROM pattern_analysis")
                    total_patterns = cursor.fetchone()[0]
                    
                    # Get pattern type distribution
                    cursor.execute("""
                        SELECT pattern_type, COUNT(*) as count 
                        FROM pattern_analysis 
                        GROUP BY pattern_type 
                        ORDER BY count DESC LIMIT 10
                    """)
                    pattern_types = [dict(row) for row in cursor.fetchall()]
                    
                    # Get recent patterns
                    cursor.execute("""
                        SELECT symbol, pattern_name, confidence, detection_timestamp
                        FROM pattern_analysis 
                        ORDER BY created_at DESC LIMIT 5
                    """)
                    recent_patterns = [dict(row) for row in cursor.fetchall()]
                    
                    # Check WAL mode
                    cursor.execute("PRAGMA journal_mode")
                    journal_mode = cursor.fetchone()[0]
                    
                    db_info = {
                        "total_patterns": total_patterns,
                        "journal_mode": journal_mode,
                        "last_connection": datetime.now().isoformat()
                    }
                    
                    pattern_stats = {
                        "pattern_types": pattern_types,
                        "recent_patterns": recent_patterns,
                        "pattern_count": total_patterns
                    }
                    
                    conn.close()
                else:
                    db_status = "connection_failed"
                    
            except Exception as e:
                db_status = f"error: {str(e)}"
            
            return jsonify({
                "status": "healthy", 
                "service": "pattern_analysis",
                "version": self.service_version,
                "implementation": "manual_algorithms",
                "yfinance_available": YFINANCE_AVAILABLE,
                "data_source": "yfinance" if YFINANCE_AVAILABLE else "simulated",
                "database_status": db_status,
                "database_info": db_info,
                "pattern_stats": pattern_stats,
                "architecture_compliance": "v3.1.2",
                "features": [
                    "database_retry_logic",
                    "wal_mode",
                    "transaction_management", 
                    "dual_registration",
                    "pattern_recognition_integration",
                    "json_serialization_fix"
                ]
            })
        
        # Dual registration endpoints for architecture compliance
        @self.app.route('/register', methods=['POST'])
        def register():
            return self._handle_registration(request)
        
        @self.app.route('/register_service', methods=['POST'])
        def register_service():
            return self._handle_registration(request)
        
        @self.app.route('/analyze_patterns/<symbol>', methods=['GET'])
        def analyze_patterns_endpoint(symbol):
            analysis = self._analyze_patterns(symbol)
            return jsonify(analysis)
        
        @self.app.route('/supported_patterns', methods=['GET'])
        def get_supported_patterns():
            return jsonify(self._get_supported_patterns())
        
        @self.app.route('/patterns/<symbol>', methods=['GET'])
        def get_patterns_for_symbol(symbol):
            """New endpoint to get all patterns for a symbol"""
            try:
                conn = self.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT pattern_type, pattern_name, confidence, entry_price, stop_loss, 
                               target_price, detection_timestamp, metadata
                        FROM pattern_analysis 
                        WHERE symbol = ?
                        ORDER BY detection_timestamp DESC LIMIT 50
                    """, (symbol.upper(),))
                    
                    patterns = []
                    for row in cursor.fetchall():
                        pattern_data = dict(row)
                        try:
                            pattern_data['metadata'] = json.loads(pattern_data['metadata'])
                        except:
                            pattern_data['metadata'] = {}
                        patterns.append(pattern_data)
                    
                    conn.close()
                    return jsonify({
                        "symbol": symbol,
                        "patterns": patterns,
                        "count": len(patterns)
                    })
                else:
                    return jsonify({"error": "Database connection failed"}), 500
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/pattern_statistics', methods=['GET'])
        def get_pattern_statistics():
            """New endpoint for comprehensive pattern statistics"""
            try:
                conn = self.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    # Overall statistics
                    cursor.execute("SELECT COUNT(*) FROM pattern_analysis")
                    total_patterns = cursor.fetchone()[0]
                    
                    # Pattern type breakdown
                    cursor.execute("""
                        SELECT pattern_type, pattern_name, COUNT(*) as count, AVG(confidence) as avg_confidence
                        FROM pattern_analysis 
                        GROUP BY pattern_type, pattern_name 
                        ORDER BY count DESC
                    """)
                    pattern_breakdown = [dict(row) for row in cursor.fetchall()]
                    
                    # Symbol performance
                    cursor.execute("""
                        SELECT symbol, COUNT(*) as pattern_count, AVG(confidence) as avg_confidence
                        FROM pattern_analysis 
                        GROUP BY symbol 
                        ORDER BY pattern_count DESC LIMIT 15
                    """)
                    symbol_stats = [dict(row) for row in cursor.fetchall()]
                    
                    # Recent activity (last 7 days)
                    cursor.execute("""
                        SELECT DATE(detection_timestamp) as date, COUNT(*) as patterns_detected
                        FROM pattern_analysis 
                        WHERE detection_timestamp >= datetime('now', '-7 days')
                        GROUP BY DATE(detection_timestamp)
                        ORDER BY date DESC
                    """)
                    daily_activity = [dict(row) for row in cursor.fetchall()]
                    
                    conn.close()
                    
                    return jsonify({
                        "total_patterns": total_patterns,
                        "pattern_breakdown": pattern_breakdown,
                        "top_symbols": symbol_stats,
                        "daily_activity": daily_activity,
                        "last_updated": datetime.now().isoformat()
                    })
                else:
                    return jsonify({"error": "Database connection failed"}), 500
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/database_status', methods=['GET'])
        def database_status():
            """New endpoint for database monitoring"""
            try:
                conn = self.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    
                    # Get comprehensive stats
                    cursor.execute("SELECT COUNT(*) FROM pattern_analysis")
                    total_patterns = cursor.fetchone()[0]
                    
                    cursor.execute("PRAGMA journal_mode")
                    journal_mode = cursor.fetchone()[0]
                    
                    # Get latest patterns
                    cursor.execute("""
                        SELECT symbol, pattern_name, confidence, detection_timestamp
                        FROM pattern_analysis 
                        ORDER BY created_at DESC LIMIT 10
                    """)
                    latest_patterns = [dict(row) for row in cursor.fetchall()]
                    
                    conn.close()
                    
                    return jsonify({
                        "status": "healthy",
                        "total_patterns": total_patterns,
                        "journal_mode": journal_mode,
                        "latest_patterns": latest_patterns,
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
                "service_name": "pattern_analysis",
                "version": self.service_version,
                "port": 5002,
                "status": "running",
                "capabilities": [
                    "pattern_detection",
                    "candlestick_analysis",
                    "trend_analysis",
                    "support_resistance_detection",
                    "pattern_recognition_integration",
                    "database_persistence"
                ],
                "supported_patterns": self._get_supported_patterns(),
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
            "service_name": "pattern_analysis",
            "version": self.service_version,
            "port": 5002,
            "capabilities": [
                "pattern_detection",
                "candlestick_analysis", 
                "trend_analysis",
                "support_resistance_detection",
                "pattern_recognition_integration",
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
    
    def _analyze_patterns(self, symbol: str) -> Dict:
        """Main pattern analysis logic with enhanced database operations"""
        self.logger.info(f"Starting pattern analysis for {symbol}")
        
        try:
            # Get market data
            hist_data = self._get_historical_data(symbol)
            if hist_data is None:
                return {'symbol': symbol, 'patterns': [], 'error': 'No data available'}
            
            # Manual pattern analysis
            basic_patterns = self._detect_basic_patterns(symbol, hist_data)
            
            # Get enhanced patterns from pattern recognition service
            enhanced_patterns = self._get_enhanced_patterns(symbol)
            
            # Combine results
            all_patterns = basic_patterns + enhanced_patterns.get('candlestick_patterns', [])
            
            # Calculate overall confidence
            confidence_score = self._calculate_confidence(all_patterns)
            
            combined_analysis = {
                'symbol': symbol,
                'basic_patterns': basic_patterns,
                'enhanced_patterns': enhanced_patterns,
                'patterns': all_patterns,
                'confidence_score': confidence_score,
                'pattern_count': len(all_patterns),
                'analysis_timestamp': datetime.now().isoformat(),
                'implementation': 'manual_algorithms',
                'data_source': 'yfinance' if YFINANCE_AVAILABLE else 'simulated'
            }
            
            # Save patterns to database using new schema-compliant method
            if all_patterns:
                pattern_records = self._prepare_patterns_for_storage(symbol, all_patterns)
                success = self.bulk_insert_patterns(pattern_records)
                if success:
                    self.logger.info(f"Successfully saved {len(pattern_records)} patterns for {symbol}")
                else:
                    self.logger.error(f"Failed to save patterns for {symbol}")
            
            self.logger.info(f"Pattern analysis completed for {symbol}: {len(all_patterns)} patterns found")
            return combined_analysis
            
        except Exception as e:
            self.logger.error(f"Error in pattern analysis for {symbol}: {e}")
            return {'symbol': symbol, 'patterns': [], 'error': str(e)}
    
    def _get_historical_data(self, symbol: str, period: str = "30d") -> Optional[pd.DataFrame]:
        """Get historical data for pattern analysis"""
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                
                if len(hist) < 20:
                    return self._generate_simulated_data(symbol)
                
                return hist
                
            except Exception as e:
                self.logger.warning(f"yfinance error for {symbol}, using simulated data: {e}")
                return self._generate_simulated_data(symbol)
        else:
            return self._generate_simulated_data(symbol)
    
    def _generate_simulated_data(self, symbol: str) -> pd.DataFrame:
        """Generate simulated OHLCV data for pattern analysis"""
        # Use symbol hash for consistent "random" data
        random.seed(hash(symbol) + int(time.time() / 86400))
        
        # Generate 30 days of simulated data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        # Start with a base price
        base_price = random.uniform(10, 200)
        prices = []
        volumes = []
        
        current_price = base_price
        for i in range(30):
            # Random daily change
            change_pct = random.uniform(-0.05, 0.05)  # -5% to +5%
            current_price *= (1 + change_pct)
            
            # Generate OHLC
            open_price = current_price * random.uniform(0.98, 1.02)
            close_price = current_price
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.05)
            low_price = min(open_price, close_price) * random.uniform(0.95, 1.0)
            volume = random.randint(100000, 1000000)
            
            prices.append([open_price, high_price, low_price, close_price])
            volumes.append(volume)
        
        # Create DataFrame
        data = pd.DataFrame(prices, columns=['Open', 'High', 'Low', 'Close'], index=dates)
        data['Volume'] = volumes
        
        return data
    
    def _detect_basic_patterns(self, symbol: str, data: pd.DataFrame) -> List[Dict]:
        """Detect basic candlestick patterns using manual calculations"""
        patterns = []
        
        try:
            close_prices = data['Close'].values
            open_prices = data['Open'].values
            high_prices = data['High'].values
            low_prices = data['Low'].values
            
            # Check last 5 days for patterns
            for i in range(-5, 0):
                if abs(i) > len(close_prices):
                    continue
                    
                current_open = open_prices[i]
                current_close = close_prices[i]
                current_high = high_prices[i]
                current_low = low_prices[i]
                
                # Calculate body and shadows
                body = abs(current_close - current_open)
                lower_shadow = min(current_open, current_close) - current_low
                upper_shadow = current_high - max(current_open, current_close)
                total_range = current_high - current_low
                
                # Avoid division by zero
                if total_range == 0:
                    continue
                
                # Doji pattern (open ≈ close) - FIXED: Convert booleans properly
                if body < (total_range * 0.1):
                    patterns.append({
                        'pattern_type': 'doji',
                        'signal_strength': 100,
                        'confidence_score': 0.7,
                        'bullish': None,  # Will be handled in JSON serialization
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_calculation',
                        'description': 'Small body indicates indecision'
                    })
                
                # Hammer pattern (small body at top, long lower shadow)
                if lower_shadow > body * 2 and upper_shadow < body * 0.5 and body > 0:
                    patterns.append({
                        'pattern_type': 'hammer',
                        'signal_strength': 100,
                        'confidence_score': 0.6,
                        'bullish': True,  # Will be handled in JSON serialization
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_calculation',
                        'description': 'Long lower shadow suggests buying pressure'
                    })
                
                # Shooting star (small body at bottom, long upper shadow)
                if upper_shadow > body * 2 and lower_shadow < body * 0.5 and body > 0:
                    patterns.append({
                        'pattern_type': 'shooting_star',
                        'signal_strength': -100,
                        'confidence_score': 0.6,
                        'bullish': False,  # Will be handled in JSON serialization
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_calculation',
                        'description': 'Long upper shadow suggests selling pressure'
                    })
                
                # Engulfing patterns (requires previous candle)
                if i > -len(close_prices) and abs(i) > 1:
                    prev_open = open_prices[i-1]
                    prev_close = close_prices[i-1]
                    prev_body = abs(prev_close - prev_open)
                    
                    # Bullish engulfing
                    if (current_close > current_open and  # Current candle is bullish
                        prev_close < prev_open and        # Previous candle is bearish
                        current_open < prev_close and     # Current opens below previous close
                        current_close > prev_open and     # Current closes above previous open
                        body > prev_body * 1.1):          # Current body is larger
                        
                        patterns.append({
                            'pattern_type': 'bullish_engulfing',
                            'signal_strength': 100,
                            'confidence_score': 0.8,
                            'bullish': True,  # Will be handled in JSON serialization
                            'detected_at': datetime.now().isoformat(),
                            'source': 'manual_calculation',
                            'description': 'Bullish candle engulfs previous bearish candle'
                        })
                    
                    # Bearish engulfing
                    elif (current_close < current_open and  # Current candle is bearish
                          prev_close > prev_open and        # Previous candle is bullish
                          current_open > prev_close and     # Current opens above previous close
                          current_close < prev_open and     # Current closes below previous open
                          body > prev_body * 1.1):          # Current body is larger
                        
                        patterns.append({
                            'pattern_type': 'bearish_engulfing',
                            'signal_strength': -100,
                            'confidence_score': 0.8,
                            'bullish': False,  # Will be handled in JSON serialization
                            'detected_at': datetime.now().isoformat(),
                            'source': 'manual_calculation',
                            'description': 'Bearish candle engulfs previous bullish candle'
                        })
            
            # Trend detection using linear regression
            if len(close_prices) >= 10:
                recent_trend = np.polyfit(range(10), close_prices[-10:], 1)[0]
                price_std = np.std(close_prices[-20:]) if len(close_prices) >= 20 else np.std(close_prices)
                
                if abs(recent_trend) > price_std * 0.01:  # Significant trend
                    patterns.append({
                        'pattern_type': 'trend_detected',
                        'signal_strength': 100 if recent_trend > 0 else -100,
                        'confidence_score': min(abs(recent_trend) * 100, 0.9),
                        'bullish': True if recent_trend > 0 else False,  # Will be handled in JSON serialization
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_calculation',
                        'description': f"{'Upward' if recent_trend > 0 else 'Downward'} trend detected"
                    })
            
            # Support and resistance levels
            if len(close_prices) >= 20:
                recent_high = np.max(high_prices[-20:])
                recent_low = np.min(low_prices[-20:])
                current_price = close_prices[-1]
                
                # Near resistance
                if current_price >= recent_high * 0.98:
                    patterns.append({
                        'pattern_type': 'near_resistance',
                        'signal_strength': -50,
                        'confidence_score': 0.7,
                        'bullish': False,  # Will be handled in JSON serialization
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_calculation',
                        'description': f'Price near resistance level: ${recent_high:.2f}'
                    })
                
                # Near support
                if current_price <= recent_low * 1.02:
                    patterns.append({
                        'pattern_type': 'near_support',
                        'signal_strength': 50,
                        'confidence_score': 0.7,
                        'bullish': True,  # Will be handled in JSON serialization
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_calculation',
                        'description': f'Price near support level: ${recent_low:.2f}'
                    })
            
        except Exception as e:
            self.logger.error(f"Error in manual pattern detection: {e}")
        
        return patterns
    
    def _get_enhanced_patterns(self, symbol: str) -> Dict:
        """Get enhanced patterns from pattern recognition service"""
        try:
            response = requests.get(f"{self.pattern_recognition_url}/detect_advanced_patterns/{symbol}", 
                                  timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Could not get enhanced patterns for {symbol}")
                return {}
        except Exception as e:
            self.logger.warning(f"Error getting enhanced patterns for {symbol}: {e}")
            return {}
    
    def _calculate_confidence(self, patterns: List[Dict]) -> float:
        """Calculate overall pattern confidence"""
        if not patterns:
            return 0.0
        
        total_confidence = sum([p.get('confidence_score', 0) for p in patterns])
        return min(total_confidence / len(patterns), 1.0)
    
    def _prepare_patterns_for_storage(self, symbol: str, patterns: List[Dict]) -> List[Dict]:
        """Prepare patterns for database storage with proper schema compliance"""
        pattern_records = []
        timestamp = datetime.now().isoformat()
        
        for pattern in patterns:
            # Make pattern data JSON-serializable
            clean_pattern = self._make_json_serializable(pattern)
            
            # Extract pattern data
            pattern_name = clean_pattern.get('pattern_type', 'unknown')
            confidence = clean_pattern.get('confidence_score', 0.0)
            
            # Calculate entry/exit prices based on pattern
            current_price = 100.0  # Default fallback
            try:
                # Try to get actual current price if available
                if hasattr(self, '_last_analyzed_price'):
                    current_price = self._last_analyzed_price
            except:
                pass
            
            entry_price = current_price
            stop_loss = current_price * 0.95 if clean_pattern.get('bullish') != 'false' else current_price * 1.05
            target_price = current_price * 1.05 if clean_pattern.get('bullish') != 'false' else current_price * 0.95
            
            pattern_record = {
                'symbol': symbol,
                'pattern_type': 'candlestick',
                'pattern_name': pattern_name,
                'confidence': float(confidence),
                'entry_price': float(entry_price),
                'stop_loss': float(stop_loss),
                'target_price': float(target_price),
                'timeframe': '1d',
                'detection_timestamp': timestamp,
                'metadata': {
                    'signal_strength': clean_pattern.get('signal_strength', 0),
                    'bullish': clean_pattern.get('bullish', 'neutral'),
                    'source': clean_pattern.get('source', 'manual_calculation'),
                    'description': clean_pattern.get('description', ''),
                    'service_version': self.service_version,
                    'original_pattern': clean_pattern
                }
            }
            
            pattern_records.append(pattern_record)
        
        return pattern_records
    
    def _make_json_serializable(self, obj):
        """CRITICAL FIX: Convert object to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, bool):
            return str(obj).lower()  # Convert True/False to "true"/"false"
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)  # Convert numpy types to standard Python types
        elif obj is None:
            return "null"  # Convert None to string
        else:
            return obj  # Return as-is for strings, numbers, etc.
    
    def _get_supported_patterns(self) -> List[str]:
        """Get list of supported pattern types"""
        return [
            'doji', 'hammer', 'shooting_star', 
            'bullish_engulfing', 'bearish_engulfing',
            'trend_detected', 'near_resistance', 'near_support',
            'advanced_chart_patterns', 'advanced_volume_patterns'
        ]
    
    def run(self):
        mode = "with yfinance" if YFINANCE_AVAILABLE else "in simulation mode"
        self.logger.info(f"Starting Pattern Analysis Service v{self.service_version} on port 5002 {mode}")
        self.logger.info("Features: DatabaseServiceMixin, WAL mode, retry logic, dual registration, JSON serialization fixes")
        self.app.run(host='0.0.0.0', port=5002, debug=False)

if __name__ == "__main__":
    service = PatternAnalysisService()
    service.run()
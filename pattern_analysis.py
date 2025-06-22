# ================================================================
# 3. pattern_analysis.py (Port 5002) - FIXED VERSION
# ================================================================
"""
Name of Service: TRADING SYSTEM PATTERN ANALYSIS - FIXED VERSION
Version: 1.0.5
Last Updated: 2025-06-17
REVISION HISTORY:
v1.0.5 (2025-06-17) - CRITICAL FIX: JSON serialization error with boolean values
v1.0.4 (2025-06-17) - Fixed websockets dependency issue with yfinance graceful import
v1.0.3 (2025-06-15) - Removed TA-Lib dependency, using only manual pattern detection
v1.0.2 (2025-06-15) - Fixed version with TA-Lib fallback
v1.0.1 (2025-06-15) - Initial version
v1.0.0 (2025-06-15) - Original implementation

Pattern Analysis Service - Analyzes technical patterns using manual calculation methods
CRITICAL BUG FIX: Fixed JSON serialization error when saving patterns with boolean values
"""

import numpy as np
import pandas as pd
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

class PatternAnalysisService:
    def __init__(self, db_path='./trading_system.db'):
        self.app = Flask(__name__)
        self.db_path = db_path
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        self.pattern_recognition_url = "http://localhost:5006"
        
        self._setup_routes()
        self._register_with_coordination()
        
    def _setup_logging(self):
        import os
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
            return jsonify({
                "status": "healthy", 
                "service": "pattern_analysis", 
                "implementation": "manual_algorithms",
                "yfinance_available": YFINANCE_AVAILABLE,
                "data_source": "yfinance" if YFINANCE_AVAILABLE else "simulated"
            })
        
        @self.app.route('/analyze_patterns/<symbol>', methods=['GET'])
        def analyze_patterns_endpoint(symbol):
            analysis = self._analyze_patterns(symbol)
            return jsonify(analysis)
        
        @self.app.route('/supported_patterns', methods=['GET'])
        def get_supported_patterns():
            return jsonify(self._get_supported_patterns())
    
    def _register_with_coordination(self):
        """Register with coordination service"""
        try:
            registration_data = {
                "service_name": "pattern_analysis", 
                "port": 5002
            }
            response = requests.post(f"{self.coordination_service_url}/register_service",
                                   json=registration_data, timeout=5)
            if response.status_code == 200:
                self.logger.info("Successfully registered with coordination service")
        except Exception as e:
            self.logger.warning(f"Could not register with coordination service: {e}")
    
    def _analyze_patterns(self, symbol: str) -> Dict:
        """Main pattern analysis logic"""
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
            
            # Save to database - FIXED VERSION with proper JSON handling
            self._save_pattern_analysis(symbol, combined_analysis)
            
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
        import random
        import time
        
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
                        'bullish': None,  # Will be converted to string
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
                        'bullish': True,  # Will be converted to string
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
                        'bullish': False,  # Will be converted to string
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
                            'bullish': True,  # Will be converted to string
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
                            'bullish': False,  # Will be converted to string
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
                        'bullish': True if recent_trend > 0 else False,  # Will be converted to string
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
                        'bullish': False,  # Will be converted to string
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
                        'bullish': True,  # Will be converted to string
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
    
    def _save_pattern_analysis(self, symbol: str, analysis_data: Dict):
        """Save pattern analysis to database - FIXED VERSION with proper JSON serialization"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # CRITICAL FIX: Convert all values to JSON-serializable format
            json_safe_data = self._make_json_serializable(analysis_data)
            
            cursor.execute('''
                INSERT INTO pattern_analysis 
                (symbol, analysis_date, pattern_type, pattern_name, confidence_score, additional_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                datetime.now().date().isoformat(),
                'combined_analysis',
                f"{len(analysis_data.get('patterns', []))} patterns detected",
                analysis_data.get('confidence_score', 0.0),
                json.dumps(json_safe_data),  # Now safe to serialize
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved pattern analysis for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error saving pattern analysis for {symbol}: {e}")
    
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
        self.logger.info(f"Starting Pattern Analysis Service on port 5002 {mode}")
        self.app.run(host='0.0.0.0', port=5002, debug=False)

if __name__ == "__main__":
    service = PatternAnalysisService()
    service.run()
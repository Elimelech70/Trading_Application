# ================================================================
# 6. pattern_recognition_service.py (Port 5006) - CORRECTED VERSION
# ================================================================
"""
Name of Service: TRADING SYSTEM ADVANCED PATTERN RECOGNITION - CORRECTED VERSION
Version: 1.0.5
Last Updated: 2025-06-19
REVISION HISTORY:
v1.0.5 (2025-06-19) - Integrated database utilities to fix database locking issues
v1.0.4 (2025-06-17) - Fixed websockets dependency issue with yfinance graceful import
v1.0.3 (2025-06-15) - Removed TA-Lib dependency, using only manual pattern detection algorithms
v1.0.2 (2025-06-15) - Enhanced pattern detection
v1.0.1 (2025-06-15) - Initial version
v1.0.0 (2025-06-15) - Original implementation

Advanced Pattern Recognition Service - Enhanced pattern detection using manual ML algorithms
Complements the basic pattern analysis with advanced mathematical algorithms
Now uses database utilities with retry logic to prevent locking issues
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

# Import database utilities
try:
    from database_utils import get_database_manager, DatabaseServiceMixin
    USE_DB_UTILS = True
except ImportError:
    USE_DB_UTILS = False
    print("Warning: database_utils not found, using direct SQLite connections")

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

class PatternRecognitionService(DatabaseServiceMixin if USE_DB_UTILS else object):
    def __init__(self, db_path='/content/trading_system.db'):
        # Initialize database utilities if available
        if USE_DB_UTILS:
            super().__init__(db_path)
        else:
            self.db_path = db_path
            
        self.app = Flask(__name__)
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        
        self._setup_routes()
        self._register_with_coordination()
        
    def _setup_logging(self):
        import os
        os.makedirs('/content/logs', exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('PatternRecognitionService')
        
        handler = logging.FileHandler('/content/logs/pattern_recognition_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy", 
                "service": "pattern_recognition", 
                "implementation": "manual_algorithms",
                "yfinance_available": YFINANCE_AVAILABLE,
                "data_source": "yfinance" if YFINANCE_AVAILABLE else "simulated",
                "database_mode": "with_retry" if USE_DB_UTILS else "direct"
            })
        
        @self.app.route('/detect_advanced_patterns/<symbol>', methods=['GET'])
        def detect_advanced_patterns(symbol):
            patterns = self._detect_advanced_patterns(symbol)
            return jsonify(patterns)
        
        @self.app.route('/candlestick_patterns/<symbol>', methods=['GET'])
        def candlestick_patterns(symbol):
            patterns = self._detect_candlestick_patterns(symbol)
            return jsonify(patterns)
        
        @self.app.route('/chart_patterns/<symbol>', methods=['GET'])
        def chart_patterns(symbol):
            patterns = self._detect_chart_patterns(symbol)
            return jsonify(patterns)
    
    def _register_with_coordination(self):
        """Register with coordination service"""
        try:
            registration_data = {
                "service_name": "pattern_recognition",
                "port": 5006
            }
            response = requests.post(f"{self.coordination_service_url}/register_service",
                                   json=registration_data, timeout=5)
            if response.status_code == 200:
                self.logger.info("Successfully registered with coordination service")
        except Exception as e:
            self.logger.warning(f"Could not register with coordination service: {e}")
    
    def _detect_advanced_patterns(self, symbol: str) -> Dict:
        """Detect advanced patterns using multiple manual techniques"""
        try:
            data = self._get_market_data(symbol)
            if data.empty:
                return {"error": "No data available"}
            
            # Different pattern types using manual algorithms
            candlestick_patterns = self._detect_candlestick_patterns(symbol, data)
            chart_patterns = self._detect_chart_patterns(symbol, data)
            volume_patterns = self._detect_volume_patterns(symbol, data)
            
            # Calculate overall pattern score
            pattern_score = self._calculate_pattern_score(candlestick_patterns, chart_patterns, volume_patterns)
            
            result = {
                'symbol': symbol,
                'candlestick_patterns': candlestick_patterns,
                'chart_patterns': chart_patterns,
                'volume_patterns': volume_patterns,
                'overall_pattern_score': pattern_score,
                'analysis_time': datetime.now().isoformat(),
                'implementation': 'manual_algorithms',
                'data_source': 'yfinance' if YFINANCE_AVAILABLE else 'simulated'
            }
            
            # Save to database with retry logic
            self._save_pattern_analysis(result)
            
            self.logger.info(f"Advanced pattern analysis completed for {symbol}: score {pattern_score}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in advanced pattern detection for {symbol}: {e}")
            return {"error": str(e)}
    
    def _get_market_data(self, symbol: str, period: str = "30d") -> pd.DataFrame:
        """Get market data for pattern analysis"""
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
    
    def _detect_candlestick_patterns(self, symbol: str, data: pd.DataFrame = None) -> List[Dict]:
        """Detect candlestick patterns using manual mathematical analysis"""
        if data is None:
            data = self._get_market_data(symbol)
        
        if data.empty:
            return []
        
        patterns = []
        
        try:
            open_prices = data['Open'].values
            high_prices = data['High'].values
            low_prices = data['Low'].values
            close_prices = data['Close'].values
            
            # Analyze last 10 days for patterns
            for i in range(max(-10, -len(close_prices)), 0):
                if abs(i) > len(close_prices) or abs(i-1) > len(close_prices):
                    continue
                
                # Current candle
                curr_open = open_prices[i]
                curr_high = high_prices[i]
                curr_low = low_prices[i]
                curr_close = close_prices[i]
                
                # Calculate current candle properties
                curr_body = abs(curr_close - curr_open)
                curr_range = curr_high - curr_low
                curr_upper_shadow = curr_high - max(curr_open, curr_close)
                curr_lower_shadow = min(curr_open, curr_close) - curr_low
                
                if curr_range == 0:
                    continue
                
                # Previous candle (for multi-candle patterns)
                if abs(i-1) < len(close_prices):
                    prev_open = open_prices[i-1]
                    prev_high = high_prices[i-1]
                    prev_low = low_prices[i-1] 
                    prev_close = close_prices[i-1]
                    prev_body = abs(prev_close - prev_open)
                
                # DOJI Pattern
                if curr_body < curr_range * 0.1:
                    patterns.append({
                        'pattern_name': 'doji',
                        'signal_strength': 0,  # Neutral
                        'confidence_score': 0.7,
                        'bullish': None,
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_algorithm',
                        'description': 'Indecision pattern - open equals close'
                    })
                
                # HAMMER Pattern
                if (curr_lower_shadow > curr_body * 2 and 
                    curr_upper_shadow < curr_body * 0.3 and 
                    curr_body > 0):
                    patterns.append({
                        'pattern_name': 'hammer',
                        'signal_strength': 80,
                        'confidence_score': 0.75,
                        'bullish': True,
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_algorithm',
                        'description': 'Bullish reversal - long lower shadow'
                    })
                
                # HANGING MAN Pattern (like hammer but at top of uptrend)
                if (curr_lower_shadow > curr_body * 2 and 
                    curr_upper_shadow < curr_body * 0.3 and
                    curr_body > 0 and
                    i > -5):  # Check if in potential uptrend
                    recent_trend = np.mean(close_prices[i-3:i]) if abs(i-3) < len(close_prices) else curr_close
                    if curr_close > recent_trend * 1.02:  # In uptrend
                        patterns.append({
                            'pattern_name': 'hanging_man',
                            'signal_strength': -60,
                            'confidence_score': 0.65,
                            'bullish': False,
                            'detected_at': datetime.now().isoformat(),
                            'source': 'manual_algorithm',
                            'description': 'Bearish reversal at top of uptrend'
                        })
                
                # SHOOTING STAR Pattern
                if (curr_upper_shadow > curr_body * 2 and 
                    curr_lower_shadow < curr_body * 0.3 and 
                    curr_body > 0):
                    patterns.append({
                        'pattern_name': 'shooting_star',
                        'signal_strength': -80,
                        'confidence_score': 0.75,
                        'bullish': False,
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_algorithm',
                        'description': 'Bearish reversal - long upper shadow'
                    })
                
                # ENGULFING Patterns (requires previous candle)
                if abs(i-1) < len(close_prices):
                    # Bullish Engulfing
                    if (curr_close > curr_open and  # Current is bullish
                        prev_close < prev_open and  # Previous is bearish
                        curr_open < prev_close and  # Opens below prev close
                        curr_close > prev_open and  # Closes above prev open
                        curr_body > prev_body * 1.1):  # Larger body
                        
                        patterns.append({
                            'pattern_name': 'bullish_engulfing',
                            'signal_strength': 90,
                            'confidence_score': 0.85,
                            'bullish': True,
                            'detected_at': datetime.now().isoformat(),
                            'source': 'manual_algorithm',
                            'description': 'Strong bullish reversal pattern'
                        })
                    
                    # Bearish Engulfing
                    elif (curr_close < curr_open and  # Current is bearish
                          prev_close > prev_open and  # Previous is bullish
                          curr_open > prev_close and  # Opens above prev close
                          curr_close < prev_open and  # Closes below prev open
                          curr_body > prev_body * 1.1):  # Larger body
                        
                        patterns.append({
                            'pattern_name': 'bearish_engulfing',
                            'signal_strength': -90,
                            'confidence_score': 0.85,
                            'bullish': False,
                            'detected_at': datetime.now().isoformat(),
                            'source': 'manual_algorithm',
                            'description': 'Strong bearish reversal pattern'
                        })
                
                # SPINNING TOP Pattern
                if (curr_body < curr_range * 0.3 and
                    curr_upper_shadow > curr_body * 0.5 and
                    curr_lower_shadow > curr_body * 0.5):
                    patterns.append({
                        'pattern_name': 'spinning_top',
                        'signal_strength': 0,
                        'confidence_score': 0.6,
                        'bullish': None,
                        'detected_at': datetime.now().isoformat(),
                        'source': 'manual_algorithm',
                        'description': 'Indecision with long shadows both ways'
                    })
            
            # THREE WHITE SOLDIERS Pattern (3 consecutive bullish candles)
            if len(close_prices) >= 3:
                for i in range(-3, 0):
                    if abs(i-2) >= len(close_prices):
                        continue
                    
                    candle1_bull = close_prices[i-2] > open_prices[i-2]
                    candle2_bull = close_prices[i-1] > open_prices[i-1] 
                    candle3_bull = close_prices[i] > open_prices[i]
                    
                    if (candle1_bull and candle2_bull and candle3_bull and
                        close_prices[i-1] > close_prices[i-2] and
                        close_prices[i] > close_prices[i-1]):
                        
                        patterns.append({
                            'pattern_name': 'three_white_soldiers',
                            'signal_strength': 85,
                            'confidence_score': 0.8,
                            'bullish': True,
                            'detected_at': datetime.now().isoformat(),
                            'source': 'manual_algorithm',
                            'description': 'Strong bullish continuation pattern'
                        })
                        break  # Only detect once
            
            # THREE BLACK CROWS Pattern (3 consecutive bearish candles)
            if len(close_prices) >= 3:
                for i in range(-3, 0):
                    if abs(i-2) >= len(close_prices):
                        continue
                    
                    candle1_bear = close_prices[i-2] < open_prices[i-2]
                    candle2_bear = close_prices[i-1] < open_prices[i-1]
                    candle3_bear = close_prices[i] < open_prices[i]
                    
                    if (candle1_bear and candle2_bear and candle3_bear and
                        close_prices[i-1] < close_prices[i-2] and
                        close_prices[i] < close_prices[i-1]):
                        
                        patterns.append({
                            'pattern_name': 'three_black_crows',
                            'signal_strength': -85,
                            'confidence_score': 0.8,
                            'bullish': False,
                            'detected_at': datetime.now().isoformat(),
                            'source': 'manual_algorithm',
                            'description': 'Strong bearish continuation pattern'
                        })
                        break  # Only detect once
                        
        except Exception as e:
            self.logger.error(f"Error in candlestick pattern detection: {e}")
        
        return patterns
    
    def _detect_chart_patterns(self, symbol: str, data: pd.DataFrame = None) -> List[Dict]:
        """Detect chart patterns like support/resistance, trends using mathematical analysis"""
        if data is None:
            data = self._get_market_data(symbol)
        
        if data.empty:
            return []
        
        patterns = []
        
        try:
            close_prices = data['Close'].values
            high_prices = data['High'].values
            low_prices = data['Low'].values
            
            # Trend detection using linear regression
            if len(close_prices) >= 20:
                # Short-term trend (10 days)
                short_x = np.arange(10)
                short_trend = np.polyfit(short_x, close_prices[-10:], 1)[0]
                
                # Long-term trend (20 days) 
                long_x = np.arange(20)
                long_trend = np.polyfit(long_x, close_prices[-20:], 1)[0]
                
                # Calculate trend strength
                price_std = np.std(close_prices[-20:])
                short_strength = abs(short_trend) / price_std if price_std > 0 else 0
                long_strength = abs(long_trend) / price_std if price_std > 0 else 0
                
                # Strong uptrend
                if short_trend > 0 and long_trend > 0 and short_strength > 0.02:
                    patterns.append({
                        'pattern_name': 'strong_uptrend',
                        'strength': min(short_strength * 10, 1.0),
                        'timeframe': 'short_and_long_term',
                        'confidence_score': 0.8,
                        'trend_slope': short_trend,
                        'description': 'Sustained upward price movement'
                    })
                
                # Strong downtrend
                elif short_trend < 0 and long_trend < 0 and short_strength > 0.02:
                    patterns.append({
                        'pattern_name': 'strong_downtrend',
                        'strength': min(short_strength * 10, 1.0),
                        'timeframe': 'short_and_long_term', 
                        'confidence_score': 0.8,
                        'trend_slope': short_trend,
                        'description': 'Sustained downward price movement'
                    })
                
                # Trend reversal
                elif (short_trend > 0 and long_trend < 0) or (short_trend < 0 and long_trend > 0):
                    patterns.append({
                        'pattern_name': 'trend_reversal',
                        'strength': min(abs(short_trend - long_trend) / price_std, 1.0),
                        'timeframe': 'reversal_detected',
                        'confidence_score': 0.7,
                        'description': 'Recent trend change detected'
                    })
            
            # Support and Resistance Levels
            current_price = close_prices[-1]
            
            # Calculate recent highs and lows
            if len(close_prices) >= 20:
                highs_20 = np.max(high_prices[-20:])
                lows_20 = np.min(low_prices[-20:])
                
                # Resistance level analysis
                if current_price >= highs_20 * 0.98:  # Within 2% of resistance
                    resistance_touches = np.sum(high_prices[-20:] >= highs_20 * 0.99)
                    patterns.append({
                        'pattern_name': 'near_resistance',
                        'resistance_level': highs_20,
                        'current_price': current_price,
                        'distance_pct': ((current_price - highs_20) / highs_20) * 100,
                        'touches': int(resistance_touches),
                        'confidence_score': min(0.9, 0.5 + resistance_touches * 0.1),
                        'description': f'Price near resistance at ${highs_20:.2f}'
                    })
                
                # Support level analysis
                if current_price <= lows_20 * 1.02:  # Within 2% of support
                    support_touches = np.sum(low_prices[-20:] <= lows_20 * 1.01)
                    patterns.append({
                        'pattern_name': 'near_support',
                        'support_level': lows_20,
                        'current_price': current_price,
                        'distance_pct': ((current_price - lows_20) / lows_20) * 100,
                        'touches': int(support_touches),
                        'confidence_score': min(0.9, 0.5 + support_touches * 0.1),
                        'description': f'Price near support at ${lows_20:.2f}'
                    })
            
            # Consolidation/Triangle patterns
            if len(close_prices) >= 15:
                recent_highs = high_prices[-15:]
                recent_lows = low_prices[-15:]
                
                # Linear regression on highs and lows
                x_vals = np.arange(len(recent_highs))
                high_trend = np.polyfit(x_vals, recent_highs, 1)[0]
                low_trend = np.polyfit(x_vals, recent_lows, 1)[0]
                
                # Consolidation (horizontal movement)
                if abs(high_trend) < np.std(recent_highs) * 0.1 and abs(low_trend) < np.std(recent_lows) * 0.1:
                    patterns.append({
                        'pattern_name': 'consolidation',
                        'high_trend': high_trend,
                        'low_trend': low_trend,
                        'range_size': (np.max(recent_highs) - np.min(recent_lows)) / current_price * 100,
                        'confidence_score': 0.75,
                        'description': 'Sideways price movement - consolidation phase'
                    })
                
                # Ascending Triangle
                elif abs(high_trend) < np.std(recent_highs) * 0.1 and low_trend > 0:
                    patterns.append({
                        'pattern_name': 'ascending_triangle',
                        'pattern_type': 'continuation',
                        'bias': 'bullish',
                        'confidence_score': 0.7,
                        'description': 'Rising lows with horizontal resistance'
                    })
                
                # Descending Triangle  
                elif abs(low_trend) < np.std(recent_lows) * 0.1 and high_trend < 0:
                    patterns.append({
                        'pattern_name': 'descending_triangle',
                        'pattern_type': 'continuation',
                        'bias': 'bearish',
                        'confidence_score': 0.7,
                        'description': 'Falling highs with horizontal support'
                    })
                
        except Exception as e:
            self.logger.error(f"Error in chart pattern detection: {e}")
        
        return patterns
    
    def _detect_volume_patterns(self, symbol: str, data: pd.DataFrame = None) -> List[Dict]:
        """Detect volume-based patterns using mathematical analysis"""
        if data is None:
            data = self._get_market_data(symbol)
        
        if data.empty:
            return []
        
        patterns = []
        
        try:
            volume = data['Volume'].values
            close_prices = data['Close'].values
            
            if len(volume) >= 20:
                avg_volume_20 = np.mean(volume[-20:])
                current_volume = volume[-1]
                
                # High volume analysis
                if current_volume > avg_volume_20 * 2:
                    price_change = (close_prices[-1] - close_prices[-2]) / close_prices[-2] * 100
                    
                    patterns.append({
                        'pattern_name': 'high_volume_breakout',
                        'volume_ratio': current_volume / avg_volume_20,
                        'price_change_pct': price_change,
                        'bullish': price_change > 0,
                        'confidence_score': min(0.9, 0.5 + (current_volume / avg_volume_20) * 0.1),
                        'description': f'Volume spike ({current_volume/avg_volume_20:.1f}x average)'
                    })
                
                # Volume trend analysis
                if len(volume) >= 10:
                    volume_trend = np.polyfit(range(10), volume[-10:], 1)[0]
                    volume_strength = abs(volume_trend) / avg_volume_20
                    
                    if volume_strength > 0.1:
                        patterns.append({
                            'pattern_name': 'volume_trend',
                            'trend_direction': 'increasing' if volume_trend > 0 else 'decreasing',
                            'trend_strength': volume_strength,
                            'confidence_score': min(0.8, 0.4 + volume_strength),
                            'description': f'{"Increasing" if volume_trend > 0 else "Decreasing"} volume trend'
                        })
                
                # On-Balance Volume (OBV) analysis
                obv = self._calculate_obv(close_prices, volume)
                if len(obv) >= 10:
                    obv_trend = np.polyfit(range(min(10, len(obv))), obv[-10:], 1)[0]
                    obv_strength = abs(obv_trend) / np.std(obv[-20:]) if len(obv) >= 20 else 0
                    
                    if obv_strength > 0.1:
                        patterns.append({
                            'pattern_name': 'obv_divergence',
                            'obv_trend': 'bullish' if obv_trend > 0 else 'bearish',
                            'strength': obv_strength,
                            'confidence_score': min(0.8, 0.5 + obv_strength),
                            'description': f'OBV showing {"accumulation" if obv_trend > 0 else "distribution"}'
                        })
                
                # Volume Price Trend (VPT) analysis
                vpt = self._calculate_vpt(close_prices, volume)
                if len(vpt) >= 10:
                    vpt_trend = np.polyfit(range(min(10, len(vpt))), vpt[-10:], 1)[0]
                    
                    if abs(vpt_trend) > np.std(vpt[-20:]) * 0.1 if len(vpt) >= 20 else 0:
                        patterns.append({
                            'pattern_name': 'volume_price_trend',
                            'vpt_direction': 'positive' if vpt_trend > 0 else 'negative',
                            'strength': abs(vpt_trend),
                            'confidence_score': 0.7,
                            'description': f'Volume-price trend is {"positive" if vpt_trend > 0 else "negative"}'
                        })
                
                # Low volume warning
                if current_volume < avg_volume_20 * 0.5:
                    patterns.append({
                        'pattern_name': 'low_volume_warning',
                        'volume_ratio': current_volume / avg_volume_20,
                        'confidence_score': 0.6,
                        'description': 'Unusually low volume - reduced reliability'
                    })
                    
        except Exception as e:
            self.logger.error(f"Error in volume pattern detection: {e}")
        
        return patterns
    
    def _calculate_obv(self, prices: np.array, volumes: np.array) -> np.array:
        """Calculate On-Balance Volume manually"""
        obv = np.zeros(len(prices))
        if len(prices) == 0:
            return obv
            
        obv[0] = volumes[0]
        
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                obv[i] = obv[i-1] + volumes[i]
            elif prices[i] < prices[i-1]:
                obv[i] = obv[i-1] - volumes[i]
            else:
                obv[i] = obv[i-1]
        
        return obv
    
    def _calculate_vpt(self, prices: np.array, volumes: np.array) -> np.array:
        """Calculate Volume Price Trend manually"""
        vpt = np.zeros(len(prices))
        if len(prices) <= 1:
            return vpt
            
        vpt[0] = volumes[0]
        
        for i in range(1, len(prices)):
            price_change_pct = (prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] != 0 else 0
            vpt[i] = vpt[i-1] + (volumes[i] * price_change_pct)
        
        return vpt
    
    def _calculate_pattern_score(self, candlestick: List, chart: List, volume: List) -> float:
        """Calculate overall pattern strength score"""
        score = 0.0
        
        # Candlestick patterns contribute 40%
        if candlestick:
            candlestick_score = sum([p.get('confidence_score', 0) for p in candlestick]) / len(candlestick)
            score += candlestick_score * 0.4
        
        # Chart patterns contribute 35%
        if chart:
            chart_score = sum([p.get('confidence_score', 0) for p in chart]) / len(chart)
            score += chart_score * 0.35
        
        # Volume patterns contribute 25%
        if volume:
            volume_score = sum([p.get('confidence_score', 0) for p in volume]) / len(volume)
            score += volume_score * 0.25
        
        return min(score, 1.0)
    
    def _save_pattern_analysis(self, analysis_data: Dict):
        """Save pattern analysis to database with retry logic"""
        try:
            data = {
                'symbol': analysis_data['symbol'],
                'detection_date': datetime.now().isoformat(),
                'pattern_category': 'advanced_combined',
                'pattern_score': analysis_data['overall_pattern_score'],
                'candlestick_patterns_count': len(analysis_data.get('candlestick_patterns', [])),
                'chart_patterns_count': len(analysis_data.get('chart_patterns', [])),
                'volume_patterns_count': len(analysis_data.get('volume_patterns', [])),
                'pattern_metadata': json.dumps(analysis_data),
                'created_at': datetime.now().isoformat()
            }
            
            if USE_DB_UTILS:
                # Use database utilities with retry logic
                success = self.save_to_database('advanced_patterns', data)
                if success:
                    self.logger.info(f"Pattern analysis saved with retry logic for {analysis_data['symbol']}")
                else:
                    self.logger.error(f"Failed to save pattern analysis for {analysis_data['symbol']}")
            else:
                # Fallback to direct connection
                conn = sqlite3.connect(self.db_path, timeout=30)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO advanced_patterns 
                    (symbol, detection_date, pattern_category, pattern_score, 
                     candlestick_patterns_count, chart_patterns_count, volume_patterns_count,
                     pattern_metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['symbol'],
                    data['detection_date'],
                    data['pattern_category'],
                    data['pattern_score'],
                    data['candlestick_patterns_count'],
                    data['chart_patterns_count'],
                    data['volume_patterns_count'],
                    data['pattern_metadata'],
                    data['created_at']
                ))
                
                conn.commit()
                conn.close()
                self.logger.info(f"Pattern analysis saved for {analysis_data['symbol']}")
            
        except Exception as e:
            self.logger.error(f"Error saving pattern analysis: {e}")
    
    def run(self):
        mode = "with yfinance" if YFINANCE_AVAILABLE else "in simulation mode"
        db_mode = "with retry logic" if USE_DB_UTILS else "direct connection"
        self.logger.info(f"Starting Pattern Recognition Service on port 5006 {mode}, database {db_mode}")
        self.app.run(host='0.0.0.0', port=5006, debug=False)

if __name__ == "__main__":
    service = PatternRecognitionService()
    service.run()

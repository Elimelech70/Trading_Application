# ================================================================
# 4. technical_analysis.py (Port 5003) - CORRECTED VERSION
# ================================================================
"""
Name of Service: TRADING SYSTEM TECHNICAL ANALYSIS - CORRECTED VERSION
Version: 1.0.4
Last Updated: 2025-06-17
REVISION HISTORY:
v1.0.4 (2025-06-17) - Fixed websockets dependency issue with yfinance graceful import
v1.0.3 (2025-06-15) - Removed TA-Lib dependency, using only manual technical indicator calculations
v1.0.2 (2025-06-15) - Fixed version with TA-Lib fallback  
v1.0.1 (2025-06-15) - Initial version
v1.0.0 (2025-06-15) - Original implementation

Technical Analysis Service - Generates trading signals using manual technical indicator calculations
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

# Try to import ML libraries
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("Scikit-learn not available, using rule-based signals only")

class TechnicalAnalysisService:
    def __init__(self, db_path='/content/trading_system.db'):
        self.app = Flask(__name__)
        self.db_path = db_path
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        
        # Initialize ML models if available
        self.ml_model = None
        self.confidence_model = None
        if ML_AVAILABLE:
            self._init_ml_models()
        
        self._setup_routes()
        self._register_with_coordination()
        
    def _setup_logging(self):
        import os
        os.makedirs('/content/logs', exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('TechnicalAnalysisService')
        
        handler = logging.FileHandler('/content/logs/technical_analysis_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_ml_models(self):
        """Initialize ML models for signal generation"""
        try:
            # Primary model: Random Forest for signal classification
            self.ml_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                class_weight='balanced'
            )
            
            # Secondary model: Gradient Boosting for confidence scoring
            self.confidence_model = GradientBoostingRegressor(
                n_estimators=50,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            self.logger.info("ML models initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing ML models: {e}")
            self.ml_model = None
            self.confidence_model = None
    
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy", 
                "service": "technical_analysis",
                "ml_available": ML_AVAILABLE,
                "yfinance_available": YFINANCE_AVAILABLE,
                "implementation": "manual_indicators",
                "data_source": "yfinance" if YFINANCE_AVAILABLE else "simulated"
            })
        
        @self.app.route('/generate_signals', methods=['POST'])
        def generate_signals_endpoint():
            securities = request.json.get('securities', [])
            signals = self._generate_signals(securities)
            return jsonify(signals)
        
        @self.app.route('/analyze/<symbol>', methods=['GET'])
        def analyze_single_symbol(symbol):
            # Single symbol analysis
            analysis = self._analyze_single_security({'symbol': symbol})
            return jsonify(analysis)
    
    def _register_with_coordination(self):
        """Register with coordination service"""
        try:
            registration_data = {
                "service_name": "technical_analysis",
                "port": 5003
            }
            response = requests.post(f"{self.coordination_service_url}/register_service",
                                   json=registration_data, timeout=5)
            if response.status_code == 200:
                self.logger.info("Successfully registered with coordination service")
        except Exception as e:
            self.logger.warning(f"Could not register with coordination service: {e}")
    
    def _generate_signals(self, securities_with_patterns: List[Dict]) -> List[Dict]:
        """Generate trading signals for securities with pattern analysis"""
        self.logger.info(f"Generating trading signals for {len(securities_with_patterns)} securities")
        
        trading_signals = []
        
        for security in securities_with_patterns:
            try:
                signal_data = self._analyze_single_security(security)
                
                if signal_data and signal_data.get('signal') in ['BUY', 'SELL']:
                    # Save to database
                    self._save_trading_signal(security['symbol'], signal_data)
                    trading_signals.append(signal_data)
                    
                    self.logger.info(f"Generated {signal_data['signal']} signal for {security['symbol']}")
                
            except Exception as e:
                self.logger.error(f"Error generating signal for {security.get('symbol', 'unknown')}: {e}")
        
        self.logger.info(f"Signal generation completed: {len(trading_signals)} signals generated")
        return trading_signals
    
    def _analyze_single_security(self, security: Dict) -> Optional[Dict]:
        """Analyze single security and generate signal"""
        symbol = security['symbol']
        
        try:
            # Get market data
            market_data = self._get_market_data(symbol)
            if market_data is None:
                return None
            
            # Calculate technical indicators using manual methods
            indicators = self._calculate_indicators_manual(market_data)
            
            # Get patterns from security data
            patterns = security.get('patterns', [])
            
            # Generate signal
            signal_data = self._generate_rule_based_signal(symbol, indicators, patterns)
            
            return signal_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get market data for analysis"""
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="30d")
                
                if len(hist) < 20:
                    return self._generate_simulated_data(symbol)
                
                return hist
                
            except Exception as e:
                self.logger.warning(f"yfinance error for {symbol}, using simulated data: {e}")
                return self._generate_simulated_data(symbol)
        else:
            return self._generate_simulated_data(symbol)
    
    def _generate_simulated_data(self, symbol: str) -> pd.DataFrame:
        """Generate simulated OHLCV data for technical analysis"""
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
            # Random daily change with some trend
            trend_factor = 0.001 if i > 15 else -0.001  # Slight trend
            change_pct = random.uniform(-0.05, 0.05) + trend_factor
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
    
    def _calculate_indicators_manual(self, data: pd.DataFrame) -> Dict:
        """Calculate technical indicators manually using mathematical formulas"""
        indicators = {}
        
        try:
            close_prices = data['Close'].values
            high_prices = data['High'].values
            low_prices = data['Low'].values
            volume = data['Volume'].values
            
            # Current price and volume
            indicators['current_price'] = float(close_prices[-1])
            indicators['current_volume'] = float(volume[-1])
            
            # RSI Calculation (14-period)
            def calculate_rsi(prices, period=14):
                if len(prices) < period + 1:
                    return 50.0  # Neutral RSI if insufficient data
                
                deltas = np.diff(prices)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                # Initial average gain and loss
                avg_gain = np.mean(gains[:period])
                avg_loss = np.mean(losses[:period])
                
                # Calculate RS and RSI for each subsequent period
                for i in range(period, len(deltas)):
                    avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                    avg_loss = (avg_loss * (period - 1) + losses[i]) / period
                
                if avg_loss == 0:
                    return 100.0
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            indicators['rsi'] = calculate_rsi(close_prices)
            
            # Simple Moving Averages
            indicators['sma_20'] = float(np.mean(close_prices[-20:]))
            indicators['sma_50'] = float(np.mean(close_prices[-50:])) if len(close_prices) >= 50 else indicators['sma_20']
            
            # Exponential Moving Average (12-period)
            def calculate_ema(prices, period):
                if len(prices) < period:
                    return np.mean(prices)
                
                multiplier = 2 / (period + 1)
                ema = np.mean(prices[:period])  # Start with SMA
                
                for price in prices[period:]:
                    ema = (price * multiplier) + (ema * (1 - multiplier))
                
                return ema
            
            indicators['ema_12'] = calculate_ema(close_prices, 12)
            indicators['ema_26'] = calculate_ema(close_prices, 26)
            
            # MACD Calculation
            macd_line = indicators['ema_12'] - indicators['ema_26']
            signal_line = calculate_ema([macd_line], 9)  # 9-period EMA of MACD
            macd_histogram = macd_line - signal_line
            
            indicators['macd'] = {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': macd_histogram
            }
            
            # Bollinger Bands (20-period, 2 standard deviations)
            sma_20 = indicators['sma_20']
            std_20 = np.std(close_prices[-20:])
            bb_upper = sma_20 + (2 * std_20)
            bb_lower = sma_20 - (2 * std_20)
            bb_position = (close_prices[-1] - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
            
            indicators['bollinger'] = {
                'upper': bb_upper,
                'middle': sma_20,
                'lower': bb_lower,
                'position': bb_position  # 0 = at lower band, 1 = at upper band
            }
            
            # Stochastic Oscillator (14-period)
            if len(close_prices) >= 14:
                low_14 = np.min(low_prices[-14:])
                high_14 = np.max(high_prices[-14:])
                k_percent = ((close_prices[-1] - low_14) / (high_14 - low_14) * 100) if high_14 != low_14 else 50
                
                # Calculate %D (3-period SMA of %K) - simplified to current %K
                indicators['stochastic'] = {
                    'k': k_percent,
                    'd': k_percent  # Simplified - normally this would be a moving average of k
                }
            else:
                indicators['stochastic'] = {'k': 50, 'd': 50}
            
            # Volume analysis
            indicators['volume_sma'] = float(np.mean(volume[-20:]))
            volume_ratio = indicators['current_volume'] / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1.0
            indicators['volume_ratio'] = volume_ratio
            
            # Price momentum (5-day rate of change)
            if len(close_prices) >= 5:
                momentum = ((close_prices[-1] - close_prices[-5]) / close_prices[-5]) * 100
                indicators['momentum_5d'] = momentum
            else:
                indicators['momentum_5d'] = 0.0
            
            # Volatility (20-day standard deviation)
            volatility = np.std(close_prices[-20:]) / np.mean(close_prices[-20:]) * 100
            indicators['volatility'] = volatility
            
        except Exception as e:
            self.logger.error(f"Error calculating manual indicators: {e}")
        
        return indicators
    
    def _generate_rule_based_signal(self, symbol: str, indicators: Dict, patterns: List[Dict]) -> Dict:
        """Generate trading signal using rule-based logic"""
        signal_score = 0
        reasons = []
        
        # RSI signals (30/70 oversold/overbought levels)
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            signal_score += 2
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > 70:
            signal_score -= 2
            reasons.append(f"RSI overbought ({rsi:.1f})")
        elif rsi < 40:
            signal_score += 1
            reasons.append(f"RSI bullish ({rsi:.1f})")
        elif rsi > 60:
            signal_score -= 1
            reasons.append(f"RSI bearish ({rsi:.1f})")
        
        # MACD signals
        macd_hist = indicators.get('macd', {}).get('histogram', 0)
        if macd_hist > 0:
            signal_score += 1
            reasons.append("MACD bullish crossover")
        elif macd_hist < 0:
            signal_score -= 1
            reasons.append("MACD bearish crossover")
        
        # Moving average signals
        current_price = indicators.get('current_price', 0)
        sma_20 = indicators.get('sma_20', current_price)
        sma_50 = indicators.get('sma_50', current_price)
        ema_12 = indicators.get('ema_12', current_price)
        
        # Price vs SMA signals
        if current_price > sma_20:
            signal_score += 1
            reasons.append("Price above SMA20")
        else:
            signal_score -= 1
            reasons.append("Price below SMA20")
        
        # EMA vs SMA crossover
        if ema_12 > sma_20:
            signal_score += 1
            reasons.append("EMA12 above SMA20")
        
        # SMA crossover
        if sma_20 > sma_50:
            signal_score += 1
            reasons.append("SMA20 above SMA50")
        elif sma_20 < sma_50:
            signal_score -= 1
            reasons.append("SMA20 below SMA50")
        
        # Bollinger Bands signals
        bb_position = indicators.get('bollinger', {}).get('position', 0.5)
        if bb_position < 0.2:
            signal_score += 1
            reasons.append("Near lower Bollinger Band")
        elif bb_position > 0.8:
            signal_score -= 1
            reasons.append("Near upper Bollinger Band")
        
        # Stochastic signals
        stoch_k = indicators.get('stochastic', {}).get('k', 50)
        if stoch_k < 20:
            signal_score += 1
            reasons.append(f"Stochastic oversold ({stoch_k:.1f})")
        elif stoch_k > 80:
            signal_score -= 1
            reasons.append(f"Stochastic overbought ({stoch_k:.1f})")
        
        # Momentum signals
        momentum = indicators.get('momentum_5d', 0)
        if momentum > 5:
            signal_score += 1
            reasons.append(f"Strong positive momentum ({momentum:.1f}%)")
        elif momentum < -5:
            signal_score -= 1
            reasons.append(f"Strong negative momentum ({momentum:.1f}%)")
        
        # Pattern signals
        bullish_patterns = len([p for p in patterns if p.get('bullish', False)])
        bearish_patterns = len([p for p in patterns if p.get('bullish') == False])
        
        signal_score += bullish_patterns
        signal_score -= bearish_patterns
        
        if bullish_patterns > 0:
            reasons.append(f"{bullish_patterns} bullish pattern(s)")
        if bearish_patterns > 0:
            reasons.append(f"{bearish_patterns} bearish pattern(s)")
        
        # Volume confirmation
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            reasons.append(f"High volume confirmation ({volume_ratio:.1f}x)")
            signal_score = int(signal_score * 1.2)  # Amplify signal on high volume
        elif volume_ratio < 0.5:
            reasons.append(f"Low volume warning ({volume_ratio:.1f}x)")
            signal_score = int(signal_score * 0.8)  # Reduce signal on low volume
        
        # Volatility adjustment
        volatility = indicators.get('volatility', 0)
        if volatility > 5:  # High volatility
            signal_score = int(signal_score * 0.9)  # Slightly reduce confidence
            reasons.append(f"High volatility ({volatility:.1f}%)")
        
        # Determine final signal
        if signal_score >= 4:
            signal = 'BUY'
            confidence = min(0.9, 0.5 + (signal_score * 0.08))
        elif signal_score <= -4:
            signal = 'SELL'
            confidence = min(0.9, 0.5 + (abs(signal_score) * 0.08))
        else:
            signal = 'HOLD'
            confidence = 0.3 + (abs(signal_score) * 0.05)
        
        # Calculate position size based on confidence and volatility
        base_quantity = 100
        volatility_factor = max(0.5, 1 - (volatility / 20))  # Reduce size for high volatility
        quantity = int(base_quantity * confidence * volatility_factor)
        
        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': round(confidence, 3),
            'current_price': current_price,
            'quantity': quantity,
            'reason': '; '.join(reasons) if reasons else 'No clear signal',
            'signal_score': signal_score,
            'indicators_used': len([k for k in indicators.keys() if not k.startswith('current')]),
            'patterns_analyzed': len(patterns),
            'rsi': rsi,
            'macd_histogram': macd_hist,
            'bb_position': bb_position,
            'volume_ratio': volume_ratio,
            'volatility': volatility,
            'timestamp': datetime.now().isoformat(),
            'implementation': 'manual_calculations',
            'data_source': 'yfinance' if YFINANCE_AVAILABLE else 'simulated'
        }
    
    def _save_trading_signal(self, symbol: str, signal_data: Dict):
        """Save trading signal to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trading_signals 
                (symbol, signal_type, signal_strength, ml_confidence, entry_price, 
                 technical_indicators, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                signal_data['signal'],
                signal_data['confidence'],
                signal_data['confidence'],  # Using same confidence for both
                signal_data.get('current_price', 0),
                json.dumps(signal_data),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved trading signal for {symbol}: {signal_data['signal']}")
            
        except Exception as e:
            self.logger.error(f"Error saving trading signal for {symbol}: {e}")
    
    def run(self):
        mode = f"ML: {ML_AVAILABLE}, yfinance: {YFINANCE_AVAILABLE}"
        self.logger.info(f"Starting Technical Analysis Service on port 5003 ({mode})")
        self.app.run(host='0.0.0.0', port=5003, debug=False)

if __name__ == "__main__":
    service = TechnicalAnalysisService()
    service.run()
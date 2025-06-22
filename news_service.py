#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM NEWS SERVICE
Version: 1.0.5
Last Updated: 2025-06-21
REVISION HISTORY:
v1.0.5 (2025-06-21) - Fixed NOT NULL constraint by ensuring article_date is always populated
v1.0.4 (2025-06-17) - Fixed websockets dependency issue with yfinance graceful import
v1.0.3 (2025-06-15) - Enhanced sentiment analysis
v1.0.2 (2025-06-15) - Initial version
v1.0.1 (2025-06-15) - Original implementation

News Service - Provides news sentiment analysis for securities
Uses multiple NLP models for comprehensive sentiment analysis
Fixed to handle yfinance websockets dependency issues gracefully
Fixed NOT NULL constraint error for article_date field
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

# Import TextBlob for sentiment analysis
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
    print("✅ TextBlob imported successfully")
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️ TextBlob not available - using keyword-based sentiment only")

# Import database utilities if available
try:
    from database_utils import DatabaseServiceMixin
    USE_DB_UTILS = True
except ImportError:
    USE_DB_UTILS = False
    print("Warning: database_utils not found, using direct SQLite connections")

class NewsService(DatabaseServiceMixin if USE_DB_UTILS else object):
    def __init__(self, db_path='./trading_system.db'):
        if USE_DB_UTILS:
            super().__init__(db_path)
        else:
            self.db_path = db_path
        
        self.app = Flask(__name__)
        self.setup_routes()
        self.setup_logging()
        
        # Sentiment keywords for basic analysis
        self.positive_keywords = [
            'upgrade', 'buy', 'strong', 'outperform', 'positive', 'growth',
            'beat', 'exceed', 'surge', 'rally', 'gain', 'profit', 'revenue',
            'bullish', 'optimistic', 'successful', 'breakthrough', 'innovation'
        ]
        
        self.negative_keywords = [
            'downgrade', 'sell', 'weak', 'underperform', 'negative', 'loss',
            'miss', 'decline', 'fall', 'drop', 'cut', 'layoff', 'lawsuit',
            'bearish', 'pessimistic', 'failure', 'concern', 'risk', 'warning'
        ]
        
        self.logger.info("News Service initialized with database utilities" if USE_DB_UTILS else "News Service initialized")
        
    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger('news_service')
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        
    def setup_routes(self):
        """Setup Flask routes"""
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "healthy", "service": "news_service"})
            
        @self.app.route('/analyze_sentiment', methods=['POST'])
        def analyze_sentiment():
            data = request.json
            symbol = data.get('symbol')
            
            if not symbol:
                return jsonify({"error": "Symbol required"}), 400
                
            analysis = self._analyze_sentiment(symbol)
            return jsonify(analysis)
            
    def _get_news_data(self, symbol: str) -> List[Dict]:
        """Fetch news data for a symbol"""
        news_items = []
        
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                news = ticker.news
                
                for item in news[:10]:  # Get latest 10 news items
                    news_items.append({
                        'title': item.get('title', ''),
                        'publisher': item.get('publisher', ''),
                        'link': item.get('link', ''),
                        'timestamp': item.get('providerPublishTime', 0)
                    })
                    
            except Exception as e:
                self.logger.error(f"Error fetching news for {symbol}: {e}")
                
        else:
            # Simulated news data when yfinance not available
            news_items = [
                {
                    'title': f"{symbol} Shows Strong Performance in Q4",
                    'publisher': 'Financial Times',
                    'link': 'https://example.com',
                    'timestamp': int(datetime.now().timestamp())
                },
                {
                    'title': f"Analysts Upgrade {symbol} to Buy Rating",
                    'publisher': 'Reuters',
                    'link': 'https://example.com',
                    'timestamp': int(datetime.now().timestamp())
                }
            ]
            
        return news_items
        
    def _calculate_sentiment(self, text: str) -> tuple:
        """Calculate sentiment score and label"""
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                
                if polarity > 0.1:
                    label = 'positive'
                elif polarity < -0.1:
                    label = 'negative'
                else:
                    label = 'neutral'
                    
                return polarity, label
                
            except Exception as e:
                self.logger.error(f"TextBlob error: {e}")
                
        # Fallback to keyword-based sentiment
        text_lower = text.lower()
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        
        if positive_count > negative_count:
            score = 0.5
            label = 'positive'
        elif negative_count > positive_count:
            score = -0.5
            label = 'negative'
        else:
            score = 0.0
            label = 'neutral'
            
        return score, label
        
    def _analyze_sentiment(self, symbol: str) -> Dict:
        """Analyze sentiment for a symbol"""
        news_items = self._get_news_data(symbol)
        
        if not news_items:
            return {
                'symbol': symbol,
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'news_count': 0,
                'analysis_time': datetime.now().isoformat()
            }
            
        sentiments = []
        positive_count = 0
        negative_count = 0
        
        for item in news_items:
            score, label = self._calculate_sentiment(item['title'])
            sentiments.append(score)
            
            if label == 'positive':
                positive_count += 1
            elif label == 'negative':
                negative_count += 1
                
        # Calculate average sentiment
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        # Determine overall label
        if avg_sentiment > 0.1:
            overall_label = 'positive'
        elif avg_sentiment < -0.1:
            overall_label = 'negative'
        else:
            overall_label = 'neutral'
            
        analysis_result = {
            'symbol': symbol,
            'sentiment_score': round(avg_sentiment, 3),
            'sentiment_label': overall_label,
            'news_count': len(news_items),
            'positive_articles': positive_count,
            'negative_articles': negative_count,
            'neutral_articles': len(news_items) - positive_count - negative_count,
            'latest_news': news_items[:5],  # Return top 5 news items
            'analysis_time': datetime.now().isoformat()
        }
        
        # Save to database
        self._save_sentiment_analysis(analysis_result)
        
        return analysis_result
        
    def _save_sentiment_analysis(self, sentiment_data: Dict):
        """Save sentiment analysis to database"""
        try:
            # Ensure article_date is always populated
            analysis_time = sentiment_data.get('analysis_time', datetime.now().isoformat())
            
            # Convert ISO format to datetime object then back to ensure consistency
            if isinstance(analysis_time, str):
                article_date = datetime.fromisoformat(analysis_time.replace('Z', '+00:00')).isoformat()
            else:
                article_date = datetime.now().isoformat()
            
            if USE_DB_UTILS:
                # Use database utilities with retry logic
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO news_sentiment 
                        (symbol, article_date, sentiment_score, sentiment_label, 
                         news_count, positive_articles, negative_articles, metadata, analysis_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sentiment_data['symbol'],
                        article_date,  # FIXED: Always populated
                        sentiment_data['sentiment_score'],
                        sentiment_data['sentiment_label'],
                        sentiment_data['news_count'],
                        sentiment_data.get('positive_articles', 0),
                        sentiment_data.get('negative_articles', 0),
                        json.dumps(sentiment_data),
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    
            else:
                # Direct SQLite connection
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO news_sentiment 
                    (symbol, article_date, sentiment_score, sentiment_label, 
                     news_count, positive_articles, negative_articles, metadata, analysis_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sentiment_data['symbol'],
                    article_date,  # FIXED: Always populated
                    sentiment_data['sentiment_score'],
                    sentiment_data['sentiment_label'],
                    sentiment_data['news_count'],
                    sentiment_data.get('positive_articles', 0),
                    sentiment_data.get('negative_articles', 0),
                    json.dumps(sentiment_data),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                
            self.logger.info(f"Saved sentiment analysis for {sentiment_data['symbol']}")
            
        except Exception as e:
            self.logger.error(f"Error saving sentiment analysis: {e}")
            # Log the specific data that caused the error for debugging
            self.logger.error(f"Failed data: {sentiment_data}")
    
    def run(self):
        mode = "with yfinance" if YFINANCE_AVAILABLE else "in simulation mode"
        textblob_status = "with TextBlob" if TEXTBLOB_AVAILABLE else "keyword-based only"
        db_mode = "with retry logic" if USE_DB_UTILS else "direct connection"
        
        self.logger.info(f"Starting News Service on port 5008 {mode}, {textblob_status}, {db_mode}")
        self.app.run(host='0.0.0.0', port=5008, debug=False)

if __name__ == "__main__":
    service = NewsService()
    service.run()

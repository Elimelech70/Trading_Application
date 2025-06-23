#!/usr/bin/env python3
"""
Mock Security Scanner for Testing
Returns fake data to test the trading system without Yahoo Finance
"""
from flask import Flask, jsonify
import random
from datetime import datetime

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "mock_scanner", "mode": "simulation"})

@app.route('/scan_securities', methods=['GET'])
def scan_securities():
    """Return mock securities for testing"""
    # Simulate some securities that meet criteria
    mock_securities = []
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    for symbol in symbols[:3]:  # Return 3 securities
        mock_securities.append({
            'symbol': symbol,
            'price': round(random.uniform(100, 500), 2),
            'volume': random.randint(1000000, 50000000),
            'change_percent': round(random.uniform(-5, 5), 2),
            'market_cap': random.randint(100000000000, 2000000000000),
            'scan_timestamp': datetime.now().isoformat(),
            'score': round(random.uniform(60, 90), 2)
        })
    
    return jsonify(mock_securities)

@app.route('/criteria', methods=['GET'])
def get_criteria():
    return jsonify({
        'min_price': 10,
        'max_price': 1000,
        'min_volume': 1000000,
        'min_market_cap': 1000000000
    })

if __name__ == "__main__":
    print("Starting Mock Security Scanner on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False)

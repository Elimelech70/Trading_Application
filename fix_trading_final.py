#!/usr/bin/env python3
"""
Final fixes for Trading System
Addresses rate limiting and response format issues
"""
import time
import subprocess
from pathlib import Path

def fix_coordination_service():
    """Fix coordination service to handle scanner list response"""
    print("🔧 Fixing coordination service scanner response handling...")
    
    try:
        with open('coordination_service.py', 'r') as f:
            content = f.read()
        
        # Find the scanner response handling
        old_code = """scan_data = scan_response.json()
                results['steps'].append({
                    "step": "security_scan",
                    "status": "success",
                    "securities_found": len(scan_data.get('securities', []))
                })
                
                # Process each security through the pipeline
                for security in scan_data.get('securities', [])[:5]:"""
        
        new_code = """scan_data = scan_response.json()
                # Handle both list and dict responses
                if isinstance(scan_data, list):
                    securities = scan_data
                else:
                    securities = scan_data.get('securities', [])
                    
                results['steps'].append({
                    "step": "security_scan", 
                    "status": "success",
                    "securities_found": len(securities)
                })
                
                # Process each security through the pipeline
                for security in securities[:5]:"""
        
        if old_code.replace('\n', ' ').replace('  ', ' ') in content.replace('\n', ' ').replace('  ', ' '):
            # Backup
            Path('coordination_service.py.backup2').write_text(content)
            
            # Replace
            content = content.replace(old_code, new_code)
            
            with open('coordination_service.py', 'w') as f:
                f.write(content)
            print("✅ Fixed scanner response handling")
        else:
            print("⚠️  Could not find exact code to replace, trying alternative fix...")
            
            # Alternative: just fix the specific lines
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "scan_data.get('securities', [])" in line:
                    # Add check before this line
                    indent = len(line) - len(line.lstrip())
                    check_lines = [
                        " " * indent + "# Handle both list and dict responses",
                        " " * indent + "if isinstance(scan_data, list):",
                        " " * (indent + 4) + "securities = scan_data",
                        " " * indent + "else:",
                        " " * (indent + 4) + "securities = scan_data.get('securities', [])"
                    ]
                    
                    # Replace the line
                    lines[i] = line.replace("scan_data.get('securities', [])", "securities")
                    
                    # Insert check before current line if not already there
                    if i > 0 and "isinstance(scan_data, list)" not in lines[i-1]:
                        for j, check_line in enumerate(reversed(check_lines)):
                            lines.insert(i, check_line)
            
            content = '\n'.join(lines)
            with open('coordination_service.py', 'w') as f:
                f.write(content)
            print("✅ Applied alternative fix")
                
    except Exception as e:
        print(f"❌ Error fixing coordination service: {e}")

def fix_database_columns():
    """Fix database column names"""
    print("\n🔧 Fixing database column names...")
    
    try:
        # Fix coordination service to use 'port' instead of 'service_port'
        with open('coordination_service.py', 'r') as f:
            content = f.read()
        
        content = content.replace('service_port', 'port')
        
        with open('coordination_service.py', 'w') as f:
            f.write(content)
            
        print("✅ Fixed column references to use 'port'")
        
    except Exception as e:
        print(f"❌ Error fixing columns: {e}")

def add_rate_limit_delay():
    """Add delay to scanner to avoid rate limiting"""
    print("\n🔧 Adding rate limit protection to scanner...")
    
    try:
        with open('security_scanner.py', 'r') as f:
            content = f.read()
        
        # Check if delay already exists
        if 'time.sleep' not in content:
            # Find the scan loop
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'for symbol in' in line and 'watchlist' in line:
                    # Add delay after the for line
                    indent = len(lines[i+1]) - len(lines[i+1].lstrip())
                    lines.insert(i+2, " " * indent + "time.sleep(0.5)  # Rate limit protection")
                    break
            
            content = '\n'.join(lines)
            
            # Also add import if needed
            if 'import time' not in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        continue
                    else:
                        lines.insert(i, 'import time')
                        break
                content = '\n'.join(lines)
            
            with open('security_scanner.py', 'w') as f:
                f.write(content)
                
            print("✅ Added rate limit protection")
        else:
            print("✅ Rate limit protection already exists")
            
    except Exception as e:
        print(f"❌ Error adding rate limit protection: {e}")

def create_mock_scanner():
    """Create a mock scanner for testing without Yahoo Finance"""
    print("\n📝 Creating mock scanner for testing...")
    
    mock_scanner = '''#!/usr/bin/env python3
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
'''
    
    with open('mock_security_scanner.py', 'w') as f:
        f.write(mock_scanner)
    
    print("✅ Created mock_security_scanner.py")
    print("   Use this to test without Yahoo Finance rate limits")

def main():
    print("🚀 Final Trading System Fixes")
    print("="*50)
    
    # Apply fixes
    fix_coordination_service()
    fix_database_columns()
    add_rate_limit_delay()
    create_mock_scanner()
    
    print("\n" + "="*50)
    print("✅ Fixes applied!")
    
    print("\n🎯 Next Steps:")
    print("\n1. Restart coordination service:")
    print("   pkill -f coordination_service.py")
    print("   python coordination_service.py &")
    
    print("\n2. For testing without Yahoo Finance rate limits:")
    print("   pkill -f security_scanner.py")
    print("   python mock_security_scanner.py &")
    
    print("\n3. Test trading cycle:")
    print("   curl -X POST http://localhost:5000/start_trading_cycle")
    
    print("\n4. To use real scanner with delays:")
    print("   pkill -f mock_security_scanner.py")
    print("   python security_scanner.py &")
    
    print("\n💡 The mock scanner will return fake data so you can test")
    print("   the full trading cycle without Yahoo Finance limits!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Name of Service: Find Trade Filter Issue
Filename: find_trade_filter.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Find why trades are filtered out
  - Examines _execute_trades method logic
  - Identifies filtering conditions
  - Shows why signals are rejected

DESCRIPTION:
The paper trading service receives signals but executes 0 trades.
This script finds what conditions are filtering out the trades.
"""

import os
import re

def find_trade_filter():
    """Find why trades are being filtered out"""
    
    print("=" * 60)
    print("FINDING TRADE FILTER ISSUE")
    print("=" * 60)
    
    paper_trading_path = '../paper_trading.py' if os.path.exists('../paper_trading.py') else 'paper_trading.py'
    
    with open(paper_trading_path, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 1. Find _execute_trades method
    print("\n1. ANALYZING _execute_trades METHOD:")
    print("-" * 40)
    
    execute_trades_start = None
    for i, line in enumerate(lines):
        if 'def _execute_trades' in line:
            execute_trades_start = i
            print(f"Found _execute_trades at line {i+1}")
            break
    
    if execute_trades_start:
        # Extract the method (up to next def or class)
        method_lines = []
        indent_level = None
        
        for i in range(execute_trades_start, len(lines)):
            line = lines[i]
            
            # Get initial indent level
            if indent_level is None and line.strip() and not line.strip().startswith('def'):
                indent_level = len(line) - len(line.lstrip())
            
            # Stop at next method/class or dedent
            if i > execute_trades_start and line.strip():
                current_indent = len(line) - len(line.lstrip())
                if current_indent < indent_level or (current_indent == 0 and line.strip()):
                    break
            
            method_lines.append((i+1, line))
        
        # Analyze the method
        print("\nMethod code analysis:")
        
        # Look for key patterns
        for line_num, line in method_lines[:50]:  # First 50 lines
            # Highlight important patterns
            if any(keyword in line for keyword in ['if', 'return', 'continue', 'filter', 'skip']):
                print(f"Line {line_num}: {line.strip()}")
                
                # Check for early returns
                if 'return []' in line or 'return list()' in line:
                    print("  ⚠️  EARLY RETURN: Returns empty list!")
                
                # Check for filtering conditions
                if 'if' in line and any(word in line for word in ['not', 'None', '==', '!=']):
                    print("  ⚠️  FILTER CONDITION: Might filter out signals")
                
                # Check for signal validation
                if 'signal' in line.lower() and 'get' in line:
                    print("  📍 Signal field access")
    
    # 2. Look for validation functions
    print("\n\n2. CHECKING FOR VALIDATION FUNCTIONS:")
    print("-" * 40)
    
    validation_patterns = [
        r'def.*validate.*signal',
        r'def.*check.*signal',
        r'def.*filter.*signal',
        r'if.*signal.*type.*in',
        r'if.*confidence.*[<>=]',
        r'if.*quantity.*[<>=]'
    ]
    
    for pattern in validation_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            print(f"Line {line_num}: {match.group()}")
    
    # 3. Check for required fields
    print("\n\n3. CHECKING SIGNAL FIELD REQUIREMENTS:")
    print("-" * 40)
    
    # Find what fields are accessed from signals
    signal_accesses = re.finditer(r'signal\s*\[\s*[\'"](\w+)[\'"]\s*\]|signal\.get\s*\(\s*[\'"](\w+)[\'"]', content)
    
    required_fields = set()
    for match in signal_accesses:
        field = match.group(1) or match.group(2)
        if field:
            required_fields.add(field)
    
    print("Fields accessed from signals:")
    for field in sorted(required_fields):
        print(f"  - {field}")
    
    # 4. Check for ALPACA_AVAILABLE check
    print("\n\n4. CHECKING FOR ALPACA_AVAILABLE:")
    print("-" * 40)
    
    alpaca_checks = re.finditer(r'if.*ALPACA_AVAILABLE|if.*self\.alpaca_api', content)
    for match in alpaca_checks:
        line_num = content[:match.start()].count('\n') + 1
        line_content = lines[line_num - 1].strip()
        print(f"Line {line_num}: {line_content}")
        
        # Check what happens if false
        if line_num < len(lines) - 5:
            for i in range(1, 6):
                next_line = lines[line_num - 1 + i].strip()
                if 'simulate' in next_line.lower() or 'return' in next_line:
                    print(f"  Line {line_num + i}: {next_line}")
    
    # 5. Test signal format
    print("\n\n5. REQUIRED SIGNAL FORMAT:")
    print("-" * 40)
    
    print("Based on the code analysis, signals should have:")
    print("  - symbol: Stock symbol (e.g., 'AAPL')")
    print("  - signal_type: 'BUY' or 'SELL'")
    
    for field in required_fields:
        if field not in ['symbol', 'signal_type']:
            print(f"  - {field}: Required field")
    
    print("\n\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    print("\n1. Check if signals have all required fields")
    print("2. Look for any validation that rejects signals")
    print("3. Ensure signal_type is exactly 'BUY' or 'SELL' (case sensitive)")
    print("4. Check confidence thresholds or other filters")
    print("5. Verify ALPACA_AVAILABLE is True in the service")
    
    print("\nTo test, try this exact signal format:")
    print("""
{
    "signals": [{
        "symbol": "AAPL",
        "signal_type": "BUY",
        "quantity": 1,
        "confidence": 0.8,
        "reason": "Test trade",
        "current_price": 150.0
    }]
}
""")
    
    print("=" * 60)


if __name__ == "__main__":
    find_trade_filter()

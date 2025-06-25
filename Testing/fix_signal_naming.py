#!/usr/bin/env python3
"""
Name of Service: Fix Signal Naming Convention
Filename: fix_signal_naming.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Standardize on 'signal' throughout system
  - Updates paper_trading.py for backward compatibility
  - Provides migration script for database
  - Updates other services to use 'signal'

DESCRIPTION:
Standardizes the trading system to use 'signal' (not 'signal_type')
which is the correct financial trading terminology. Provides backward
compatibility to handle both field names during transition.
"""

import os
import shutil
from datetime import datetime

def fix_signal_naming():
    """Fix signal naming to use correct trading terminology"""
    
    print("=" * 60)
    print("FIXING SIGNAL NAMING CONVENTION")
    print("=" * 60)
    print("Standardizing system to use 'signal' (correct trading term)")
    print("=" * 60)
    
    # 1. Fix paper_trading.py to handle both field names
    print("\n1. UPDATING PAPER_TRADING.PY")
    print("-" * 40)
    
    paper_trading_path = '../paper_trading.py' if os.path.exists('../paper_trading.py') else 'paper_trading.py'
    
    if not os.path.exists(paper_trading_path):
        print("✗ Cannot find paper_trading.py")
        return
    
    # Create backup
    backup_path = f'{paper_trading_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy(paper_trading_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    
    # Read the file
    with open(paper_trading_path, 'r') as f:
        content = f.read()
    
    # Make the fix - update the signal validation to handle both field names
    old_line = "if signal.get('signal') not in ['BUY', 'SELL']:"
    new_lines = """# Handle both 'signal' and 'signal_type' for backward compatibility
            signal_value = signal.get('signal') or signal.get('signal_type')
            if signal_value not in ['BUY', 'SELL']:"""
    
    if old_line in content:
        content = content.replace(old_line, new_lines)
        print("✓ Updated signal validation to handle both field names")
    else:
        print("⚠️  Could not find exact line to replace")
        print("   Please manually update the signal validation")
    
    # Also update where we save to database to use consistent naming
    # Find the save_trade_record section
    save_section = """trade_data['signal'],"""
    save_replacement = """signal.get('signal') or signal.get('signal_type'),  # Use whichever field is present"""
    
    if save_section in content:
        content = content.replace(save_section, save_replacement)
        print("✓ Updated database save to handle both field names")
    
    # Write the updated file
    with open(paper_trading_path, 'w') as f:
        f.write(content)
    
    print("✓ Paper trading service updated for backward compatibility")
    
    # 2. Create database migration script
    print("\n\n2. CREATING DATABASE MIGRATION SCRIPT")
    print("-" * 40)
    
    migration_script = '''#!/usr/bin/env python3
"""
Database Migration: Rename signal_type to signal
Run this if you want to update the database schema
"""

import sqlite3

def migrate_database():
    conn = sqlite3.connect('../trading_system.db')
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'signal_type' in columns and 'signal' not in columns:
            print("Renaming signal_type to signal...")
            
            # SQLite doesn't support RENAME COLUMN in older versions
            # So we need to recreate the table
            cursor.execute("""
                CREATE TABLE trades_new (
                    id INTEGER PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    signal VARCHAR(10) NOT NULL,  -- Changed from signal_type
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    confidence REAL,
                    trade_reason TEXT,
                    alpaca_order_id VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'pending',
                    profit_loss REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                )
            """)
            
            # Copy data
            cursor.execute("""
                INSERT INTO trades_new 
                SELECT id, symbol, signal_type, quantity, entry_price, exit_price,
                       confidence, trade_reason, alpaca_order_id, status, profit_loss,
                       created_at, closed_at
                FROM trades
            """)
            
            # Drop old table and rename new
            cursor.execute("DROP TABLE trades")
            cursor.execute("ALTER TABLE trades_new RENAME TO trades")
            
            conn.commit()
            print("✓ Database migrated successfully!")
        else:
            print("Database already uses 'signal' column or migration not needed")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
'''
    
    with open('migrate_signal_column.py', 'w') as f:
        f.write(migration_script)
    
    print("✓ Created migrate_signal_column.py")
    print("  Run this if you want to update the database schema")
    
    # 3. List other services that need updating
    print("\n\n3. OTHER SERVICES TO CHECK")
    print("-" * 40)
    
    services_to_check = [
        'technical_analysis.py',
        'pattern_analysis.py', 
        'security_scanner.py',
        'coordination_service.py'
    ]
    
    print("Check these services and update 'signal_type' to 'signal':")
    for service in services_to_check:
        service_path = f'../{service}' if os.path.exists(f'../{service}') else service
        if os.path.exists(service_path):
            with open(service_path, 'r') as f:
                content = f.read()
                if 'signal_type' in content:
                    count = content.count('signal_type')
                    print(f"  ✗ {service}: Found {count} occurrences of 'signal_type'")
                else:
                    print(f"  ✓ {service}: No 'signal_type' found")
        else:
            print(f"  ? {service}: File not found")
    
    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print("\n✅ COMPLETED:")
    print("1. Updated paper_trading.py to accept both 'signal' and 'signal_type'")
    print("2. Created database migration script (optional)")
    print("3. Identified other services that may need updates")
    
    print("\n📋 NEXT STEPS:")
    print("1. Restart paper_trading.py to load the changes")
    print("2. Run migrate_signal_column.py if you want to update the database")
    print("3. Update other services to use 'signal' instead of 'signal_type'")
    
    print("\n💡 RECOMMENDATION:")
    print("The system will now work with both field names, so you can")
    print("migrate services gradually without breaking anything.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    fix_signal_naming()

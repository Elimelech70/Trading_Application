#!/usr/bin/env python3
"""
Database Structure Inspector
Examines the trading database to show all tables and their schemas
"""

import sqlite3
from pathlib import Path

def inspect_database(db_path='./trading_system.db'):
    """Inspect database structure"""
    
    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    print(f"\n🔍 Inspecting database: {db_path}")
    print("="*60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("⚠️  No tables found in database!")
            return
        
        print(f"\n📋 Found {len(tables)} tables:")
        print("-"*60)
        
        for table in tables:
            table_name = table[0]
            print(f"\n📊 Table: {table_name}")
            print("-"*40)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                col_id, name, dtype, not_null, default, is_pk = col
                pk_indicator = " [PRIMARY KEY]" if is_pk else ""
                null_indicator = " NOT NULL" if not_null else ""
                default_str = f" DEFAULT {default}" if default else ""
                print(f"  - {name}: {dtype}{pk_indicator}{null_indicator}{default_str}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\nRow count: {count}")
            
            # Show sample data for small tables
            if count > 0 and count <= 5:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                rows = cursor.fetchall()
                print("\nSample data:")
                for row in rows:
                    print(f"  {row}")
            elif count > 5:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                print("\nSample data (first 3 rows):")
                for row in rows:
                    print(f"  {row}")
        
        # Check for common trading-related tables
        print("\n\n🔎 Checking for common trading tables:")
        print("-"*40)
        
        common_tables = [
            'trades', 'positions', 'orders', 'portfolio', 'portfolio_status',
            'accounts', 'transactions', 'market_data', 'symbols', 'watchlist',
            'trade_history', 'order_history', 'balance_history', 'performance'
        ]
        
        for table_name in common_tables:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            
            exists = cursor.fetchone() is not None
            status = "✅" if exists else "❌"
            print(f"{status} {table_name}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_database()

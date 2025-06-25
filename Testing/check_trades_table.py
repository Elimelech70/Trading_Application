#!/usr/bin/env python3
"""
Name of Service: Check Trades Table Structure
Filename: check_trades_table.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Simple trades table checker
  - Shows exact column names
  - Handles None values properly
  - Checks for sample data

DESCRIPTION:
Simplified script to check the trades table structure
and identify the correct column names.
"""

import sqlite3
import os

# Handle running from Testing folder
db_path = '../trading_system.db' if os.path.exists('../trading_system.db') else './trading_system.db'

def check_trades_table():
    """Check trades table structure"""
    print("=" * 60)
    print("TRADES TABLE STRUCTURE CHECK")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    try:
        # 1. Get column names using a different method
        print("\n1. TRADES TABLE COLUMNS:")
        print("-" * 40)
        
        # Execute a query that returns no rows but gives us column names
        cursor.execute("SELECT * FROM trades WHERE 1=0")
        column_names = [description[0] for description in cursor.description]
        
        print("Columns found:")
        for col in column_names:
            print(f"  - {col}")
        
        # 2. Check which column is the primary key
        print("\n2. CHECKING FOR ID COLUMNS:")
        print("-" * 40)
        
        id_columns = [col for col in column_names if 'id' in col.lower()]
        print(f"Columns containing 'id': {id_columns}")
        
        # 3. Get detailed schema info
        print("\n3. DETAILED COLUMN INFO:")
        print("-" * 40)
        
        cursor.execute("PRAGMA table_info(trades)")
        for row in cursor.fetchall():
            # Handle None values
            col_name = row[1] if row[1] else "NULL"
            col_type = row[2] if row[2] else "NULL"
            not_null = "YES" if row[3] else "NO"
            default = row[4] if row[4] is not None else "NULL"
            pk = "PK" if row[5] else ""
            
            print(f"{col_name:<20} {col_type:<15} NotNull:{not_null:<5} Default:{default:<10} {pk}")
        
        # 4. Count trades
        print("\n4. TRADE COUNT:")
        print("-" * 40)
        
        cursor.execute("SELECT COUNT(*) FROM trades")
        count = cursor.fetchone()[0]
        print(f"Total trades: {count}")
        
        # 5. If there are trades, show a sample
        if count > 0:
            print("\n5. SAMPLE TRADE:")
            print("-" * 40)
            
            cursor.execute("SELECT * FROM trades LIMIT 1")
            row = cursor.fetchone()
            
            for col in column_names:
                value = row[col]
                print(f"{col}: {value}")
        
        # 6. Create correct query for diagnostic
        print("\n6. CORRECT QUERY FOR DIAGNOSTIC:")
        print("-" * 40)
        
        # Find the actual ID column
        actual_id_column = None
        for col in ['id', 'trade_id', 'order_id']:
            if col in column_names:
                actual_id_column = col
                break
        
        if actual_id_column:
            print(f"✓ Found ID column: '{actual_id_column}'")
            print(f"\nUse this query in diagnostic:")
            print(f"SELECT {actual_id_column}, symbol, side, quantity, status,")
            print(f"       alpaca_order_id, created_at")
            print(f"FROM trades")
            print(f"ORDER BY created_at DESC")
        else:
            print("✗ No ID column found!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_trades_table()

#!/usr/bin/env python3
"""
Name of Service: Check Database Schema
Filename: check_db_schema.py
Version: 1.0.0
Last Updated: 2025-06-25
REVISION HISTORY:
v1.0.0 (2025-06-25) - Check actual database schema
  - Shows exact column names in trades table
  - Lists all tables in database
  - Helps identify schema mismatches

DESCRIPTION:
Quick script to check the actual database schema to fix
the "no such column: trade_id" error.
"""

import sqlite3
import os

# Handle running from Testing folder
db_path = '../trading_system.db' if os.path.exists('../trading_system.db') else './trading_system.db'

def check_schema():
    """Check database schema"""
    print("=" * 60)
    print("DATABASE SCHEMA CHECK")
    print("=" * 60)
    print(f"Database: {db_path}")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # List all tables
        print("\n1. ALL TABLES IN DATABASE:")
        print("-" * 40)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check trades table schema
        print("\n2. TRADES TABLE SCHEMA:")
        print("-" * 40)
        cursor.execute("PRAGMA table_info(trades)")
        columns = cursor.fetchall()
        if columns:
            print("Column Name | Type | NotNull | Default | Primary Key")
            print("-" * 50)
            for col in columns:
                print(f"{col[1]:15} | {col[2]:10} | {col[3]:7} | {col[4]:7} | {col[5]}")
        else:
            print("✗ Trades table not found!")
            
        # Check for any trades
        try:
            # Try different possible column names
            for id_col in ['id', 'trade_id', 'order_id']:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM trades")
                    count = cursor.fetchone()[0]
                    print(f"\nTotal trades in table: {count}")
                    
                    if count > 0:
                        cursor.execute(f"SELECT * FROM trades LIMIT 1")
                        row = cursor.fetchone()
                        cols = [desc[0] for desc in cursor.description]
                        print("\nSample trade columns:")
                        for i, col in enumerate(cols):
                            print(f"  {col}: {row[i]}")
                    break
                except:
                    continue
        except Exception as e:
            print(f"Error querying trades: {e}")
            
        # Check for trading_signals table
        print("\n3. CHECKING FOR TRADING_SIGNALS TABLE:")
        print("-" * 40)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trading_signals'")
        if cursor.fetchone():
            print("✓ trading_signals table exists")
            cursor.execute("SELECT COUNT(*) FROM trading_signals")
            count = cursor.fetchone()[0]
            print(f"  Total signals: {count}")
        else:
            print("✗ trading_signals table not found")
            
            # Check for similar tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%signal%'")
            similar = cursor.fetchall()
            if similar:
                print("  Found similar tables:")
                for table in similar:
                    print(f"    - {table[0]}")
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_schema()

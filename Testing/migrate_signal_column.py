#!/usr/bin/env python3
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

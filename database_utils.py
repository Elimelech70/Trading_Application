#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM - DATABASE UTILITIES
Version: 1.0.0
Last Updated: 2025-06-19
REVISION HISTORY:
v1.0.0 (2025-06-19) - Initial implementation to fix database locking issues

Database Utilities - Provides centralized database connection management
with retry logic, WAL mode, and proper error handling to prevent locking issues
"""

import sqlite3
import time
import logging
import os
from contextlib import contextmanager
from typing import Optional, Any, List, Tuple
import threading
import random

# Global lock for database operations
_db_lock = threading.Lock()

class DatabaseManager:
    """Centralized database management with retry logic and WAL mode"""
    
    def __init__(self, db_path: str = '/content/trading_system.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Connection settings for better concurrency
        self.timeout = 30.0  # Increase timeout to 30 seconds
        self.max_retries = 5
        self.retry_delay_base = 0.1  # Base delay in seconds
        self.retry_delay_max = 2.0   # Maximum delay in seconds
        
        # Initialize database with WAL mode
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with WAL mode for better concurrency"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            
            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Optimize for concurrent access
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Database initialized with WAL mode at {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic retry and cleanup"""
        conn = None
        attempt = 0
        
        while attempt < self.max_retries:
            try:
                # Use the global lock for write operations
                with _db_lock:
                    conn = sqlite3.connect(self.db_path, timeout=self.timeout)
                    
                    # Set pragmas for each connection
                    conn.execute("PRAGMA foreign_keys=ON")
                    conn.execute("PRAGMA journal_mode=WAL")
                    
                    # Set row factory for dict-like access
                    conn.row_factory = sqlite3.Row
                    
                    yield conn
                    
                    # Successful completion
                    conn.commit()
                    return
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    attempt += 1
                    if attempt < self.max_retries:
                        # Exponential backoff with jitter
                        delay = min(
                            self.retry_delay_base * (2 ** attempt) + random.uniform(0, 0.1),
                            self.retry_delay_max
                        )
                        self.logger.warning(
                            f"Database locked, retry {attempt}/{self.max_retries} "
                            f"after {delay:.2f}s"
                        )
                        time.sleep(delay)
                    else:
                        self.logger.error(f"Database locked after {self.max_retries} retries")
                        raise
                else:
                    raise
                    
            except Exception as e:
                self.logger.error(f"Database error: {e}")
                if conn:
                    conn.rollback()
                raise
                
            finally:
                if conn:
                    conn.close()
    
    def execute_with_retry(self, query: str, params: Optional[Tuple] = None) -> Optional[sqlite3.Cursor]:
        """Execute a query with automatic retry logic"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
    
    def executemany_with_retry(self, query: str, params_list: List[Tuple]) -> Optional[sqlite3.Cursor]:
        """Execute many queries with automatic retry logic"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor
    
    def fetchone_with_retry(self, query: str, params: Optional[Tuple] = None) -> Optional[sqlite3.Row]:
        """Fetch one row with automatic retry logic"""
        cursor = self.execute_with_retry(query, params)
        return cursor.fetchone() if cursor else None
    
    def fetchall_with_retry(self, query: str, params: Optional[Tuple] = None) -> List[sqlite3.Row]:
        """Fetch all rows with automatic retry logic"""
        cursor = self.execute_with_retry(query, params)
        return cursor.fetchall() if cursor else []
    
    def insert_with_retry(self, table: str, data: dict) -> Optional[int]:
        """Insert data into table with retry logic"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(data.values()))
            return cursor.lastrowid
    
    def update_with_retry(self, table: str, data: dict, where_clause: str, where_params: Tuple) -> int:
        """Update data in table with retry logic"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = tuple(data.values()) + where_params
        
        cursor = self.execute_with_retry(query, params)
        return cursor.rowcount if cursor else 0
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.fetchone_with_retry(query, (table_name,))
        return result is not None
    
    def get_table_info(self, table_name: str) -> List[dict]:
        """Get information about table columns"""
        query = f"PRAGMA table_info({table_name})"
        rows = self.fetchall_with_retry(query)
        return [dict(row) for row in rows] if rows else []
    
    def vacuum_database(self):
        """Vacuum database to optimize performance"""
        try:
            # VACUUM cannot be run within a transaction
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            conn.execute("VACUUM")
            conn.close()
            self.logger.info("Database vacuumed successfully")
        except Exception as e:
            self.logger.error(f"Error vacuuming database: {e}")
    
    def checkpoint_wal(self):
        """Checkpoint WAL to main database file"""
        try:
            with self.get_connection() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self.logger.info("WAL checkpoint completed")
        except Exception as e:
            self.logger.error(f"Error checkpointing WAL: {e}")


# Global database manager instance
_db_manager = None


def get_database_manager(db_path: str = '/content/trading_system.db') -> DatabaseManager:
    """Get or create the global database manager instance"""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    
    return _db_manager


# Convenience functions for backward compatibility
@contextmanager
def get_db_connection(db_path: str = '/content/trading_system.db'):
    """Get a database connection with automatic retry and cleanup"""
    manager = get_database_manager(db_path)
    with manager.get_connection() as conn:
        yield conn


def execute_with_retry(query: str, params: Optional[Tuple] = None, 
                      db_path: str = '/content/trading_system.db') -> Optional[sqlite3.Cursor]:
    """Execute a query with automatic retry logic"""
    manager = get_database_manager(db_path)
    return manager.execute_with_retry(query, params)


def save_with_retry(table: str, data: dict, 
                   db_path: str = '/content/trading_system.db') -> Optional[int]:
    """Save data to table with automatic retry logic"""
    manager = get_database_manager(db_path)
    return manager.insert_with_retry(table, data)


# Example usage for services
class DatabaseServiceMixin:
    """Mixin class for services to use database utilities"""
    
    def __init__(self, db_path: str = '/content/trading_system.db'):
        self.db_manager = get_database_manager(db_path)
        self.db_path = db_path
    
    def save_to_database(self, table: str, data: dict) -> bool:
        """Save data to database with retry logic"""
        try:
            row_id = self.db_manager.insert_with_retry(table, data)
            return row_id is not None
        except Exception as e:
            self.logger.error(f"Error saving to {table}: {e}")
            return False
    
    def update_database(self, table: str, data: dict, 
                       where_clause: str, where_params: Tuple) -> bool:
        """Update database with retry logic"""
        try:
            rows_affected = self.db_manager.update_with_retry(
                table, data, where_clause, where_params
            )
            return rows_affected > 0
        except Exception as e:
            self.logger.error(f"Error updating {table}: {e}")
            return False
    
    def query_database(self, query: str, params: Optional[Tuple] = None) -> List[dict]:
        """Query database with retry logic"""
        try:
            rows = self.db_manager.fetchall_with_retry(query, params)
            return [dict(row) for row in rows] if rows else []
        except Exception as e:
            self.logger.error(f"Error querying database: {e}")
            return []


if __name__ == "__main__":
    # Test the database utilities
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Database Utilities...")
    
    # Initialize database manager
    db_manager = get_database_manager()
    
    # Test connection
    print("\n1. Testing connection with retry...")
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
        tables = cursor.fetchall()
        print(f"   Found {len(tables)} tables")
        for table in tables:
            print(f"   - {table['name']}")
    
    # Test retry logic
    print("\n2. Testing retry logic...")
    try:
        result = db_manager.fetchone_with_retry(
            "SELECT COUNT(*) as count FROM selected_securities"
        )
        if result:
            print(f"   Selected securities count: {result['count']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\nDatabase utilities test completed!")

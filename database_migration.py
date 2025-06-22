#!/usr/bin/env python3
"""
TRADING SYSTEM DATABASE MIGRATION
Service: Database Migration Script
Version: 1.0.5
Last Updated: 2025-06-20

REVISION HISTORY:
- v1.0.6 (2025-06-20) db_path ./trading_database.db
- v1.0.5 (2025-06-20) - Fixed verify_schema connection handling, ensured consistent table naming
- v1.0.4 (2025-06-19) - Enhanced startup coordination and health check improvements  
- v1.0.3 (2025-06-17) - Initial database schema with comprehensive trading tables

This script creates and manages the SQLite database schema for the trading system.
It includes tables for:
- Service coordination and registry
- Security scanning results
- Pattern analysis
- Technical indicators
- ML model predictions
- Strategy evaluations
- Risk metrics
- Orders and executions
- News sentiment analysis
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database_migration')

class DatabaseMigration:
    def __init__(self, db_path='./trading_system.db'):
        self.db_path = './trading_system.db'
        self.tables_created = []
        
    def create_connection(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)
    
    def execute_migration(self):
        """Execute all database migrations"""
        logger.info(f"Starting database migration for {self.db_path}")
        
        try:
            # Create all tables
            self.create_service_coordination_table()
            self.create_scanning_results_table()
            self.create_pattern_analysis_table()
            self.create_technical_indicators_table()
            self.create_ml_predictions_table()
            self.create_strategy_evaluations_table()
            self.create_risk_metrics_table()
            self.create_orders_table()
            self.create_news_sentiment_table()
            
            # Verify schema
            self.verify_schema()
            
            logger.info("Database migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            return False
    
    def create_service_coordination_table(self):
        """Create service coordination table for service registry"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_coordination (
                service_name TEXT PRIMARY KEY,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                status TEXT NOT NULL,
                last_heartbeat TIMESTAMP,
                start_time TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('service_coordination')
        logger.info("Created service_coordination table")
    
    def create_scanning_results_table(self):
        """Create table for security scanner results"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scanning_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                scan_timestamp TIMESTAMP NOT NULL,
                price REAL,
                volume INTEGER,
                change_percent REAL,
                relative_volume REAL,
                market_cap REAL,
                scan_type TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scanning_symbol 
            ON scanning_results(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scanning_timestamp 
            ON scanning_results(scan_timestamp)
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('scanning_results')
        logger.info("Created scanning_results table")
    
    def create_pattern_analysis_table(self):
        """Create table for pattern analysis results"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                confidence REAL,
                entry_price REAL,
                stop_loss REAL,
                target_price REAL,
                timeframe TEXT,
                detection_timestamp TIMESTAMP NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pattern_symbol 
            ON pattern_analysis(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pattern_timestamp 
            ON pattern_analysis(detection_timestamp)
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('pattern_analysis')
        logger.info("Created pattern_analysis table")
    
    def create_technical_indicators_table(self):
        """Create table for technical indicators"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                indicator_name TEXT NOT NULL,
                indicator_value REAL,
                signal TEXT,
                timeframe TEXT,
                calculation_timestamp TIMESTAMP NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_technical_symbol 
            ON technical_indicators(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_technical_indicator 
            ON technical_indicators(indicator_name)
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('technical_indicators')
        logger.info("Created technical_indicators table")
    
    def create_ml_predictions_table(self):
        """Create table for ML model predictions"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT,
                prediction_type TEXT NOT NULL,
                prediction_value REAL,
                confidence REAL,
                features_used TEXT,
                prediction_timestamp TIMESTAMP NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ml_symbol 
            ON ml_predictions(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ml_model 
            ON ml_predictions(model_name)
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('ml_predictions')
        logger.info("Created ml_predictions table")
    
    def create_strategy_evaluations_table(self):
        """Create table for strategy evaluations"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                entry_signal TEXT,
                entry_price REAL,
                stop_loss REAL,
                target_price REAL,
                position_size INTEGER,
                risk_reward_ratio REAL,
                expected_return REAL,
                confidence_score REAL,
                evaluation_timestamp TIMESTAMP NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_strategy_symbol 
            ON strategy_evaluations(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_strategy_name 
            ON strategy_evaluations(strategy_name)
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('strategy_evaluations')
        logger.info("Created strategy_evaluations table")
    
    def create_risk_metrics_table(self):
        """Create table for risk management metrics"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                portfolio_value REAL,
                position_size REAL,
                risk_amount REAL,
                risk_percentage REAL,
                max_positions INTEGER,
                current_positions INTEGER,
                daily_loss_limit REAL,
                current_daily_loss REAL,
                var_95 REAL,
                sharpe_ratio REAL,
                calculation_timestamp TIMESTAMP NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_risk_timestamp 
            ON risk_metrics(calculation_timestamp)
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('risk_metrics')
        logger.info("Created risk_metrics table")
    
    def create_orders_table(self):
        """Create table for orders and executions"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                order_type TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL,
                stop_price REAL,
                status TEXT NOT NULL,
                filled_quantity INTEGER DEFAULT 0,
                average_fill_price REAL,
                commission REAL,
                strategy_name TEXT,
                entry_reason TEXT,
                exit_reason TEXT,
                created_timestamp TIMESTAMP NOT NULL,
                updated_timestamp TIMESTAMP,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_orders_symbol 
            ON orders(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_orders_status 
            ON orders(status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_orders_order_id 
            ON orders(order_id)
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('orders')
        logger.info("Created orders table")
    
    def create_news_sentiment_table(self):
        """Create table for news sentiment analysis"""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_sentiment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                headline TEXT NOT NULL,
                source TEXT,
                article_date TIMESTAMP NOT NULL,
                sentiment_score REAL,
                sentiment_label TEXT,
                relevance_score REAL,
                impact_score REAL,
                analysis_timestamp TIMESTAMP NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_news_symbol 
            ON news_sentiment(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_news_date 
            ON news_sentiment(article_date)
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('news_sentiment')
        logger.info("Created news_sentiment table")
    
    def verify_schema(self):
        """Verify all tables were created successfully"""
        conn = None
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'service_coordination',
                'scanning_results',
                'pattern_analysis',
                'technical_indicators',
                'ml_predictions',
                'strategy_evaluations',
                'risk_metrics',
                'orders',
                'news_sentiment'
            ]
            
            missing_tables = set(expected_tables) - set(existing_tables)
            
            if missing_tables:
                logger.error(f"Missing tables: {missing_tables}")
                return False
            
            logger.info(f"Schema verification successful. Found {len(existing_tables)} tables.")
            logger.info(f"Tables: {', '.join(sorted(existing_tables))}")
            
            # Verify service_coordination table structure
            cursor.execute("PRAGMA table_info(service_coordination)")
            columns = [row[1] for row in cursor.fetchall()]
            logger.info(f"service_coordination columns: {columns}")
            
            return True
            
        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False
        finally:
            if conn:
                conn.close()

def main():
    """Main function to run migration"""
    logger.info("Starting Trading System Database Migration v1.0.5")
    
    # Check if database already exists
    db_path = Path('trading_system.db')
    if db_path.exists():
        logger.warning(f"Database {db_path} already exists. Migration will update schema if needed.")
    
    # Run migration
    migration = DatabaseMigration()
    success = migration.execute_migration()
    
    if success:
        logger.info("Database migration completed successfully!")
        logger.info(f"Created/verified tables: {', '.join(migration.tables_created)}")
    else:
        logger.error("Database migration failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM DATABASE MIGRATION
Filename: database_migration_v106.py
Version: 1.0.6
Last Updated: 2025-06-26
REVISION HISTORY:
v1.0.6 (2025-06-26) - Current directory path standardization and complete schema
  - Updated database path to ./trading_system.db  
  - Updated logs path to ./logs/
  - Added missing tables: trades, positions, portfolio_status, balance_history, transactions, ml_models
  - Enhanced workflow tracking tables with complete implementation
  - Added WAL mode configuration for concurrent access
  - Implemented all 17 tables per Database Schema Documentation v1.0.0
  - Added comprehensive backup and recovery procedures
v1.0.5 (2025-06-20) - Fixed verify_schema connection handling, ensured consistent table naming
v1.0.4 (2025-06-19) - Enhanced startup coordination and health check improvements  
v1.0.3 (2025-06-17) - Initial database schema with comprehensive trading tables

DESCRIPTION:
This script creates and manages the SQLite database schema for the Trading System v3.1.2
in the current directory. It implements the complete 17-table schema documented in 
Trading System Database Schema Documentation v1.0.0.

Tables Created:
- Core Trading: trades, orders, positions, portfolio_status, balance_history, transactions
- Analysis: scanning_results, pattern_analysis, technical_indicators, news_sentiment
- Machine Learning: ml_predictions, ml_models  
- Risk & Strategy: strategy_evaluations, risk_metrics
- System Management: service_coordination, trading_cycles, workflow_tracking, workflow_events, workflow_metrics

Platform: Current directory with persistent storage
Database: SQLite with WAL mode for concurrent access
"""

import sqlite3
import logging
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

# Project Root Configuration  
PROJECT_ROOT = os.path.abspath('.')
DATABASE_PATH = './trading_system.db'
LOGS_PATH = './logs'
BACKUPS_PATH = './backups'

# Version constant for tracking
VERSION = "1.0.6"

# Configure logging for GitHub Codespaces
def setup_logging():
    """Setup logging for GitHub Codespaces environment"""
    # Ensure logs directory exists
    os.makedirs(LOGS_PATH, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{LOGS_PATH}/database_migration.log'),
            logging.StreamHandler()  # Also log to console for Codespaces
        ]
    )
    return logging.getLogger('database_migration')

logger = setup_logging()

class DatabaseMigration:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.project_root = PROJECT_ROOT
        self.tables_created = []
        self.indexes_created = []
        
        # Ensure required directories exist
        self.ensure_directories()
        
        logger.info(f"Database Migration v{VERSION} initialized")
        logger.info(f"Database path: {self.db_path}")
        logger.info(f"Project root: {self.project_root}")
        
    def ensure_directories(self):
        """Create required directory structure in project root"""
        required_dirs = [
            LOGS_PATH,
            BACKUPS_PATH,
            './data',
            './config'
        ]
        
        for directory in required_dirs:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory: {directory}")
    
    def get_connection(self):
        """Get database connection with optimized configuration"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrent access
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA temp_store = MEMORY")
        
        return conn
    
    def backup_database(self):
        """Create timestamped backup of existing database"""
        if not os.path.exists(self.db_path):
            logger.info("No existing database to backup")
            return None
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'{BACKUPS_PATH}/trading_system_backup_{timestamp}.db'
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def create_tables(self):
        """Create all required database tables"""
        logger.info("Creating database tables...")
        
        # Core Trading Tables
        self.create_trades_table()
        self.create_orders_table()
        self.create_positions_table()
        self.create_portfolio_status_table()
        self.create_balance_history_table()
        self.create_transactions_table()
        
        # Analysis Tables
        self.create_scanning_results_table()
        self.create_pattern_analysis_table()
        self.create_technical_indicators_table()
        self.create_news_sentiment_table()
        
        # Machine Learning Tables
        self.create_ml_predictions_table()
        self.create_ml_models_table()
        
        # Risk & Strategy Tables
        self.create_strategy_evaluations_table()
        self.create_risk_metrics_table()
        
        # System Management Tables
        self.create_service_coordination_table()
        self.create_trading_cycles_table()
        self.create_workflow_tracking_table()
        self.create_workflow_events_table()
        self.create_workflow_metrics_table()
        self.create_trading_schedule_config_table()
        
        logger.info(f"Created {len(self.tables_created)} tables")
    
    def create_indexes(self):
        """Create performance indexes"""
        logger.info("Creating database indexes...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        indexes = [
            # Symbol-based indexes
            "CREATE INDEX IF NOT EXISTS idx_scanning_symbol ON scanning_results(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_pattern_symbol ON pattern_analysis(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_technical_symbol ON technical_indicators(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_ml_symbol ON ml_predictions(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_strategy_symbol ON strategy_evaluations(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_news_symbol ON news_sentiment(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)",
            
            # Time-based indexes
            "CREATE INDEX IF NOT EXISTS idx_scanning_timestamp ON scanning_results(scan_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_pattern_timestamp ON pattern_analysis(detection_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_risk_timestamp ON risk_metrics(calculation_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_news_date ON news_sentiment(article_date)",
            "CREATE INDEX IF NOT EXISTS idx_trades_created ON trades(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_portfolio_timestamp ON portfolio_status(timestamp)",
            
            # Lookup indexes
            "CREATE INDEX IF NOT EXISTS idx_technical_indicator ON technical_indicators(indicator_name)",
            "CREATE INDEX IF NOT EXISTS idx_ml_model ON ml_predictions(model_name)",
            "CREATE INDEX IF NOT EXISTS idx_strategy_name ON strategy_evaluations(strategy_name)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_cycle ON workflow_tracking(cycle_id)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                self.indexes_created.append(index_sql.split()[5])  # Extract index name
            except Exception as e:
                logger.error(f"Failed to create index: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"Created {len(self.indexes_created)} indexes")
    
    # Core Trading Tables
    def create_trades_table(self):
        """Create trades table for executed trades and performance tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(10) NOT NULL,
                signal_type VARCHAR(10) NOT NULL,
                quantity INTEGER NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                confidence REAL,
                trade_reason TEXT,
                alpaca_order_id VARCHAR(100),
                status VARCHAR(20) DEFAULT 'pending',
                profit_loss REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                strategy_name VARCHAR(50),
                position_id INTEGER,
                commission REAL DEFAULT 0.0,
                FOREIGN KEY (position_id) REFERENCES positions(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('trades')
        logger.info("Created trades table")
    
    def create_orders_table(self):
        """Create orders table for order management and tracking"""
        conn = self.get_connection()
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
        
        conn.commit()
        conn.close()
        self.tables_created.append('orders')
        logger.info("Created orders table")
    
    def create_positions_table(self):
        """Create positions table for real-time position tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                quantity INTEGER NOT NULL,
                average_cost REAL NOT NULL,
                current_price REAL,
                market_value REAL,
                unrealized_pnl REAL,
                realized_pnl REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('positions')
        logger.info("Created positions table")
    
    def create_portfolio_status_table(self):
        """Create portfolio_status table for historical portfolio tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                total_value REAL NOT NULL,
                cash_balance REAL NOT NULL,
                positions_value REAL NOT NULL,
                daily_pnl REAL,
                total_pnl REAL,
                margin_used REAL DEFAULT 0,
                buying_power REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('portfolio_status')
        logger.info("Created portfolio_status table")
    
    def create_balance_history_table(self):
        """Create balance_history table for cash flow tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                cash_balance REAL NOT NULL,
                change_amount REAL NOT NULL,
                change_reason TEXT,
                transaction_type VARCHAR(20),
                related_trade_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (related_trade_id) REFERENCES trades(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('balance_history')
        logger.info("Created balance_history table")
    
    def create_transactions_table(self):
        """Create transactions table for detailed transaction history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                symbol TEXT,
                transaction_type VARCHAR(20) NOT NULL,
                quantity INTEGER,
                price REAL,
                amount REAL NOT NULL,
                commission REAL DEFAULT 0,
                description TEXT,
                timestamp TIMESTAMP NOT NULL,
                related_order_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (related_order_id) REFERENCES orders(order_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('transactions')
        logger.info("Created transactions table")
    
    def create_scanning_results_table(self):
        """Create scanning_results table for security scanner results"""
        conn = self.get_connection()
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
        
        conn.commit()
        conn.close()
        self.tables_created.append('scanning_results')
        logger.info("Created scanning_results table")
    
    def create_pattern_analysis_table(self):
        """Create pattern_analysis table for technical patterns"""
        conn = self.get_connection()
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
        
        conn.commit()
        conn.close()
        self.tables_created.append('pattern_analysis')
        logger.info("Created pattern_analysis table")
    
    def create_technical_indicators_table(self):
        """Create technical_indicators table for calculated indicators"""
        conn = self.get_connection()
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
        
        conn.commit()
        conn.close()
        self.tables_created.append('technical_indicators')
        logger.info("Created technical_indicators table")
    
    def create_news_sentiment_table(self):
        """Create news_sentiment table for sentiment analysis"""
        conn = self.get_connection()
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
        
        conn.commit()
        conn.close()
        self.tables_created.append('news_sentiment')
        logger.info("Created news_sentiment table")
    
    def create_ml_predictions_table(self):
        """Create ml_predictions table for machine learning predictions"""
        conn = self.get_connection()
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
        
        conn.commit()
        conn.close()
        self.tables_created.append('ml_predictions')
        logger.info("Created ml_predictions table")
    
    def create_ml_models_table(self):
        """Create ml_models table for stored machine learning models"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT UNIQUE NOT NULL,
                model_version TEXT,
                model_type TEXT,
                model_data BLOB,
                training_accuracy REAL,
                validation_accuracy REAL,
                feature_names TEXT,
                hyperparameters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('ml_models')
        logger.info("Created ml_models table")
    
    def create_strategy_evaluations_table(self):
        """Create strategy_evaluations table for trading strategy evaluation"""
        conn = self.get_connection()
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
        
        conn.commit()
        conn.close()
        self.tables_created.append('strategy_evaluations')
        logger.info("Created strategy_evaluations table")
    
    def create_risk_metrics_table(self):
        """Create risk_metrics table for portfolio risk calculations"""
        conn = self.get_connection()
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
        
        conn.commit()
        conn.close()
        self.tables_created.append('risk_metrics')
        logger.info("Created risk_metrics table")
    
    def create_service_coordination_table(self):
        """Create service_coordination table for service registry"""
        conn = self.get_connection()
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
    
    def create_trading_cycles_table(self):
        """Create trading_cycles table for trading cycle tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                securities_scanned INTEGER DEFAULT 0,
                patterns_found INTEGER DEFAULT 0,
                trades_executed INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('trading_cycles')
        logger.info("Created trading_cycles table")
    
    def create_workflow_tracking_table(self):
        """Create workflow_tracking table for detailed workflow phase tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                duration_seconds REAL,
                items_processed INTEGER DEFAULT 0,
                items_succeeded INTEGER DEFAULT 0,
                items_failed INTEGER DEFAULT 0,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('workflow_tracking')
        logger.info("Created workflow_tracking table")
    
    def create_workflow_events_table(self):
        """Create workflow_events table for workflow event logging"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('workflow_events')
        logger.info("Created workflow_events table")
    
    def create_workflow_metrics_table(self):
        """Create workflow_metrics table for aggregated workflow performance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_duration_seconds REAL,
                securities_scanned INTEGER DEFAULT 0,
                patterns_detected INTEGER DEFAULT 0,
                signals_generated INTEGER DEFAULT 0,
                trades_executed INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                error_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('workflow_metrics')
        logger.info("Created workflow_metrics table")
    
    def create_trading_schedule_config_table(self):
        """Create trading_schedule_config table for trading schedule configuration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_schedule_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                config TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        self.tables_created.append('trading_schedule_config')
        logger.info("Created trading_schedule_config table")
    
    def seed_initial_data(self):
        """Populate database with initial configuration data"""
        logger.info("Seeding initial data...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Initial trading schedule configuration
        initial_config = {
            "enabled": False,
            "interval_minutes": 30,
            "market_hours_only": True,
            "start_time": "09:30",
            "end_time": "16:00",
            "timezone": "America/New_York",
            "excluded_days": ["Saturday", "Sunday"],
            "last_run": None,
            "next_run": None
        }
        
        cursor.execute('''
            INSERT OR IGNORE INTO trading_schedule_config (id, config)
            VALUES (1, ?)
        ''', (json.dumps(initial_config),))
        
        conn.commit()
        conn.close()
        logger.info("Initial data seeded")
    
    def verify_schema(self):
        """Verify all tables were created successfully"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'balance_history', 'ml_models', 'ml_predictions', 'news_sentiment',
                'orders', 'pattern_analysis', 'portfolio_status', 'positions',
                'risk_metrics', 'scanning_results', 'service_coordination',
                'strategy_evaluations', 'technical_indicators', 'trades',
                'trading_cycles', 'trading_schedule_config', 'transactions',
                'workflow_events', 'workflow_metrics', 'workflow_tracking'
            ]
            
            missing_tables = set(expected_tables) - set(existing_tables)
            extra_tables = set(existing_tables) - set(expected_tables)
            
            if missing_tables:
                logger.error(f"Missing tables: {missing_tables}")
                return False
            
            if extra_tables:
                logger.warning(f"Extra tables found: {extra_tables}")
            
            logger.info(f"Schema verification successful. Found {len(existing_tables)} tables.")
            logger.info(f"Tables: {', '.join(sorted(existing_tables))}")
            
            # Verify database configuration
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            logger.info(f"Journal mode: {journal_mode}")
            
            cursor.execute("PRAGMA foreign_keys")
            foreign_keys = cursor.fetchone()[0]
            logger.info(f"Foreign keys: {'enabled' if foreign_keys else 'disabled'}")
            
            return True
            
        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_schema_info(self):
        """Return detailed database schema information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        schema_info = {
            'database_path': self.db_path,
            'tables': {},
            'indexes': [],
            'configuration': {}
        }
        
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            schema_info['tables'][table] = [
                {
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'default': col[4],
                    'primary_key': bool(col[5])
                }
                for col in columns
            ]
        
        # Get index information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
        schema_info['indexes'] = [row[0] for row in cursor.fetchall()]
        
        # Get configuration
        pragma_checks = [
            'journal_mode', 'synchronous', 'cache_size', 'foreign_keys', 'temp_store'
        ]
        
        for pragma in pragma_checks:
            cursor.execute(f"PRAGMA {pragma}")
            result = cursor.fetchone()
            schema_info['configuration'][pragma] = result[0] if result else None
        
        conn.close()
        return schema_info
    
    def run_migration(self):
        """Execute complete migration process"""
        logger.info(f"Starting Trading System Database Migration v{VERSION}")
        logger.info(f"Target: Current directory environment")
        logger.info(f"Database: {self.db_path}")
        
        try:
            # Backup existing database
            backup_path = self.backup_database()
            
            # Create tables
            self.create_tables()
            
            # Create indexes
            self.create_indexes()
            
            # Seed initial data
            self.seed_initial_data()
            
            # Verify schema
            if not self.verify_schema():
                raise Exception("Schema verification failed")
            
            logger.info("=" * 60)
            logger.info("DATABASE MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info(f"Tables created: {len(self.tables_created)}")
            logger.info(f"Indexes created: {len(self.indexes_created)}")
            logger.info(f"Database path: {self.db_path}")
            logger.info(f"Backup created: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            return False

def main():
    """Main function to run migration"""
    logger.info("=" * 60)
    logger.info("TRADING SYSTEM DATABASE MIGRATION v1.0.6")
    logger.info("Current Directory Edition")
    logger.info("=" * 60)
    
    # Initialize migration
    migration = DatabaseMigration()
    
    # Run migration
    success = migration.run_migration()
    
    if success:
        logger.info("Database migration completed successfully!")
        logger.info(f"Database ready at: {DATABASE_PATH}")
        logger.info(f"Logs available at: {LOGS_PATH}")
        
        # Display schema info
        schema_info = migration.get_schema_info()
        logger.info(f"Total tables: {len(schema_info['tables'])}")
        logger.info(f"Total indexes: {len(schema_info['indexes'])}")
        
        return 0
    else:
        logger.error("Database migration failed!")
        return 1

if __name__ == "__main__":
    exit(main())
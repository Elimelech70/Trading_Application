# Trading System Functional Specification - Database Schema Addendum

**Name of Service**: TRADING SYSTEM FUNCTIONAL SPECIFICATION - DATABASE SCHEMA ADDENDUM  
**Version**: 1.0.0  
**Last Updated**: 2025-06-24  
**Parent Document**: Trading System Functional Specification v1.1.0  
**Platform**: GitHub Codespaces  

## REVISION HISTORY
- v1.0.0 (2025-06-24) - Initial database schema addendum
  - Complete schema documentation for all 17 tables
  - Integration mapping between services and database tables
  - Cross-reference with service implementations
  - Identified missing portfolio management components
  - Added implementation guidelines and best practices

---

## Executive Summary

This addendum to the Trading System Functional Specification v1.1.0 provides detailed database schema documentation and integration mappings. It documents how each service interacts with the database layer, ensuring data consistency and proper information flow throughout the trading system. The database serves as the central persistence layer for all trading operations, analysis results, and system coordination.

---

## Table of Contents

1. [Integration Overview](#1-integration-overview)
2. [Service-to-Database Mapping](#2-service-to-database-mapping)
3. [Database Schema Reference](#3-database-schema-reference)
4. [Data Flow Patterns](#4-data-flow-patterns)
5. [Implementation Guidelines](#5-implementation-guidelines)
6. [Missing Components Analysis](#6-missing-components-analysis)

---

## 1. Integration Overview

The Trading System database serves as the central data repository for all services defined in the Functional Specification v1.1.0. Each service has specific database interactions:

### Read/Write Patterns
- **Write-Heavy Services**: security_scanner, pattern_analysis, technical_analysis, paper_trading
- **Read-Heavy Services**: reporting_service, web_dashboard_service
- **Mixed Pattern Services**: coordination_service, news_service
- **Schema Management**: database_migration (DDL operations only)

### Connection Strategy
All services use a consistent connection pattern:
```python
def get_connection(self):
    conn = sqlite3.connect(self.db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn
```

---

## 2. Service-to-Database Mapping

### 2.1 coordination_service.py

**Primary Tables**:
- `service_coordination` - Service registry and health status
- `trading_cycles` - Trading cycle orchestration
- `workflow_tracking` - Detailed phase tracking
- `workflow_events` - Event logging
- `workflow_metrics` - Performance metrics

**Database Operations**:
```python
# Service registration
INSERT INTO service_coordination (service_name, host, port, status, last_heartbeat)

# Trading cycle management
INSERT INTO trading_cycles (cycle_id, status, start_time)
UPDATE trading_cycles SET end_time = ?, patterns_found = ?, trades_executed = ?

# Workflow tracking
INSERT INTO workflow_tracking (cycle_id, phase, status, start_time)
UPDATE workflow_tracking SET end_time = ?, items_processed = ?
```

**Data Dependencies**: None (orchestrates other services)

---

### 2.2 security_scanner.py

**Primary Tables**:
- `scanning_results` - Securities meeting criteria

**Secondary Tables** (read):
- `trading_schedule_config` - Schedule configuration

**Database Operations**:
```python
# Store scan results
INSERT INTO scanning_results (
    symbol, scan_timestamp, price, volume, change_percent, 
    relative_volume, market_cap, scan_type, metadata
)

# Retrieve recent scans
SELECT * FROM scanning_results 
WHERE scan_timestamp > datetime('now', '-1 hour')
```

**Data Dependencies**: Feeds into pattern_analysis and technical_analysis

---

### 2.3 pattern_analysis.py

**Primary Tables**:
- `pattern_analysis` - Detected patterns

**Secondary Tables** (read):
- `scanning_results` - Securities to analyze

**Database Operations**:
```python
# Store pattern detections
INSERT INTO pattern_analysis (
    symbol, pattern_type, pattern_name, confidence,
    entry_price, stop_loss, target_price, timeframe,
    detection_timestamp, metadata
)

# Retrieve patterns for signal generation
SELECT * FROM pattern_analysis 
WHERE symbol = ? AND detection_timestamp > ?
```

**Data Dependencies**: 
- Input: scanning_results
- Output: Used by technical_analysis for signal generation

---

### 2.4 technical_analysis.py

**Primary Tables**:
- `technical_indicators` - Calculated indicators
- `ml_predictions` - ML model predictions (if enabled)

**Secondary Tables** (read):
- `pattern_analysis` - Pattern data for signal generation
- `ml_models` - Stored ML models

**Database Operations**:
```python
# Store technical indicators
INSERT INTO technical_indicators (
    symbol, indicator_name, indicator_value, signal,
    timeframe, calculation_timestamp, metadata
)

# Store ML predictions
INSERT INTO ml_predictions (
    symbol, model_name, model_version, prediction_type,
    prediction_value, confidence, features_used, 
    prediction_timestamp
)

# Generate composite signals
SELECT t.*, p.pattern_name, p.confidence as pattern_confidence
FROM technical_indicators t
LEFT JOIN pattern_analysis p ON t.symbol = p.symbol
WHERE t.symbol = ? AND t.signal != 'NEUTRAL'
```

**Data Dependencies**:
- Input: pattern_analysis results
- Output: Trading signals for paper_trading

---

### 2.5 paper_trading.py

**Primary Tables**:
- `trades` - Executed trades
- `orders` - Order management

**Secondary Tables** (write):
- `risk_metrics` - Risk calculations

**Database Operations**:
```python
# Create new trade
INSERT INTO trades (
    symbol, signal_type, quantity, entry_price,
    confidence, trade_reason, alpaca_order_id, status
)

# Create order record
INSERT INTO orders (
    order_id, symbol, order_type, side, quantity,
    price, status, strategy_name, entry_reason
)

# Update trade on exit
UPDATE trades 
SET exit_price = ?, profit_loss = ?, status = 'closed', closed_at = ?
WHERE id = ?

# Update order status
UPDATE orders 
SET status = ?, filled_quantity = ?, average_fill_price = ?
WHERE order_id = ?
```

**Data Dependencies**:
- Input: Signals from technical_analysis
- Output: Trade execution records

---

### 2.6 pattern_recognition_service.py

**Primary Tables**:
- `pattern_analysis` - Advanced pattern storage (same table, different pattern_type)

**Database Operations**:
```python
# Store advanced patterns
INSERT INTO pattern_analysis (
    symbol, pattern_type, pattern_name, confidence,
    entry_price, stop_loss, target_price, timeframe,
    detection_timestamp, metadata
)
VALUES (?, 'advanced', ?, ?, ?, ?, ?, ?, ?, ?)

# Aggregate pattern confidence
SELECT pattern_type, AVG(confidence) as avg_confidence
FROM pattern_analysis
WHERE symbol = ? AND detection_timestamp > ?
GROUP BY pattern_type
```

**Data Dependencies**: Enhances pattern_analysis results

---

### 2.7 news_service.py

**Primary Tables**:
- `news_sentiment` - Sentiment analysis results

**Database Operations**:
```python
# Store sentiment analysis
INSERT INTO news_sentiment (
    symbol, headline, source, article_date,
    sentiment_score, sentiment_label, relevance_score,
    impact_score, analysis_timestamp, metadata
)

# Retrieve recent sentiment
SELECT AVG(sentiment_score) as avg_sentiment,
       COUNT(*) as article_count
FROM news_sentiment
WHERE symbol = ? AND article_date > datetime('now', '-24 hours')
```

**Data Dependencies**: Used by security_scanner for selection criteria

---

### 2.8 reporting_service.py

**Primary Tables** (all read-only):
- All tables for comprehensive analytics

**Key Queries**:
```python
# Daily P&L Summary
SELECT 
    DATE(closed_at) as trade_date,
    COUNT(*) as trades,
    SUM(profit_loss) as daily_pnl,
    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins
FROM trades
WHERE closed_at IS NOT NULL
GROUP BY DATE(closed_at)

# Pattern Effectiveness
SELECT 
    p.pattern_name,
    COUNT(t.id) as trade_count,
    AVG(t.profit_loss) as avg_pnl,
    SUM(CASE WHEN t.profit_loss > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(t.id) as win_rate
FROM pattern_analysis p
JOIN trades t ON p.symbol = t.symbol 
    AND t.created_at BETWEEN p.detection_timestamp AND datetime(p.detection_timestamp, '+1 day')
GROUP BY p.pattern_name

# System Health
SELECT 
    service_name,
    status,
    (julianday('now') - julianday(last_heartbeat)) * 24 * 60 as minutes_since_heartbeat
FROM service_coordination
```

**Data Dependencies**: Reads from all tables

---

### 2.9 database_migration.py

**Primary Tables**: All (DDL operations)

**Schema Operations**:
- CREATE TABLE statements for all tables
- CREATE INDEX statements for performance
- Initial data seeding
- Schema version management

**Key Methods**:
```python
def create_tables(self)
def create_indexes(self)
def seed_initial_data(self)
def verify_schema(self)
def backup_database(self)
```

---

## 3. Database Schema Reference

The complete database schema documentation is maintained in the companion document "Trading System Database Schema Documentation v1.0.0". Key highlights:

### Table Categories
1. **Core Trading**: trades, orders
2. **Analysis**: scanning_results, pattern_analysis, technical_indicators, news_sentiment
3. **Machine Learning**: ml_predictions, ml_models
4. **Risk & Strategy**: strategy_evaluations, risk_metrics
5. **System Management**: service_coordination, trading_cycles, workflow_* tables

### Performance Indexes
- Symbol-based indexes for fast lookups
- Timestamp indexes for time-range queries
- Status indexes for filtering active records

### Data Types
- **Timestamps**: TIMESTAMP type with CURRENT_TIMESTAMP defaults
- **Prices**: REAL type for decimal precision
- **Quantities**: INTEGER for share counts
- **Metadata**: TEXT type storing JSON for flexibility

---

## 4. Data Flow Patterns

### 4.1 Trading Cycle Flow
```
scanning_results → pattern_analysis → technical_indicators → trades/orders
                ↓                  ↓                     ↓
        news_sentiment      ml_predictions        risk_metrics
```

### 4.2 Service Coordination Flow
```
service_coordination ← [heartbeat] ← all services
        ↓
trading_cycles → workflow_tracking → workflow_events → workflow_metrics
```

### 4.3 Analysis Pipeline
```
Market Data → scanning_results
     ↓              ↓
pattern_analysis  news_sentiment
     ↓              ↓
technical_indicators (combined analysis)
     ↓
strategy_evaluations → trades
```

---

## 5. Implementation Guidelines

### 5.1 Connection Management
```python
class ServiceBase:
    def __init__(self, db_path='./trading_system.db'):
        self.db_path = db_path
        self._conn = None
    
    @property
    def conn(self):
        if self._conn is None:
            self._conn = self._get_connection()
        return self._conn
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn
    
    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
```

### 5.2 Transaction Handling
```python
def save_batch_results(self, results):
    """Save multiple results in a single transaction"""
    try:
        with self.conn:  # Auto-commit on success
            cursor = self.conn.cursor()
            cursor.executemany(
                "INSERT INTO scanning_results (...) VALUES (...)",
                results
            )
        return True
    except sqlite3.Error as e:
        logger.error(f"Batch insert failed: {e}")
        return False
```

### 5.3 Error Handling
```python
def safe_query(self, query, params=None):
    """Execute query with error handling"""
    try:
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Query failed: {e}")
        return []
```

### 5.4 Data Validation
```python
def validate_trade_data(self, trade_data):
    """Validate trade data before insertion"""
    required_fields = ['symbol', 'signal_type', 'quantity', 'entry_price']
    
    for field in required_fields:
        if field not in trade_data or trade_data[field] is None:
            raise ValueError(f"Missing required field: {field}")
    
    if trade_data['signal_type'] not in ['BUY', 'SELL']:
        raise ValueError("Invalid signal_type")
    
    if trade_data['quantity'] <= 0:
        raise ValueError("Quantity must be positive")
    
    if trade_data['entry_price'] <= 0:
        raise ValueError("Entry price must be positive")
```

---

## 6. Missing Components Analysis

### 6.1 Portfolio Management Tables (Not Implemented)

**Recommended: positions table**
```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    average_cost REAL NOT NULL,
    current_price REAL,
    market_value REAL,
    unrealized_pnl REAL,
    realized_pnl REAL DEFAULT 0,
    last_updated TIMESTAMP,
    UNIQUE(symbol)
);
```

**Recommended: portfolio_status table**
```sql
CREATE TABLE portfolio_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    total_value REAL NOT NULL,
    cash_balance REAL NOT NULL,
    positions_value REAL NOT NULL,
    daily_pnl REAL,
    total_pnl REAL,
    margin_used REAL DEFAULT 0,
    buying_power REAL
);
```

### 6.2 Impact on Current Implementation

Without dedicated portfolio tables:
1. **P&L Calculation**: Must be computed from trades table
2. **Position Tracking**: Reconstructed from trade history
3. **Cash Management**: Estimated from initial capital and trades
4. **Real-time Valuation**: Not available without current prices

### 6.3 Workarounds in Current System

The reporting_service and P&L report script implement workarounds:
```python
# Estimate portfolio value from trades
initial_capital = 100000  # User-provided
closed_pnl = sum(trade['profit_loss'] for trade in closed_trades)
open_positions_cost = sum(trade['entry_price'] * trade['quantity'] for trade in open_trades)
estimated_portfolio_value = initial_capital + closed_pnl
```

---

## 7. Recommendations

### 7.1 Immediate Improvements
1. **Add position tracking table** for real-time portfolio management
2. **Implement portfolio_status table** for historical tracking
3. **Create balance_history table** for cash flow tracking
4. **Add transaction log** for audit trail

### 7.2 Schema Enhancements
1. **Add foreign key constraints** between related tables
2. **Implement CHECK constraints** for data validation
3. **Standardize timestamp formats** across all tables
4. **Add composite indexes** for common query patterns

### 7.3 Performance Optimization
1. **Implement connection pooling** for high-frequency operations
2. **Use prepared statements** for repeated queries
3. **Schedule regular VACUUM** operations
4. **Monitor slow queries** with EXPLAIN QUERY PLAN

---

**Document Status**: Complete  
**Integration**: Fully mapped with Functional Specification v1.1.0  
**Database Tables**: 17 documented, 10 missing identified  
**Service Mappings**: All 9 services mapped to database operations
# Trading System Database Schema Documentation

**Name of Service**: TRADING SYSTEM DATABASE SCHEMA DOCUMENTATION  
**Version**: 1.0.0  
**Last Updated**: 2025-06-24  
**Platform**: GitHub Codespaces  
**Database**: SQLite (trading_system.db)  

## REVISION HISTORY
- v1.0.0 (2025-06-24) - Initial comprehensive database schema documentation
  - Documented all 17 tables with complete column specifications
  - Added index documentation for performance optimization
  - Identified missing portfolio tracking tables
  - Included data type specifications and constraints
  - Cross-referenced with service implementations

---

## Executive Summary

This document provides comprehensive technical documentation for the Trading System database schema. The database uses SQLite and contains 17 tables that manage trading operations, analysis results, and system coordination. This documentation serves as the authoritative reference for database structure and relationships within the Trading System v3.0 Hybrid Architecture.

---

## Database Overview

### Database Engine
- **Type**: SQLite 3
- **File**: `trading_system.db`
- **Location**: 
  - Development: `./trading_system.db`
  - GitHub Codespaces: `/workspaces/trading-system/trading_system.db`
  - Legacy Colab: `/content/trading_system.db` (deprecated)

### Database Configuration
```sql
PRAGMA journal_mode = WAL;          -- Write-Ahead Logging for concurrency
PRAGMA synchronous = NORMAL;        -- Balance between safety and speed
PRAGMA cache_size = -64000;         -- 64MB cache
PRAGMA foreign_keys = ON;           -- Enforce referential integrity
PRAGMA temp_store = MEMORY;         -- Use memory for temporary tables
```

### Table Categories
1. **Core Trading Tables** (2): trades, orders
2. **Analysis Tables** (4): scanning_results, pattern_analysis, technical_indicators, news_sentiment
3. **Machine Learning Tables** (2): ml_predictions, ml_models
4. **Risk & Strategy Tables** (2): strategy_evaluations, risk_metrics
5. **System Management Tables** (7): service_coordination, trading_cycles, workflow_tracking, workflow_events, workflow_metrics, trading_schedule_config, sqlite_sequence

---

## Table Structures

### 1. Core Trading Tables

#### 1.1 trades
**Purpose**: Stores executed trades and their performance metrics  
**Primary Key**: id  
**Indexes**: None (recommended: symbol, status, created_at)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing trade ID |
| symbol | VARCHAR(10) | NOT NULL | Trading symbol (e.g., AAPL, MSFT) |
| signal_type | VARCHAR(10) | NOT NULL | Trade direction: BUY or SELL |
| quantity | INTEGER | NOT NULL | Number of shares traded |
| entry_price | REAL | NOT NULL | Price at trade entry |
| exit_price | REAL | | Price at trade exit (NULL if position open) |
| confidence | REAL | | Signal confidence score (0.0-1.0) |
| trade_reason | TEXT | | Detailed rationale for trade entry |
| alpaca_order_id | VARCHAR(100) | | Alpaca Paper Trading API order ID |
| status | VARCHAR(20) | DEFAULT 'pending' | Trade status: pending/open/closed/cancelled |
| profit_loss | REAL | | Calculated P&L in dollars |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Trade entry timestamp |
| closed_at | TIMESTAMP | | Trade exit timestamp |

**Row Count**: 0 (as of inspection)

#### 1.2 orders
**Purpose**: Tracks all order submissions and executions  
**Primary Key**: id  
**Indexes**: idx_orders_symbol, idx_orders_status, idx_orders_order_id

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing order ID |
| order_id | TEXT | NOT NULL, UNIQUE | Unique order identifier (UUID or broker ID) |
| symbol | TEXT | NOT NULL | Trading symbol |
| order_type | TEXT | NOT NULL | Order type: MARKET/LIMIT/STOP/STOP_LIMIT |
| side | TEXT | NOT NULL | Order side: BUY or SELL |
| quantity | INTEGER | NOT NULL | Number of shares ordered |
| price | REAL | | Limit price (NULL for market orders) |
| stop_price | REAL | | Stop trigger price |
| status | TEXT | NOT NULL | Order status: pending/filled/partial/cancelled/rejected |
| filled_quantity | INTEGER | DEFAULT 0 | Number of shares executed |
| average_fill_price | REAL | | Average price of execution |
| commission | REAL | | Trading commission charged |
| strategy_name | TEXT | | Name of strategy that generated order |
| entry_reason | TEXT | | Reason for entering position |
| exit_reason | TEXT | | Reason for exiting position |
| created_timestamp | TIMESTAMP | NOT NULL | Order creation time |
| updated_timestamp | TIMESTAMP | | Last status update time |
| metadata | TEXT | | Additional JSON data |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Database record creation |

**Row Count**: 0 (as of inspection)

---

### 2. Analysis Tables

#### 2.1 scanning_results
**Purpose**: Securities identified by the scanner service meeting trading criteria  
**Primary Key**: id  
**Indexes**: idx_scanning_symbol, idx_scanning_timestamp

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing scan ID |
| symbol | TEXT | NOT NULL | Trading symbol scanned |
| scan_timestamp | TIMESTAMP | NOT NULL | When scan was performed |
| price | REAL | | Current market price |
| volume | INTEGER | | Daily trading volume |
| change_percent | REAL | | Daily price change percentage |
| relative_volume | REAL | | Volume relative to average |
| market_cap | REAL | | Market capitalization in dollars |
| scan_type | TEXT | | Type of scan: momentum/value/breakout |
| metadata | TEXT | | Additional JSON data |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 0 (as of inspection)

#### 2.2 pattern_analysis
**Purpose**: Technical patterns detected in price data by pattern analysis services  
**Primary Key**: id  
**Indexes**: idx_pattern_symbol, idx_pattern_timestamp

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing pattern ID |
| symbol | TEXT | NOT NULL | Trading symbol analyzed |
| pattern_type | TEXT | NOT NULL | Pattern category: candlestick/chart/volume |
| pattern_name | TEXT | NOT NULL | Specific pattern: hammer/doji/triangle |
| confidence | REAL | | Pattern confidence score (0.0-1.0) |
| entry_price | REAL | | Suggested entry price |
| stop_loss | REAL | | Recommended stop loss level |
| target_price | REAL | | Price target based on pattern |
| timeframe | TEXT | | Analysis timeframe: 1d/4h/1h |
| detection_timestamp | TIMESTAMP | NOT NULL | When pattern was detected |
| metadata | TEXT | | Additional pattern details JSON |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 0 (as of inspection)

#### 2.3 technical_indicators
**Purpose**: Calculated technical analysis indicators for trading decisions  
**Primary Key**: id  
**Indexes**: idx_technical_symbol, idx_technical_indicator

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing indicator ID |
| symbol | TEXT | NOT NULL | Trading symbol |
| indicator_name | TEXT | NOT NULL | Indicator type: RSI/MACD/BB/SMA |
| indicator_value | REAL | | Calculated indicator value |
| signal | TEXT | | Generated signal: BUY/SELL/NEUTRAL |
| timeframe | TEXT | | Calculation timeframe |
| calculation_timestamp | TIMESTAMP | NOT NULL | When indicator was calculated |
| metadata | TEXT | | Additional calculation details JSON |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 0 (as of inspection)

#### 2.4 news_sentiment
**Purpose**: News sentiment analysis results for market intelligence  
**Primary Key**: id  
**Indexes**: idx_news_symbol, idx_news_date

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing sentiment ID |
| symbol | TEXT | NOT NULL | Trading symbol |
| headline | TEXT | NOT NULL | News article headline |
| source | TEXT | | News source: Yahoo/Reuters/Bloomberg |
| article_date | TIMESTAMP | NOT NULL | Article publication date |
| sentiment_score | REAL | | Sentiment score (-1.0 to 1.0) |
| sentiment_label | TEXT | | Sentiment: positive/negative/neutral |
| relevance_score | REAL | | Relevance to symbol (0.0-1.0) |
| impact_score | REAL | | Expected market impact (0.0-1.0) |
| analysis_timestamp | TIMESTAMP | NOT NULL | When analysis was performed |
| metadata | TEXT | | Additional analysis details JSON |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 0 (as of inspection)

---

### 3. Machine Learning Tables

#### 3.1 ml_predictions
**Purpose**: Predictions from machine learning models  
**Primary Key**: id  
**Indexes**: idx_ml_symbol, idx_ml_model

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing prediction ID |
| symbol | TEXT | NOT NULL | Trading symbol |
| model_name | TEXT | NOT NULL | Model identifier: rf_classifier/gb_regressor |
| model_version | TEXT | | Model version string |
| prediction_type | TEXT | NOT NULL | Prediction type: direction/price/volatility |
| prediction_value | REAL | | Predicted value |
| confidence | REAL | | Prediction confidence (0.0-1.0) |
| features_used | TEXT | | JSON array of feature names |
| prediction_timestamp | TIMESTAMP | NOT NULL | When prediction was made |
| metadata | TEXT | | Additional model details JSON |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 0 (as of inspection)

#### 3.2 ml_models
**Purpose**: Stored machine learning model data  
**Primary Key**: id  
**Indexes**: None

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing model ID |
| model_name | TEXT | NOT NULL | Model identifier |
| model_data | BLOB | | Serialized model (pickle format) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Model creation time |

**Row Count**: 0 (as of inspection)

---

### 4. Risk & Strategy Tables

#### 4.1 strategy_evaluations
**Purpose**: Trading strategy evaluation results  
**Primary Key**: id  
**Indexes**: idx_strategy_symbol, idx_strategy_name

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing evaluation ID |
| symbol | TEXT | NOT NULL | Trading symbol |
| strategy_name | TEXT | NOT NULL | Strategy identifier |
| entry_signal | TEXT | | Signal that triggered entry |
| entry_price | REAL | | Recommended entry price |
| stop_loss | REAL | | Stop loss level |
| target_price | REAL | | Take profit target |
| position_size | INTEGER | | Recommended position size |
| risk_reward_ratio | REAL | | Risk/reward calculation |
| expected_return | REAL | | Expected return percentage |
| confidence_score | REAL | | Strategy confidence (0.0-1.0) |
| evaluation_timestamp | TIMESTAMP | NOT NULL | When evaluation was performed |
| metadata | TEXT | | Additional strategy details JSON |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 0 (as of inspection)

#### 4.2 risk_metrics
**Purpose**: Portfolio risk calculations and limits  
**Primary Key**: id  
**Indexes**: idx_risk_timestamp

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing risk ID |
| symbol | TEXT | | Trading symbol (NULL for portfolio-level) |
| portfolio_value | REAL | | Total portfolio value |
| position_size | REAL | | Position size in dollars |
| risk_amount | REAL | | Dollar amount at risk |
| risk_percentage | REAL | | Percentage of portfolio at risk |
| max_positions | INTEGER | | Maximum allowed positions |
| current_positions | INTEGER | | Current open positions |
| daily_loss_limit | REAL | | Maximum daily loss allowed |
| current_daily_loss | REAL | | Current day's loss |
| var_95 | REAL | | 95% Value at Risk |
| sharpe_ratio | REAL | | Portfolio Sharpe ratio |
| calculation_timestamp | TIMESTAMP | NOT NULL | When metrics were calculated |
| metadata | TEXT | | Additional risk details JSON |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 0 (as of inspection)

---

### 5. System Management Tables

#### 5.1 service_coordination
**Purpose**: Service registry and health tracking  
**Primary Key**: service_name  
**Indexes**: None

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| service_name | TEXT | PRIMARY KEY | Service identifier |
| host | TEXT | NOT NULL | Service host address |
| port | INTEGER | NOT NULL | Service port number |
| status | TEXT | NOT NULL | Service status: running/stopped/error |
| last_heartbeat | TIMESTAMP | | Last successful health check |
| start_time | TIMESTAMP | | Service start timestamp |
| metadata | TEXT | | Additional service info JSON |

**Row Count**: 0 (as of inspection)

#### 5.2 trading_cycles
**Purpose**: Trading cycle execution tracking  
**Primary Key**: id  
**Indexes**: None

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing cycle ID |
| cycle_id | TEXT | NOT NULL | Unique cycle identifier |
| status | TEXT | NOT NULL | Cycle status: running/completed/failed |
| start_time | TIMESTAMP | | Cycle start time |
| end_time | TIMESTAMP | | Cycle completion time |
| securities_scanned | INTEGER | DEFAULT 0 | Number of securities analyzed |
| patterns_found | INTEGER | DEFAULT 0 | Number of patterns detected |
| trades_executed | INTEGER | DEFAULT 0 | Number of trades placed |
| error_count | INTEGER | DEFAULT 0 | Number of errors encountered |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 15 (as of inspection)  
**Sample Data**: Shows completed cycles with minimal activity (0 securities scanned, 0 patterns, 0 trades)

#### 5.3 workflow_tracking
**Purpose**: Detailed workflow phase tracking  
**Primary Key**: id  
**Indexes**: None

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing tracking ID |
| cycle_id | TEXT | NOT NULL | Trading cycle identifier |
| phase | TEXT | NOT NULL | Workflow phase name |
| status | TEXT | NOT NULL | Phase status |
| start_time | TEXT | | Phase start time |
| end_time | TEXT | | Phase end time |
| duration_seconds | REAL | | Phase execution duration |
| items_processed | INTEGER | DEFAULT 0 | Items processed in phase |
| items_succeeded | INTEGER | DEFAULT 0 | Successful item count |
| items_failed | INTEGER | DEFAULT 0 | Failed item count |
| error_message | TEXT | | Error details if failed |
| retry_count | INTEGER | DEFAULT 0 | Number of retry attempts |
| metadata | TEXT | | Additional phase details JSON |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 0 (as of inspection)

#### 5.4 workflow_events
**Purpose**: Workflow event logging  
**Primary Key**: id  
**Indexes**: None

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing event ID |
| cycle_id | TEXT | NOT NULL | Trading cycle identifier |
| phase | TEXT | NOT NULL | Workflow phase name |
| event_type | TEXT | NOT NULL | Event type: start/complete/error |
| event_data | TEXT | | Event details JSON |
| timestamp | TEXT | DEFAULT CURRENT_TIMESTAMP | Event timestamp |

**Row Count**: 0 (as of inspection)

#### 5.5 workflow_metrics
**Purpose**: Aggregated workflow performance metrics  
**Primary Key**: id  
**Indexes**: None

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing metric ID |
| cycle_id | TEXT | NOT NULL | Trading cycle identifier |
| status | TEXT | NOT NULL | Overall cycle status |
| start_time | TEXT | NOT NULL | Cycle start time |
| end_time | TEXT | | Cycle end time |
| total_duration_seconds | REAL | | Total execution time |
| securities_scanned | INTEGER | DEFAULT 0 | Total securities analyzed |
| patterns_detected | INTEGER | DEFAULT 0 | Total patterns found |
| signals_generated | INTEGER | DEFAULT 0 | Total signals created |
| trades_executed | INTEGER | DEFAULT 0 | Total trades placed |
| success_rate | REAL | DEFAULT 0.0 | Overall success percentage |
| error_count | INTEGER | DEFAULT 0 | Total errors encountered |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Record creation time |

**Row Count**: 0 (as of inspection)

#### 5.6 trading_schedule_config
**Purpose**: Trading schedule configuration storage  
**Primary Key**: id  
**Indexes**: None

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Configuration ID |
| config | TEXT | NOT NULL | JSON configuration object |

**Row Count**: 1 (as of inspection)  
**Current Configuration**:
```json
{
  "enabled": false,
  "interval_minutes": 30,
  "market_hours_only": true,
  "start_time": "09:30",
  "end_time": "16:00",
  "timezone": "America/New_York",
  "excluded_days": ["Saturday", "Sunday"],
  "last_run": "2025-06-23T13:15:20.701703",
  "next_run": null
}
```

#### 5.7 sqlite_sequence
**Purpose**: SQLite internal table for AUTOINCREMENT tracking  
**System Table**: Yes

| Column | Type | Description |
|--------|------|-------------|
| name | | Table name with AUTOINCREMENT |
| seq | | Current sequence value |

**Current Value**: trading_cycles sequence at 15

---

## Performance Indexes

The following indexes are created for query optimization:

### Symbol-based Indexes
- `idx_scanning_symbol` on scanning_results(symbol)
- `idx_pattern_symbol` on pattern_analysis(symbol)
- `idx_technical_symbol` on technical_indicators(symbol)
- `idx_ml_symbol` on ml_predictions(symbol)
- `idx_strategy_symbol` on strategy_evaluations(symbol)
- `idx_orders_symbol` on orders(symbol)
- `idx_news_symbol` on news_sentiment(symbol)

### Time-based Indexes
- `idx_scanning_timestamp` on scanning_results(scan_timestamp)
- `idx_pattern_timestamp` on pattern_analysis(detection_timestamp)
- `idx_risk_timestamp` on risk_metrics(calculation_timestamp)
- `idx_news_date` on news_sentiment(article_date)

### Lookup Indexes
- `idx_technical_indicator` on technical_indicators(indicator_name)
- `idx_ml_model` on ml_predictions(model_name)
- `idx_strategy_name` on strategy_evaluations(strategy_name)
- `idx_orders_status` on orders(status)
- `idx_orders_order_id` on orders(order_id)

---

## Missing Components

Based on the inspection, the following tables are missing but commonly found in trading systems:

### Portfolio Management
- **positions** - Real-time position tracking
- **portfolio** - Portfolio value and composition
- **portfolio_status** - Current portfolio state
- **balance_history** - Historical cash balance tracking

### Account Management
- **accounts** - Trading account information
- **transactions** - Detailed transaction history

### Market Data
- **market_data** - Historical price data cache
- **symbols** - Symbol metadata and configuration
- **watchlist** - User-defined watchlists

### Performance Tracking
- **trade_history** - Detailed trade execution history
- **order_history** - Complete order state transitions
- **performance** - Performance metrics and analytics

---

## Data Integrity Considerations

### 1. Foreign Key Relationships
Currently, no foreign key constraints are defined between tables. Recommended relationships:
- orders.symbol → symbols.symbol (when symbols table exists)
- trades.alpaca_order_id → orders.order_id
- pattern_analysis.symbol → scanning_results.symbol
- technical_indicators.symbol → scanning_results.symbol

### 2. Data Consistency
- All timestamps should use consistent format (some tables use TEXT, others TIMESTAMP)
- Symbol names should be normalized (uppercase) across all tables
- Status values should use consistent enumerations

### 3. Missing Constraints
- CHECK constraints for valid ranges (confidence scores 0.0-1.0)
- UNIQUE constraints for natural keys (e.g., symbol+timestamp combinations)
- NOT NULL constraints for critical fields

---

## Usage Notes

### 1. Connection Configuration
```python
conn = sqlite3.connect('trading_system.db', timeout=30.0)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")
```

### 2. Concurrent Access
The database uses WAL mode for better concurrent read access. Writers still serialize.

### 3. Backup Strategy
Regular backups should be performed, especially before schema migrations:
```bash
sqlite3 trading_system.db ".backup trading_system_backup.db"
```

### 4. Performance Optimization
- Use prepared statements for repeated queries
- Batch inserts for bulk data loading
- Regular VACUUM operations to reclaim space
- Monitor query performance with EXPLAIN QUERY PLAN

---

**Document Status**: Complete  
**Tables Documented**: 17 of 17  
**Indexes Documented**: 15  
**Missing Tables Identified**: 10  
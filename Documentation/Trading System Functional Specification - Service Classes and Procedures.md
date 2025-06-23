# Trading System Functional Specification - Service Classes and Procedures

**Name of Service**: TRADING SYSTEM FUNCTIONAL SPECIFICATION - SERVICE CLASSES AND PROCEDURES  
**Version**: 1.1.0 (GitHub Codespaces Edition)  
**Last Updated**: 2025-06-23  
**Platform**: GitHub Codespaces  

## REVISION HISTORY
- v1.1.0 (2025-06-23) - Updated for GitHub Codespaces environment, removed Google Drive/Colab dependencies
- v1.0.0 (2025-06-15) - Initial functional specification documenting all service classes and procedures

---

## Executive Summary

This document provides a comprehensive technical reference for all services in the Trading System v3.0 Hybrid Architecture, now optimized for GitHub Codespaces. It catalogs each service Python file, the classes they contain, their methods/procedures, and describes the high-level functional flows that enable automated trading operations.

**Implementation Note**: The system uses manual mathematical implementations for all technical analysis and pattern detection. While the code includes optional TA-Lib support, the current implementation relies on custom algorithms for RSI, MACD, Bollinger Bands, moving averages, and candlestick pattern recognition.

**Platform Note**: All services are designed to run within the GitHub Codespaces environment with persistent workspace storage, integrated Git version control, and no external cloud storage dependencies.

---

## Table of Contents

1. [Core Trading Services](#1-core-trading-services)
2. [Supporting Services](#2-supporting-services)
3. [Management Services](#3-management-services)
4. [High-Level Functional Flows](#4-high-level-functional-flows)
5. [Service Integration Patterns](#5-service-integration-patterns)

---

## 1. Core Trading Services

### 1.1 coordination_service.py

**Main Class**: `CoordinationService`

**Purpose**: Central orchestrator managing the entire trading workflow and service coordination.

#### Class Methods:
- **`__init__(self, db_path)`**: Initializes coordination service, sets up Flask app and service registry
  - Default db_path: `/workspaces/trading-system/trading_system.db`
- **`_setup_logging(self)`**: Configures logging to `/workspaces/trading-system/logs/coordination_service.log`
- **`_setup_routes(self)`**: Defines REST API endpoints for workflow control
- **`_call_service(self, service_name, endpoint, method, data)`**: HTTP client for inter-service communication
- **`_save_service_registration(self, service_name, port)`**: Persists service registration to database
- **`_start_trading_cycle_record(self, cycle_id)`**: Creates new trading cycle record in database
- **`_update_cycle_progress(self, cycle_id, **kwargs)`**: Updates trading cycle progress metrics
- **`_complete_trading_cycle(self, cycle_id)`**: Marks trading cycle as completed
- **`_get_recent_cycles(self)`**: Retrieves recent trading cycle history
- **`run(self)`**: Starts Flask web server on port 5000

#### Key REST Endpoints:
- **`/health`**: Service health check
- **`/register_service`**: Service registration endpoint
- **`/start_trading_cycle`**: Initiates complete trading workflow
- **`/service_status`**: Returns registered service status
- **`/trading_cycles`**: Returns recent trading cycle history

#### High-Level Function - Trading Cycle Orchestration:
1. **Cycle Initialization**: Creates unique cycle ID and database record
2. **Security Scanning**: Calls security scanner to identify trading candidates
3. **Pattern Analysis**: Requests pattern analysis for each security
4. **Signal Generation**: Calls technical analysis to generate trading signals
5. **Trade Execution**: Submits signals to paper trading service
6. **Cycle Completion**: Updates database with final results and metrics

---

### 1.2 security_scanner.py

**Main Class**: `SecurityScannerService`

**Purpose**: Scans market for securities meeting predefined trading criteria.

#### Class Methods:
- **`__init__(self, db_path)`**: Initializes scanner with trading criteria and database connection
- **`_setup_logging(self)`**: Configures logging to `/workspaces/trading-system/logs/security_scanner_service.log`
- **`_setup_routes(self)`**: Defines REST API endpoints for scanning operations
- **`_register_with_coordination(self)`**: Registers service with coordination service
- **`_scan_securities(self)`**: Main scanning logic that evaluates watchlist securities
- **`_get_watchlist(self)`**: Returns list of symbols to analyze
- **`_analyze_security(self, symbol)`**: Performs detailed analysis of individual security
- **`_meets_criteria(self, security)`**: Evaluates if security meets trading criteria
- **`_get_news_sentiment(self, symbol)`**: Retrieves sentiment analysis from news service
- **`_save_selected_security(self, security_data)`**: Persists selected security to database
- **`run(self)`**: Starts Flask web server on port 5001

#### Key REST Endpoints:
- **`/health`**: Service health check
- **`/scan_securities`**: Main scanning endpoint
- **`/criteria`**: Get/update trading criteria

#### High-Level Function - Security Selection:
1. **Watchlist Evaluation**: Iterates through predefined symbol list
2. **Market Data Retrieval**: Fetches current and historical price/volume data
3. **Criteria Assessment**: Applies trading rules (price range, volume, momentum)
4. **Sentiment Integration**: Incorporates news sentiment analysis
5. **Selection Persistence**: Saves qualifying securities to database with selection rationale

---

### 1.3 pattern_analysis.py

**Main Class**: `PatternAnalysisService`

**Purpose**: Detects technical patterns in price data using manual calculation methods and pattern recognition algorithms.

#### Class Methods:
- **`__init__(self, db_path)`**: Initializes pattern analysis with manual pattern detection
- **`_setup_logging(self)`**: Configures logging to `/workspaces/trading-system/logs/pattern_analysis_service.log`
- **`_setup_routes(self)`**: Defines REST API endpoints for pattern analysis
- **`_register_with_coordination(self)`**: Registers service with coordination service
- **`_analyze_patterns(self, symbol)`**: Main pattern analysis orchestrator
- **`_get_historical_data(self, symbol, period)`**: Retrieves market data for analysis
- **`_detect_basic_patterns_fallback(self, symbol, data)`**: Manual pattern detection using price movement analysis
- **`_detect_basic_patterns_talib(self, symbol, data)`**: Optional TA-Lib patterns (not used in current implementation)
- **`_get_enhanced_patterns(self, symbol)`**: Calls pattern recognition service for advanced patterns
- **`_calculate_confidence(self, patterns)`**: Computes overall pattern confidence score
- **`_save_pattern_analysis(self, symbol, analysis_data)`**: Persists analysis to database
- **`_get_supported_patterns(self)`**: Returns list of supported pattern types
- **`run(self)`**: Starts Flask web server on port 5002

#### Key REST Endpoints:
- **`/health`**: Service health check
- **`/analyze_patterns/<symbol>`**: Main pattern analysis endpoint
- **`/supported_patterns`**: Lists available pattern types

#### High-Level Function - Pattern Detection:
1. **Data Acquisition**: Retrieves 30-day historical price data
2. **Manual Pattern Analysis**: Applies mathematical pattern detection algorithms (Doji, Hammer, Shooting Star, trend analysis)
3. **Price Movement Analysis**: Analyzes body-to-shadow ratios, trend slopes, and momentum indicators
4. **Enhanced Pattern Integration**: Calls advanced pattern recognition service
5. **Confidence Scoring**: Calculates weighted confidence based on pattern strength
6. **Result Compilation**: Combines all patterns with metadata and saves to database

---

### 1.4 technical_analysis.py

**Main Class**: `TechnicalAnalysisService`

**Purpose**: Generates BUY/SELL/HOLD trading signals using manual technical indicator calculations and rule-based analysis.

#### Class Methods:
- **`__init__(self, db_path)`**: Initializes technical analysis with manual indicator calculations
- **`_init_ml_models(self)`**: Sets up RandomForest and GradientBoosting models if scikit-learn available
- **`_setup_logging(self)`**: Configures logging to `/workspaces/trading-system/logs/technical_analysis_service.log`
- **`_setup_routes(self)`**: Defines REST API endpoints for signal generation
- **`_register_with_coordination(self)`**: Registers service with coordination service
- **`_generate_signals(self, securities_with_patterns)`**: Main signal generation orchestrator
- **`_analyze_single_security(self, security)`**: Analyzes individual security for trading signals
- **`_get_market_data(self, symbol)`**: Retrieves market data for indicator calculation
- **`_calculate_indicators_manual(self, data)`**: Manual calculation of RSI, MACD, Bollinger Bands, moving averages
- **`_calculate_indicators_talib(self, data)`**: Optional TA-Lib indicators (not used in current implementation)
- **`_generate_rule_based_signal(self, symbol, indicators, patterns)`**: Applies trading rules to generate signals
- **`_save_trading_signal(self, symbol, signal_data)`**: Persists trading signal to database
- **`run(self)`**: Starts Flask web server on port 5003

#### Key REST Endpoints:
- **`/health`**: Service health check with ML/scikit-learn availability
- **`/generate_signals`**: Main signal generation endpoint
- **`/analyze/<symbol>`**: Single symbol analysis endpoint

#### High-Level Function - Signal Generation:
1. **Market Data Processing**: Retrieves and validates price/volume data
2. **Manual Technical Indicator Calculation**: Computes RSI using delta analysis, MACD using EMA calculations, Bollinger Bands using standard deviation, and moving averages
3. **Pattern Integration**: Incorporates pattern analysis results
4. **Rule-Based Analysis**: Applies scoring algorithm based on indicator convergence and thresholds
5. **Signal Classification**: Determines BUY/SELL/HOLD with confidence level based on combined indicator signals
6. **Signal Persistence**: Saves signals to database with supporting rationale

---

### 1.5 paper_trading.py

**Main Class**: `PaperTradingService`

**Purpose**: Executes trades using Alpaca Paper Trading API or simulation mode.

#### Class Methods:
- **`__init__(self, db_path)`**: Initializes paper trading with Alpaca API configuration
- **`_setup_alpaca_api(self)`**: Establishes connection to Alpaca Paper Trading API
  - API credentials stored in Codespaces secrets or .env file
- **`_setup_logging(self)`**: Configures logging to `/workspaces/trading-system/logs/paper_trading_service.log`
- **`_setup_routes(self)`**: Defines REST API endpoints for trade execution
- **`_register_with_coordination(self)`**: Registers service with coordination service
- **`_execute_trades(self, trading_signals)`**: Main trade execution orchestrator
- **`_execute_single_trade(self, signal)`**: Executes individual trade via Alpaca API
- **`_simulate_trade_execution(self, signal)`**: Simulates trade when API unavailable
- **`_save_trade_record(self, trade_data)`**: Persists trade record to database
- **`_get_account_info(self)`**: Retrieves account balance and status
- **`_get_positions(self)`**: Returns current portfolio positions
- **`run(self)`**: Starts Flask web server on port 5005

#### Key REST Endpoints:
- **`/health`**: Service health check with Alpaca connection status
- **`/execute_trades`**: Main trade execution endpoint
- **`/account`**: Account information endpoint
- **`/positions`**: Current positions endpoint

#### High-Level Function - Trade Execution:
1. **Signal Processing**: Validates incoming trading signals
2. **Account Verification**: Checks available buying power and account status
3. **Price Discovery**: Retrieves current market price for each symbol
4. **Order Placement**: Submits market orders via Alpaca Paper Trading API
5. **Trade Recording**: Saves execution details to database
6. **Portfolio Tracking**: Updates position and P&L calculations

---

## 2. Supporting Services

### 2.1 pattern_recognition_service.py

**Main Class**: `PatternRecognitionService`

**Purpose**: Advanced pattern detection using ML techniques and comprehensive technical analysis.

#### Class Methods:
- **`__init__(self, db_path)`**: Initializes advanced pattern recognition
- **`_setup_logging(self)`**: Configures logging to `/workspaces/trading-system/logs/pattern_recognition_service.log`
- **`_setup_routes(self)`**: Defines REST API endpoints for advanced pattern detection
- **`_register_with_coordination(self)`**: Registers service with coordination service
- **`_detect_advanced_patterns(self, symbol)`**: Main advanced pattern detection orchestrator
- **`_get_market_data(self, symbol, period)`**: Retrieves extended market data
- **`_detect_candlestick_patterns(self, symbol, data)`**: Manual candlestick pattern detection using price analysis algorithms
- **`_detect_chart_patterns(self, symbol, data)`**: Support/resistance and trend pattern detection
- **`_detect_volume_patterns(self, symbol, data)`**: Volume-based pattern analysis
- **`_calculate_obv(self, prices, volumes)`**: On-Balance Volume calculation
- **`_calculate_pattern_score(self, candlestick, chart, volume)`**: Weighted pattern scoring
- **`_save_pattern_analysis(self, analysis_data)`**: Persists advanced patterns to database
- **`run(self)`**: Starts Flask web server on port 5006

#### Key REST Endpoints:
- **`/health`**: Service health check
- **`/detect_advanced_patterns/<symbol>`**: Main advanced pattern endpoint
- **`/candlestick_patterns/<symbol>`**: Candlestick pattern analysis
- **`/chart_patterns/<symbol>`**: Chart pattern analysis

#### High-Level Function - Advanced Pattern Recognition:
1. **Extended Data Analysis**: Analyzes multiple timeframes and extended history
2. **Multi-Dimensional Pattern Detection**: Combines candlestick, chart, and volume patterns
3. **Pattern Validation**: Cross-validates patterns using multiple techniques
4. **Confidence Scoring**: Applies weighted scoring across pattern categories
5. **Pattern Persistence**: Saves comprehensive pattern analysis with metadata

---

### 2.2 news_service.py

**Main Class**: `NewsService`

**Purpose**: Provides sentiment analysis of news articles using NLP techniques.

#### Class Methods:
- **`__init__(self, db_path)`**: Initializes news service with sentiment analysis capabilities
- **`_setup_logging(self)`**: Configures logging to `/workspaces/trading-system/logs/news_service.log`
- **`_setup_routes(self)`**: Defines REST API endpoints for sentiment analysis
- **`_register_with_coordination(self)`**: Registers service with coordination service
- **`_analyze_news_sentiment(self, symbol)`**: Main sentiment analysis orchestrator
- **`_analyze_text_sentiment(self, text)`**: Multi-method text sentiment analysis
- **`_keyword_based_sentiment(self, text)`**: Financial keyword sentiment analysis
- **`_save_sentiment_analysis(self, sentiment_data)`**: Persists sentiment data to database
- **`run(self)`**: Starts Flask web server on port 5008

#### Key REST Endpoints:
- **`/health`**: Service health check
- **`/news_sentiment/<symbol>`**: Sentiment analysis for specific symbol
- **`/bulk_news_sentiment`**: Bulk sentiment analysis endpoint

#### High-Level Function - News Sentiment Analysis:
1. **News Retrieval**: Fetches recent news articles via Yahoo Finance API
2. **Content Processing**: Extracts and cleans article titles and summaries
3. **Sentiment Analysis**: Applies TextBlob and keyword-based sentiment scoring
4. **Sentiment Aggregation**: Calculates weighted average sentiment scores
5. **Sentiment Classification**: Assigns positive/negative/neutral labels with confidence

---

### 2.3 reporting_service.py

**Main Class**: `ReportingService`

**Purpose**: Generates comprehensive trading analytics, performance reports, and system health metrics.

#### Class Methods:
- **`__init__(self, db_path)`**: Initializes reporting service with database analytics
- **`_setup_logging(self)`**: Configures logging to `/workspaces/trading-system/logs/reporting_service.log`
- **`_setup_routes(self)`**: Defines REST API endpoints for various reports
- **`_register_with_coordination(self)`**: Registers service with coordination service
- **`_generate_daily_summary(self)`**: Creates daily trading activity summary
- **`_analyze_pattern_effectiveness(self)`**: Analyzes which patterns generate best returns
- **`_generate_performance_report(self, days)`**: Creates comprehensive performance analytics
- **`_analyze_trading_cycles(self)`**: Analyzes trading cycle efficiency and success rates
- **`_generate_system_health_report(self)`**: Creates system and service health report
- **`run(self)`**: Starts Flask web server on port 5009

#### Key REST Endpoints:
- **`/health`**: Service health check
- **`/daily_summary`**: Daily trading summary report
- **`/pattern_effectiveness`**: Pattern performance analysis
- **`/trading_performance`**: Comprehensive performance report
- **`/system_health`**: System health and service status
- **`/cycle_analysis`**: Trading cycle analysis

#### High-Level Function - Performance Analytics:
1. **Data Aggregation**: Collects trading data across multiple timeframes
2. **Performance Calculation**: Computes win rates, P&L, Sharpe ratios, drawdowns
3. **Pattern Analysis**: Evaluates effectiveness of different trading patterns
4. **System Monitoring**: Tracks service health and system performance metrics
5. **Report Generation**: Creates formatted reports for stakeholder consumption

---

## 3. Management Services

### 3.1 database_migration.py

**Main Class**: `DatabaseMigration`

**Purpose**: Manages database schema creation, migrations, and initial data seeding.

#### Class Methods:
- **`__init__(self, db_path)`**: Initializes database migration handler
  - Default path: `/workspaces/trading-system/trading_system.db`
- **`ensure_directories(self)`**: Creates required directory structure in workspace
- **`get_connection(self)`**: Returns SQLite connection with foreign keys enabled
- **`create_tables(self)`**: Creates all required database tables
- **`seed_initial_data(self)`**: Populates database with initial configuration data
- **`backup_database(self)`**: Creates timestamped database backups in `/workspaces/trading-system/backups/`
- **`verify_schema(self)`**: Validates that all required tables exist
- **`get_schema_info(self)`**: Returns detailed database schema information
- **`run_migration(self)`**: Executes complete migration process
- **`main(self)`**: Command-line entry point for migration

#### High-Level Function - Database Initialization:
1. **Schema Creation**: Creates all required tables with proper relationships
2. **Index Creation**: Adds performance indexes for key queries
3. **Initial Data Seeding**: Populates service registry and configuration tables
4. **Backup Creation**: Creates safety backup before any migrations (stored in workspace)
5. **Schema Validation**: Verifies database integrity after migration

---

### 3.2 hybrid_manager.py

**Main Class**: Multiple classes in hybrid_components package

**Purpose**: Automated service lifecycle management optimized for GitHub Codespaces.

#### Main Classes:
- **`HybridServiceManager`**: Primary service orchestrator
- **`LifecycleManager`**: Service start/stop/restart management
- **`RecoveryManager`**: Checkpoint and recovery functionality  
- **`MonitoringEngine`**: Health monitoring and auto-restart
- **`ConfigurationManager`**: System and service configuration

#### Key Methods (HybridServiceManager):
- **`__init__(self, config)`**: Initializes hybrid manager with configuration
  - Config path: `/workspaces/trading-system/config/`
- **`start(self, recovery_mode)`**: Starts complete trading system
- **`stop(self)`**: Graceful shutdown of all services
- **`restart_service(self, service_name)`**: Restarts specific service
- **`get_status(self)`**: Returns comprehensive system status
- **`_run_database_migration(self)`**: Executes database setup
- **`_save_checkpoint(self)`**: Saves system state to workspace (Git-tracked)
- **`_load_checkpoint(self)`**: Loads previous system state

#### High-Level Function - System Management:
1. **Service Orchestration**: Starts services in dependency order
2. **Health Monitoring**: Continuously monitors service health via HTTP endpoints
3. **Auto-Recovery**: Automatically restarts failed services with exponential backoff
4. **State Persistence**: Saves system checkpoints to workspace for recovery
5. **Resource Management**: Manages subprocess lifecycle and resource cleanup

---

## 4. High-Level Functional Flows

### 4.1 Complete Trading Cycle Flow

**Orchestrator**: CoordinationService

**Flow Steps**:
1. **Cycle Initiation** → CoordinationService creates unique cycle ID
2. **Security Selection** → SecurityScannerService identifies trading candidates  
3. **Pattern Analysis** → PatternAnalysisService detects technical patterns
4. **Signal Generation** → TechnicalAnalysisService creates trading signals
5. **Trade Execution** → PaperTradingService executes trades via Alpaca API
6. **Cycle Completion** → CoordinationService updates final metrics

**Data Flow**: Database → Services → Database (with HTTP REST API communication)
**Storage**: All data persisted in `/workspaces/trading-system/trading_system.db`

---

### 4.2 System Startup Flow

**Orchestrator**: HybridServiceManager

**Flow Steps**:
1. **Environment Setup** → Validates GitHub Codespaces workspace structure
2. **Database Migration** → Ensures schema is current
3. **Configuration Loading** → Loads service and system configurations from workspace
4. **Service Startup** → Starts services in dependency order with health checks
5. **Registration** → Services register with coordination service
6. **Monitoring Activation** → Begins health monitoring and checkpoint saving

**Workspace Requirements**: Persistent storage in `/workspaces/trading-system/`

---

### 4.3 Pattern Analysis Flow

**Orchestrator**: PatternAnalysisService

**Flow Steps**:
1. **Data Acquisition** → Retrieves 30-day price/volume history
2. **Manual Pattern Detection** → Applies mathematical pattern recognition algorithms
3. **Advanced Pattern Integration** → Calls PatternRecognitionService
4. **Confidence Calculation** → Weighted scoring across pattern types
5. **Result Persistence** → Saves comprehensive analysis to database

---

### 4.4 Trade Execution Flow

**Orchestrator**: PaperTradingService

**Flow Steps**:
1. **Signal Validation** → Verifies signal format and requirements
2. **Account Verification** → Checks buying power and account status
3. **Price Discovery** → Retrieves current market prices
4. **Order Placement** → Submits market orders via Alpaca Paper API
5. **Trade Recording** → Persists execution details and updates portfolio

**API Credentials**: Stored in Codespaces secrets or .env file

---

## 5. Service Integration Patterns

### 5.1 Service Registration Pattern
All services register with CoordinationService on startup, providing:
- Service name and port
- Health check endpoint
- Version information
- Dependency requirements

### 5.2 REST API Communication Pattern
Services communicate via HTTP REST APIs with:
- JSON request/response format
- Standardized error handling
- Timeout configuration
- Retry logic for critical operations

### 5.3 Database Integration Pattern
All services share SQLite database with:
- Connection pooling
- Transaction management
- Foreign key relationships
- Indexed queries for performance
- WAL mode for concurrent access

### 5.4 Health Monitoring Pattern
HybridServiceManager monitors services via:
- Process status checks
- HTTP health endpoint validation
- Restart policies with exponential backoff
- Critical vs non-critical service designation

### 5.5 Error Handling Pattern
Services implement consistent error handling:
- Structured logging with levels
- Graceful degradation for non-critical failures
- Error propagation to coordination service
- Recovery mechanisms for transient failures

### 5.6 GitHub Codespaces Integration Pattern
All services utilize Codespaces features:
- Persistent workspace storage (no external drives)
- Integrated terminal for service management
- VS Code debugging capabilities
- Git-based version control for configurations
- Environment variables via Codespaces secrets

---

**Document Status**: Complete Technical Reference - GitHub Codespaces Edition  
**Coverage**: All 9 services with detailed class and method documentation  
**Integration**: Comprehensive functional flow documentation for GitHub Codespaces environment  
**Storage**: All data persisted in `/workspaces/trading-system/` workspace
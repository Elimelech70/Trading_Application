#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM COORDINATION SERVICE
Filename: coordination_service_v108.py
Version: 1.0.8
Last Updated: 2025-06-26
REVISION HISTORY:
v1.0.8 (2025-06-26) - Enhanced version combining v107 features with database improvements
  - Retained all critical endpoints from v107: /force_register_all, /latest_cycle, /schedule/config
  - Added comprehensive database retry logic with exponential backoff
  - Implemented WAL mode configuration for better concurrent access
  - Enhanced workflow tracking with events and metrics tables
  - Added database schema validation on startup
  - Improved error handling and recovery mechanisms
  - Maintained backward compatibility with dual registration endpoints
  - Combined robust path handling from v107 with database utilities from architecture
v1.0.7 (2025-06-23) - Fixed endpoint naming for web dashboard compatibility
v1.0.6 (2025-06-22) - Made paths environment-agnostic, works in any directory
v1.0.5 (2025-06-22) - Fixed schema mismatch: use host/port from service_coordination table
v1.0.4 (2025-06-20) - Fixed table name mismatch (use service_coordination not service_registry)
v1.0.3 (2025-06-19) - Added trading schedule endpoints for automated trading
v1.0.2 (2025-06-19) - Enhanced with persistent registration and auto-registration
v1.0.1 (2025-06-11) - Implemented database utilities for retry logic
v1.0.0 (2025-06-11) - Initial release with standardized authentication

DESCRIPTION:
Central orchestrator for all trading system services implementing Enhanced Hybrid
Microservices Architecture v3.1.2. Combines robust database operations with
comprehensive workflow tracking and maintains full backward compatibility.

Key Features:
- Service registry with health monitoring and force registration
- Trading cycle orchestration with comprehensive workflow tracking
- Advanced scheduled trading with flexible configuration
- Database operations with automatic retry logic and WAL mode
- Comprehensive error handling and recovery mechanisms
- Full backward compatibility with existing endpoints

Platform: Environment-agnostic with robust path handling
Database: ./trading_system.db with WAL mode for concurrent access
Port: 5000 (coordination service)
"""

import os
import requests
import logging
import sqlite3
import threading
import json
import time
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from typing import Dict, List, Optional
from pathlib import Path

# Version constant
VERSION = "1.0.8"

# Try to import database utilities (maintain compatibility)
try:
    from database_utils import DatabaseManager, DatabaseServiceMixin as ExternalDBMixin
    USE_EXTERNAL_DB_UTILS = True
except ImportError:
    USE_EXTERNAL_DB_UTILS = False
    print("Warning: database_utils not found. Using built-in database utilities.")

class DatabaseServiceMixin:
    """Built-in database operations mixin with automatic retry logic"""
    
    def get_db_connection(self, retries=5, timeout=30):
        """Get database connection with retry logic and WAL mode"""
        for attempt in range(retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=timeout)
                conn.row_factory = sqlite3.Row
                
                # Enable WAL mode for better concurrent access
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA temp_store = MEMORY")
                
                return conn
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < retries - 1:
                    wait_time = (2 ** attempt) * 0.1  # Exponential backoff
                    self.logger.warning(f"Database locked, retrying in {wait_time}s (attempt {attempt + 1}/{retries})")
                    time.sleep(wait_time)
                else:
                    raise
    
    def execute_with_retry(self, query, params=None, retries=5):
        """Execute query with automatic retry on lock"""
        for attempt in range(retries):
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    conn.commit()
                    result = cursor.rowcount
                else:
                    result = cursor.fetchall()
                
                conn.close()
                return result
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < retries - 1:
                    wait_time = (2 ** attempt) * 0.1
                    self.logger.warning(f"Query failed due to lock, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Query failed after {retries} attempts: {e}")
                    raise

class CoordinationService(DatabaseServiceMixin):
    def __init__(self, port=5000, db_path=None):
        self.app = Flask(__name__)
        self.port = port
        
        # Environment-agnostic paths (from v107)
        if db_path is None:
            self.db_path = str(Path('./trading_system.db').resolve())
        else:
            self.db_path = str(Path(db_path).resolve())
            
        self.logger = self._setup_logging()
        
        # Initialize database utilities if available
        if USE_EXTERNAL_DB_UTILS:
            self.db_manager = DatabaseManager(self.db_path)
            self.logger.info("Using external database utilities")
        else:
            self.logger.info("Using built-in database utilities")
        
        # Service registry - in memory for fast access
        self.service_registry = {}
        
        # Trading schedule configuration (from v107)
        self.schedule_config = {
            "enabled": True,
            "interval_minutes": 30,
            "market_hours_only": True,
            "start_time": "09:30",
            "end_time": "16:00",
            "timezone": "America/New_York",
            "excluded_days": ["Saturday", "Sunday"],
            "last_run": None,
            "next_run": None
        }
        
        # Service port mapping (per Architecture v3.1.2)
        self.service_ports = {
            "coordination": 5000,
            "scanner": 5001,
            "pattern": 5002,
            "technical": 5003,
            "trading": 5005,
            "pattern_rec": 5006,
            "news": 5008,
            "reporting": 5009,
            "dashboard": 5010
        }
        
        # Initialize system
        self._validate_database()
        self._init_database()
        self._load_schedule_config()
        self._setup_routes()
        self._load_service_registry()
        self._start_background_tasks()
        
        self.logger.info(f"Coordination Service v{VERSION} initialized")
        self.logger.info(f"Database: {self.db_path}")
        self.logger.info(f"Port: {self.port}")
        
    def _setup_logging(self):
        """Setup logging with environment-agnostic paths"""
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('CoordinationService')
        
        # Create logs directory if it doesn't exist
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'coordination_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _validate_database(self):
        """Validate database exists and has required tables"""
        if not os.path.exists(self.db_path):
            self.logger.error(f"Database not found: {self.db_path}")
            self.logger.error("Please run database_migration_v106.py first")
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        # Verify required tables exist
        required_tables = [
            'service_coordination', 'trading_cycles', 'workflow_tracking',
            'workflow_events', 'workflow_metrics', 'trading_schedule_config'
        ]
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = set(required_tables) - set(existing_tables)
            if missing_tables:
                self.logger.warning(f"Some tables missing, will create: {missing_tables}")
            
            conn.close()
            self.logger.info("Database validation completed")
            
        except Exception as e:
            self.logger.error(f"Database validation failed: {e}")
            raise
    
    def _init_database(self):
        """Initialize database tables (maintains v107 compatibility)"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create service_coordination table (matching database_migration.py)
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
            
            # Create trading_schedule_config table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_schedule_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    config TEXT NOT NULL
                )
            ''')
            
            # Create trading_cycles table
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
            
            # Create workflow tracking tables (enhanced from my v105)
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
            self.logger.info("Database tables initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
        
    def _load_service_registry(self):
        """Load service registry from database on startup"""
        try:
            results = self.execute_with_retry(
                'SELECT service_name, host, port, status, last_heartbeat FROM service_coordination'
            )
            
            for row in results:
                self.service_registry[row[0]] = {
                    'url': f"http://{row[1]}:{row[2]}",
                    'host': row[1],
                    'port': row[2],
                    'status': row[3],
                    'last_heartbeat': row[4]
                }
                
            self.logger.info(f"Loaded {len(self.service_registry)} services from database")
            
        except Exception as e:
            self.logger.error(f"Error loading service registry: {e}")
            
    def _load_schedule_config(self):
        """Load schedule configuration from database"""
        try:
            results = self.execute_with_retry(
                'SELECT config FROM trading_schedule_config WHERE id = 1'
            )
            
            if results:
                self.schedule_config = json.loads(results[0][0])
                self.logger.info("Loaded schedule configuration from database")
                
        except Exception as e:
            self.logger.warning(f"Could not load schedule config: {e}")
            
    def _save_schedule_config(self):
        """Save schedule configuration to database"""
        try:
            self.execute_with_retry(
                'INSERT OR REPLACE INTO trading_schedule_config (id, config) VALUES (1, ?)',
                (json.dumps(self.schedule_config),)
            )
            self.logger.info("Schedule configuration saved")
            
        except Exception as e:
            self.logger.error(f"Error saving schedule config: {e}")
            
    def _setup_routes(self):
        """Setup Flask routes (combining v107 endpoints with enhanced functionality)"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy", 
                "service": "coordination",
                "version": VERSION,
                "database": "connected",
                "services_registered": len(self.service_registry)
            })
        
        # Support both /register and /register_service for compatibility (from v107)
        @self.app.route('/register', methods=['POST'])
        @self.app.route('/register_service', methods=['POST'])
        def register_service():
            """Register a service with the coordinator"""
            data = request.json
            service_name = data.get('service_name')
            port = data.get('port')
            host = data.get('host', 'localhost')
            
            if not service_name or not port:
                return jsonify({"error": "service_name and port required"}), 400
            
            # Validate port matches expected ports
            expected_port = self.service_ports.get(service_name)
            if expected_port and port != expected_port:
                self.logger.warning(f"Service {service_name} registered on port {port}, expected {expected_port}")
            
            # Store in memory
            self.service_registry[service_name] = {
                'url': f"http://{host}:{port}",
                'host': host,
                'port': port,
                'status': 'active',
                'last_heartbeat': datetime.now().isoformat()
            }
            
            # Persist to database
            self._persist_service_registration(service_name, host, port)
            
            self.logger.info(f"Registered service: {service_name} on {host}:{port}")
            return jsonify({
                "status": "registered", 
                "service": service_name,
                "url": f"http://{host}:{port}"
            })
        
        @self.app.route('/force_register_all', methods=['POST'])
        def force_register_all():
            """Force registration of all known services (from v107)"""
            known_services = {
                "coordination": 5000,
                "scanner": 5001,
                "pattern": 5002,
                "technical": 5003,
                "trading": 5005,
                "pattern_rec": 5006,
                "news": 5008,
                "reporting": 5009,
                "dashboard": 5010
            }
            
            registered = []
            for service_name, port in known_services.items():
                if self._check_service_health(service_name, port):
                    self.service_registry[service_name] = {
                        'url': f"http://localhost:{port}",
                        'host': 'localhost',
                        'port': port,
                        'status': 'active',
                        'last_heartbeat': datetime.now().isoformat()
                    }
                    self._persist_service_registration(service_name, 'localhost', port)
                    registered.append(service_name)
            
            return jsonify({
                "status": "completed",
                "registered": registered,
                "count": len(registered)
            })
            
        @self.app.route('/schedule/status', methods=['GET'])
        def get_schedule_status():
            """Get current trading schedule status"""
            return jsonify(self.schedule_config)
            
        @self.app.route('/schedule/config', methods=['GET', 'POST'])
        def schedule_config():
            """Get or set trading schedule configuration (from v107)"""
            if request.method == 'GET':
                return jsonify(self.schedule_config)
            
            else:  # POST - Update configuration
                try:
                    config = request.json
                    
                    # Update configuration
                    self.schedule_config.update(config)
                    
                    # Save to database
                    self._save_schedule_config()
                    
                    self.logger.info(f"Schedule configuration updated: {config}")
                    
                    return jsonify({
                        "status": "success",
                        "message": "Schedule configuration updated",
                        "config": self.schedule_config
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error updating schedule config: {e}")
                    return jsonify({"error": str(e)}), 500

        @self.app.route('/schedule/enable', methods=['POST'])
        def enable_schedule():
            """Enable scheduled trading"""
            data = request.json or {}
            
            # Update configuration
            self.schedule_config['enabled'] = True
            if 'interval_minutes' in data:
                self.schedule_config['interval_minutes'] = data['interval_minutes']
            if 'market_hours_only' in data:
                self.schedule_config['market_hours_only'] = data['market_hours_only']
                
            # Calculate next run time
            self.schedule_config['next_run'] = (
                datetime.now() + timedelta(minutes=self.schedule_config['interval_minutes'])
            ).isoformat()
            
            self._save_schedule_config()
            
            return jsonify({
                "message": "Trading schedule enabled",
                "next_run": self.schedule_config['next_run'],
                "interval_minutes": self.schedule_config['interval_minutes']
            })
            
        @self.app.route('/schedule/disable', methods=['POST'])
        def disable_schedule():
            """Disable scheduled trading"""
            self.schedule_config['enabled'] = False
            self.schedule_config['next_run'] = None
            self._save_schedule_config()
            
            return jsonify({"message": "Trading schedule disabled"})
        
        @self.app.route('/service_status', methods=['GET'])
        def service_status():
            """Get comprehensive service status (v107 format)"""
            comprehensive_status = {}
            
            # Known services
            all_services = {
                "coordination": 5000,
                "scanner": 5001,
                "pattern": 5002,
                "technical": 5003,
                "trading": 5005,
                "pattern_rec": 5006,
                "news": 5008,
                "reporting": 5009,
                "dashboard": 5010
            }
            
            for service_name, default_port in all_services.items():
                if service_name in self.service_registry:
                    # Service is registered
                    info = self.service_registry[service_name]
                    is_healthy = self._check_service_health(service_name, info['port'])
                    
                    comprehensive_status[service_name] = {
                        'name': service_name.replace('_', ' ').title(),
                        'url': info['url'],
                        'port': info['port'],
                        'registered': True,
                        'status': 'active' if is_healthy else 'inactive',
                        'healthy': is_healthy,
                        'last_heartbeat': info.get('last_heartbeat', 'unknown')
                    }
                else:
                    # Not registered, check if it's running
                    is_healthy = self._check_service_health(service_name, default_port)
                    
                    # Auto-register if healthy
                    if is_healthy:
                        self.service_registry[service_name] = {
                            'url': f"http://localhost:{default_port}",
                            'host': 'localhost',
                            'port': default_port,
                            'status': 'active',
                            'last_heartbeat': datetime.now().isoformat()
                        }
                        self._persist_service_registration(service_name, 'localhost', default_port)
                        
                    comprehensive_status[service_name] = {
                        'name': service_name.replace('_', ' ').title(),
                        'url': f"http://localhost:{default_port}",
                        'port': default_port,
                        'registered': is_healthy,
                        'status': 'active' if is_healthy else 'not_found',
                        'healthy': is_healthy,
                        'last_heartbeat': datetime.now().isoformat() if is_healthy else None
                    }
                        
            return jsonify(comprehensive_status)
            
        @self.app.route('/start_trading_cycle', methods=['POST'])
        def start_trading_cycle():
            """Start a complete trading cycle with enhanced tracking"""
            cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            try:
                # Execute trading workflow
                results = self._execute_trading_workflow(cycle_id)
                
                # Update last run time
                self.schedule_config['last_run'] = datetime.now().isoformat()
                if self.schedule_config['enabled']:
                    self.schedule_config['next_run'] = (
                        datetime.now() + timedelta(minutes=self.schedule_config['interval_minutes'])
                    ).isoformat()
                self._save_schedule_config()
                
                return jsonify(results)
                
            except Exception as e:
                self.logger.error(f"Trading cycle failed: {e}")
                
                # Record failed cycle
                self._record_trading_cycle(cycle_id, 'failed', error_count=1)
                
                return jsonify({
                    "error": str(e), 
                    "cycle_id": cycle_id,
                    "status": "failed"
                }), 500
        
        @self.app.route('/latest_cycle', methods=['GET'])
        def latest_cycle():
            """Get latest trading cycle information (from v107)"""
            try:
                results = self.execute_with_retry('''
                    SELECT cycle_id, status, start_time, end_time, 
                           securities_scanned, patterns_found, trades_executed
                    FROM trading_cycles
                    ORDER BY created_at DESC
                    LIMIT 1
                ''')
                
                if results:
                    row = results[0]
                    return jsonify({
                        'cycle_id': row[0],
                        'status': row[1],
                        'start_time': row[2],
                        'end_time': row[3],
                        'securities_scanned': row[4],
                        'patterns_found': row[5],
                        'trades_executed': row[6]
                    })
                else:
                    return jsonify({'status': 'No cycles found'})
                    
            except Exception as e:
                self.logger.error(f"Error getting latest cycle: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/trading_cycles', methods=['GET'])
        def get_trading_cycles():
            """Get recent trading cycles"""
            try:
                limit = request.args.get('limit', 10, type=int)
                results = self.execute_with_retry(
                    'SELECT * FROM trading_cycles ORDER BY created_at DESC LIMIT ?',
                    (limit,)
                )
                
                cycles = []
                for row in results:
                    cycles.append({
                        'id': row[0],
                        'cycle_id': row[1],
                        'status': row[2],
                        'start_time': row[3],
                        'end_time': row[4],
                        'securities_scanned': row[5],
                        'patterns_found': row[6],
                        'trades_executed': row[7],
                        'error_count': row[8],
                        'created_at': row[9]
                    })
                
                return jsonify(cycles)
                
            except Exception as e:
                self.logger.error(f"Error retrieving trading cycles: {e}")
                return jsonify({"error": str(e)}), 500
            
    def _persist_service_registration(self, service_name: str, host: str, port: int):
        """Persist service registration to database with retry logic"""
        try:
            self.execute_with_retry(
                '''INSERT OR REPLACE INTO service_coordination 
                   (service_name, host, port, status, last_heartbeat, start_time)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (service_name, host, port, 'active', datetime.now(), datetime.now())
            )
            self.logger.info(f"Persisted registration for {service_name}")
            
        except Exception as e:
            self.logger.warning(f"Failed to persist {service_name} registration: {e}")
            
    def _check_service_health(self, service_name: str, port: int) -> bool:
        """Check if a service is healthy"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _execute_trading_workflow(self, cycle_id: str) -> Dict:
        """Execute complete trading workflow with comprehensive tracking"""
        self.logger.info(f"Starting trading cycle: {cycle_id}")
        
        # Initialize cycle tracking
        self._record_trading_cycle(cycle_id, 'running')
        
        results = {
            "cycle_id": cycle_id,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "securities_processed": 0,
            "patterns_found": 0,
            "signals_generated": 0,
            "trades_executed": 0,
            "errors": []
        }
        
        try:
            # Step 1: Security Scanning
            self._record_workflow_event(cycle_id, 'security_scan', 'start')
            scan_results = self._execute_security_scan()
            
            if scan_results['success']:
                # Handle both list and dict responses (from v107)
                scan_data = scan_results['data']
                if isinstance(scan_data, list):
                    securities = scan_data
                else:
                    securities = scan_data.get('securities', [])
                    
                results['securities_processed'] = len(securities)
                results['steps'].append({
                    "step": "security_scan",
                    "status": "success",
                    "securities_found": len(securities),
                    "timestamp": datetime.now().isoformat()
                })
                self._record_workflow_event(cycle_id, 'security_scan', 'complete', 
                                           {"securities_found": len(securities)})
                
                # Step 2: Pattern Analysis for each security
                all_patterns = []
                for security in securities[:5]:  # Limit to top 5 for performance
                    symbol = security['symbol']
                    pattern_results = self._execute_pattern_analysis(symbol)
                    if pattern_results['success']:
                        security['patterns'] = pattern_results['data']
                        all_patterns.extend(pattern_results['data'].get('patterns', []))
                
                results['patterns_found'] = len(all_patterns)
                
                # Step 3: Technical Analysis and Signal Generation
                signals = []
                for security in securities[:5]:
                    signal_results = self._execute_technical_analysis(security)
                    if signal_results['success']:
                        security_signals = signal_results['data'].get('signals', [])
                        signals.extend(security_signals)
                
                results['signals_generated'] = len(signals)
                
                # Step 4: Trade Execution
                if signals:
                    trade_results = self._execute_trades(signals)
                    if trade_results['success']:
                        results['trades_executed'] = trade_results['data'].get('trades_executed', 0)
                        results['steps'].append({
                            "step": "trade_execution",
                            "status": "success",
                            "trades_executed": results['trades_executed'],
                            "timestamp": datetime.now().isoformat()
                        })
                
            else:
                results['errors'].append(f"Security scan failed: {scan_results['error']}")
                
        except Exception as e:
            self.logger.error(f"Trading workflow error: {e}")
            results['errors'].append(str(e))
            self._record_workflow_event(cycle_id, 'workflow', 'error', {"error": str(e)})
        
        # Finalize cycle
        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (
            datetime.fromisoformat(results['end_time']) - 
            datetime.fromisoformat(results['start_time'])
        ).total_seconds()
        
        # Update cycle record
        status = 'completed' if not results['errors'] else 'completed_with_errors'
        self._record_trading_cycle(
            cycle_id, status, 
            end_time=results['end_time'],
            securities_scanned=results['securities_processed'],
            patterns_found=results['patterns_found'],
            trades_executed=results['trades_executed'],
            error_count=len(results['errors'])
        )
        
        self.logger.info(f"Trading cycle {cycle_id} completed: {status}")
        return results
    
    def _execute_security_scan(self) -> Dict:
        """Execute security scanning via security scanner service"""
        try:
            scanner_info = self.service_registry.get('scanner')
            if not scanner_info:
                return {"success": False, "error": "Security scanner not registered"}
            
            response = requests.get(f"{scanner_info['url']}/scan_securities", timeout=30)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Scanner returned status {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_pattern_analysis(self, symbol: str) -> Dict:
        """Execute pattern analysis for a specific symbol"""
        try:
            pattern_info = self.service_registry.get('pattern')
            if not pattern_info:
                return {"success": False, "error": "Pattern analysis service not registered"}
            
            response = requests.get(f"{pattern_info['url']}/analyze_patterns/{symbol}", timeout=20)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Pattern analysis returned status {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_technical_analysis(self, security: Dict) -> Dict:
        """Execute technical analysis and signal generation"""
        try:
            tech_info = self.service_registry.get('technical')
            if not tech_info:
                return {"success": False, "error": "Technical analysis service not registered"}
            
            response = requests.post(
                f"{tech_info['url']}/generate_signals", 
                json={"securities": [security]}, 
                timeout=20
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Technical analysis returned status {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_trades(self, signals: List) -> Dict:
        """Execute trades via paper trading service"""
        try:
            trading_info = self.service_registry.get('trading')
            if not trading_info:
                return {"success": False, "error": "Paper trading service not registered"}
            
            response = requests.post(
                f"{trading_info['url']}/execute_trades", 
                json={"signals": signals}, 
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": {"trades_executed": len(data)}}
            else:
                return {"success": False, "error": f"Trading service returned status {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _record_trading_cycle(self, cycle_id: str, status: str, **kwargs):
        """Record trading cycle to database"""
        try:
            if status == 'running':
                self.execute_with_retry(
                    '''INSERT INTO trading_cycles 
                       (cycle_id, status, start_time) 
                       VALUES (?, ?, ?)''',
                    (cycle_id, status, datetime.now())
                )
            else:
                # Update existing record
                update_fields = []
                params = [status]
                
                for field, value in kwargs.items():
                    update_fields.append(f"{field} = ?")
                    params.append(value)
                
                params.append(cycle_id)
                
                update_sql = f'''UPDATE trading_cycles 
                               SET status = ?, {', '.join(update_fields)}
                               WHERE cycle_id = ?'''
                
                self.execute_with_retry(update_sql, params)
                
        except Exception as e:
            self.logger.error(f"Error recording trading cycle: {e}")
    
    def _record_workflow_event(self, cycle_id: str, phase: str, event_type: str, event_data=None):
        """Record workflow event to database"""
        try:
            self.execute_with_retry(
                '''INSERT INTO workflow_events 
                   (cycle_id, phase, event_type, event_data, timestamp) 
                   VALUES (?, ?, ?, ?, ?)''',
                (cycle_id, phase, event_type, 
                 json.dumps(event_data) if event_data else None,
                 datetime.now().isoformat())
            )
        except Exception as e:
            self.logger.error(f"Error recording workflow event: {e}")
            
    def _start_background_tasks(self):
        """Start background tasks for health monitoring and scheduling"""
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Start schedule thread
        schedule_thread = threading.Thread(target=self._schedule_loop, daemon=True)
        schedule_thread.start()
        
        self.logger.info("Started background tasks (heartbeat and scheduling)")
        
    def _heartbeat_loop(self):
        """Background task to update service heartbeats"""
        while True:
            try:
                for service_name in list(self.service_registry.keys()):
                    info = self.service_registry[service_name]
                    if self._check_service_health(service_name, info['port']):
                        info['status'] = 'active'
                        info['last_heartbeat'] = datetime.now().isoformat()
                        
                        # Update database
                        self.execute_with_retry(
                            'UPDATE service_coordination SET last_heartbeat = ?, status = ? WHERE service_name = ?',
                            (datetime.now(), 'active', service_name)
                        )
                    else:
                        info['status'] = 'inactive'
                        
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Heartbeat loop error: {e}")
                time.sleep(30)
                
    def _schedule_loop(self):
        """Background task for scheduled trading"""
        while True:
            try:
                if self.schedule_config['enabled'] and self.schedule_config['next_run']:
                    next_run = datetime.fromisoformat(self.schedule_config['next_run'])
                    
                    if datetime.now() >= next_run:
                        # Check market hours if required
                        if self.schedule_config['market_hours_only']:
                            current_time = datetime.now().time()
                            start_time = datetime.strptime(self.schedule_config['start_time'], "%H:%M").time()
                            end_time = datetime.strptime(self.schedule_config['end_time'], "%H:%M").time()
                            
                            if not (start_time <= current_time <= end_time):
                                # Skip - outside market hours
                                self.schedule_config['next_run'] = (
                                    datetime.now() + timedelta(minutes=self.schedule_config['interval_minutes'])
                                ).isoformat()
                                self._save_schedule_config()
                                time.sleep(60)
                                continue
                                
                        # Execute trading cycle
                        self.logger.info("Executing scheduled trading cycle")
                        try:
                            requests.post(f"http://localhost:{self.port}/start_trading_cycle", timeout=60)
                        except Exception as e:
                            self.logger.error(f"Scheduled trading cycle failed: {e}")
                            
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Schedule loop error: {e}")
                time.sleep(60)
                
    def run(self):
        """Run the coordination service"""
        self.logger.info(f"Starting Coordination Service v{VERSION} on port {self.port}")
        self.logger.info(f"Database: {self.db_path}")
        self.logger.info(f"Services registered: {len(self.service_registry)}")
        
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

if __name__ == "__main__":
    service = CoordinationService()
    service.run()
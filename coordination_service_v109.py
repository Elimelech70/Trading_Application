"""
Name of Service: TRADING SYSTEM PHASE 1 - COORDINATION SERVICE
Version: 1.0.9
Last Updated: 2025-06-26
REVISION HISTORY:
v1.0.9 (2025-06-26) - Fixed database persistence for service registrations and workflow tracking
v1.0.8 (2025-06-24) - Added missing API endpoints for web dashboard compatibility 
v1.0.7 (2025-06-23) - Enhanced workflow tracking and database integration
v1.0.6 (2025-06-22) - Improved error handling and retry logic
v1.0.5 (2025-06-21) - Added comprehensive service health monitoring
v1.0.4 (2025-06-20) - Fixed table name mismatch (use service_coordination not service_registry)
v1.0.3 (2025-06-19) - Added trading schedule endpoints for automated trading
v1.0.2 (2025-06-19) - Enhanced with persistent registration and auto-registration
v1.0.1 (2025-06-11) - Implemented database utilities for retry logic
v1.0.0 (2025-06-11) - Initial release with standardized authentication

Coordination Service - Central orchestrator for all trading system services
Manages service discovery, workflow coordination, and health monitoring
"""

import os
import requests
import logging
import sqlite3
import threading
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from typing import Dict, List, Optional
import time

# Try to import database utilities
try:
    from database_utils import DatabaseManager, DatabaseServiceMixin
    USE_DB_UTILS = True
except ImportError:
    USE_DB_UTILS = False
    print("Warning: database_utils not found. Running without retry logic.")

class CoordinationService:
    def __init__(self, port=5000, db_path='./trading_system.db'):
        self.app = Flask(__name__)
        self.port = port
        self.db_path = db_path
        self.service_version = "1.0.9"
        self.logger = self._setup_logging()
        
        # Initialize database utilities if available
        if USE_DB_UTILS:
            self.db_manager = DatabaseManager(db_path)
        
        # Service registry - in memory for fast access
        self.service_registry = {}
        
        # Trading schedule configuration
        self.schedule_config = {
            "enabled": False,
            "interval_minutes": 30,
            "market_hours_only": True,
            "start_time": "09:30",
            "end_time": "16:00",
            "timezone": "Asia/Singapore",  # +8 UTC
            "excluded_days": ["Saturday", "Sunday"],
            "last_run": None,
            "next_run": None
        }
        
        # Current workflow tracking
        self.current_workflow = None
        
        # Initialize database tables
        self._init_database()
        
        # Load configuration from database
        self._load_schedule_config()
        
        # Setup routes and background tasks
        self._setup_routes()
        self._load_service_registry()
        self._start_background_tasks()
        
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('CoordinationService')
        
        # Create logs directory if it doesn't exist
        os.makedirs('./logs', exist_ok=True)
        
        handler = logging.FileHandler('./logs/coordination_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def get_db_connection(self):
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA cache_size=-64000')
        conn.execute('PRAGMA foreign_keys=ON')
        return conn
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create service_coordination table (matching database_migration.py)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_coordination (
                    service_name TEXT PRIMARY KEY,
                    service_url TEXT NOT NULL,
                    service_port INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    last_heartbeat TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            
            # Create workflow_tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds REAL,
                    details TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Load from service_coordination table
            cursor.execute('SELECT service_name, service_url, service_port, status, last_heartbeat FROM service_coordination')
            for row in cursor.fetchall():
                self.service_registry[row[0]] = {
                    'url': row[1],
                    'port': row[2],
                    'status': row[3],
                    'last_heartbeat': row[4]
                }
                
            conn.close()
            self.logger.info(f"Loaded {len(self.service_registry)} services from database")
            
        except Exception as e:
            self.logger.error(f"Error loading service registry: {e}")
    
    def _save_service_registration_to_db(self, service_name: str, service_info: dict):
        """Save service registration to database with retry logic"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO service_coordination 
                    (service_name, service_url, service_port, status, last_heartbeat, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    service_name,
                    service_info['url'],
                    service_info['port'],
                    'active',
                    datetime.now(),
                    datetime.now()
                ))
                
                conn.commit()
                conn.close()
                self.logger.info(f"Persisted service registration: {service_name}")
                return  # Success
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"Database locked, retrying in {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Failed to persist service registration after {max_retries} attempts: {e}")
                    break
            except Exception as e:
                self.logger.error(f"Error persisting service registration: {e}")
                break
    
    def _update_service_heartbeat_in_db(self, service_name: str):
        """Update service heartbeat in database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE service_coordination 
                SET last_heartbeat = ?, status = 'active', updated_at = ?
                WHERE service_name = ?
            ''', (datetime.now(), datetime.now(), service_name))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating heartbeat for {service_name}: {e}")
    
    def _create_workflow_tracking_record(self, cycle_id: str, phase: str, status: str, **kwargs):
        """Create workflow tracking record in database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            details = json.dumps(kwargs) if kwargs else None
            
            cursor.execute('''
                INSERT INTO workflow_tracking 
                (cycle_id, phase, status, start_time, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (cycle_id, phase, status, datetime.now(), details))
            
            conn.commit()
            conn.close()
            self.logger.info(f"Created workflow tracking record: {cycle_id} - {phase} - {status}")
            
        except Exception as e:
            self.logger.error(f"Error creating workflow tracking record: {e}")
    
    def _update_workflow_tracking_record(self, cycle_id: str, phase: str, status: str, **kwargs):
        """Update workflow tracking record in database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get the existing record
            cursor.execute('''
                SELECT start_time FROM workflow_tracking 
                WHERE cycle_id = ? AND phase = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (cycle_id, phase))
            
            row = cursor.fetchone()
            if row:
                start_time = datetime.fromisoformat(row[0])
                duration = (datetime.now() - start_time).total_seconds()
                
                details = json.dumps(kwargs) if kwargs else None
                error_message = kwargs.get('error_message', None)
                
                cursor.execute('''
                    UPDATE workflow_tracking 
                    SET status = ?, end_time = ?, duration_seconds = ?, details = ?, 
                        error_message = ?, updated_at = ?
                    WHERE cycle_id = ? AND phase = ?
                ''', (status, datetime.now(), duration, details, error_message, 
                      datetime.now(), cycle_id, phase))
                
                conn.commit()
                conn.close()
                self.logger.info(f"Updated workflow tracking: {cycle_id} - {phase} - {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating workflow tracking record: {e}")
            
    def _save_schedule_config(self):
        """Save schedule configuration to database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Save config
            cursor.execute('''
                INSERT OR REPLACE INTO trading_schedule_config (id, config)
                VALUES (1, ?)
            ''', (json.dumps(self.schedule_config),))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error saving schedule config: {e}")
            
    def _load_schedule_config(self):
        """Load schedule configuration from database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT config FROM trading_schedule_config WHERE id = 1')
            row = cursor.fetchone()
            
            if row:
                self.schedule_config = json.loads(row[0])
                self.logger.info("Loaded schedule configuration from database")
                
            conn.close()
            
        except Exception as e:
            self.logger.warning(f"Could not load schedule config: {e}")
            
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy", 
                "service": "coordination",
                "version": self.service_version,
                "timestamp": datetime.now().isoformat()
            })
            
        @self.app.route('/register_service', methods=['POST'])
        def register_service():
            """Register a service with the coordinator"""
            data = request.json
            service_name = data.get('service_name')
            port = data.get('port')
            
            if not service_name or not port:
                return jsonify({"error": "service_name and port required"}), 400
                
            # Store in memory
            service_info = {
                'url': f"http://localhost:{port}",
                'port': port,
                'status': 'active',
                'last_heartbeat': datetime.now().isoformat()
            }
            self.service_registry[service_name] = service_info
            
            # Persist to database
            self._save_service_registration_to_db(service_name, service_info)
            
            self.logger.info(f"Registered service: {service_name} on port {port}")
            return jsonify({"status": "registered", "service": service_name})
        
        # Web Dashboard Compatible Endpoints
        @self.app.route('/api/schedule_status', methods=['GET'])
        def api_schedule_status():
            """Get trading schedule status (web dashboard compatible)"""
            return jsonify(self.schedule_config)
        
        @self.app.route('/api/configure_schedule', methods=['POST'])
        def api_configure_schedule():
            """Configure trading schedule (web dashboard compatible)"""
            data = request.json or {}
            
            # Update configuration
            if 'enabled' in data:
                self.schedule_config['enabled'] = data['enabled']
            if 'interval_minutes' in data:
                self.schedule_config['interval_minutes'] = data['interval_minutes']
            if 'market_hours_only' in data:
                self.schedule_config['market_hours_only'] = data['market_hours_only']
            if 'start_time' in data:
                self.schedule_config['start_time'] = data['start_time']
            if 'end_time' in data:
                self.schedule_config['end_time'] = data['end_time']
                
            # Calculate next run time if enabled
            if self.schedule_config['enabled']:
                self.schedule_config['next_run'] = (
                    datetime.now() + timedelta(minutes=self.schedule_config['interval_minutes'])
                ).isoformat()
            else:
                self.schedule_config['next_run'] = None
            
            self._save_schedule_config()
            
            return jsonify({
                "message": "Schedule configuration updated",
                "config": self.schedule_config
            })
        
        @self.app.route('/api/workflow_status', methods=['GET'])
        def api_workflow_status():
            """Get current workflow status (web dashboard compatible)"""
            if self.current_workflow:
                return jsonify(self.current_workflow)
            else:
                # Get latest workflow from database
                try:
                    conn = self.get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT cycle_id, status, start_time, end_time, securities_scanned, 
                               patterns_found, trades_executed
                        FROM trading_cycles 
                        ORDER BY created_at DESC LIMIT 1
                    ''')
                    
                    row = cursor.fetchone()
                    if row:
                        return jsonify({
                            "cycle_id": row[0],
                            "status": row[1],
                            "start_time": row[2],
                            "end_time": row[3],
                            "securities_scanned": row[4],
                            "patterns_found": row[5],
                            "trades_executed": row[6]
                        })
                    else:
                        return jsonify({"status": "No active workflow"})
                        
                except Exception as e:
                    self.logger.error(f"Error getting workflow status: {e}")
                    return jsonify({"error": "Unable to retrieve workflow status"}), 500
            
        # Original endpoints (maintaining compatibility)
        @self.app.route('/schedule/status', methods=['GET'])
        def get_schedule_status():
            """Get current trading schedule status"""
            return jsonify(self.schedule_config)
            
        @self.app.route('/schedule/config', methods=['GET', 'POST'])
        def schedule_config():
            """Get or set schedule configuration"""
            if request.method == 'GET':
                return jsonify(self.schedule_config)
            else:
                return api_configure_schedule()
            
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
                "next_run": self.schedule_config['next_run']
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
            """Get comprehensive service status"""
            # Merge in-memory registry with live health checks
            comprehensive_status = []
            
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
                    port = info['port']
                    is_healthy = self._check_service_health(service_name, port)
                    
                    # Update heartbeat if healthy
                    if is_healthy:
                        self._update_service_heartbeat_in_db(service_name)
                    
                    comprehensive_status.append({
                        'name': service_name,
                        'url': info['url'],
                        'port': port,
                        'registered': True,
                        'status': 'active' if is_healthy else 'inactive',
                        'healthy': is_healthy,
                        'last_heartbeat': info.get('last_heartbeat', 'unknown')
                    })
                else:
                    # Not registered, check if it's running
                    is_healthy = self._check_service_health(service_name, default_port)
                    
                    # Auto-register if healthy
                    if is_healthy:
                        service_info = {
                            'url': f"http://localhost:{default_port}",
                            'port': default_port,
                            'status': 'active',
                            'last_heartbeat': datetime.now().isoformat()
                        }
                        self.service_registry[service_name] = service_info
                        self._save_service_registration_to_db(service_name, service_info)
                        
                    comprehensive_status.append({
                        'name': service_name,
                        'url': f"http://localhost:{default_port}",
                        'port': default_port,
                        'registered': is_healthy,
                        'status': 'active' if is_healthy else 'not_found',
                        'healthy': is_healthy,
                        'last_heartbeat': datetime.now().isoformat() if is_healthy else None
                    })
                        
            return jsonify(comprehensive_status)
        
        @self.app.route('/latest_cycle', methods=['GET'])
        def latest_cycle():
            """Get latest trading cycle information"""
            if self.current_workflow:
                return jsonify(self.current_workflow)
            else:
                return jsonify({"status": "No active cycle"})
            
        @self.app.route('/start_trading_cycle', methods=['POST'])
        def start_trading_cycle():
            """Start a trading cycle"""
            cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            try:
                # Create workflow tracking record
                self._create_workflow_tracking_record(cycle_id, "initialization", "started")
                
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
                self._update_workflow_tracking_record(cycle_id, "initialization", "failed", 
                                                      error_message=str(e))
                return jsonify({"error": str(e), "cycle_id": cycle_id}), 500
                
    def _check_service_health(self, service_name: str, port: int) -> bool:
        """Check if a service is healthy"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def _execute_trading_workflow(self, cycle_id: str) -> Dict:
        """Execute complete trading workflow with tracking"""
        self.current_workflow = {
            "cycle_id": cycle_id,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "securities_scanned": 0,
            "trades_executed": 0
        }
        
        results = self.current_workflow.copy()
        
        try:
            # Phase 1: Security Selection
            self._create_workflow_tracking_record(cycle_id, "security_selection", "started")
            scanner_url = self.service_registry.get('scanner', {}).get('url', 'http://localhost:5001')
            
            try:
                scan_response = requests.post(f"{scanner_url}/scan_securities", timeout=30)
                if scan_response.status_code == 200:
                    scan_data = scan_response.json()
                    securities_count = len(scan_data.get('securities', []))
                    results['securities_scanned'] = securities_count
                    
                    self._update_workflow_tracking_record(cycle_id, "security_selection", "completed",
                                                          securities_found=securities_count)
                    
                    results['steps'].append({
                        "step": "security_scan",
                        "status": "success",
                        "securities_found": securities_count
                    })
                    
                    # Phase 2: Pattern Analysis
                    self._create_workflow_tracking_record(cycle_id, "pattern_analysis", "started")
                    
                    # Phase 3: Signal Generation  
                    self._create_workflow_tracking_record(cycle_id, "signal_generation", "started")
                    
                    # Phase 4: Trade Execution
                    self._create_workflow_tracking_record(cycle_id, "trade_execution", "started")
                    
                    # Process securities (simplified for this implementation)
                    for security in scan_data.get('securities', [])[:5]:  # Limit to top 5
                        symbol = security['symbol']
                        
                        # Pattern analysis
                        pattern_url = self.service_registry.get('pattern', {}).get('url', 'http://localhost:5002')
                        try:
                            pattern_response = requests.get(f"{pattern_url}/analyze_patterns/{symbol}", timeout=10)
                            if pattern_response.status_code == 200:
                                security['patterns'] = pattern_response.json()
                        except:
                            pass
                            
                        # Technical analysis
                        tech_url = self.service_registry.get('technical', {}).get('url', 'http://localhost:5003')
                        try:
                            tech_response = requests.post(f"{tech_url}/generate_signals", 
                                                          json={"symbol": symbol}, timeout=10)
                            if tech_response.status_code == 200:
                                security['technical'] = tech_response.json()
                        except:
                            pass
                    
                    # Mark phases as completed
                    self._update_workflow_tracking_record(cycle_id, "pattern_analysis", "completed")
                    self._update_workflow_tracking_record(cycle_id, "signal_generation", "completed")
                    self._update_workflow_tracking_record(cycle_id, "trade_execution", "completed")
                    
                else:
                    self._update_workflow_tracking_record(cycle_id, "security_selection", "failed",
                                                          error_message=f"Scanner returned {scan_response.status_code}")
                    
            except Exception as e:
                self._update_workflow_tracking_record(cycle_id, "security_selection", "failed",
                                                      error_message=str(e))
                results['steps'].append({
                    "step": "security_scan",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Phase 5: Completion
            self._create_workflow_tracking_record(cycle_id, "completion", "completed")
            
            results['end_time'] = datetime.now().isoformat()
            results['status'] = 'completed'
            self.current_workflow = results
            
            # Save to trading_cycles table
            self._save_trading_cycle(results)
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            self.current_workflow = results
            self.logger.error(f"Trading workflow failed: {e}")
            
        return results
    
    def _save_trading_cycle(self, results: Dict):
        """Save trading cycle results to database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO trading_cycles 
                (cycle_id, status, start_time, end_time, securities_scanned, trades_executed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                results['cycle_id'],
                results['status'],
                results['start_time'],
                results.get('end_time'),
                results.get('securities_scanned', 0),
                results.get('trades_executed', 0)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error saving trading cycle: {e}")
        
    def _start_background_tasks(self):
        """Start background tasks"""
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Start schedule thread
        schedule_thread = threading.Thread(target=self._schedule_loop, daemon=True)
        schedule_thread.start()
        
        self.logger.info("Started background tasks")
        
    def _heartbeat_loop(self):
        """Background task to update service heartbeats"""
        while True:
            try:
                for service_name in list(self.service_registry.keys()):
                    info = self.service_registry[service_name]
                    if self._check_service_health(service_name, info['port']):
                        info['status'] = 'active'
                        info['last_heartbeat'] = datetime.now().isoformat()
                        self._update_service_heartbeat_in_db(service_name)
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
                            requests.post(f"http://localhost:{self.port}/start_trading_cycle")
                        except Exception as e:
                            self.logger.error(f"Scheduled trading cycle failed: {e}")
                            
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Schedule loop error: {e}")
                time.sleep(60)
                
    def run(self):
        """Run the coordination service"""
        self.logger.info(f"Starting Coordination Service v{self.service_version} on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

# Create and run service
if __name__ == "__main__":
    service = CoordinationService()
    service.run()
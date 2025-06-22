#!/usr/bin/env python3
"""
TRADING SYSTEM PHASE 1
Service: coordination_service_v105.py
Version: 1.0.5
Last Updated: 2025-06-22

REVISION HISTORY:
- v1.0.5 (2025-06-22) - Fixed schema mismatch: use host/port from service_coordination table
- v1.0.4 (2025-06-20) - Fixed table name mismatch (use service_coordination not service_registry)
- v1.0.3 (2025-06-19) - Added trading schedule endpoints for automated trading
- v1.0.2 (2025-06-19) - Enhanced with persistent registration and auto-registration
- v1.0.1 (2025-06-11) - Implemented database utilities for retry logic
- v1.0.0 (2025-06-11) - Initial release with standardized authentication

PURPOSE:
Coordination Service - Central orchestrator for all trading system services
Manages service discovery, workflow coordination, and health monitoring
Fixed to match actual database schema from database_migration.py
"""

import os
import requests
import logging
import sqlite3
import threading
import json
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
    def __init__(self, port=5000, db_path='/content/trading_system.db'):
        self.app = Flask(__name__)
        self.port = port
        self.db_path = db_path
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
            "timezone": "America/New_York",
            "excluded_days": ["Saturday", "Sunday"],
            "last_run": None,
            "next_run": None
        }
        
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
        os.makedirs('/content/logs', exist_ok=True)
        
        handler = logging.FileHandler('/content/logs/coordination_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create service_coordination table (matching database_migration.py schema)
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
            
            conn.commit()
            conn.close()
            self.logger.info("Database tables initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
        
    def _load_service_registry(self):
        """Load service registry from database on startup - FIXED TO MATCH SCHEMA"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load from service_coordination table with correct column names
            cursor.execute('SELECT service_name, host, port, status, last_heartbeat FROM service_coordination')
            for row in cursor.fetchall():
                service_name = row[0]
                host = row[1]
                port = row[2]
                status = row[3]
                last_heartbeat = row[4]
                
                # Build URL from host and port
                url = f"http://{host}:{port}"
                
                self.service_registry[service_name] = {
                    'url': url,
                    'host': host,
                    'port': port,
                    'status': status,
                    'last_heartbeat': last_heartbeat
                }
                
            conn.close()
            self.logger.info(f"Loaded {len(self.service_registry)} services from database")
            
        except Exception as e:
            self.logger.error(f"Error loading service registry: {e}")
            
    def _save_schedule_config(self):
        """Save schedule configuration to database"""
        try:
            conn = sqlite3.connect(self.db_path)
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT config FROM trading_schedule_config WHERE id = 1')
            row = cursor.fetchone()
            
            if row:
                self.schedule_config = json.loads(row[0])
                
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error loading schedule config: {e}")
            
    def _persist_service_registration(self, service_name: str, port: int):
        """Persist service registration to database - FIXED TO MATCH SCHEMA"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert or update with correct column names
            cursor.execute('''
                INSERT OR REPLACE INTO service_coordination 
                (service_name, host, port, status, last_heartbeat, start_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                service_name,
                'localhost',  # host
                port,         # port
                'active',     # status
                datetime.now().isoformat(),  # last_heartbeat
                datetime.now().isoformat()   # start_time
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error persisting service registration: {e}")
            
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({'status': 'healthy', 'service': 'coordination'}), 200
            
        @self.app.route('/register', methods=['POST'])
        def register_service():
            data = request.json
            service_name = data.get('service_name')
            port = data.get('port')
            
            if not service_name or not port:
                return jsonify({'error': 'service_name and port required'}), 400
                
            # Register service
            self.service_registry[service_name] = {
                'url': f"http://localhost:{port}",
                'host': 'localhost',
                'port': port,
                'status': 'active',
                'last_heartbeat': datetime.now().isoformat()
            }
            
            # Persist to database
            self._persist_service_registration(service_name, port)
            
            self.logger.info(f"Registered service: {service_name} on port {port}")
            return jsonify({'status': 'registered'}), 200
            
        @self.app.route('/services', methods=['GET'])
        def get_services():
            return jsonify(self.service_registry), 200
            
        @self.app.route('/services/status', methods=['GET'])
        def get_services_status():
            """Get comprehensive status of all known services"""
            comprehensive_status = []
            
            # Check all known services including those not registered
            all_services = {
                "coordination": 5000,
                "scanner": 5001,
                "pattern": 5002,
                "technical": 5003,
                "trading": 5005,
                "pattern_rec": 5006,
                "news": 5008,
                "reporting": 5009,
                "dashboard": 5004
            }
            
            for service_name, default_port in all_services.items():
                if service_name in self.service_registry:
                    # Service is registered
                    info = self.service_registry[service_name]
                    port = info['port']
                    is_healthy = self._check_service_health(service_name, port)
                    
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
                        self.service_registry[service_name] = {
                            'url': f"http://localhost:{default_port}",
                            'host': 'localhost',
                            'port': default_port,
                            'status': 'active',
                            'last_heartbeat': datetime.now().isoformat()
                        }
                        self._persist_service_registration(service_name, default_port)
                        
                    comprehensive_status.append({
                        'name': service_name,
                        'url': f"http://localhost:{default_port}",
                        'port': default_port,
                        'registered': is_healthy,
                        'status': 'active' if is_healthy else 'inactive',
                        'healthy': is_healthy,
                        'last_heartbeat': datetime.now().isoformat() if is_healthy else 'never'
                    })
                    
            return jsonify(comprehensive_status), 200
            
        @self.app.route('/trigger/scan', methods=['POST'])
        def trigger_scan():
            """Trigger a security scan across the system"""
            try:
                # Start a new trading cycle
                cycle_id = f"CYCLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Record cycle start
                self._start_trading_cycle(cycle_id)
                
                # Trigger scanner service
                if 'scanner' in self.service_registry:
                    scanner_url = self.service_registry['scanner']['url']
                    response = requests.post(f"{scanner_url}/scan/all", timeout=5)
                    
                    if response.status_code == 200:
                        return jsonify({
                            'status': 'scan_initiated',
                            'cycle_id': cycle_id,
                            'timestamp': datetime.now().isoformat()
                        }), 200
                        
                return jsonify({'error': 'Scanner service not available'}), 503
                
            except Exception as e:
                self.logger.error(f"Error triggering scan: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/schedule', methods=['GET'])
        def get_schedule():
            """Get current trading schedule configuration"""
            return jsonify(self.schedule_config), 200
            
        @self.app.route('/schedule', methods=['PUT'])
        def update_schedule():
            """Update trading schedule configuration"""
            data = request.json
            
            # Update configuration
            for key in ['enabled', 'interval_minutes', 'market_hours_only', 
                       'start_time', 'end_time', 'timezone', 'excluded_days']:
                if key in data:
                    self.schedule_config[key] = data[key]
                    
            # Save to database
            self._save_schedule_config()
            
            # Calculate next run time if enabled
            if self.schedule_config['enabled']:
                self.schedule_config['next_run'] = self._calculate_next_run()
                
            return jsonify(self.schedule_config), 200
            
        @self.app.route('/cycles', methods=['GET'])
        def get_trading_cycles():
            """Get recent trading cycles"""
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT cycle_id, status, start_time, end_time, 
                           securities_scanned, patterns_found, trades_executed, error_count
                    FROM trading_cycles
                    ORDER BY created_at DESC
                    LIMIT 20
                ''')
                
                cycles = []
                for row in cursor.fetchall():
                    cycles.append({
                        'cycle_id': row[0],
                        'status': row[1],
                        'start_time': row[2],
                        'end_time': row[3],
                        'securities_scanned': row[4],
                        'patterns_found': row[5],
                        'trades_executed': row[6],
                        'error_count': row[7]
                    })
                    
                conn.close()
                return jsonify(cycles), 200
                
            except Exception as e:
                self.logger.error(f"Error getting trading cycles: {e}")
                return jsonify({'error': str(e)}), 500
                
    def _check_service_health(self, service_name: str, port: int) -> bool:
        """Check if a service is healthy"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def _start_trading_cycle(self, cycle_id: str):
        """Record the start of a trading cycle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trading_cycles (cycle_id, status, start_time)
                VALUES (?, ?, ?)
            ''', (cycle_id, 'RUNNING', datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error starting trading cycle: {e}")
            
    def _calculate_next_run(self) -> str:
        """Calculate next scheduled run time"""
        now = datetime.now()
        next_run = now + timedelta(minutes=self.schedule_config['interval_minutes'])
        
        # If market hours only, adjust to next market open
        if self.schedule_config['market_hours_only']:
            # Simple implementation - would need timezone handling in production
            if next_run.weekday() >= 5:  # Weekend
                days_until_monday = 7 - next_run.weekday()
                next_run = next_run + timedelta(days=days_until_monday)
                next_run = next_run.replace(hour=9, minute=30, second=0)
                
        return next_run.isoformat()
        
    def _scheduled_trading_cycle(self):
        """Execute scheduled trading cycles"""
        while True:
            try:
                if self.schedule_config['enabled']:
                    # Check if it's time to run
                    now = datetime.now()
                    next_run_str = self.schedule_config.get('next_run')
                    
                    if next_run_str:
                        next_run = datetime.fromisoformat(next_run_str)
                        
                        if now >= next_run:
                            # Trigger trading cycle
                            self.logger.info("Executing scheduled trading cycle")
                            
                            # Make internal request to trigger scan
                            requests.post(f"http://localhost:{self.port}/trigger/scan")
                            
                            # Update last run and calculate next run
                            self.schedule_config['last_run'] = now.isoformat()
                            self.schedule_config['next_run'] = self._calculate_next_run()
                            self._save_schedule_config()
                            
                # Sleep for 30 seconds before checking again
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in scheduled trading cycle: {e}")
                time.sleep(60)  # Wait longer on error
                
    def _monitor_services(self):
        """Background task to monitor service health"""
        while True:
            try:
                for service_name, info in list(self.service_registry.items()):
                    port = info['port']
                    is_healthy = self._check_service_health(service_name, port)
                    
                    if is_healthy:
                        info['status'] = 'active'
                        info['last_heartbeat'] = datetime.now().isoformat()
                    else:
                        info['status'] = 'inactive'
                        
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in service monitoring: {e}")
                time.sleep(60)
                
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        # Start service monitor
        monitor_thread = threading.Thread(target=self._monitor_services)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Start scheduled trading
        schedule_thread = threading.Thread(target=self._scheduled_trading_cycle)
        schedule_thread.daemon = True
        schedule_thread.start()
        
        self.logger.info("Background tasks started")
        
    def run(self):
        """Start the Flask application"""
        self.logger.info(f"Starting Coordination Service on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

if __name__ == "__main__":
    service = CoordinationService()
    service.run()
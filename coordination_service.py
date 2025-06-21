"""
Name of Service: TRADING SYSTEM PHASE 1 - COORDINATION SERVICE
Version: 1.0.4
Last Updated: 2025-06-20
REVISION HISTORY:
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
            
            conn.commit()
            conn.close()
            self.logger.info("Database tables initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
        
    def _load_service_registry(self):
        """Load service registry from database on startup"""
        try:
            conn = sqlite3.connect(self.db_path)
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
                self.logger.info("Loaded schedule configuration from database")
                
            conn.close()
            
        except Exception as e:
            self.logger.warning(f"Could not load schedule config: {e}")
            
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({"status": "healthy", "service": "coordination"})
            
        @self.app.route('/register', methods=['POST'])
        def register_service():
            """Register a service with the coordinator"""
            data = request.json
            service_name = data.get('service_name')
            port = data.get('port')
            
            if not service_name or not port:
                return jsonify({"error": "service_name and port required"}), 400
                
            # Store in memory
            self.service_registry[service_name] = {
                'url': f"http://localhost:{port}",
                'port': port,
                'status': 'active',
                'last_heartbeat': datetime.now().isoformat()
            }
            
            # Persist to database
            self._persist_service_registration(service_name, port)
            
            self.logger.info(f"Registered service: {service_name} on port {port}")
            return jsonify({"status": "registered", "service": service_name})
            
        @self.app.route('/schedule/status', methods=['GET'])
        def get_schedule_status():
            """Get current trading schedule status"""
            return jsonify(self.schedule_config)
            
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
                        'status': 'active' if is_healthy else 'not_found',
                        'healthy': is_healthy,
                        'last_heartbeat': datetime.now().isoformat() if is_healthy else None
                    })
                        
            return jsonify(comprehensive_status)
            
        @self.app.route('/start_trading_cycle', methods=['POST'])
        def start_trading_cycle():
            """Start a trading cycle"""
            cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
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
                return jsonify({"error": str(e), "cycle_id": cycle_id}), 500
                
    def _persist_service_registration(self, service_name: str, port: int, max_retries: int = 3):
        """Persist service registration to database with retry logic"""
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO service_coordination 
                    (service_name, service_url, service_port, status, last_heartbeat, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    service_name,
                    f"http://localhost:{port}",
                    port,
                    'active',
                    datetime.now(),
                    datetime.now()
                ))
                
                conn.commit()
                conn.close()
                return  # Success
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed to persist {service_name}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    self.logger.warning(f"Registered {service_name} in memory only - persistence failed")
            
    def _check_service_health(self, service_name: str, port: int) -> bool:
        """Check if a service is healthy"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def _execute_trading_workflow(self, cycle_id: str) -> Dict:
        """Execute complete trading workflow"""
        results = {
            "cycle_id": cycle_id,
            "start_time": datetime.now().isoformat(),
            "steps": []
        }
        
        # Step 1: Scan securities
        scanner_url = self.service_registry.get('scanner', {}).get('url', 'http://localhost:5001')
        try:
            scan_response = requests.post(f"{scanner_url}/scan_securities", timeout=30)
            if scan_response.status_code == 200:
                scan_data = scan_response.json()
                results['steps'].append({
                    "step": "security_scan",
                    "status": "success",
                    "securities_found": len(scan_data.get('securities', []))
                })
                
                # Process each security through the pipeline
                for security in scan_data.get('securities', [])[:5]:  # Limit to top 5
                    symbol = security['symbol']
                    
                    # Pattern analysis
                    pattern_url = self.service_registry.get('pattern', {}).get('url', 'http://localhost:5002')
                    try:
                        pattern_response = requests.get(f"{pattern_url}/analyze_patterns/{symbol}")
                        if pattern_response.status_code == 200:
                            security['patterns'] = pattern_response.json()
                    except:
                        pass
                        
                    # Technical analysis
                    tech_url = self.service_registry.get('technical', {}).get('url', 'http://localhost:5003')
                    try:
                        tech_response = requests.post(f"{tech_url}/generate_signals", json={"symbol": symbol})
                        if tech_response.status_code == 200:
                            security['technical'] = tech_response.json()
                    except:
                        pass
                        
        except Exception as e:
            results['steps'].append({
                "step": "security_scan",
                "status": "failed",
                "error": str(e)
            })
            
        results['end_time'] = datetime.now().isoformat()
        return results
        
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
        self.logger.info(f"Starting Coordination Service on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

# Create and run service
if __name__ == "__main__":
    service = CoordinationService()
    service.run()
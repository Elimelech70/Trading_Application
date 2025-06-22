#!/usr/bin/env python3
"""
TRADING SYSTEM PHASE 1
Service: enhanced_startup_manager.py
Version: 2.0.1
Last Updated: 2025-01-11

REVISION HISTORY:
- v2.0.1 (2025-01-11) - Integrated with google_drive_service_v101.py
- v2.0.0 (2025-01-10) - Enhanced startup sequence with comprehensive checks
- v1.0.0 (2024-12-28) - Initial version

PURPOSE:
Provides comprehensive startup management for the Trading System with
integrated Google Drive support via the unified service.
"""

import os
import sys
import time
import psutil
import sqlite3
import subprocess
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import the Google Drive service
from google_drive_service_v101 import get_drive_service

class EnhancedStartupManager:
    """
    Enhanced startup manager with comprehensive pre-flight checks,
    dependency management, and Google Drive integration.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize startup manager"""
        self.logger = logger or self._setup_default_logger()
        self.start_time = datetime.now()
        
        # Initialize Google Drive service
        self.drive_service = get_drive_service(self.logger)
        
        # System configuration
        self.services = {
            'coordination': {
                'name': 'coordination_service',
                'port': 5000,
                'critical': True,
                'dependencies': [],
                'startup_delay': 5
            },
            'scanner': {
                'name': 'security_scanner',
                'port': 5001,
                'critical': True,
                'dependencies': ['coordination'],
                'startup_delay': 3
            },
            'pattern': {
                'name': 'pattern_analysis',
                'port': 5002,
                'critical': True,
                'dependencies': ['coordination'],
                'startup_delay': 3
            },
            'technical': {
                'name': 'technical_analysis',
                'port': 5003,
                'critical': True,
                'dependencies': ['coordination'],
                'startup_delay': 3
            },
            'trading': {
                'name': 'paper_trading',
                'port': 5005,
                'critical': True,
                'dependencies': ['technical'],
                'startup_delay': 3
            },
            'pattern_rec': {
                'name': 'pattern_recognition_service',
                'port': 5006,
                'critical': True,
                'dependencies': ['coordination'],
                'startup_delay': 3
            },
            'news': {
                'name': 'news_service',
                'port': 5008,
                'critical': False,
                'dependencies': [],
                'startup_delay': 3
            },
            'reporting': {
                'name': 'reporting_service',
                'port': 5009,
                'critical': False,
                'dependencies': ['coordination'],
                'startup_delay': 3
            },
            'dashboard': {
                'name': 'web_dashboard',
                'port': 8080,
                'critical': False,
                'dependencies': ['coordination'],
                'startup_delay': 3
            }
        }
        
        # Track startup state
        self.startup_state = {
            'phase': 'initialization',
            'checks_passed': {},
            'services_started': {},
            'errors': [],
            'warnings': []
        }
        
    def _setup_default_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('EnhancedStartupManager')
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def run_startup_sequence(self) -> bool:
        """Run the complete startup sequence"""
        try:
            self.logger.info("="*60)
            self.logger.info("🚀 TRADING SYSTEM ENHANCED STARTUP SEQUENCE v2.0.1")
            self.logger.info("="*60)
            
            # Save initial state
            self._save_startup_state()
            
            # Phase 1: Pre-flight checks
            if not self._run_preflight_checks():
                return False
            
            # Phase 2: Database preparation
            if not self._prepare_database():
                return False
            
            # Phase 3: Service startup
            if not self._start_services():
                return False
            
            # Phase 4: Post-startup validation
            if not self._validate_system():
                return False
            
            # Phase 5: Generate report
            self._generate_startup_report()
            
            self.logger.info("✅ STARTUP SEQUENCE COMPLETED SUCCESSFULLY")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Startup sequence failed: {e}")
            self.startup_state['errors'].append(f"Fatal error: {str(e)}")
            self._save_startup_state()
            return False
    
    def _run_preflight_checks(self) -> bool:
        """Run comprehensive pre-flight checks"""
        self.logger.info("\n📋 PHASE 1: PRE-FLIGHT CHECKS")
        self.startup_state['phase'] = 'preflight_checks'
        
        checks = [
            ('Google Drive Connection', self._check_google_drive),
            ('System Resources', self._check_system_resources),
            ('Port Availability', self._check_ports),
            ('Python Dependencies', self._check_dependencies),
            ('Service Files', self._check_service_files),
            ('Configuration Files', self._check_config_files)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                passed, message = check_func()
                self.startup_state['checks_passed'][check_name] = passed
                
                if passed:
                    self.logger.info(f"✅ {check_name}: {message}")
                else:
                    self.logger.error(f"❌ {check_name}: {message}")
                    self.startup_state['errors'].append(f"{check_name}: {message}")
                    all_passed = False
                    
            except Exception as e:
                self.logger.error(f"❌ {check_name}: Exception - {str(e)}")
                self.startup_state['checks_passed'][check_name] = False
                self.startup_state['errors'].append(f"{check_name}: {str(e)}")
                all_passed = False
        
        self._save_startup_state()
        return all_passed
    
    def _check_google_drive(self) -> Tuple[bool, str]:
        """Check Google Drive connection"""
        try:
            # Test by listing files in data folder
            files = self.drive_service.list_files('data')
            return True, f"Connected, {len(files)} files in data folder"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def _check_system_resources(self) -> Tuple[bool, str]:
        """Check system resources"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        issues = []
        if cpu_percent > 90:
            issues.append(f"High CPU usage: {cpu_percent}%")
        if memory.percent > 90:
            issues.append(f"High memory usage: {memory.percent}%")
        if disk.percent > 95:
            issues.append(f"Low disk space: {disk.percent}% used")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%"
    
    def _check_ports(self) -> Tuple[bool, str]:
        """Check if required ports are available"""
        occupied_ports = []
        
        for service_id, config in self.services.items():
            port = config['port']
            if self._is_port_in_use(port):
                occupied_ports.append(f"{config['name']}:{port}")
        
        if occupied_ports:
            return False, f"Ports in use: {', '.join(occupied_ports)}"
        
        return True, "All ports available"
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def _check_dependencies(self) -> Tuple[bool, str]:
        """Check Python dependencies"""
        required_packages = [
            'flask', 'requests', 'pandas', 'numpy', 'yfinance',
            'psutil', 'tabulate', 'googleapiclient', 'google.auth'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.split('.')[0])
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            return False, f"Missing packages: {', '.join(missing_packages)}"
        
        return True, "All dependencies installed"
    
    def _check_service_files(self) -> Tuple[bool, str]:
        """Check if all service files exist in Google Drive"""
        missing_files = []
        
        # List all Python files in the main directory
        files = self.drive_service.list_files()
        file_names = [f['name'] for f in files]
        
        for service_id, config in self.services.items():
            filename = f"{config['name']}.py"
            if filename not in file_names:
                missing_files.append(filename)
        
        # Check for hybrid_manager.py
        if 'hybrid_manager.py' not in file_names:
            missing_files.append('hybrid_manager.py')
        
        if missing_files:
            return False, f"Missing files: {', '.join(missing_files)}"
        
        return True, "All service files present"
    
    def _check_config_files(self) -> Tuple[bool, str]:
        """Check configuration files"""
        try:
            # Check if config exists
            config = self.drive_service.load_json('trading_config.json', 'config')
            if not config:
                # Create default config
                default_config = {
                    'system_name': 'Trading System Phase 1',
                    'version': '2.0.1',
                    'startup_manager': 'enhanced_startup_manager_v201',
                    'services': self.services,
                    'created_at': datetime.now().isoformat()
                }
                self.drive_service.save_json('trading_config.json', default_config, 'config')
                return True, "Created default configuration"
            
            return True, "Configuration loaded"
            
        except Exception as e:
            return False, f"Config error: {str(e)}"
    
    def _prepare_database(self) -> bool:
        """Prepare database for operation"""
        self.logger.info("\n🗄️ PHASE 2: DATABASE PREPARATION")
        self.startup_state['phase'] = 'database_preparation'
        
        try:
            # Check database info
            db_info = self.drive_service.get_database_info()
            
            if not db_info['exists']:
                self.logger.info("Database not found, creating new database...")
                # Download and run database migration
                try:
                    migration_content = self.drive_service.read_file('database_migration.py')
                    # Save temporarily and execute
                    temp_migration = Path('/tmp/database_migration.py')
                    temp_migration.write_bytes(migration_content)
                    
                    result = subprocess.run(
                        [sys.executable, str(temp_migration)],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        raise Exception(f"Migration failed: {result.stderr}")
                    
                    self.logger.info("✅ Database created successfully")
                    
                except Exception as e:
                    self.logger.error(f"❌ Database creation failed: {e}")
                    return False
            else:
                self.logger.info(f"✅ Database exists: {db_info['size']} bytes, "
                               f"last modified: {db_info['last_modified']}")
            
            # Verify database structure
            if not self._verify_database_structure():
                return False
            
            self._save_startup_state()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Database preparation failed: {e}")
            self.startup_state['errors'].append(f"Database error: {str(e)}")
            self._save_startup_state()
            return False
    
    def _verify_database_structure(self) -> bool:
        """Verify database has required tables"""
        # For Google Drive, we'll download the DB temporarily to check
        try:
            db_content = self.drive_service.read_file('trading.db', 'data')
            temp_db = Path('/tmp/trading_check.db')
            temp_db.write_bytes(db_content)
            
            conn = sqlite3.connect(str(temp_db))
            cursor = conn.cursor()
            
            # Check for required tables
            required_tables = [
                'services', 'api_connections', 'system_metrics',
                'security_logs', 'trading_signals', 'paper_trades'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [t for t in required_tables if t not in existing_tables]
            
            conn.close()
            temp_db.unlink()
            
            if missing_tables:
                self.logger.warning(f"⚠️ Missing tables: {', '.join(missing_tables)}")
                return False
            
            self.logger.info("✅ Database structure verified")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Database verification failed: {e}")
            return False
    
    def _start_services(self) -> bool:
        """Start all services in dependency order"""
        self.logger.info("\n🚀 PHASE 3: SERVICE STARTUP")
        self.startup_state['phase'] = 'service_startup'
        
        # Kill any existing processes first
        self._cleanup_existing_processes()
        
        # Determine startup method
        if self._should_use_hybrid_manager():
            return self._start_with_hybrid_manager()
        else:
            return self._start_services_directly()
    
    def _cleanup_existing_processes(self):
        """Clean up any existing service processes"""
        self.logger.info("Cleaning up existing processes...")
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('_service.py' in arg for arg in cmdline):
                    self.logger.info(f"Terminating existing process: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.terminate()
                    proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                pass
    
    def _should_use_hybrid_manager(self) -> bool:
        """Determine if hybrid manager should be used"""
        try:
            # Check if hybrid_manager.py exists
            files = self.drive_service.list_files()
            return any(f['name'] == 'hybrid_manager.py' for f in files)
        except:
            return False
    
    def _start_with_hybrid_manager(self) -> bool:
        """Start services using hybrid manager"""
        try:
            self.logger.info("Starting services with hybrid_manager.py...")
            
            # Download hybrid manager to temp location
            hybrid_content = self.drive_service.read_file('hybrid_manager.py')
            temp_hybrid = Path('/tmp/hybrid_manager.py')
            temp_hybrid.write_bytes(hybrid_content)
            
            # Start hybrid manager
            process = subprocess.Popen(
                [sys.executable, str(temp_hybrid), 'start'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for startup
            time.sleep(10)
            
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.logger.error(f"Hybrid manager failed to start: {stderr.decode()}")
                return False
            
            self.logger.info("✅ Hybrid manager started successfully")
            
            # Verify services are running
            time.sleep(5)
            return self._verify_all_services_running()
            
        except Exception as e:
            self.logger.error(f"❌ Hybrid manager startup failed: {e}")
            return False
    
    def _start_services_directly(self) -> bool:
        """Start services directly without hybrid manager"""
        self.logger.info("Starting services directly...")
        
        # Start in dependency order
        startup_order = self._get_startup_order()
        
        for service_id in startup_order:
            config = self.services[service_id]
            
            try:
                # Download service file to temp
                service_content = self.drive_service.read_file(f"{config['name']}.py")
                temp_service = Path(f"/tmp/{config['name']}.py")
                temp_service.write_bytes(service_content)
                
                # Start service
                process = subprocess.Popen(
                    [sys.executable, str(temp_service)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for startup
                time.sleep(config['startup_delay'])
                
                # Check if started
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    if config['critical']:
                        self.logger.error(f"❌ Critical service {config['name']} failed: {stderr.decode()}")
                        return False
                    else:
                        self.logger.warning(f"⚠️ Non-critical service {config['name']} failed")
                        self.startup_state['warnings'].append(f"{config['name']} failed to start")
                else:
                    self.logger.info(f"✅ Started {config['name']}")
                    self.startup_state['services_started'][service_id] = True
                    
            except Exception as e:
                if config['critical']:
                    self.logger.error(f"❌ Failed to start {config['name']}: {e}")
                    return False
                else:
                    self.logger.warning(f"⚠️ Failed to start {config['name']}: {e}")
                    self.startup_state['warnings'].append(f"{config['name']}: {str(e)}")
        
        self._save_startup_state()
        return True
    
    def _get_startup_order(self) -> List[str]:
        """Get service startup order based on dependencies"""
        order = []
        remaining = set(self.services.keys())
        
        while remaining:
            for service_id in list(remaining):
                config = self.services[service_id]
                deps = config['dependencies']
                
                if all(dep in order for dep in deps):
                    order.append(service_id)
                    remaining.remove(service_id)
        
        return order
    
    def _verify_all_services_running(self) -> bool:
        """Verify all services are running"""
        all_running = True
        
        for service_id, config in self.services.items():
            if self._check_service_health(config['name'], config['port']):
                self.logger.info(f"✅ {config['name']} is healthy")
                self.startup_state['services_started'][service_id] = True
            else:
                if config['critical']:
                    self.logger.error(f"❌ Critical service {config['name']} not responding")
                    all_running = False
                else:
                    self.logger.warning(f"⚠️ Non-critical service {config['name']} not responding")
                    self.startup_state['warnings'].append(f"{config['name']} not responding")
        
        return all_running
    
    def _check_service_health(self, service_name: str, port: int) -> bool:
        """Check if a service is healthy"""
        import requests
        
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _validate_system(self) -> bool:
        """Validate the complete system is operational"""
        self.logger.info("\n🔍 PHASE 4: SYSTEM VALIDATION")
        self.startup_state['phase'] = 'validation'
        
        try:
            # Run diagnostic toolkit if available
            diagnostic_result = self._run_diagnostic_toolkit()
            
            # Check coordination service
            coord_healthy = self._check_service_health('coordination_service', 5000)
            
            # Calculate system score
            services_running = len(self.startup_state['services_started'])
            total_services = len(self.services)
            system_score = (services_running / total_services) * 100
            
            self.logger.info(f"\n📊 SYSTEM STATUS:")
            self.logger.info(f"   Services Running: {services_running}/{total_services}")
            self.logger.info(f"   System Score: {system_score:.0f}/100")
            self.logger.info(f"   Coordination Service: {'✅ Healthy' if coord_healthy else '❌ Unhealthy'}")
            
            if diagnostic_result:
                self.logger.info(f"   Diagnostic Score: {diagnostic_result}")
            
            self._save_startup_state()
            
            return system_score >= 80 and coord_healthy
            
        except Exception as e:
            self.logger.error(f"❌ System validation failed: {e}")
            return False
    
    def _run_diagnostic_toolkit(self) -> Optional[str]:
        """Run diagnostic toolkit if available"""
        try:
            # Check if diagnostic toolkit exists
            files = self.drive_service.list_files()
            diagnostic_file = next((f for f in files if 'diagnostic_toolkit' in f['name']), None)
            
            if diagnostic_file:
                # Download and run
                diagnostic_content = self.drive_service.read_file(diagnostic_file['name'])
                temp_diagnostic = Path(f"/tmp/{diagnostic_file['name']}")
                temp_diagnostic.write_bytes(diagnostic_content)
                
                result = subprocess.run(
                    [sys.executable, str(temp_diagnostic), '--report'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Parse score from output
                    for line in result.stdout.split('\n'):
                        if 'System Score:' in line:
                            return line.strip()
                
        except Exception as e:
            self.logger.debug(f"Diagnostic toolkit not available: {e}")
        
        return None
    
    def _generate_startup_report(self):
        """Generate comprehensive startup report"""
        self.logger.info("\n📄 PHASE 5: STARTUP REPORT GENERATION")
        
        duration = (datetime.now() - self.start_time).total_seconds()
        
        report = {
            'startup_time': self.start_time.isoformat(),
            'duration_seconds': duration,
            'implementation_id': 'STARTUP-' + datetime.now().strftime('%Y%m%d-%H%M%S'),
            'checks_passed': self.startup_state['checks_passed'],
            'services_started': self.startup_state['services_started'],
            'errors': self.startup_state['errors'],
            'warnings': self.startup_state['warnings'],
            'final_status': 'SUCCESS' if not self.startup_state['errors'] else 'FAILED'
        }
        
        # Save report to Google Drive
        report_filename = f"startup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.drive_service.save_json(report_filename, report, 'reports')
        
        self.logger.info(f"\n📊 STARTUP SUMMARY:")
        self.logger.info(f"   Duration: {duration:.1f} seconds")
        self.logger.info(f"   Checks Passed: {sum(1 for v in self.startup_state['checks_passed'].values() if v)}/{len(self.startup_state['checks_passed'])}")
        self.logger.info(f"   Services Started: {len(self.startup_state['services_started'])}/{len(self.services)}")
        self.logger.info(f"   Errors: {len(self.startup_state['errors'])}")
        self.logger.info(f"   Warnings: {len(self.startup_state['warnings'])}")
        self.logger.info(f"   Report Saved: {report_filename}")
    
    def _save_startup_state(self):
        """Save current startup state to Google Drive"""
        try:
            state_data = {
                'timestamp': datetime.now().isoformat(),
                'phase': self.startup_state['phase'],
                'checks_passed': self.startup_state['checks_passed'],
                'services_started': self.startup_state['services_started'],
                'errors': self.startup_state['errors'][-10:],  # Last 10 errors
                'warnings': self.startup_state['warnings'][-10:]  # Last 10 warnings
            }
            
            self.drive_service.save_json('startup_state.json', state_data, 'coordination')
            
        except Exception as e:
            self.logger.debug(f"Failed to save startup state: {e}")


def main():
    """Main entry point"""
    print("🚀 ENHANCED STARTUP MANAGER v2.0.1")
    print("=" * 60)
    
    # Initialize and run
    manager = EnhancedStartupManager()
    success = manager.run_startup_sequence()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

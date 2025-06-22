#!/usr/bin/env python3
"""
TRADING SYSTEM PHASE 1 - ENHANCED VERSION (CLI ONLY)
Service: Hybrid Service Manager (CLI Service Control)
Version: 3.0.2-CLI
Last Updated: 2025-06-20

REVISION HISTORY:
- v3.0.2-CLI (2025-06-20) - Removed GUI for headless operation in Google Colab
- v3.0.2 (2025-06-20) - Added database table verification, startup delays, health check verification
- v3.0.1 (2025-06-19) - Enhanced with architecture implementation requirements
- v3.0.0 (2025-06-18) - Major refactor with GUI, enhanced monitoring and orchestration

This CLI version provides:
1. Service lifecycle management
2. Real-time health monitoring
3. System metrics and performance tracking
4. Database table verification before startup
5. Command-line interface for Google Colab
"""

import subprocess
import psutil
import requests
import json
import time
import threading
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
import logging
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('hybrid_manager')

class ServiceManager:
    def __init__(self):
        # Updated service list to match v3.0.2
        self.services = [
            {"name": "coordination_service", "port": 5000, "process": None, "status": "Stopped", "critical": True, "startup_delay": 5},
            {"name": "security_scanner", "port": 5001, "process": None, "status": "Stopped", "critical": True, "startup_delay": 3},
            {"name": "pattern_analysis", "port": 5002, "process": None, "status": "Stopped", "critical": True, "startup_delay": 3},
            {"name": "technical_analysis", "port": 5003, "process": None, "status": "Stopped", "critical": True, "startup_delay": 3},
            {"name": "paper_trading", "port": 5005, "process": None, "status": "Stopped", "critical": True, "startup_delay": 3},
            {"name": "pattern_recognition_service", "port": 5006, "process": None, "status": "Stopped", "critical": True, "startup_delay": 3},
            {"name": "news_service", "port": 5008, "process": None, "status": "Stopped", "critical": False, "startup_delay": 3},
            {"name": "reporting_service", "port": 5009, "process": None, "status": "Stopped", "critical": False, "startup_delay": 3},
            {"name": "web_dashboard", "port": 8080, "process": None, "status": "Stopped", "critical": False, "startup_delay": 3}
        ]
        self.monitoring_active = False
        self.db_path = "./trading_system.db"
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutdown signal received. Stopping services...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)
        
    def verify_database_tables(self):
        """Verify all required database tables exist"""
        try:
            if not Path(self.db_path).exists():
                logger.error(f"Database {self.db_path} not found!")
                return False
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # List of required tables from v3.0.2
            required_tables = [
                'service_registry',
                'trading_schedule',
                'news_articles',
                'technical_indicators',
                'patterns',
                'signals',
                'trades',
                'risk_metrics',
                'ml_predictions',
                'system_events'
            ]
            
            # Check each table
            missing_tables = []
            for table in required_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not cursor.fetchone():
                    missing_tables.append(table)
            
            conn.close()
            
            if missing_tables:
                logger.warning(f"Missing database tables: {missing_tables}")
                logger.info("Running database migration...")
                return self.run_database_migration()
            
            logger.info("All required database tables verified ✓")
            return True
            
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            return False
    
    def run_database_migration(self):
        """Run database migration if needed"""
        try:
            migration_path = Path("./database_migration.py")
            if migration_path.exists():
                result = subprocess.run([sys.executable, str(migration_path)], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("Database migration completed successfully")
                    return True
                else:
                    logger.error(f"Database migration failed: {result.stderr}")
                    return False
            else:
                logger.error("database_migration.py not found")
                return False
        except Exception as e:
            logger.error(f"Migration error: {str(e)}")
            return False
    
    def start_service(self, service):
        """Start an individual service with health check verification"""
        try:
            if service["process"] and service["process"].poll() is None:
                logger.info(f"{service['name']} is already running")
                return True
                
            logger.info(f"Starting {service['name']}...")
            
            # Build command based on service name
            if service["name"] == "web_dashboard":
                cmd = [sys.executable, f"./web_dashboard_service.py"]
            else:
                cmd = [sys.executable, f"./{service['name']}.py"]
                
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            service["process"] = process
            service["status"] = "Starting"
            service["start_time"] = datetime.now()
            
            # Wait for startup delay
            logger.info(f"Waiting {service['startup_delay']}s for {service['name']} to initialize...")
            time.sleep(service['startup_delay'])
            
            # Verify service is healthy
            if self.check_service_health(service):
                service["status"] = "Running"
                logger.info(f"✓ {service['name']} started successfully (PID: {process.pid})")
                return True
            else:
                service["status"] = "Failed"
                if process.poll() is None:
                    process.terminate()
                    process.wait()
                logger.error(f"✗ {service['name']} failed health check")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {service['name']}: {str(e)}")
            service["status"] = "Error"
            return False
    
    def check_service_health(self, service, max_retries=10):
        """Check if a service is healthy via HTTP endpoint"""
        url = f"http://localhost:{service['port']}/health"
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return True
            except:
                pass
            
            if attempt < max_retries - 1:
                time.sleep(1)
        
        return False
    
    def stop_service(self, service):
        """Stop an individual service"""
        try:
            if service["process"] and service["process"].poll() is None:
                logger.info(f"Stopping {service['name']}...")
                service["process"].terminate()
                service["process"].wait(timeout=5)
                service["status"] = "Stopped"
                service["process"] = None
                logger.info(f"✓ {service['name']} stopped")
            else:
                service["status"] = "Stopped"
                service["process"] = None
        except subprocess.TimeoutExpired:
            logger.warning(f"Force killing {service['name']}")
            service["process"].kill()
            service["process"].wait()
            service["status"] = "Stopped"
            service["process"] = None
        except Exception as e:
            logger.error(f"Error stopping {service['name']}: {str(e)}")
    
    def start_all_services(self):
        """Start all services in the correct order"""
        print("\n🚀 STARTING TRADING SYSTEM SERVICES")
        print("=" * 60)
        
        # Verify database first
        if not self.verify_database_tables():
            print("❌ Database verification failed. Cannot start services.")
            return False
        
        # Start coordination service first (it's the master)
        coord_service = next(s for s in self.services if s["name"] == "coordination_service")
        if not self.start_service(coord_service):
            print("❌ Failed to start coordination service. Aborting.")
            return False
        
        # Start other services
        for service in self.services:
            if service["name"] != "coordination_service":
                self.start_service(service)
        
        # Print status
        self.print_status()
        
        # Start monitoring
        if self.monitoring_active:
            self.start_monitoring()
        
        return True
    
    def stop_all_services(self):
        """Stop all services"""
        print("\n🛑 STOPPING ALL SERVICES")
        print("=" * 60)
        
        for service in reversed(self.services):  # Stop in reverse order
            self.stop_service(service)
        
        print("✓ All services stopped")
    
    def print_status(self):
        """Print current service status"""
        print("\n📊 SERVICE STATUS")
        print("=" * 60)
        print(f"{'Service':<25} {'Status':<12} {'Port':<6} {'PID':<8} {'Uptime'}")
        print("-" * 60)
        
        for service in self.services:
            if service["process"] and service["process"].poll() is None:
                pid = service["process"].pid
                uptime = str(datetime.now() - service.get("start_time", datetime.now())).split('.')[0]
            else:
                pid = "-"
                uptime = "-"
            
            status_icon = {
                "Running": "✓",
                "Stopped": "✗",
                "Starting": "⏳",
                "Failed": "❌",
                "Error": "⚠️"
            }.get(service["status"], "?")
            
            print(f"{service['name']:<25} {status_icon} {service['status']:<10} {service['port']:<6} {pid:<8} {uptime}")
        
        print("=" * 60)
        
        # System metrics
        print("\n📈 SYSTEM METRICS")
        print("=" * 60)
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            print(f"CPU Usage: {cpu_percent}%")
            print(f"Memory: {memory.percent}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)")
            print(f"Disk: {disk.percent}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)")
        except Exception as e:
            print(f"Error getting system metrics: {e}")
        print("=" * 60)
    
    def monitor_services(self):
        """Monitor services and restart if needed"""
        monitor_count = 0
        while self.running and self.monitoring_active:
            monitor_count += 1
            
            for service in self.services:
                if service["process"] and service["process"].poll() is not None:
                    # Service crashed
                    logger.warning(f"{service['name']} crashed! Restarting...")
                    service["status"] = "Crashed"
                    self.start_service(service)
            
            # Print status every 10 checks (5 minutes)
            if monitor_count % 10 == 0:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Monitor check #{monitor_count}")
                self.print_status()
            
            time.sleep(30)  # Check every 30 seconds
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        self.monitoring_active = True
        monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
        monitor_thread.start()
        logger.info("Service monitoring started")


def main():
    """Main entry point"""
    manager = ServiceManager()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            manager.monitoring_active = True
            if manager.start_all_services():
                print("\n✅ Trading System Started Successfully!")
                print("Press Ctrl+C to stop the system\n")
                
                # Keep running
                try:
                    while manager.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            else:
                print("\n❌ Failed to start trading system")
                sys.exit(1)
                
        elif command == "stop":
            manager.stop_all_services()
            
        elif command == "status":
            manager.print_status()
            
        elif command == "restart":
            manager.stop_all_services()
            time.sleep(2)
            manager.monitoring_active = True
            manager.start_all_services()
            
        elif command == "help":
            print("Trading System Hybrid Manager v3.0.2-CLI")
            print("\nUsage: python hybrid_manager.py [command]")
            print("\nCommands:")
            print("  start    - Start all services with monitoring")
            print("  stop     - Stop all services")
            print("  status   - Show current service status")
            print("  restart  - Restart all services")
            print("  help     - Show this help message")
        else:
            print(f"Unknown command: {command}")
            print("Use 'python hybrid_manager.py help' for usage")
    else:
        # Default: start with monitoring
        print("Starting Trading System (use 'python hybrid_manager.py help' for options)")
        manager.monitoring_active = True
        if manager.start_all_services():
            print("\n✅ Trading System Started Successfully!")
            print("Press Ctrl+C to stop the system\n")
            
            try:
                while manager.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("\n❌ Failed to start trading system")
            sys.exit(1)


if __name__ == "__main__":
    main()

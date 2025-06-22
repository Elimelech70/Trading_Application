"""
Name of Service: TRADING SYSTEM HYBRID ARCHITECTURE - SERVICE MANAGER
Version: 3.0.0
Last Updated: 2025-06-15
REVISION HISTORY:
v3.0.0 (2025-06-15) - Initial hybrid service manager implementation
"""

import os
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional
from .lifecycle_manager import LifecycleManager
from .recovery_manager import RecoveryManager
from .monitoring_engine import MonitoringEngine
from .config_manager import ConfigurationManager

class HybridServiceManager:
    """Main manager for hybrid architecture - manages v2.0 services with simplified approach"""
    
    def __init__(self, config: ConfigurationManager):
        """Initialize the hybrid service manager"""
        self.config = config
        self.logger = logging.getLogger('HybridServiceManager')
        
        # Service registry from configuration
        self.services = config.get_services()
        
        # Component managers
        self.lifecycle = LifecycleManager(self)
        self.recovery = RecoveryManager(self)
        self.monitor = MonitoringEngine(self)
        
        # State tracking
        self.running = False
        self.start_time = None
        
        self.logger.info("Hybrid Service Manager initialized")
    
    def start(self, recovery_mode: bool = False):
        """Start the trading system"""
        try:
            self.start_time = datetime.now()
            
            if recovery_mode and self.recovery.checkpoint_exists():
                # Recover from checkpoint
                self.logger.info("Starting in recovery mode")
                self.recovery.restore_from_checkpoint()
            else:
                # Fresh start
                self.logger.info("Starting fresh system")
                
                # Run database migration first
                self._run_database_migration()
                
                # Start all services
                self.lifecycle.start_all_services()
            
            # Mark system as running
            self.running = True
            
            # Start monitoring in background
            self.monitor.start()
            
            # Save initial checkpoint
            self.recovery.save_checkpoint()
            
            self.logger.info("Trading system started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting system: {str(e)}")
            self.stop()
            raise
    
    def stop(self):
        """Graceful shutdown of all services"""
        try:
            self.logger.info("Initiating graceful shutdown")
            self.running = False
            
            # Stop monitoring
            self.monitor.stop()
            
            # Save final state
            if self.recovery:
                self.recovery.save_final_state()
            
            # Stop all services
            self.lifecycle.stop_all_services()
            
            self.logger.info("Trading system stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        return self.lifecycle.restart_service(service_name)
    
    def get_status(self) -> Dict:
        """Get current system status"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        service_statuses = {}
        for name in self.services:
            service_statuses[name] = self.lifecycle.get_service_status(name)
        
        return {
            'system_status': 'running' if self.running else 'stopped',
            'uptime_seconds': uptime,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'services': service_statuses,
            'monitoring': {
                'enabled': self.monitor.is_running(),
                'checks_performed': self.monitor.get_check_count()
            },
            'recovery': {
                'last_checkpoint': self.recovery.get_last_checkpoint_time(),
                'checkpoints_saved': self.recovery.get_checkpoint_count()
            }
        }
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0
    
    def _run_database_migration(self):
        """Run database migration before starting services"""
        self.logger.info("Running database migration")
        
        import subprocess
        try:
            # Run migration script
            result = subprocess.run(
                ['python', 'database_migration.py'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Database migration failed: {result.stderr}")
            
            self.logger.info("Database migration completed successfully")
            
        except subprocess.TimeoutExpired:
            raise Exception("Database migration timed out")
        except Exception as e:
            raise Exception(f"Database migration error: {str(e)}")

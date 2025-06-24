"""
Name of Service: TRADING SYSTEM HYBRID ARCHITECTURE - LIFECYCLE MANAGER
Version: 3.0.1
Last Updated: 2025-06-15
REVISION HISTORY:
v3.0.1 (2025-06-15) - Added dashboard to startup_order and stop_order
v3.0.0 (2025-06-15) - Initial lifecycle manager implementation
"""

import subprocess
import time
import logging
import requests
import os
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ProcessInfo:
    """Information about a managed subprocess"""
    name: str
    config: dict
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    status: str = "stopped"  # stopped, starting, running, crashed, unhealthy

class LifecycleManager:
    """Manages service lifecycle - start, stop, restart, health checks"""
    
    def __init__(self, manager):
        self.manager = manager
        self.logger = logging.getLogger('LifecycleManager')
        self.processes: Dict[str, ProcessInfo] = {}
        
        # Initialize process info for each service
        for name, config in manager.services.items():
            self.processes[name] = ProcessInfo(name=name, config=config)
    
    def start_all_services(self):
        """Start all services in dependency order"""
        self.logger.info("Starting all services")
        
        # Service startup order (based on dependencies)
        startup_order = [
            'coordination',      # Must start first
            'scanner',          # Needs coordination
            'pattern',          # Needs coordination
            'technical',        # Needs coordination
            'news',            # Independent
            'pattern_rec',     # Independent
            'trading',         # Needs technical analysis
            'reporting',        # Needs all others
            'dashboard'         # Web UI - starts last
        ]
        
        for service_name in startup_order:
            if service_name in self.processes:
                success = self.start_service(service_name)
                if not success and self._is_critical_service(service_name):
                    raise Exception(f"Failed to start critical service: {service_name}")
                
                # Wait between service starts
                time.sleep(self.processes[service_name].config.get('startup_delay', 2))
    
    def start_service(self, name: str) -> bool:
        """Start individual service"""
        if name not in self.processes:
            self.logger.error(f"Unknown service: {name}")
            return False
        
        process_info = self.processes[name]
        
        # Check if already running
        if process_info.status == "running" and self._is_process_alive(process_info):
            self.logger.info(f"Service {name} is already running")
            return True
        
        self.logger.info(f"Starting service: {name}")
        process_info.status = "starting"
        
        try:
            # Prepare command
            service_file = process_info.config['file']
            cmd = ['python', '-u', service_file]  # -u for unbuffered output
            
            # Start subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd='./',
                env=self._get_service_env()
            )
            
            # Update process info
            process_info.process = process
            process_info.pid = process.pid
            process_info.started_at = datetime.now()
            
            # Wait for startup
            time.sleep(process_info.config.get('startup_delay', 2))
            
            # Verify service is healthy
            if self._check_service_health(name):
                process_info.status = "running"
                self.logger.info(f"Service {name} started successfully (PID: {process.pid})")
                return True
            else:
                self.logger.error(f"Service {name} failed health check after startup")
                self.stop_service(name)
                process_info.status = "crashed"
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting service {name}: {str(e)}")
            process_info.status = "crashed"
            return False
    
    def stop_service(self, name: str) -> bool:
        """Stop individual service"""
        if name not in self.processes:
            return False
        
        process_info = self.processes[name]
        
        if process_info.process and self._is_process_alive(process_info):
            self.logger.info(f"Stopping service: {name}")
            
            try:
                # Try graceful shutdown first
                process_info.process.terminate()
                
                # Wait up to 5 seconds for graceful shutdown
                for _ in range(50):
                    if process_info.process.poll() is not None:
                        break
                    time.sleep(0.1)
                
                # Force kill if still running
                if process_info.process.poll() is None:
                    self.logger.warning(f"Force killing service: {name}")
                    process_info.process.kill()
                    process_info.process.wait()
                
                process_info.status = "stopped"
                self.logger.info(f"Service {name} stopped")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping service {name}: {str(e)}")
                return False
        
        return True
    
    def stop_all_services(self):
        """Stop all services in reverse order"""
        self.logger.info("Stopping all services")
        
        # Stop in reverse order
        stop_order = ['dashboard', 'reporting', 'trading', 'pattern_rec', 'news', 
                     'technical', 'pattern', 'scanner', 'coordination']
        
        for service_name in stop_order:
            if service_name in self.processes:
                self.stop_service(service_name)
    
    def restart_service(self, name: str, reason: str = "Manual restart") -> bool:
        """Restart a service"""
        if name not in self.processes:
            return False
        
        process_info = self.processes[name]
        process_info.restart_count += 1
        
        self.logger.info(f"Restarting service {name}: {reason}")
        
        # Check restart limit
        max_restarts = self.manager.config.get_system_config()['max_restart_attempts']
        if process_info.restart_count > max_restarts:
            self.logger.error(f"Service {name} exceeded max restart attempts ({max_restarts})")
            process_info.status = "failed"
            return False
        
        # Stop the service
        self.stop_service(name)
        
        # Wait before restart (exponential backoff)
        backoff_base = self.manager.config.get_system_config()['restart_backoff_base']
        wait_time = min(backoff_base * (2 ** (process_info.restart_count - 1)), 60)
        self.logger.info(f"Waiting {wait_time}s before restart")
        time.sleep(wait_time)
        
        # Start the service
        success = self.start_service(name)
        
        if success:
            # Reset restart count on successful restart
            process_info.restart_count = 0
        
        return success
    
    def check_service_health(self, name: str) -> bool:
        """Check if a service is healthy"""
        return self._check_service_health(name)
    
    def get_service_status(self, name: str) -> Dict:
        """Get detailed status of a service"""
        if name not in self.processes:
            return {'error': 'Unknown service'}
        
        process_info = self.processes[name]
        
        return {
            'name': name,
            'status': process_info.status,
            'pid': process_info.pid,
            'port': process_info.config.get('port'),
            'started_at': process_info.started_at.isoformat() if process_info.started_at else None,
            'uptime': (datetime.now() - process_info.started_at).total_seconds() if process_info.started_at else 0,
            'restart_count': process_info.restart_count,
            'last_health_check': process_info.last_health_check.isoformat() if process_info.last_health_check else None,
            'is_alive': self._is_process_alive(process_info),
            'is_healthy': self._check_service_health(name)
        }
    
    def _is_process_alive(self, process_info: ProcessInfo) -> bool:
        """Check if subprocess is still running"""
        if process_info.process:
            return process_info.process.poll() is None
        return False
    
    def _check_service_health(self, name: str) -> bool:
        """Check service health via HTTP endpoint"""
        if name not in self.processes:
            return False
        
        process_info = self.processes[name]
        
        # First check if process is alive
        if not self._is_process_alive(process_info):
            return False
        
        # Then check HTTP health endpoint
        try:
            port = process_info.config.get('port')
            health_endpoint = process_info.config.get('health_endpoint', '/health')
            url = f"http://localhost:{port}{health_endpoint}"
            
            response = requests.get(url, timeout=5)
            is_healthy = response.status_code == 200
            
            process_info.last_health_check = datetime.now()
            
            return is_healthy
            
        except Exception:
            return False
    
    def _get_service_env(self) -> dict:
        """Get environment variables for services"""
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'  # Ensure unbuffered output
        return env
    
    def _is_critical_service(self, name: str) -> bool:
        """Check if service is critical for system operation"""
        critical_services = ['coordination', 'scanner', 'technical']
        return name in critical_services

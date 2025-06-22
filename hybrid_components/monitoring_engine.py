"""
Name of Service: TRADING SYSTEM HYBRID ARCHITECTURE - MONITORING ENGINE
Version: 3.0.0
Last Updated: 2025-06-15
REVISION HISTORY:
v3.0.0 (2025-06-15) - Initial monitoring engine implementation
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List

class MonitoringEngine:
    """Monitors service health and triggers auto-restart when needed"""
    
    def __init__(self, manager):
        self.manager = manager
        self.logger = logging.getLogger('MonitoringEngine')
        
        # Monitoring state
        self.running = False
        self.monitor_thread = None
        self.check_count = 0
        self.last_checkpoint_save = None
        
        # Get monitoring intervals from config
        system_config = manager.config.get_system_config()
        self.health_check_interval = system_config['health_check_interval']
        self.checkpoint_interval = system_config['checkpoint_interval']
        
        # Metrics storage
        self.service_metrics = {}
        self._init_metrics()
    
    def start(self):
        """Start monitoring in background thread"""
        if self.running:
            self.logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Monitoring engine started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Monitoring engine stopped")
    
    def is_running(self) -> bool:
        """Check if monitoring is active"""
        return self.running
    
    def get_check_count(self) -> int:
        """Get number of health checks performed"""
        return self.check_count
    
    def get_service_metrics(self, service_name: str) -> Dict:
        """Get metrics for a specific service"""
        return self.service_metrics.get(service_name, {})
    
    def _init_metrics(self):
        """Initialize metrics storage for each service"""
        for service_name in self.manager.services:
            self.service_metrics[service_name] = {
                'health_checks_total': 0,
                'health_checks_passed': 0,
                'crashes_detected': 0,
                'auto_restarts': 0,
                'last_crash_time': None,
                'uptime_percentage': 100.0
            }
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting monitoring loop")
        self.last_checkpoint_save = datetime.now()
        
        while self.running:
            try:
                # Perform health checks
                self._check_all_services()
                
                # Save checkpoint if needed
                if self._should_save_checkpoint():
                    self.manager.recovery.save_checkpoint()
                    self.last_checkpoint_save = datetime.now()
                
                # Sleep until next check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)  # Brief pause before continuing
    
    def _check_all_services(self):
        """Check health of all services"""
        self.check_count += 1
        
        for service_name in self.manager.services:
            self._check_service(service_name)
    
    def _check_service(self, service_name: str):
        """Check individual service health"""
        try:
            lifecycle = self.manager.lifecycle
            process_info = lifecycle.processes.get(service_name)
            
            if not process_info:
                return
            
            metrics = self.service_metrics[service_name]
            metrics['health_checks_total'] += 1
            
            # Check if process is alive
            is_alive = lifecycle._is_process_alive(process_info)
            
            if not is_alive and process_info.status == 'running':
                # Service crashed
                self.logger.error(f"Service {service_name} crashed!")
                metrics['crashes_detected'] += 1
                metrics['last_crash_time'] = datetime.now().isoformat()
                process_info.status = 'crashed'
                
                # Attempt auto-restart
                if self._should_restart_service(service_name):
                    self.logger.info(f"Auto-restarting service {service_name}")
                    success = lifecycle.restart_service(service_name, "Crash detected")
                    
                    if success:
                        metrics['auto_restarts'] += 1
                    else:
                        self.logger.error(f"Failed to auto-restart {service_name}")
                        self._handle_critical_failure(service_name)
            
            elif is_alive:
                # Check HTTP health
                is_healthy = lifecycle.check_service_health(service_name)
                
                if is_healthy:
                    metrics['health_checks_passed'] += 1
                    if process_info.status != 'running':
                        process_info.status = 'running'
                else:
                    # Service is running but unhealthy
                    self.logger.warning(f"Service {service_name} is unhealthy")
                    process_info.status = 'unhealthy'
                    
                    # Consider restart if persistently unhealthy
                    if self._is_persistently_unhealthy(service_name):
                        self.logger.warning(f"Service {service_name} persistently unhealthy, restarting")
                        lifecycle.restart_service(service_name, "Persistent health check failures")
                        metrics['auto_restarts'] += 1
            
            # Update uptime percentage
            if metrics['health_checks_total'] > 0:
                metrics['uptime_percentage'] = round(
                    (metrics['health_checks_passed'] / metrics['health_checks_total']) * 100, 2
                )
                
        except Exception as e:
            self.logger.error(f"Error checking service {service_name}: {str(e)}")
    
    def _should_restart_service(self, service_name: str) -> bool:
        """Determine if a service should be auto-restarted"""
        process_info = self.manager.lifecycle.processes.get(service_name)
        if not process_info:
            return False
        
        # Check restart limit
        max_restarts = self.manager.config.get_system_config()['max_restart_attempts']
        if process_info.restart_count >= max_restarts:
            self.logger.error(f"Service {service_name} exceeded max restart attempts")
            return False
        
        # Check if it's a critical service
        critical_services = ['coordination', 'scanner', 'technical']
        if service_name in critical_services:
            return True
        
        # For non-critical services, check if system can continue
        running_services = sum(1 for p in self.manager.lifecycle.processes.values() 
                              if p.status == 'running')
        
        # Restart if we have enough other services running
        return running_services >= 4
    
    def _is_persistently_unhealthy(self, service_name: str) -> bool:
        """Check if a service has been unhealthy for too long"""
        metrics = self.service_metrics[service_name]
        
        # If last 5 health checks failed, consider it persistently unhealthy
        recent_checks = min(5, metrics['health_checks_total'])
        recent_failures = metrics['health_checks_total'] - metrics['health_checks_passed']
        
        return recent_failures >= recent_checks
    
    def _should_save_checkpoint(self) -> bool:
        """Determine if it's time to save a checkpoint"""
        if not self.last_checkpoint_save:
            return True
        
        time_since_last = datetime.now() - self.last_checkpoint_save
        return time_since_last.total_seconds() >= self.checkpoint_interval
    
    def _handle_critical_failure(self, service_name: str):
        """Handle critical service failures"""
        critical_services = ['coordination', 'scanner', 'technical']
        
        if service_name in critical_services:
            self.logger.critical(f"Critical service {service_name} failed to restart!")
            
            # Save emergency checkpoint
            self.manager.recovery.save_checkpoint()
            
            # Consider stopping the system if coordination service fails
            if service_name == 'coordination':
                self.logger.critical("Coordination service failure - stopping system")
                self.manager.stop()
    
    def get_system_health_summary(self) -> Dict:
        """Get overall system health summary"""
        total_services = len(self.manager.services)
        running_services = sum(1 for p in self.manager.lifecycle.processes.values() 
                              if p.status == 'running')
        
        # Calculate overall health score
        health_score = (running_services / total_services) * 100
        
        # Get service with most crashes
        worst_service = max(self.service_metrics.items(), 
                           key=lambda x: x[1]['crashes_detected'])
        
        return {
            'health_score': round(health_score, 1),
            'total_services': total_services,
            'running_services': running_services,
            'total_health_checks': self.check_count,
            'monitoring_uptime': self._get_monitoring_uptime(),
            'worst_performing_service': {
                'name': worst_service[0],
                'crashes': worst_service[1]['crashes_detected'],
                'uptime_percentage': worst_service[1]['uptime_percentage']
            },
            'last_checkpoint': self.last_checkpoint_save.isoformat() if self.last_checkpoint_save else None
        }
    
    def _get_monitoring_uptime(self) -> float:
        """Get monitoring engine uptime in seconds"""
        # This is a simplified calculation
        return self.check_count * self.health_check_interval

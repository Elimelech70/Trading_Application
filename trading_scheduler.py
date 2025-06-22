"""
Name of Service: TRADING SYSTEM PHASE 1 - TRADING SCHEDULER
Version: 1.0.0
Last Updated: 2025-06-19
REVISION HISTORY:
v1.0.0 (2025-06-19) - Initial release with automated trading schedule management

Trading Scheduler Service - Manages automated trading cycles based on configured schedule
"""

import os
import requests
import logging
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify
import pytz

class TradingSchedulerService:
    def __init__(self, port=5011):
        self.app = Flask(__name__)
        self.port = port
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        
        # Service state
        self.is_running = True
        self.scheduler_thread = None
        
        # Setup routes and start scheduler
        self._setup_routes()
        self._register_with_coordination()
        self._start_scheduler()
        
    def _setup_logging(self):
        import os
        os.makedirs('./logs', exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('TradingSchedulerService')
        
        handler = logging.FileHandler('./logs/trading_scheduler_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _register_with_coordination(self):
        """Register with coordination service"""
        try:
            registration_data = {
                "service_name": "scheduler",
                "port": self.port,
                "endpoints": ["/health", "/status"]
            }
            response = requests.post(f"{self.coordination_service_url}/register_service", 
                                   json=registration_data, timeout=5)
            if response.status_code == 200:
                self.logger.info("Successfully registered with coordination service")
        except Exception as e:
            self.logger.warning(f"Could not register with coordination service: {e}")
    
    def _start_scheduler(self):
        """Start the scheduler thread"""
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Trading scheduler started")
    
    def _scheduler_loop(self):
        """Main scheduler loop that coordinates with coordination service"""
        while self.is_running:
            try:
                # Get schedule configuration from coordination service
                response = requests.get(f"{self.coordination_service_url}/schedule/status", timeout=5)
                
                if response.status_code == 200:
                    schedule_status = response.json()
                    
                    # The coordination service handles the actual scheduling logic
                    # This service just monitors and logs
                    if schedule_status.get('enabled'):
                        next_run = schedule_status.get('next_run')
                        if next_run:
                            self.logger.info(f"Trading schedule active. Next run: {next_run}")
                    else:
                        self.logger.debug("Trading schedule is disabled")
                
                # Check every minute
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "healthy", "service": "scheduler"})
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """Get scheduler service status"""
            try:
                # Get schedule info from coordination service
                response = requests.get(f"{self.coordination_service_url}/schedule/status", timeout=5)
                
                if response.status_code == 200:
                    schedule_info = response.json()
                    return jsonify({
                        "service": "Trading Scheduler",
                        "running": self.is_running,
                        "schedule_enabled": schedule_info.get('enabled', False),
                        "next_run": schedule_info.get('next_run'),
                        "last_run": schedule_info.get('last_run'),
                        "message": "Scheduler service is monitoring trading schedule"
                    })
                
            except Exception as e:
                self.logger.error(f"Error getting status: {e}")
            
            return jsonify({
                "service": "Trading Scheduler",
                "running": self.is_running,
                "message": "Unable to get schedule information"
            })
    
    def run(self):
        """Start the scheduler service"""
        self.logger.info(f"Starting Trading Scheduler Service on port {self.port}")
        
        # Run in production mode
        from waitress import serve
        serve(self.app, host='0.0.0.0', port=self.port, threads=2)

if __name__ == "__main__":
    scheduler = TradingSchedulerService()
    scheduler.run()

"""
Name of Service: TRADING SYSTEM PHASE 1 - WEB DASHBOARD SERVICE
Version: 1.0.4
Last Updated: 2025-06-19
REVISION HISTORY:
v1.0.4 (2025-06-19) - Added Trade tab with trading controls and schedule display
v1.0.3 (2025-06-19) - Enhanced with fallback status checking and auto-registration
v1.0.2 (2025-06-17) - Fixed real-time updates and WebSocket functionality
v1.0.1 (2025-06-15) - Added comprehensive monitoring dashboard
v1.0.0 (2025-06-15) - Initial web dashboard implementation

Web Dashboard Service - Provides real-time monitoring and control interface
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import json
import time

class WebDashboardService:
    def __init__(self, port=5010):
        self.app = Flask(__name__)
        CORS(self.app)
        self.port = port
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        
        # Status cache to reduce load
        self.status_cache = {
            'data': None,
            'timestamp': None,
            'cache_duration': 10  # seconds
        }
        
        self._setup_routes()
        self._register_with_coordination()
        self._initialize_service_registry()
        
    def _setup_logging(self):
        import os
        os.makedirs('./logs', exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('WebDashboardService')
        
        handler = logging.FileHandler('./logs/web_dashboard_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _initialize_service_registry(self):
        """Force registration of all healthy services on startup"""
        try:
            response = requests.post(f"{self.coordination_service_url}/force_register_all", timeout=5)
            if response.status_code == 200:
                self.logger.info("Initialized service registry")
        except Exception as e:
            self.logger.warning(f"Could not initialize registry: {e}")
    
    def _register_with_coordination(self):
        """Register with coordination service"""
        try:
            registration_data = {
                "service_name": "dashboard",
                "port": self.port,
                "endpoints": ["/", "/api/status", "/api/services", "/api/trading_cycle", 
                             "/api/trade/start_cycle", "/api/schedule/status", "/api/schedule/config"]
            }
            response = requests.post(f"{self.coordination_service_url}/register_service", 
                                   json=registration_data, timeout=5)
            if response.status_code == 200:
                self.logger.info("Successfully registered with coordination service")
        except Exception as e:
            self.logger.warning(f"Could not register with coordination service: {e}")
    
    def _check_service_health_direct(self, service_name: str, port: int) -> bool:
        """Check service health directly"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _get_service_status_with_fallback(self):
        """Get comprehensive service status with fallback to direct health checks"""
        # Check cache first
        if self.status_cache['data'] and self.status_cache['timestamp']:
            cache_age = (datetime.now() - self.status_cache['timestamp']).total_seconds()
            if cache_age < self.status_cache['cache_duration']:
                return self.status_cache['data']
        
        services_info = {}
        
        # Known services and their ports
        known_services = {
            "coordination": {"port": 5000, "name": "Coordination Service"},
            "scanner": {"port": 5001, "name": "Security Scanner"},
            "pattern": {"port": 5002, "name": "Pattern Analysis"},
            "technical": {"port": 5003, "name": "Technical Analysis"},
            "trading": {"port": 5005, "name": "Paper Trading"},
            "pattern_rec": {"port": 5006, "name": "Pattern Recognition"},
            "news": {"port": 5008, "name": "News Service"},
            "reporting": {"port": 5009, "name": "Reporting Service"},
            "dashboard": {"port": 5010, "name": "Web Dashboard"},
            "scheduler": {"port": 5011, "name": "Trading Scheduler"}
        }
        
        # Try to get status from coordination service first
        try:
            response = requests.get(f"{self.coordination_service_url}/service_status", timeout=3)
            if response.status_code == 200:
                coord_status = response.json()
                
                # Merge with our known services
                for service_id, service_info in known_services.items():
                    if service_id in coord_status:
                        services_info[service_id] = {
                            **service_info,
                            **coord_status[service_id],
                            'registered': True
                        }
                    else:
                        # Not in coordination service, check directly
                        is_healthy = self._check_service_health_direct(service_id, service_info['port'])
                        services_info[service_id] = {
                            **service_info,
                            'healthy': is_healthy,
                            'registered': False,
                            'status': 'active' if is_healthy else 'inactive'
                        }
                        
                        # If healthy but not registered, try to register it
                        if is_healthy and service_id != 'dashboard':
                            self._attempt_service_registration(service_id, service_info['port'])
        except Exception as e:
            self.logger.error(f"Could not get coordination status: {e}")
            
            # Fallback: check all services directly
            for service_id, service_info in known_services.items():
                is_healthy = self._check_service_health_direct(service_id, service_info['port'])
                services_info[service_id] = {
                    **service_info,
                    'healthy': is_healthy,
                    'registered': False,
                    'status': 'active' if is_healthy else 'inactive'
                }
        
        # Cache the result
        self.status_cache['data'] = services_info
        self.status_cache['timestamp'] = datetime.now()
        
        return services_info
    
    def _attempt_service_registration(self, service_name: str, port: int):
        """Attempt to register a healthy but unregistered service"""
        try:
            registration_data = {
                "service_name": service_name,
                "port": port
            }
            requests.post(f"{self.coordination_service_url}/register_service", 
                         json=registration_data, timeout=2)
        except:
            pass  # Silent fail, will retry on next check
    
    def _setup_routes(self):
        @self.app.route('/')
        def dashboard():
            return render_template_string(DASHBOARD_HTML)
        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "healthy", "service": "dashboard"})
        
        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            """Get overall system status"""
            services = self._get_service_status_with_fallback()
            
            total_services = len(services)
            active_services = sum(1 for s in services.values() if s.get('healthy', False))
            
            # Determine overall status
            if active_services == total_services:
                overall_status = "Fully Operational"
                status_class = "success"
            elif active_services >= total_services * 0.7:
                overall_status = "Degraded Performance"
                status_class = "warning"
            elif active_services > 0:
                overall_status = "Partial Outage"
                status_class = "danger"
            else:
                overall_status = "System Offline"
                status_class = "danger"
            
            return jsonify({
                "overall_status": overall_status,
                "status_class": status_class,
                "active_services": active_services,
                "total_services": total_services,
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/api/services', methods=['GET'])
        def api_services():
            """Get detailed service status"""
            services = self._get_service_status_with_fallback()
            return jsonify(services)
        
        @self.app.route('/api/trading_cycle', methods=['GET'])
        def api_trading_cycle():
            """Get latest trading cycle info"""
            try:
                response = requests.get(f"{self.coordination_service_url}/latest_cycle", timeout=5)
                if response.status_code == 200:
                    return jsonify(response.json())
            except:
                pass
            
            return jsonify({"status": "No active cycle"})
        
        @self.app.route('/api/trade/start_cycle', methods=['POST'])
        def start_trading_cycle():
            """Start a new trading cycle"""
            try:
                response = requests.post(f"{self.coordination_service_url}/start_trading_cycle", timeout=30)
                if response.status_code == 200:
                    return jsonify(response.json())
                else:
                    return jsonify({"error": "Failed to start trading cycle"}), 500
            except Exception as e:
                return jsonify({"error": f"Error starting cycle: {str(e)}"}), 500
        
        @self.app.route('/api/schedule/status', methods=['GET'])
        def get_schedule_status():
            """Get trading schedule status"""
            try:
                response = requests.get(f"{self.coordination_service_url}/schedule/status", timeout=5)
                if response.status_code == 200:
                    return jsonify(response.json())
            except:
                pass
            
            # Default if scheduler not available
            return jsonify({
                "enabled": False,
                "message": "Trading scheduler not available",
                "next_run": None
            })
        
        @self.app.route('/api/schedule/config', methods=['GET', 'POST'])
        def schedule_config():
            """Get or set trading schedule configuration"""
            if request.method == 'GET':
                try:
                    response = requests.get(f"{self.coordination_service_url}/schedule/config", timeout=5)
                    if response.status_code == 200:
                        return jsonify(response.json())
                except:
                    pass
                
                # Default configuration
                return jsonify({
                    "enabled": False,
                    "interval_minutes": 30,
                    "market_hours_only": True,
                    "start_time": "09:30",
                    "end_time": "16:00"
                })
            
            else:  # POST
                try:
                    response = requests.post(f"{self.coordination_service_url}/schedule/config", 
                                           json=request.json, timeout=5)
                    if response.status_code == 200:
                        return jsonify(response.json())
                except Exception as e:
                    return jsonify({"error": str(e)}), 500
    
    def run(self):
        """Start the dashboard service"""
        self.logger.info(f"Starting Web Dashboard Service on port {self.port}")
        
        # Run in production mode
        from waitress import serve
        serve(self.app, host='0.0.0.0', port=self.port, threads=4)

# Enhanced Dashboard HTML with Trade tab
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Trading System Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        .status-card {
            transition: all 0.3s ease;
        }
        .status-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .service-indicator {
            width: 15px;
            height: 15px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }
        .service-healthy {
            background-color: #28a745;
        }
        .service-unhealthy {
            background-color: #dc3545;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .cycle-info {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        .main-status {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .btn-trade {
            font-size: 1.2rem;
            padding: 10px 30px;
            margin: 10px;
        }
        .schedule-info {
            background-color: #e9ecef;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="#">Trading System Dashboard</a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text" id="current-time"></span>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Nav tabs -->
        <ul class="nav nav-tabs" id="dashboardTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button">Overview</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="services-tab" data-bs-toggle="tab" data-bs-target="#services" type="button">Services</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="trade-tab" data-bs-toggle="tab" data-bs-target="#trade" type="button">Trade</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="history-tab" data-bs-toggle="tab" data-bs-target="#history" type="button">Trading History</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="logs-tab" data-bs-toggle="tab" data-bs-target="#logs" type="button">Logs</button>
            </li>
        </ul>

        <!-- Tab content -->
        <div class="tab-content" id="dashboardTabContent">
            <!-- Overview Tab -->
            <div class="tab-pane fade show active" id="overview" role="tabpanel">
                <div class="row mt-4">
                    <div class="col-md-12">
                        <div class="card status-card">
                            <div class="card-body text-center">
                                <h5 class="card-title">System Status</h5>
                                <div id="overall-status" class="main-status">Loading...</div>
                                <p class="card-text">
                                    <span id="active-services">0</span> / <span id="total-services">0</span> Services Active
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="cycle-info" id="cycle-info">
                    <h5>Latest Trading Cycle</h5>
                    <div id="cycle-details">No cycle data available</div>
                </div>
            </div>

            <!-- Services Tab -->
            <div class="tab-pane fade" id="services" role="tabpanel">
                <div class="row mt-4" id="services-grid">
                    <!-- Services will be populated here -->
                </div>
            </div>

            <!-- Trade Tab -->
            <div class="tab-pane fade" id="trade" role="tabpanel">
                <div class="row mt-4">
                    <div class="col-md-12 text-center">
                        <h3>Trading Controls</h3>
                        
                        <div class="mt-4">
                            <button class="btn btn-success btn-lg btn-trade" onclick="startTradingCycle()">
                                Start Trading Cycle
                            </button>
                        </div>
                        
                        <div class="schedule-info">
                            <h5>Trading Schedule</h5>
                            <div id="schedule-status">Loading schedule...</div>
                            
                            <div class="mt-3">
                                <button class="btn btn-primary" onclick="showScheduleConfig()">
                                    Configure Schedule
                                </button>
                            </div>
                        </div>
                        
                        <div id="trading-result" class="mt-4"></div>
                    </div>
                </div>
                
                <!-- Schedule Configuration Modal -->
                <div class="modal fade" id="scheduleModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Trading Schedule Configuration</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <form id="scheduleForm">
                                    <div class="mb-3">
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" id="scheduleEnabled">
                                            <label class="form-check-label" for="scheduleEnabled">
                                                Enable Automated Trading
                                            </label>
                                        </div>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="intervalMinutes" class="form-label">Trading Interval (minutes)</label>
                                        <input type="number" class="form-control" id="intervalMinutes" value="30" min="5" max="240">
                                    </div>
                                    
                                    <div class="mb-3">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="marketHoursOnly" checked>
                                            <label class="form-check-label" for="marketHoursOnly">
                                                Trade only during market hours
                                            </label>
                                        </div>
                                    </div>
                                    
                                    <div class="row">
                                        <div class="col">
                                            <label for="startTime" class="form-label">Start Time</label>
                                            <input type="time" class="form-control" id="startTime" value="09:30">
                                        </div>
                                        <div class="col">
                                            <label for="endTime" class="form-label">End Time</label>
                                            <input type="time" class="form-control" id="endTime" value="16:00">
                                        </div>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-primary" onclick="saveScheduleConfig()">Save Schedule</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Trading History Tab -->
            <div class="tab-pane fade" id="history" role="tabpanel">
                <div class="mt-4">
                    <h5>Recent Trading Activity</h5>
                    <p>Trading history will be displayed here once trading begins.</p>
                </div>
            </div>

            <!-- Logs Tab -->
            <div class="tab-pane fade" id="logs" role="tabpanel">
                <div class="mt-4">
                    <h5>System Logs</h5>
                    <div class="bg-dark text-light p-3 rounded" style="height: 400px; overflow-y: auto;">
                        <pre id="log-content">Logs will appear here...</pre>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let scheduleModal;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            scheduleModal = new bootstrap.Modal(document.getElementById('scheduleModal'));
            updateDashboard();
            setInterval(updateDashboard, 5000);
            setInterval(updateTime, 1000);
            updateTime();
        });

        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = now.toLocaleString();
        }

        async function updateDashboard() {
            try {
                // Update overall status
                const statusResponse = await axios.get('/api/status');
                const status = statusResponse.data;
                
                const statusElement = document.getElementById('overall-status');
                statusElement.textContent = status.overall_status;
                statusElement.className = 'main-status text-' + status.status_class;
                
                document.getElementById('active-services').textContent = status.active_services;
                document.getElementById('total-services').textContent = status.total_services;
                
                // Update services grid
                const servicesResponse = await axios.get('/api/services');
                updateServicesGrid(servicesResponse.data);
                
                // Update cycle info
                const cycleResponse = await axios.get('/api/trading_cycle');
                updateCycleInfo(cycleResponse.data);
                
                // Update schedule status
                updateScheduleStatus();
                
            } catch (error) {
                console.error('Error updating dashboard:', error);
            }
        }

        function updateServicesGrid(services) {
            const grid = document.getElementById('services-grid');
            grid.innerHTML = '';
            
            Object.entries(services).forEach(([id, service]) => {
                const isHealthy = service.healthy || false;
                const isRegistered = service.registered || false;
                
                const card = document.createElement('div');
                card.className = 'col-md-4 mb-3';
                card.innerHTML = `
                    <div class="card status-card ${isHealthy ? 'border-success' : 'border-danger'}">
                        <div class="card-body">
                            <h5 class="card-title">
                                <span class="service-indicator ${isHealthy ? 'service-healthy' : 'service-unhealthy'}"></span>
                                ${service.name}
                            </h5>
                            <p class="card-text">
                                Port: ${service.port}<br>
                                Status: ${isHealthy ? 'Healthy' : 'Unhealthy'}<br>
                                Registered: ${isRegistered ? 'Yes' : 'No'}
                            </p>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function updateCycleInfo(cycleData) {
            const cycleDetails = document.getElementById('cycle-details');
            
            if (cycleData && cycleData.cycle_id) {
                cycleDetails.innerHTML = `
                    <p><strong>Cycle ID:</strong> ${cycleData.cycle_id}</p>
                    <p><strong>Status:</strong> ${cycleData.status}</p>
                    <p><strong>Started:</strong> ${cycleData.started_at || 'N/A'}</p>
                    <p><strong>Securities Scanned:</strong> ${cycleData.securities_scanned || 0}</p>
                    <p><strong>Patterns Analyzed:</strong> ${cycleData.patterns_analyzed || 0}</p>
                    <p><strong>Signals Generated:</strong> ${cycleData.signals_generated || 0}</p>
                    <p><strong>Trades Executed:</strong> ${cycleData.trades_executed || 0}</p>
                `;
            } else {
                cycleDetails.innerHTML = '<p>No active trading cycle</p>';
            }
        }
        
        async function startTradingCycle() {
            const resultDiv = document.getElementById('trading-result');
            resultDiv.innerHTML = '<div class="alert alert-info">Starting trading cycle...</div>';
            
            try {
                const response = await axios.post('/api/trade/start_cycle');
                resultDiv.innerHTML = `
                    <div class="alert alert-success">
                        <h5>Trading Cycle Started Successfully!</h5>
                        <p>Cycle ID: ${response.data.cycle_id}</p>
                        <p>Status: ${response.data.status}</p>
                        <p>Securities Scanned: ${response.data.securities_scanned}</p>
                        <p>Trades Executed: ${response.data.trades_executed}</p>
                    </div>
                `;
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <h5>Error Starting Trading Cycle</h5>
                        <p>${error.response?.data?.error || error.message}</p>
                    </div>
                `;
            }
        }
        
        async function updateScheduleStatus() {
            try {
                const response = await axios.get('/api/schedule/status');
                const status = response.data;
                
                const scheduleDiv = document.getElementById('schedule-status');
                if (status.enabled) {
                    scheduleDiv.innerHTML = `
                        <p class="text-success"><strong>Schedule Active</strong></p>
                        <p>Next run: ${status.next_run || 'Calculating...'}</p>
                        <p>Interval: ${status.interval_minutes || 30} minutes</p>
                    `;
                } else {
                    scheduleDiv.innerHTML = `
                        <p class="text-muted">Automated trading is disabled</p>
                        <p>Click "Configure Schedule" to enable</p>
                    `;
                }
            } catch (error) {
                console.error('Error updating schedule status:', error);
            }
        }
        
        async function showScheduleConfig() {
            try {
                const response = await axios.get('/api/schedule/config');
                const config = response.data;
                
                document.getElementById('scheduleEnabled').checked = config.enabled || false;
                document.getElementById('intervalMinutes').value = config.interval_minutes || 30;
                document.getElementById('marketHoursOnly').checked = config.market_hours_only !== false;
                document.getElementById('startTime').value = config.start_time || '09:30';
                document.getElementById('endTime').value = config.end_time || '16:00';
                
                scheduleModal.show();
            } catch (error) {
                alert('Error loading schedule configuration');
            }
        }
        
        async function saveScheduleConfig() {
            const config = {
                enabled: document.getElementById('scheduleEnabled').checked,
                interval_minutes: parseInt(document.getElementById('intervalMinutes').value),
                market_hours_only: document.getElementById('marketHoursOnly').checked,
                start_time: document.getElementById('startTime').value,
                end_time: document.getElementById('endTime').value
            };
            
            try {
                await axios.post('/api/schedule/config', config);
                scheduleModal.hide();
                updateScheduleStatus();
                alert('Schedule configuration saved successfully!');
            } catch (error) {
                alert('Error saving schedule configuration');
            }
        }
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    dashboard = WebDashboardService()
    dashboard.run()

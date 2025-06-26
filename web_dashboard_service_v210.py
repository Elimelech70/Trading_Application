#!/usr/bin/env python3
"""
Name of Service: Web Dashboard Service
Filename: web_dashboard_service.py
Version: 2.1.0
Last Updated: 2025-01-27
REVISION HISTORY:
v2.1.0 (2025-01-27) - Separated trading dashboard from main system health dashboard
v2.0.0 (2025-06-24) - Provides comprehensive trading system monitoring with integrated workflow tracking
v1.0.4 (2025-06-19) - Added Trade tab with trading controls and schedule display
v1.0.3 (2025-06-19) - Enhanced with fallback status checking and auto-registration
v1.0.2 (2025-06-17) - Fixed real-time updates and WebSocket functionality
v1.0.1 (2025-06-15) - Added comprehensive monitoring dashboard
v1.0.0 (2025-06-15) - Initial web dashboard implementation
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
import requests

# Import workflow tracking components
from trading_workflow_tracker import TradingWorkflowTracker, WorkflowPhase

class WebDashboardService:
    """
    Web dashboard service with separated system health and trading dashboards
    Main page focuses on system health, trading details on separate page
    """
    
    def __init__(self, db_path='./trading_system.db', port=5010):
        self.db_path = db_path
        self.port = port
        self.app = Flask(__name__)
        
        # Enable CORS
        CORS(self.app)
        
        # Initialize SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize workflow tracker
        self.workflow_tracker = TradingWorkflowTracker(db_path=db_path)
        
        # Service registry for health checks
        self.services = {
            'coordination': {'port': 5000, 'name': 'Coordination Service'},
            'scanner': {'port': 5001, 'name': 'Security Scanner'},
            'pattern': {'port': 5002, 'name': 'Pattern Analysis'},
            'technical': {'port': 5003, 'name': 'Technical Analysis'},
            'trading': {'port': 5005, 'name': 'Paper Trading'},
            'pattern_rec': {'port': 5006, 'name': 'Pattern Recognition'},
            'news': {'port': 5008, 'name': 'News Service'},
            'reporting': {'port': 5009, 'name': 'Reporting Service'},
            'dashboard': {'port': 5010, 'name': 'Web Dashboard'},
            'scheduler': {'port': 5011, 'name': 'Trading Scheduler'}
        }
        
        # Status cache to reduce load
        self.status_cache = {
            'data': None,
            'timestamp': None,
            'cache_duration': 5  # seconds
        }
        
        # Setup
        self._setup_logging()
        self._setup_routes()
        self._setup_workflow_routes()
        self._setup_socketio()
        
        # Background monitoring
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()
        
    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('WebDashboardService')
        
        # File handler
        os.makedirs('./logs', exist_ok=True)
        handler = logging.FileHandler('./logs/web_dashboard_service.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
    
    def _setup_routes(self):
        """Setup main dashboard routes"""
        
        @self.app.route('/')
        def index():
            """Main system health dashboard page"""
            return self._render_main_dashboard()
        
        @self.app.route('/trading')
        def trading_dashboard():
            """Enhanced trading dashboard page"""
            return self._render_trading_dashboard()
        
        @self.app.route('/workflow')
        def workflow_dashboard():
            """Workflow tracking dashboard"""
            if os.path.exists('trading_workflow_dashboard.html'):
                with open('trading_workflow_dashboard.html', 'r') as f:
                    return f.read()
            return "Workflow dashboard not found", 404
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "service": "web-dashboard",
                "timestamp": datetime.now().isoformat()
            })
        
        # System Overview APIs
        @self.app.route('/api/system/overview')
        def get_system_overview():
            """Get complete system overview"""
            try:
                overview = {
                    'trading_stats': self._get_trading_stats(),
                    'system_health': self._get_system_health(),
                    'active_positions': self._get_active_positions(),
                    'recent_trades': self._get_recent_trades(),
                    'workflow_status': self.workflow_tracker.get_workflow_summary()
                }
                return jsonify(overview)
            except Exception as e:
                self.logger.error(f"Error getting system overview: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/services/health')
        def get_services_health():
            """Get health status of all services"""
            return jsonify(self._get_system_health())
        
        @self.app.route('/api/status')
        def api_status():
            """Get overall system status"""
            services = self._get_system_health()
            
            total_services = len(services)
            active_services = sum(1 for s in services.values() if s.get('status') == 'healthy')
            
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
        
        @self.app.route('/api/services')
        def api_services():
            """Get detailed service status"""
            return jsonify(self._get_system_health())
        
        @self.app.route('/api/trading/stats')
        def get_trading_stats():
            """Get trading statistics"""
            return jsonify(self._get_trading_stats())
        
        @self.app.route('/api/trading/positions')
        def get_positions():
            """Get current positions"""
            return jsonify(self._get_active_positions())
        
        @self.app.route('/api/trading/trades')
        def get_recent_trades():
            """Get recent trades"""
            limit = int(request.args.get('limit', 50))
            return jsonify(self._get_recent_trades(limit))
        
        @self.app.route('/api/trading/performance')
        def get_performance():
            """Get performance metrics"""
            days = int(request.args.get('days', 7))
            return jsonify(self._get_performance_metrics(days))
        
        @self.app.route('/api/patterns/effectiveness')
        def get_pattern_effectiveness():
            """Get pattern effectiveness analysis"""
            return jsonify(self._analyze_pattern_effectiveness())
        
        @self.app.route('/api/alerts')
        def get_alerts():
            """Get system alerts"""
            return jsonify(self._get_system_alerts())
        
        @self.app.route('/api/trading_cycle')
        def api_trading_cycle():
            """Get latest trading cycle info"""
            try:
                response = requests.get("http://localhost:5000/latest_cycle", timeout=5)
                if response.status_code == 200:
                    return jsonify(response.json())
            except:
                pass
            
            return jsonify({"status": "No active cycle"})
        
        @self.app.route('/api/trade/start_cycle', methods=['POST'])
        def start_trading_cycle():
            """Start a new trading cycle"""
            try:
                response = requests.post("http://localhost:5000/start_trading_cycle", timeout=30)
                if response.status_code == 200:
                    return jsonify(response.json())
                else:
                    return jsonify({"error": "Failed to start trading cycle"}), 500
            except Exception as e:
                return jsonify({"error": f"Error starting cycle: {str(e)}"}), 500
        
        @self.app.route('/api/schedule/status')
        def get_schedule_status():
            """Get trading schedule status"""
            try:
                response = requests.get("http://localhost:5000/schedule/status", timeout=5)
                if response.status_code == 200:
                    return jsonify(response.json())
            except:
                pass
            
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
                    response = requests.get("http://localhost:5000/schedule/config", timeout=5)
                    if response.status_code == 200:
                        return jsonify(response.json())
                except:
                    pass
                
                return jsonify({
                    "enabled": False,
                    "interval_minutes": 30,
                    "market_hours_only": True,
                    "start_time": "09:30",
                    "end_time": "16:00"
                })
            
            else:  # POST
                try:
                    response = requests.post("http://localhost:5000/schedule/config", 
                                           json=request.json, timeout=5)
                    if response.status_code == 200:
                        return jsonify(response.json())
                except Exception as e:
                    return jsonify({"error": str(e)}), 500
    
    def _setup_workflow_routes(self):
        """Setup workflow tracking routes"""
        
        @self.app.route('/api/workflow/current')
        def get_current_workflow():
            """Get current workflow status"""
            try:
                summary = self.workflow_tracker.get_workflow_summary()
                if not summary:
                    history = self.workflow_tracker.get_workflow_history(limit=1)
                    if history:
                        return jsonify(history[0])
                    return jsonify({"error": "No workflow data available"}), 404
                
                # Add completed phases count
                completed_phases = sum(
                    1 for phase_data in summary.get("phases", {}).values()
                    if phase_data.get("status") == "completed"
                )
                summary["completed_phases"] = completed_phases
                return jsonify(summary)
            except Exception as e:
                self.logger.error(f"Error getting current workflow: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/workflow/history')
        def get_workflow_history():
            """Get workflow execution history"""
            try:
                limit = int(request.args.get('limit', 10))
                history = self.workflow_tracker.get_workflow_history(limit=limit)
                return jsonify(history)
            except Exception as e:
                self.logger.error(f"Error getting workflow history: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/workflow/phase/<phase_name>')
        def get_phase_status(phase_name):
            """Get status of a specific phase"""
            try:
                phase_map = {
                    'initialization': WorkflowPhase.INITIALIZATION,
                    'security_selection': WorkflowPhase.SECURITY_SELECTION,
                    'pattern_analysis': WorkflowPhase.PATTERN_ANALYSIS,
                    'signal_generation': WorkflowPhase.SIGNAL_GENERATION,
                    'trade_execution': WorkflowPhase.TRADE_EXECUTION,
                    'completion': WorkflowPhase.COMPLETION
                }
                
                if phase_name not in phase_map:
                    return jsonify({"error": "Invalid phase name"}), 400
                
                phase = phase_map[phase_name]
                status = self.workflow_tracker.get_phase_status(phase)
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting phase status: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/workflow/metrics/phases')
        def get_phase_metrics():
            """Get performance metrics for all phases"""
            try:
                metrics = self.workflow_tracker.get_phase_performance_stats()
                return jsonify(metrics)
            except Exception as e:
                self.logger.error(f"Error getting phase metrics: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/workflow/active')
        def get_active_workflows():
            """Get list of active workflows"""
            try:
                active = self.workflow_tracker.get_active_workflows()
                return jsonify(active)
            except Exception as e:
                self.logger.error(f"Error getting active workflows: {e}")
                return jsonify({"error": str(e)}), 500
    
    def _setup_socketio(self):
        """Setup SocketIO events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.logger.info("Dashboard client connected")
            emit('connected', {'data': 'Connected to trading dashboard'})
            
            # Send initial data
            emit('system_overview', {
                'trading_stats': self._get_trading_stats(),
                'system_health': self._get_system_health(),
                'workflow_status': self.workflow_tracker.get_workflow_summary()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.logger.info("Dashboard client disconnected")
        
        @self.socketio.on('subscribe_updates')
        def handle_subscribe(data):
            """Subscribe to specific updates"""
            update_type = data.get('type', 'all')
            self.logger.info(f"Client subscribed to {update_type} updates")
    
    def _get_system_health(self):
        """Check health of all trading services with caching"""
        # Check cache first
        if self.status_cache['data'] and self.status_cache['timestamp']:
            cache_age = (datetime.now() - self.status_cache['timestamp']).total_seconds()
            if cache_age < self.status_cache['cache_duration']:
                return self.status_cache['data']
        
        health_status = {}
        
        for service_key, service_info in self.services.items():
            try:
                response = requests.get(
                    f"http://localhost:{service_info['port']}/health",
                    timeout=2
                )
                health_status[service_key] = {
                    'name': service_info['name'],
                    'port': service_info['port'],
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'response_time': response.elapsed.total_seconds()
                }
            except:
                health_status[service_key] = {
                    'name': service_info['name'],
                    'port': service_info['port'],
                    'status': 'offline',
                    'response_time': None
                }
        
        # Update cache
        self.status_cache['data'] = health_status
        self.status_cache['timestamp'] = datetime.now()
        
        return health_status
    
    def _get_trading_stats(self):
        """Get current trading statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Today's stats
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN status = 'filled' THEN 1 ELSE 0 END) as filled_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl
                FROM trades
                WHERE DATE(created_at) = ?
            ''', (today,))
            
            today_stats = cursor.fetchone()
            
            # Active positions
            cursor.execute('''
                SELECT COUNT(*) as active_positions,
                       SUM(quantity * current_price) as total_value
                FROM positions
                WHERE status = 'open'
            ''')
            
            position_stats = cursor.fetchone()
            
            # Account info
            cursor.execute('''
                SELECT cash_balance, buying_power, total_value
                FROM account_status
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            
            account_info = cursor.fetchone()
            
            return {
                'today': {
                    'total_trades': today_stats[0] or 0,
                    'filled_trades': today_stats[1] or 0,
                    'winning_trades': today_stats[2] or 0,
                    'total_pnl': today_stats[3] or 0,
                    'avg_pnl': today_stats[4] or 0,
                    'win_rate': (today_stats[2] / today_stats[0] * 100) if today_stats[0] > 0 else 0
                },
                'positions': {
                    'active_count': position_stats[0] or 0,
                    'total_value': position_stats[1] or 0
                },
                'account': {
                    'cash_balance': account_info[0] if account_info else 0,
                    'buying_power': account_info[1] if account_info else 0,
                    'total_value': account_info[2] if account_info else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting trading stats: {e}")
            return {}
        finally:
            conn.close()
    
    def _get_active_positions(self):
        """Get current active positions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT symbol, quantity, entry_price, current_price,
                       (current_price - entry_price) * quantity as unrealized_pnl,
                       ((current_price - entry_price) / entry_price * 100) as pnl_percent,
                       created_at
                FROM positions
                WHERE status = 'open'
                ORDER BY created_at DESC
            ''')
            
            positions = []
            for row in cursor.fetchall():
                positions.append(dict(row))
            
            return positions
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
        finally:
            conn.close()
    
    def _get_recent_trades(self, limit=50):
        """Get recent trade history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT trade_id, symbol, side, quantity, fill_price,
                       pnl, status, created_at, completed_at
                FROM trades
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            trades = []
            for row in cursor.fetchall():
                trades.append(dict(row))
            
            return trades
            
        except Exception as e:
            self.logger.error(f"Error getting trades: {e}")
            return []
        finally:
            conn.close()
    
    def _get_performance_metrics(self, days=7):
        """Get performance metrics over specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT 
                    DATE(created_at) as trade_date,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(pnl) as daily_pnl,
                    AVG(pnl) as avg_trade_pnl,
                    MAX(pnl) as best_trade,
                    MIN(pnl) as worst_trade
                FROM trades
                WHERE DATE(created_at) >= ?
                GROUP BY DATE(created_at)
                ORDER BY trade_date
            ''', (start_date,))
            
            daily_metrics = []
            for row in cursor.fetchall():
                daily_metrics.append({
                    'date': row[0],
                    'total_trades': row[1],
                    'winning_trades': row[2],
                    'win_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0,
                    'daily_pnl': row[3],
                    'avg_trade_pnl': row[4],
                    'best_trade': row[5],
                    'worst_trade': row[6]
                })
            
            # Calculate aggregate metrics
            total_trades = sum(d['total_trades'] for d in daily_metrics)
            total_wins = sum(d['winning_trades'] for d in daily_metrics)
            total_pnl = sum(d['daily_pnl'] for d in daily_metrics)
            
            return {
                'daily_metrics': daily_metrics,
                'summary': {
                    'total_trades': total_trades,
                    'total_wins': total_wins,
                    'win_rate': (total_wins / total_trades * 100) if total_trades > 0 else 0,
                    'total_pnl': total_pnl,
                    'avg_daily_pnl': total_pnl / days if days > 0 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {'daily_metrics': [], 'summary': {}}
        finally:
            conn.close()
    
    def _analyze_pattern_effectiveness(self):
        """Analyze effectiveness of different patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    p.pattern_type,
                    COUNT(DISTINCT t.trade_id) as total_trades,
                    SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    AVG(t.pnl) as avg_pnl,
                    SUM(t.pnl) as total_pnl
                FROM pattern_analysis p
                JOIN trading_signals s ON p.symbol = s.symbol 
                    AND DATE(p.created_at) = DATE(s.created_at)
                JOIN trades t ON s.symbol = t.symbol 
                    AND DATE(s.created_at) = DATE(t.created_at)
                WHERE t.status = 'closed'
                GROUP BY p.pattern_type
                ORDER BY total_pnl DESC
            ''')
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append({
                    'pattern_type': row[0],
                    'total_trades': row[1],
                    'winning_trades': row[2],
                    'win_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0,
                    'avg_pnl': row[3],
                    'total_pnl': row[4]
                })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {e}")
            return []
        finally:
            conn.close()
    
    def _get_system_alerts(self):
        """Get system alerts and warnings"""
        alerts = []
        
        # Check service health
        health = self._get_system_health()
        for service, status in health.items():
            if status['status'] != 'healthy':
                alerts.append({
                    'type': 'error',
                    'service': status['name'],
                    'message': f"{status['name']} is {status['status']}",
                    'timestamp': datetime.now().isoformat()
                })
        
        # Check recent workflow failures
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT COUNT(*) as failed_count
                FROM workflow_metrics
                WHERE status = 'failed'
                AND created_at > datetime('now', '-1 hour')
            ''')
            
            failed_count = cursor.fetchone()[0]
            if failed_count > 3:
                alerts.append({
                    'type': 'warning',
                    'service': 'Workflow System',
                    'message': f"{failed_count} workflow failures in the last hour",
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
        finally:
            conn.close()
        
        return alerts
    
    def _render_main_dashboard(self):
        """Render the main system health dashboard HTML"""
        return MAIN_DASHBOARD_HTML
    
    def _render_trading_dashboard(self):
        """Render the enhanced trading dashboard HTML"""
        return TRADING_DASHBOARD_HTML
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        def monitor():
            while not self.stop_monitoring.is_set():
                try:
                    # Broadcast system updates
                    self.socketio.emit('system_update', {
                        'trading_stats': self._get_trading_stats(),
                        'system_health': self._get_system_health(),
                        'alerts': self._get_system_alerts(),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Broadcast workflow updates
                    workflow_status = self.workflow_tracker.get_workflow_summary()
                    if workflow_status:
                        self.socketio.emit('workflow_update', workflow_status)
                    
                except Exception as e:
                    self.logger.error(f"Error in monitoring: {e}")
                
                time.sleep(5)  # Update every 5 seconds
        
        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("Monitoring thread started")
    
    def stop_monitoring(self):
        """Stop monitoring thread"""
        self.stop_monitoring.set()
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("Monitoring thread stopped")
    
    def _register_with_coordination(self):
        """Register with coordination service"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.post(
                    'http://localhost:5000/register_service',
                    json={'service_name': 'dashboard', 'port': self.port},
                    timeout=5
                )
                if response.status_code == 200:
                    self.logger.info("Successfully registered with coordination service")
                    return True
            except Exception as e:
                self.logger.warning(f"Failed to register (attempt {retry_count + 1}): {e}")
            
            retry_count += 1
            time.sleep(2)
        
        self.logger.error("Failed to register with coordination service after max retries")
        return False
    
    def run(self):
        """Run the dashboard service"""
        self.logger.info(f"Starting Web Dashboard Service v2.1.0 on port {self.port}")
        
        # Register with coordination service
        threading.Thread(target=self._register_with_coordination, daemon=True).start()
        
        # Start monitoring
        self.start_monitoring()
        
        try:
            # Run with SocketIO
            self.socketio.run(
                self.app,
                host='0.0.0.0',
                port=self.port,
                debug=False
            )
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.stop_monitoring()
        except Exception as e:
            self.logger.error(f"Error running service: {e}")
            self.stop_monitoring()
            raise


# Main System Health Dashboard HTML
MAIN_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Trading System Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body {
            background-color: #f8f9fa;
        }
        .status-card {
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .status-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .service-indicator {
            width: 20px;
            height: 20px;
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
        .service-offline {
            background-color: #6c757d;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .main-status {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .nav-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .nav-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }
        .nav-card a {
            text-decoration: none;
            color: #007bff;
            font-size: 1.2rem;
        }
        .system-info {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
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
        <!-- System Status Overview -->
        <div class="system-info">
            <div class="text-center">
                <h2>System Status</h2>
                <div id="overall-status" class="main-status">Loading...</div>
                <p class="lead">
                    <span id="active-services">0</span> / <span id="total-services">0</span> Services Active
                </p>
            </div>
        </div>

        <!-- Navigation Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="nav-card">
                    <h5>Trading Dashboard</h5>
                    <p>View trading statistics and performance</p>
                    <a href="/trading">Open Trading Dashboard →</a>
                </div>
            </div>
            <div class="col-md-3">
                <div class="nav-card">
                    <h5>Workflow Monitor</h5>
                    <p>Track trading workflow execution</p>
                    <a href="/workflow">Open Workflow Monitor →</a>
                </div>
            </div>
            <div class="col-md-3">
                <div class="nav-card">
                    <h5>System API</h5>
                    <p>Access system data via API</p>
                    <a href="/api/system/overview" target="_blank">View API →</a>
                </div>
            </div>
            <div class="col-md-3">
                <div class="nav-card">
                    <h5>Health Check</h5>
                    <p>Service health endpoint</p>
                    <a href="/health" target="_blank">Check Health →</a>
                </div>
            </div>
        </div>

        <!-- Services Grid -->
        <h3>Service Status</h3>
        <div class="row" id="services-grid">
            <!-- Services will be populated here -->
        </div>

        <!-- Recent Alerts -->
        <div class="mt-4">
            <h3>System Alerts</h3>
            <div id="alerts-container">
                <p class="text-muted">No active alerts</p>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
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
                
                // Update alerts
                const alertsResponse = await axios.get('/api/alerts');
                updateAlerts(alertsResponse.data);
                
            } catch (error) {
                console.error('Error updating dashboard:', error);
            }
        }

        function updateServicesGrid(services) {
            const grid = document.getElementById('services-grid');
            grid.innerHTML = '';
            
            Object.entries(services).forEach(([id, service]) => {
                const isHealthy = service.status === 'healthy';
                const isOffline = service.status === 'offline';
                
                const card = document.createElement('div');
                card.className = 'col-md-4 mb-3';
                card.innerHTML = `
                    <div class="card status-card ${isHealthy ? 'border-success' : (isOffline ? 'border-secondary' : 'border-danger')}">
                        <div class="card-body">
                            <h5 class="card-title">
                                <span class="service-indicator ${isHealthy ? 'service-healthy' : (isOffline ? 'service-offline' : 'service-unhealthy')}"></span>
                                ${service.name}
                            </h5>
                            <p class="card-text">
                                Port: ${service.port}<br>
                                Status: <strong>${service.status}</strong><br>
                                ${service.response_time ? `Response: ${(service.response_time * 1000).toFixed(0)}ms` : 'No response'}
                            </p>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            
            if (alerts.length === 0) {
                container.innerHTML = '<p class="text-muted">No active alerts</p>';
                return;
            }
            
            container.innerHTML = '';
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${alert.type === 'error' ? 'danger' : 'warning'} alert-dismissible`;
                alertDiv.innerHTML = `
                    <strong>${alert.service}:</strong> ${alert.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                container.appendChild(alertDiv);
            });
        }
    </script>
</body>
</html>
'''

# Enhanced Trading Dashboard HTML
TRADING_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Trading Dashboard - Trading System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>
    <style>
        body {
            background-color: #0a0e1a;
            color: #e0e6ed;
        }
        .dashboard-header {
            background: linear-gradient(135deg, #1a1f2e 0%, #151922 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: linear-gradient(135deg, #1a1f2e 0%, #151922 100%);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #00d4ff;
        }
        .positive {
            color: #00ff88;
        }
        .negative {
            color: #ff4757;
        }
        .data-table {
            background: #1a1f2e;
            border-radius: 10px;
            overflow: hidden;
        }
        .table {
            color: #e0e6ed;
        }
        .btn-trade {
            background: linear-gradient(45deg, #00d4ff, #0099ff);
            border: none;
            padding: 10px 30px;
            font-weight: bold;
        }
        .btn-trade:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 212, 255, 0.3);
        }
        .nav-link {
            color: #8892a6;
        }
        .nav-link.active {
            background-color: rgba(0, 212, 255, 0.1) !important;
            color: #00d4ff !important;
            border-color: transparent !important;
        }
        .workflow-phase {
            padding: 10px;
            margin: 5px;
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.05);
        }
        .workflow-phase.completed {
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
        }
        .workflow-phase.active {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
        }
        .workflow-phase.pending {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .back-link {
            color: #00d4ff;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .back-link:hover {
            color: #0099ff;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <!-- Back to Main Dashboard -->
        <a href="/" class="back-link">
            ← Back to System Dashboard
        </a>

        <!-- Header -->
        <div class="dashboard-header">
            <h1>Trading Dashboard</h1>
            <p class="mb-0">Real-time trading statistics and performance monitoring</p>
        </div>

        <!-- Nav tabs -->
        <ul class="nav nav-tabs mb-4" id="tradingTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button">Overview</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="positions-tab" data-bs-toggle="tab" data-bs-target="#positions" type="button">Positions</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="trades-tab" data-bs-toggle="tab" data-bs-target="#trades" type="button">Recent Trades</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="workflow-tab" data-bs-toggle="tab" data-bs-target="#workflow" type="button">Workflow</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="controls-tab" data-bs-toggle="tab" data-bs-target="#controls" type="button">Controls</button>
            </li>
        </ul>

        <!-- Tab content -->
        <div class="tab-content" id="tradingTabContent">
            <!-- Overview Tab -->
            <div class="tab-pane fade show active" id="overview" role="tabpanel">
                <div class="row">
                    <!-- Today's Performance -->
                    <div class="col-md-3">
                        <div class="metric-card">
                            <h6>Today's P&L</h6>
                            <div class="metric-value" id="today-pnl">$0.00</div>
                            <small id="today-trades">0 trades</small>
                        </div>
                    </div>
                    
                    <!-- Win Rate -->
                    <div class="col-md-3">
                        <div class="metric-card">
                            <h6>Win Rate</h6>
                            <div class="metric-value" id="win-rate">0%</div>
                            <small id="win-loss">0W / 0L</small>
                        </div>
                    </div>
                    
                    <!-- Active Positions -->
                    <div class="col-md-3">
                        <div class="metric-card">
                            <h6>Active Positions</h6>
                            <div class="metric-value" id="active-positions">0</div>
                            <small id="position-value">$0.00 value</small>
                        </div>
                    </div>
                    
                    <!-- Account Value -->
                    <div class="col-md-3">
                        <div class="metric-card">
                            <h6>Account Value</h6>
                            <div class="metric-value" id="account-value">$0.00</div>
                            <small id="buying-power">$0.00 buying power</small>
                        </div>
                    </div>
                </div>

                <!-- Performance Chart -->
                <div class="metric-card mt-4">
                    <h5>7-Day Performance</h5>
                    <canvas id="performanceChart" height="100"></canvas>
                </div>

                <!-- Pattern Effectiveness -->
                <div class="metric-card mt-4">
                    <h5>Pattern Effectiveness</h5>
                    <div id="pattern-effectiveness">
                        <p class="text-muted">Loading pattern data...</p>
                    </div>
                </div>
            </div>

            <!-- Positions Tab -->
            <div class="tab-pane fade" id="positions" role="tabpanel">
                <div class="data-table">
                    <table class="table table-dark">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Quantity</th>
                                <th>Entry Price</th>
                                <th>Current Price</th>
                                <th>P&L</th>
                                <th>P&L %</th>
                                <th>Opened</th>
                            </tr>
                        </thead>
                        <tbody id="positions-table">
                            <tr><td colspan="7" class="text-center">No active positions</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Trades Tab -->
            <div class="tab-pane fade" id="trades" role="tabpanel">
                <div class="data-table">
                    <table class="table table-dark">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Quantity</th>
                                <th>Price</th>
                                <th>P&L</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="trades-table">
                            <tr><td colspan="7" class="text-center">No recent trades</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Workflow Tab -->
            <div class="tab-pane fade" id="workflow" role="tabpanel">
                <div class="metric-card">
                    <h5>Current Workflow Status</h5>
                    <div id="workflow-status">
                        <p class="text-muted">No active workflow</p>
                    </div>
                    
                    <div class="mt-4">
                        <h6>Workflow Phases</h6>
                        <div id="workflow-phases" class="d-flex flex-wrap">
                            <!-- Phases will be populated here -->
                        </div>
                    </div>
                </div>

                <div class="metric-card mt-4">
                    <h5>Recent Workflow History</h5>
                    <div id="workflow-history">
                        <p class="text-muted">Loading history...</p>
                    </div>
                </div>
            </div>

            <!-- Controls Tab -->
            <div class="tab-pane fade" id="controls" role="tabpanel">
                <div class="text-center">
                    <h3>Trading Controls</h3>
                    
                    <div class="mt-4">
                        <button class="btn btn-trade btn-lg" onclick="startTradingCycle()">
                            Start Trading Cycle
                        </button>
                    </div>
                    
                    <div class="metric-card mt-4">
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
        </div>
    </div>

    <!-- Schedule Configuration Modal -->
    <div class="modal fade" id="scheduleModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content bg-dark text-light">
                <div class="modal-header">
                    <h5 class="modal-title">Trading Schedule Configuration</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
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

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let socket;
        let performanceChart;
        let scheduleModal;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            scheduleModal = new bootstrap.Modal(document.getElementById('scheduleModal'));
            initializeWebSocket();
            initializeChart();
            updateTradingData();
            setInterval(updateTradingData, 10000); // Update every 10 seconds
        });

        function initializeWebSocket() {
            socket = io();
            
            socket.on('connect', function() {
                console.log('Connected to trading dashboard');
                socket.emit('subscribe_updates', {type: 'trading'});
            });
            
            socket.on('system_update', function(data) {
                updateMetrics(data.trading_stats);
            });
            
            socket.on('workflow_update', function(data) {
                updateWorkflowStatus(data);
            });
        }

        function initializeChart() {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Daily P&L',
                        data: [],
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#8892a6'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            },
                            ticks: {
                                color: '#8892a6'
                            }
                        }
                    }
                }
            });
        }

        async function updateTradingData() {
            try {
                // Get system overview
                const response = await axios.get('/api/system/overview');
                const data = response.data;
                
                updateMetrics(data.trading_stats);
                updatePositions();
                updateTrades();
                updatePerformance();
                updateWorkflowStatus(data.workflow_status);
                updateScheduleStatus();
                
            } catch (error) {
                console.error('Error updating trading data:', error);
            }
        }

        function updateMetrics(stats) {
            if (!stats || !stats.today) return;
            
            // Today's P&L
            const pnlElement = document.getElementById('today-pnl');
            const pnl = stats.today.total_pnl || 0;
            pnlElement.textContent = '$' + pnl.toFixed(2);
            pnlElement.className = 'metric-value ' + (pnl >= 0 ? 'positive' : 'negative');
            document.getElementById('today-trades').textContent = stats.today.total_trades + ' trades';
            
            // Win Rate
            document.getElementById('win-rate').textContent = (stats.today.win_rate || 0).toFixed(1) + '%';
            document.getElementById('win-loss').textContent = 
                stats.today.winning_trades + 'W / ' + 
                (stats.today.total_trades - stats.today.winning_trades) + 'L';
            
            // Active Positions
            document.getElementById('active-positions').textContent = stats.positions.active_count || 0;
            document.getElementById('position-value').textContent = 
                '$' + (stats.positions.total_value || 0).toFixed(2) + ' value';
            
            // Account Value
            document.getElementById('account-value').textContent = 
                '$' + (stats.account.total_value || 0).toFixed(2);
            document.getElementById('buying-power').textContent = 
                '$' + (stats.account.buying_power || 0).toFixed(2) + ' buying power';
        }

        async function updatePositions() {
            try {
                const response = await axios.get('/api/trading/positions');
                const positions = response.data;
                
                const tbody = document.getElementById('positions-table');
                if (positions.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center">No active positions</td></tr>';
                    return;
                }
                
                tbody.innerHTML = positions.map(pos => `
                    <tr>
                        <td>${pos.symbol}</td>
                        <td>${pos.quantity}</td>
                        <td>$${pos.entry_price.toFixed(2)}</td>
                        <td>$${pos.current_price.toFixed(2)}</td>
                        <td class="${pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}">
                            $${pos.unrealized_pnl.toFixed(2)}
                        </td>
                        <td class="${pos.pnl_percent >= 0 ? 'positive' : 'negative'}">
                            ${pos.pnl_percent.toFixed(2)}%
                        </td>
                        <td>${new Date(pos.created_at).toLocaleDateString()}</td>
                    </tr>
                `).join('');
                
            } catch (error) {
                console.error('Error updating positions:', error);
            }
        }

        async function updateTrades() {
            try {
                const response = await axios.get('/api/trading/trades?limit=20');
                const trades = response.data;
                
                const tbody = document.getElementById('trades-table');
                if (trades.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center">No recent trades</td></tr>';
                    return;
                }
                
                tbody.innerHTML = trades.map(trade => `
                    <tr>
                        <td>${new Date(trade.created_at).toLocaleString()}</td>
                        <td>${trade.symbol}</td>
                        <td>${trade.side}</td>
                        <td>${trade.quantity}</td>
                        <td>$${(trade.fill_price || 0).toFixed(2)}</td>
                        <td class="${trade.pnl >= 0 ? 'positive' : 'negative'}">
                            ${trade.pnl ? '$' + trade.pnl.toFixed(2) : '-'}
                        </td>
                        <td>${trade.status}</td>
                    </tr>
                `).join('');
                
            } catch (error) {
                console.error('Error updating trades:', error);
            }
        }

        async function updatePerformance() {
            try {
                const response = await axios.get('/api/trading/performance?days=7');
                const data = response.data;
                
                if (data.daily_metrics && data.daily_metrics.length > 0) {
                    const labels = data.daily_metrics.map(d => 
                        new Date(d.date).toLocaleDateString('en-US', {month: 'short', day: 'numeric'})
                    );
                    const values = data.daily_metrics.map(d => d.daily_pnl);
                    
                    performanceChart.data.labels = labels;
                    performanceChart.data.datasets[0].data = values;
                    performanceChart.update();
                }
                
                // Update pattern effectiveness
                const patternsResponse = await axios.get('/api/patterns/effectiveness');
                const patterns = patternsResponse.data;
                
                const patternDiv = document.getElementById('pattern-effectiveness');
                if (patterns.length === 0) {
                    patternDiv.innerHTML = '<p class="text-muted">No pattern data available</p>';
                } else {
                    patternDiv.innerHTML = patterns.map(p => `
                        <div class="d-flex justify-content-between mb-2">
                            <span>${p.pattern_type}</span>
                            <span>
                                Win Rate: ${p.win_rate.toFixed(1)}% | 
                                Avg P&L: $${p.avg_pnl.toFixed(2)}
                            </span>
                        </div>
                    `).join('');
                }
                
            } catch (error) {
                console.error('Error updating performance:', error);
            }
        }

        function updateWorkflowStatus(workflow) {
            const statusDiv = document.getElementById('workflow-status');
            const phasesDiv = document.getElementById('workflow-phases');
            
            if (!workflow || !workflow.cycle_id) {
                statusDiv.innerHTML = '<p class="text-muted">No active workflow</p>';
                phasesDiv.innerHTML = '';
                return;
            }
            
            statusDiv.innerHTML = `
                <p><strong>Cycle ID:</strong> ${workflow.cycle_id}</p>
                <p><strong>Status:</strong> ${workflow.status}</p>
                <p><strong>Progress:</strong> ${workflow.completed_phases || 0} / 6 phases completed</p>
            `;
            
            // Update phases
            const phases = [
                'initialization',
                'security_selection', 
                'pattern_analysis',
                'signal_generation',
                'trade_execution',
                'completion'
            ];
            
            phasesDiv.innerHTML = phases.map(phase => {
                const phaseData = workflow.phases && workflow.phases[phase];
                let status = 'pending';
                if (phaseData) {
                    status = phaseData.status || 'pending';
                }
                
                return `
                    <div class="workflow-phase ${status}">
                        ${phase.replace(/_/g, ' ').toUpperCase()}
                    </div>
                `;
            }).join('');
            
            updateWorkflowHistory();
        }

        async function updateWorkflowHistory() {
            try {
                const response = await axios.get('/api/workflow/history?limit=5');
                const history = response.data;
                
                const historyDiv = document.getElementById('workflow-history');
                if (history.length === 0) {
                    historyDiv.innerHTML = '<p class="text-muted">No workflow history</p>';
                    return;
                }
                
                historyDiv.innerHTML = history.map(h => `
                    <div class="mb-3 p-3 border rounded">
                        <strong>Cycle ${h.cycle_id}</strong> - ${h.status}<br>
                        Duration: ${h.total_duration_seconds ? h.total_duration_seconds.toFixed(1) + 's' : 'N/A'}<br>
                        Securities: ${h.securities_scanned}, Signals: ${h.signals_generated}, Trades: ${h.trades_executed}
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Error updating workflow history:', error);
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
                
                // Refresh data
                updateTradingData();
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
    # Run the service
    service = WebDashboardService(port=5010)
    service.run()

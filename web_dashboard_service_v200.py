#!/usr/bin/env python3
"""
Name of Service: Web Dashboard Service
Filename: web_dashboard_service.py
Version: 2.0.0
Last Updated: 2025-06-24
REVISION HISTORY:
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
from pl_tracking_enhancement import pl_bp, PLTracker
import threading
import time
import requests

# Import workflow tracking components
from trading_workflow_tracker import TradingWorkflowTracker, WorkflowPhase

class WebDashboardService:
    """
    Enhanced web dashboard service with integrated workflow tracking
    Provides real-time monitoring of trading system and workflow execution
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

        # In __init__ method after workflow tracker init
        self.pl_tracker = PLTracker(db_path=self.db_path)
        self.app.register_blueprint(pl_bp)
        
        # Service registry for health checks
        self.services = {
            'coordination': {'port': 5000, 'name': 'Coordination Service'},
            'scanner': {'port': 5001, 'name': 'Security Scanner'},
            'pattern': {'port': 5002, 'name': 'Pattern Analysis'},
            'technical': {'port': 5003, 'name': 'Technical Analysis'},
            'trading': {'port': 5005, 'name': 'Paper Trading'},
            'pattern_rec': {'port': 5006, 'name': 'Pattern Recognition'},
            'news': {'port': 5008, 'name': 'News Service'},
            'reporting': {'port': 5009, 'name': 'Reporting Service'}
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
            """Main dashboard page"""
            return self._render_main_dashboard()
        
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
    
    def _setup_workflow_routes(self):
        """Setup workflow tracking routes"""
        
        # Workflow Status APIs
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
        
        # Workflow Control APIs (for coordination service integration)
        @self.app.route('/api/workflow/start', methods=['POST'])
        def start_workflow():
            """Start tracking a new workflow"""
            data = request.json
            cycle_id = data.get('cycle_id')
            
            if not cycle_id:
                return jsonify({"error": "cycle_id required"}), 400
            
            success = self.workflow_tracker.start_workflow(cycle_id)
            
            # Emit real-time update
            self.socketio.emit('workflow_started', {
                'cycle_id': cycle_id,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({"success": success, "cycle_id": cycle_id})
        
        @self.app.route('/api/workflow/phase/start', methods=['POST'])
        def start_phase():
            """Start a workflow phase"""
            data = request.json
            phase_name = data.get('phase')
            metadata = data.get('metadata', {})
            
            phase_map = {
                'initialization': WorkflowPhase.INITIALIZATION,
                'security_selection': WorkflowPhase.SECURITY_SELECTION,
                'pattern_analysis': WorkflowPhase.PATTERN_ANALYSIS,
                'signal_generation': WorkflowPhase.SIGNAL_GENERATION,
                'trade_execution': WorkflowPhase.TRADE_EXECUTION,
                'completion': WorkflowPhase.COMPLETION
            }
            
            if phase_name not in phase_map:
                return jsonify({"error": "Invalid phase"}), 400
            
            success = self.workflow_tracker.start_phase(phase_map[phase_name], metadata)
            
            # Emit real-time update
            self.socketio.emit('phase_started', {
                'phase': phase_name,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({"success": success})
        
        @self.app.route('/api/workflow/phase/update', methods=['POST'])
        def update_phase():
            """Update phase progress"""
            data = request.json
            phase_name = data.get('phase')
            
            phase_map = {
                'initialization': WorkflowPhase.INITIALIZATION,
                'security_selection': WorkflowPhase.SECURITY_SELECTION,
                'pattern_analysis': WorkflowPhase.PATTERN_ANALYSIS,
                'signal_generation': WorkflowPhase.SIGNAL_GENERATION,
                'trade_execution': WorkflowPhase.TRADE_EXECUTION,
                'completion': WorkflowPhase.COMPLETION
            }
            
            if phase_name not in phase_map:
                return jsonify({"error": "Invalid phase"}), 400
            
            success = self.workflow_tracker.update_phase_progress(
                phase_map[phase_name],
                items_processed=data.get('items_processed'),
                items_succeeded=data.get('items_succeeded'),
                items_failed=data.get('items_failed'),
                metadata=data.get('metadata')
            )
            
            # Emit real-time update
            self.socketio.emit('phase_updated', {
                'phase': phase_name,
                'progress': data
            })
            
            return jsonify({"success": success})
        
        @self.app.route('/api/workflow/phase/complete', methods=['POST'])
        def complete_phase():
            """Complete a workflow phase"""
            data = request.json
            phase_name = data.get('phase')
            success = data.get('success', True)
            error_message = data.get('error_message')
            
            phase_map = {
                'initialization': WorkflowPhase.INITIALIZATION,
                'security_selection': WorkflowPhase.SECURITY_SELECTION,
                'pattern_analysis': WorkflowPhase.PATTERN_ANALYSIS,
                'signal_generation': WorkflowPhase.SIGNAL_GENERATION,
                'trade_execution': WorkflowPhase.TRADE_EXECUTION,
                'completion': WorkflowPhase.COMPLETION
            }
            
            if phase_name not in phase_map:
                return jsonify({"error": "Invalid phase"}), 400
            
            result = self.workflow_tracker.complete_phase(
                phase_map[phase_name], success, error_message
            )
            
            # Emit real-time update
            self.socketio.emit('phase_completed', {
                'phase': phase_name,
                'success': success,
                'error': error_message
            })
            
            return jsonify({"success": result})
        
        @self.app.route('/api/workflow/complete', methods=['POST'])
        def complete_workflow():
            """Complete the current workflow"""
            data = request.json
            success = data.get('success', True)
            
            summary = self.workflow_tracker.complete_workflow(success)
            
            # Emit real-time update
            self.socketio.emit('workflow_completed', {
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify(summary)
        
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
        """Check health of all trading services"""
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
        """Render the main dashboard HTML"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading System Dashboard</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #0a0e1a;
                    color: #e0e6ed;
                    margin: 0;
                    padding: 20px;
                }
                .header {
                    background: linear-gradient(135deg, #1a1f2e 0%, #151922 100%);
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .nav-links {
                    display: flex;
                    gap: 20px;
                }
                .nav-links a {
                    color: #00d4ff;
                    text-decoration: none;
                    padding: 10px 20px;
                    background: rgba(0, 212, 255, 0.1);
                    border-radius: 5px;
                    transition: all 0.3s;
                }
                .nav-links a:hover {
                    background: rgba(0, 212, 255, 0.2);
                }
                .content {
                    background: linear-gradient(135deg, #1a1f2e 0%, #151922 100%);
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                }
                h1 {
                    background: linear-gradient(45deg, #00d4ff, #0099ff);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin: 0;
                }
                .status {
                    margin-top: 20px;
                    padding: 20px;
                    background: rgba(0, 255, 136, 0.1);
                    border-radius: 10px;
                    color: #00ff88;
                }
                .api-list {
                    text-align: left;
                    margin-top: 30px;
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                }
                .api-list h3 {
                    color: #00d4ff;
                }
                .api-list ul {
                    list-style: none;
                    padding: 0;
                }
                .api-list li {
                    margin: 10px 0;
                }
                .api-list a {
                    color: #8892a6;
                    text-decoration: none;
                }
                .api-list a:hover {
                    color: #00d4ff;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Trading System Dashboard</h1>
                <div class="nav-links">
                    <a href="/workflow">Workflow Monitor</a>
                    <a href="/api/system/overview">System API</a>
                    <a href="/health">Health Check</a>
                </div>
            </div>
            
            <div class="content">
                <div class="status">
                    <h2>System Status: Operational</h2>
                    <p>Web Dashboard Service v2.0.0</p>
                </div>
                
                <div class="api-list">
                    <h3>Available Endpoints</h3>
                    
                    <h4>Dashboards</h4>
                    <ul>
                        <li><a href="/workflow">/workflow</a> - Trading Workflow Monitor</li>
                    </ul>
                    
                    <h4>System APIs</h4>
                    <ul>
                        <li><a href="/api/system/overview">/api/system/overview</a> - Complete system overview</li>
                        <li><a href="/api/services/health">/api/services/health</a> - Service health status</li>
                        <li><a href="/api/alerts">/api/alerts</a> - System alerts</li>
                    </ul>
                    
                    <h4>Trading APIs</h4>
                    <ul>
                        <li><a href="/api/trading/stats">/api/trading/stats</a> - Trading statistics</li>
                        <li><a href="/api/trading/positions">/api/trading/positions</a> - Active positions</li>
                        <li><a href="/api/trading/trades">/api/trading/trades</a> - Recent trades</li>
                        <li><a href="/api/trading/performance">/api/trading/performance</a> - Performance metrics</li>
                        <li><a href="/api/patterns/effectiveness">/api/patterns/effectiveness</a> - Pattern analysis</li>
                    </ul>
                    
                    <h4>Workflow APIs</h4>
                    <ul>
                        <li><a href="/api/workflow/current">/api/workflow/current</a> - Current workflow status</li>
                        <li><a href="/api/workflow/history">/api/workflow/history</a> - Workflow history</li>
                        <li><a href="/api/workflow/metrics/phases">/api/workflow/metrics/phases</a> - Phase performance</li>
                        <li><a href="/api/workflow/active">/api/workflow/active</a> - Active workflows</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        '''
    
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
        self.logger.info(f"Starting Enhanced Web Dashboard Service on port {self.port}")
        
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


if __name__ == "__main__":
    # Run the service
    service = WebDashboardService(port=5010)
    service.run()

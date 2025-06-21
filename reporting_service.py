# ================================================================
# 8. reporting_service.py (Port 5009)
# ================================================================
"""
Reporting Service - Generates comprehensive trading reports and analytics
Provides insights into trading performance and pattern effectiveness
"""

import sqlite3
import pandas as pd
import logging
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from typing import Dict, List, Optional

class ReportingService:
    def __init__(self, db_path='/content/trading_system.db'):
        self.app = Flask(__name__)
        self.db_path = db_path
        self.logger = self._setup_logging()
        self.coordination_service_url = "http://localhost:5000"
        
        self._setup_routes()
        self._register_with_coordination()
        
    def _setup_logging(self):
        import os
        os.makedirs('/content/logs', exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('ReportingService')
        
        handler = logging.FileHandler('/content/logs/reporting_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "healthy", "service": "reporting"})
        
        @self.app.route('/daily_summary', methods=['GET'])
        def daily_summary():
            report = self._generate_daily_summary()
            return jsonify(report)
        
        @self.app.route('/pattern_effectiveness', methods=['GET'])
        def pattern_effectiveness():
            report = self._analyze_pattern_effectiveness()
            return jsonify(report)
        
        @self.app.route('/trading_performance', methods=['GET'])
        def trading_performance():
            days = request.args.get('days', 30, type=int)
            report = self._generate_performance_report(days)
            return jsonify(report)
        
        @self.app.route('/system_health', methods=['GET'])
        def system_health():
            report = self._generate_system_health_report()
            return jsonify(report)
        
        @self.app.route('/cycle_analysis', methods=['GET'])
        def cycle_analysis():
            report = self._analyze_trading_cycles()
            return jsonify(report)
    
    def _register_with_coordination(self):
        """Register with coordination service"""
        try:
            registration_data = {
                "service_name": "reporting",
                "port": 5009
            }
            response = requests.post(f"{self.coordination_service_url}/register_service",
                                   json=registration_data, timeout=5)
            if response.status_code == 200:
                self.logger.info("Successfully registered with coordination service")
        except Exception as e:
            self.logger.warning(f"Could not register with coordination service: {e}")
    
    def _generate_daily_summary(self) -> Dict:
        """Generate daily trading summary"""
        try:
            today = datetime.now().date()
            
            conn = sqlite3.connect(self.db_path)
            
            # Trading statistics
            query = '''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(profit_loss) as total_pnl,
                    AVG(profit_loss) as avg_pnl,
                    MAX(profit_loss) as best_trade,
                    MIN(profit_loss) as worst_trade
                FROM trades 
                WHERE DATE(created_at) = ?
            '''
            
            cursor = conn.cursor()
            cursor.execute(query, (today,))
            trade_result = cursor.fetchone()
            
            # Securities scanned today
            securities_query = '''
                SELECT COUNT(*) as securities_scanned
                FROM selected_securities
                WHERE DATE(created_at) = ?
            '''
            cursor.execute(securities_query, (today,))
            securities_result = cursor.fetchone()
            
            # Patterns analyzed today
            patterns_query = '''
                SELECT COUNT(*) as patterns_analyzed,
                       AVG(confidence_score) as avg_confidence
                FROM pattern_analysis
                WHERE DATE(created_at) = ?
            '''
            cursor.execute(patterns_query, (today,))
            patterns_result = cursor.fetchone()
            
            # Trading signals generated today
            signals_query = '''
                SELECT COUNT(*) as signals_generated,
                       SUM(CASE WHEN signal_type = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
                       SUM(CASE WHEN signal_type = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
                       AVG(confidence) as avg_signal_confidence
                FROM trading_signals
                WHERE DATE(created_at) = ?
            '''
            cursor.execute(signals_query, (today,))
            signals_result = cursor.fetchone()
            
            conn.close()
            
            total_trades = trade_result[0] or 0
            winning_trades = trade_result[1] or 0
            
            summary = {
                'date': str(today),
                'trading_activity': {
                    'securities_scanned': securities_result[0] or 0,
                    'patterns_analyzed': patterns_result[0] or 0,
                    'average_pattern_confidence': round(patterns_result[1] or 0, 3),
                    'signals_generated': signals_result[0] or 0,
                    'buy_signals': signals_result[1] or 0,
                    'sell_signals': signals_result[2] or 0,
                    'average_signal_confidence': round(signals_result[3] or 0, 3)
                },
                'trading_performance': {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': total_trades - winning_trades,
                    'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
                    'total_pnl': round(trade_result[2] or 0, 2),
                    'average_pnl': round(trade_result[3] or 0, 2),
                    'best_trade': round(trade_result[4] or 0, 2),
                    'worst_trade': round(trade_result[5] or 0, 2)
                },
                'generated_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Generated daily summary: {total_trades} trades, {summary['trading_performance']['win_rate']:.1f}% win rate")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating daily summary: {e}")
            return {"error": str(e)}
    
    def _analyze_pattern_effectiveness(self) -> Dict:
        """Analyze which patterns are most effective for trading"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get pattern effectiveness from trades
            query = '''
                SELECT 
                    COALESCE(pattern_used, 'unknown') as pattern_name,
                    COUNT(*) as trade_count,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                    AVG(profit_loss) as avg_pnl,
                    SUM(profit_loss) as total_pnl,
                    AVG(confidence) as avg_confidence
                FROM trades 
                WHERE status IN ('executed', 'simulated', 'closed')
                GROUP BY COALESCE(pattern_used, 'unknown')
                HAVING COUNT(*) >= 1
                ORDER BY avg_pnl DESC
            '''
            
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
            pattern_analysis = []
            for row in results:
                pattern_name = row[0]
                trade_count = row[1]
                winning_trades = row[2]
                avg_pnl = row[3]
                total_pnl = row[4]
                avg_confidence = row[5]
                
                pattern_analysis.append({
                    'pattern_name': pattern_name,
                    'trade_count': trade_count,
                    'winning_trades': winning_trades,
                    'losing_trades': trade_count - winning_trades,
                    'win_rate': round((winning_trades / trade_count * 100) if trade_count > 0 else 0, 1),
                    'average_pnl': round(avg_pnl, 2),
                    'total_pnl': round(total_pnl, 2),
                    'average_confidence': round(avg_confidence or 0, 3),
                    'effectiveness_score': round((avg_pnl * (winning_trades / trade_count)) if trade_count > 0 else 0, 3)
                })
            
            # Get pattern detection statistics
            pattern_stats_query = '''
                SELECT 
                    COUNT(*) as total_analyses,
                    AVG(patterns_detected) as avg_patterns_per_symbol,
                    AVG(confidence_score) as avg_analysis_confidence
                FROM pattern_analysis
                WHERE created_at >= date('now', '-30 days')
            '''
            
            cursor.execute(pattern_stats_query)
            stats_result = cursor.fetchone()
            
            conn.close()
            
            # Sort by effectiveness score
            pattern_analysis.sort(key=lambda x: x['effectiveness_score'], reverse=True)
            
            report = {
                'pattern_effectiveness': pattern_analysis,
                'best_pattern': pattern_analysis[0] if pattern_analysis else None,
                'worst_pattern': pattern_analysis[-1] if pattern_analysis else None,
                'total_patterns_analyzed': len(pattern_analysis),
                'pattern_detection_stats': {
                    'total_analyses_30d': stats_result[0] or 0,
                    'avg_patterns_per_symbol': round(stats_result[1] or 0, 1),
                    'avg_analysis_confidence': round(stats_result[2] or 0, 3)
                },
                'generated_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Pattern effectiveness analysis: {len(pattern_analysis)} patterns analyzed")
            return report
            
        except Exception as e:
            self.logger.error(f"Error analyzing pattern effectiveness: {e}")
            return {"error": str(e)}
    
    def _generate_performance_report(self, days: int = 30) -> Dict:
        """Generate trading performance report for specified period"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Overall performance
            overall_query = '''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as total_winners,
                    SUM(profit_loss) as total_pnl,
                    AVG(profit_loss) as avg_pnl,
                    MAX(profit_loss) as best_trade,
                    MIN(profit_loss) as worst_trade,
                    AVG(confidence) as avg_confidence
                FROM trades 
                WHERE created_at >= ?
            '''
            
            cursor.execute(overall_query, (start_date,))
            overall_result = cursor.fetchone()
            
            # Daily performance
            daily_query = '''
                SELECT 
                    DATE(created_at) as trade_date,
                    COUNT(*) as daily_trades,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as daily_winners,
                    SUM(profit_loss) as daily_pnl
                FROM trades 
                WHERE created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY trade_date DESC
                LIMIT 30
            '''
            
            cursor.execute(daily_query, (start_date,))
            daily_results = cursor.fetchall()
            
            # Symbol performance
            symbol_query = '''
                SELECT 
                    symbol,
                    COUNT(*) as trade_count,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(profit_loss) as total_pnl,
                    AVG(profit_loss) as avg_pnl
                FROM trades 
                WHERE created_at >= ?
                GROUP BY symbol
                HAVING COUNT(*) >= 2
                ORDER BY total_pnl DESC
                LIMIT 10
            '''
            
            cursor.execute(symbol_query, (start_date,))
            symbol_results = cursor.fetchall()
            
            conn.close()
            
            # Process results
            total_trades = overall_result[0] or 0
            total_winners = overall_result[1] or 0
            
            # Daily performance
            daily_performance = []
            for row in daily_results:
                daily_trades = row[1]
                daily_winners = row[2]
                
                daily_performance.append({
                    'date': row[0],
                    'trades': daily_trades,
                    'winners': daily_winners,
                    'losers': daily_trades - daily_winners,
                    'win_rate': round((daily_winners / daily_trades * 100) if daily_trades > 0 else 0, 1),
                    'pnl': round(row[3], 2)
                })
            
            # Symbol performance
            symbol_performance = []
            for row in symbol_results:
                symbol_trades = row[1]
                symbol_winners = row[2]
                
                symbol_performance.append({
                    'symbol': row[0],
                    'trade_count': symbol_trades,
                    'winning_trades': symbol_winners,
                    'win_rate': round((symbol_winners / symbol_trades * 100) if symbol_trades > 0 else 0, 1),
                    'total_pnl': round(row[3], 2),
                    'average_pnl': round(row[4], 2)
                })
            
            report = {
                'period_days': days,
                'start_date': start_date.date().isoformat(),
                'end_date': datetime.now().date().isoformat(),
                'overall_performance': {
                    'total_trades': total_trades,
                    'winning_trades': total_winners,
                    'losing_trades': total_trades - total_winners,
                    'win_rate': round((total_winners / total_trades * 100) if total_trades > 0 else 0, 1),
                    'total_pnl': round(overall_result[2] or 0, 2),
                    'average_pnl': round(overall_result[3] or 0, 2),
                    'best_trade': round(overall_result[4] or 0, 2),
                    'worst_trade': round(overall_result[5] or 0, 2),
                    'average_confidence': round(overall_result[6] or 0, 3)
                },
                'daily_performance': daily_performance,
                'top_symbols': symbol_performance,
                'generated_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Generated {days}-day performance report: {total_trades} trades")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}
    
    def _analyze_trading_cycles(self) -> Dict:
        """Analyze trading cycle performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT 
                    cycle_id,
                    status,
                    started_at,
                    completed_at,
                    securities_scanned,
                    patterns_analyzed,
                    signals_generated,
                    trades_executed
                FROM trading_cycles
                ORDER BY started_at DESC
                LIMIT 20
            '''
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            cycles = []
            successful_cycles = 0
            total_securities = 0
            total_trades = 0
            
            for row in results:
                cycle = {
                    'cycle_id': row[0],
                    'status': row[1],
                    'started_at': row[2],
                    'completed_at': row[3],
                    'securities_scanned': row[4] or 0,
                    'patterns_analyzed': row[5] or 0,
                    'signals_generated': row[6] or 0,
                    'trades_executed': row[7] or 0,
                    'conversion_rate': round((row[7] / row[4] * 100) if row[4] and row[4] > 0 else 0, 1)
                }
                cycles.append(cycle)
                
                if row[1] == 'completed':
                    successful_cycles += 1
                    total_securities += row[4] or 0
                    total_trades += row[7] or 0
            
            conn.close()
            
            report = {
                'recent_cycles': cycles,
                'summary': {
                    'total_cycles': len(cycles),
                    'successful_cycles': successful_cycles,
                    'success_rate': round((successful_cycles / len(cycles) * 100) if cycles else 0, 1),
                    'avg_securities_per_cycle': round(total_securities / successful_cycles if successful_cycles > 0 else 0, 1),
                    'avg_trades_per_cycle': round(total_trades / successful_cycles if successful_cycles > 0 else 0, 1),
                    'overall_conversion_rate': round((total_trades / total_securities * 100) if total_securities > 0 else 0, 1)
                },
                'generated_at': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error analyzing trading cycles: {e}")
            return {"error": str(e)}
    
    def _generate_system_health_report(self) -> Dict:
        """Generate system health and service status report"""
        try:
            # Check database connectivity
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count records in key tables
            table_counts = {}
            tables = ['selected_securities', 'pattern_analysis', 'trading_signals', 'trades', 'news_sentiment']
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                except:
                    table_counts[table] = 0
            
            # Get recent activity
            cursor.execute('''
                SELECT COUNT(*) FROM selected_securities 
                WHERE created_at >= datetime('now', '-24 hours')
            ''')
            recent_securities = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM trades 
                WHERE created_at >= datetime('now', '-24 hours')
            ''')
            recent_trades = cursor.fetchone()[0]
            
            conn.close()
            
            # Try to get service status from coordination service
            service_status = {}
            try:
                response = requests.get(f"{self.coordination_service_url}/service_status", timeout=5)
                if response.status_code == 200:
                    service_status = response.json()
            except:
                service_status = {"error": "Could not reach coordination service"}
            
            report = {
                'database_health': {
                    'status': 'connected',
                    'table_record_counts': table_counts,
                    'recent_activity_24h': {
                        'securities_scanned': recent_securities,
                        'trades_executed': recent_trades
                    }
                },
                'service_registry': service_status,
                'system_status': 'operational',
                'last_check': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating system health report: {e}")
            return {"error": str(e)}
    
    def run(self):
        self.logger.info("Starting Reporting Service on port 5009")
        self.app.run(host='0.0.0.0', port=5009, debug=False)

if __name__ == "__main__":
    service = ReportingService()
    service.run()
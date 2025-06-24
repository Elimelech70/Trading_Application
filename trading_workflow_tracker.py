#!/usr/bin/env python3
"""
Trading Workflow Tracker
Tracks and monitors the complete trading cycle execution
Version: 1.0.0
"""

import os
import time
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
import requests

class WorkflowPhase(Enum):
    """Trading workflow phases as defined in functional specification"""
    INITIALIZATION = "initialization"
    SECURITY_SELECTION = "security_selection"
    PATTERN_ANALYSIS = "pattern_analysis"
    SIGNAL_GENERATION = "signal_generation"
    TRADE_EXECUTION = "trade_execution"
    COMPLETION = "completion"

class PhaseStatus(Enum):
    """Status of workflow phases"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"

@dataclass
class PhaseMetrics:
    """Metrics for each workflow phase"""
    phase: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    items_processed: int = 0
    items_succeeded: int = 0
    items_failed: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None

@dataclass
class WorkflowMetrics:
    """Overall workflow metrics"""
    cycle_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    securities_scanned: int = 0
    patterns_detected: int = 0
    signals_generated: int = 0
    trades_executed: int = 0
    success_rate: float = 0.0
    error_count: int = 0

class TradingWorkflowTracker:
    """
    Tracks and monitors trading workflow execution
    Provides real-time status updates and comprehensive metrics
    """
    
    def __init__(self, db_path='./trading_system.db', log_dir='./logs'):
        self.db_path = db_path
        self.log_dir = log_dir
        self.current_cycle = None
        self.phase_metrics = {}
        self.workflow_metrics = None
        self._lock = threading.Lock()
        
        # Ensure directories exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize database tables
        self._init_database()
        
        # Service endpoints
        self.service_endpoints = {
            'coordination': 'http://localhost:5000',
            'scanner': 'http://localhost:5001',
            'pattern': 'http://localhost:5002',
            'technical': 'http://localhost:5003',
            'trading': 'http://localhost:5005'
        }
        
        self.logger.info("Trading Workflow Tracker initialized")
    
    def _setup_logging(self):
        """Configure logging"""
        self.logger = logging.getLogger('TradingWorkflowTracker')
        self.logger.setLevel(logging.INFO)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'workflow_tracker.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Console handler for important messages
        console = logging.StreamHandler()
        console.setLevel(logging.WARNING)
        console.setFormatter(formatter)
        self.logger.addHandler(console)
    
    def _init_database(self):
        """Initialize workflow tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Workflow tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                duration_seconds REAL,
                items_processed INTEGER DEFAULT 0,
                items_succeeded INTEGER DEFAULT 0,
                items_failed INTEGER DEFAULT 0,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cycle_id, phase)
            )
        ''')
        
        # Workflow metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_duration_seconds REAL,
                securities_scanned INTEGER DEFAULT 0,
                patterns_detected INTEGER DEFAULT 0,
                signals_generated INTEGER DEFAULT 0,
                trades_executed INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                error_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Workflow events table for detailed tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_cycle ON workflow_tracking(cycle_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_phase ON workflow_tracking(phase)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_cycle ON workflow_metrics(cycle_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_cycle ON workflow_events(cycle_id)')
        
        conn.commit()
        conn.close()
    
    def start_workflow(self, cycle_id: str) -> bool:
        """Start tracking a new workflow"""
        with self._lock:
            try:
                self.current_cycle = cycle_id
                self.phase_metrics = {}
                
                # Initialize workflow metrics
                self.workflow_metrics = WorkflowMetrics(
                    cycle_id=cycle_id,
                    status="running",
                    start_time=datetime.now()
                )
                
                # Save to database
                self._save_workflow_metrics()
                
                # Initialize all phases
                for phase in WorkflowPhase:
                    self.phase_metrics[phase.value] = PhaseMetrics(
                        phase=phase.value,
                        status=PhaseStatus.PENDING.value
                    )
                    self._save_phase_metrics(phase.value)
                
                # Log event
                self._log_event(cycle_id, "workflow", "started", {
                    "timestamp": datetime.now().isoformat()
                })
                
                self.logger.info(f"Started tracking workflow: {cycle_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error starting workflow: {e}")
                return False
    
    def start_phase(self, phase: WorkflowPhase, metadata: Dict = None) -> bool:
        """Mark a phase as started"""
        with self._lock:
            try:
                if phase.value not in self.phase_metrics:
                    self.logger.error(f"Phase {phase.value} not initialized")
                    return False
                
                metrics = self.phase_metrics[phase.value]
                metrics.status = PhaseStatus.RUNNING.value
                metrics.start_time = datetime.now()
                metrics.metadata = metadata or {}
                
                self._save_phase_metrics(phase.value)
                self._log_event(self.current_cycle, phase.value, "started", metadata)
                
                self.logger.info(f"Started phase: {phase.value} for cycle: {self.current_cycle}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error starting phase {phase.value}: {e}")
                return False
    
    def update_phase_progress(self, phase: WorkflowPhase, 
                            items_processed: int = None,
                            items_succeeded: int = None,
                            items_failed: int = None,
                            metadata: Dict = None) -> bool:
        """Update progress for a running phase"""
        with self._lock:
            try:
                if phase.value not in self.phase_metrics:
                    return False
                
                metrics = self.phase_metrics[phase.value]
                
                if items_processed is not None:
                    metrics.items_processed = items_processed
                if items_succeeded is not None:
                    metrics.items_succeeded = items_succeeded
                if items_failed is not None:
                    metrics.items_failed = items_failed
                
                if metadata:
                    if metrics.metadata is None:
                        metrics.metadata = {}
                    metrics.metadata.update(metadata)
                
                self._save_phase_metrics(phase.value)
                
                # Log progress event
                self._log_event(self.current_cycle, phase.value, "progress", {
                    "items_processed": metrics.items_processed,
                    "items_succeeded": metrics.items_succeeded,
                    "items_failed": metrics.items_failed
                })
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating phase progress: {e}")
                return False
    
    def complete_phase(self, phase: WorkflowPhase, success: bool = True, 
                      error_message: str = None) -> bool:
        """Mark a phase as completed"""
        with self._lock:
            try:
                if phase.value not in self.phase_metrics:
                    return False
                
                metrics = self.phase_metrics[phase.value]
                metrics.end_time = datetime.now()
                
                if metrics.start_time:
                    duration = (metrics.end_time - metrics.start_time).total_seconds()
                    metrics.duration_seconds = duration
                
                metrics.status = PhaseStatus.COMPLETED.value if success else PhaseStatus.FAILED.value
                metrics.error_message = error_message
                
                self._save_phase_metrics(phase.value)
                
                # Update workflow metrics based on phase
                self._update_workflow_metrics_for_phase(phase, metrics)
                
                # Log completion event
                self._log_event(self.current_cycle, phase.value, "completed", {
                    "success": success,
                    "duration": metrics.duration_seconds,
                    "error": error_message
                })
                
                self.logger.info(f"Completed phase: {phase.value}, success: {success}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error completing phase: {e}")
                return False
    
    def retry_phase(self, phase: WorkflowPhase) -> bool:
        """Mark a phase for retry"""
        with self._lock:
            try:
                if phase.value not in self.phase_metrics:
                    return False
                
                metrics = self.phase_metrics[phase.value]
                metrics.status = PhaseStatus.RETRYING.value
                metrics.retry_count += 1
                
                self._save_phase_metrics(phase.value)
                
                self._log_event(self.current_cycle, phase.value, "retry", {
                    "retry_count": metrics.retry_count
                })
                
                self.logger.info(f"Retrying phase: {phase.value}, attempt: {metrics.retry_count}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error setting phase retry: {e}")
                return False
    
    def complete_workflow(self, success: bool = True) -> Dict:
        """Complete the workflow and return final metrics"""
        with self._lock:
            try:
                if not self.workflow_metrics:
                    return {}
                
                self.workflow_metrics.end_time = datetime.now()
                self.workflow_metrics.total_duration_seconds = (
                    self.workflow_metrics.end_time - self.workflow_metrics.start_time
                ).total_seconds()
                
                self.workflow_metrics.status = "completed" if success else "failed"
                
                # Calculate success rate
                total_items = sum(m.items_processed for m in self.phase_metrics.values())
                successful_items = sum(m.items_succeeded for m in self.phase_metrics.values())
                
                if total_items > 0:
                    self.workflow_metrics.success_rate = successful_items / total_items
                
                # Count errors
                self.workflow_metrics.error_count = sum(
                    1 for m in self.phase_metrics.values() 
                    if m.status == PhaseStatus.FAILED.value
                )
                
                self._save_workflow_metrics()
                
                # Log completion
                self._log_event(self.current_cycle, "workflow", "completed", {
                    "success": success,
                    "duration": self.workflow_metrics.total_duration_seconds,
                    "success_rate": self.workflow_metrics.success_rate
                })
                
                self.logger.info(f"Completed workflow: {self.current_cycle}, success: {success}")
                
                # Return summary
                return self.get_workflow_summary()
                
            except Exception as e:
                self.logger.error(f"Error completing workflow: {e}")
                return {}
    
    def get_workflow_summary(self) -> Dict:
        """Get comprehensive workflow summary"""
        if not self.workflow_metrics:
            return {}
        
        summary = {
            "cycle_id": self.workflow_metrics.cycle_id,
            "status": self.workflow_metrics.status,
            "start_time": self.workflow_metrics.start_time.isoformat() if self.workflow_metrics.start_time else None,
            "end_time": self.workflow_metrics.end_time.isoformat() if self.workflow_metrics.end_time else None,
            "duration_seconds": self.workflow_metrics.total_duration_seconds,
            "metrics": {
                "securities_scanned": self.workflow_metrics.securities_scanned,
                "patterns_detected": self.workflow_metrics.patterns_detected,
                "signals_generated": self.workflow_metrics.signals_generated,
                "trades_executed": self.workflow_metrics.trades_executed,
                "success_rate": self.workflow_metrics.success_rate,
                "error_count": self.workflow_metrics.error_count
            },
            "phases": {}
        }
        
        # Add phase details
        for phase_name, metrics in self.phase_metrics.items():
            summary["phases"][phase_name] = {
                "status": metrics.status,
                "duration_seconds": metrics.duration_seconds,
                "items_processed": metrics.items_processed,
                "items_succeeded": metrics.items_succeeded,
                "items_failed": metrics.items_failed,
                "retry_count": metrics.retry_count,
                "error_message": metrics.error_message
            }
        
        return summary
    
    def get_phase_status(self, phase: WorkflowPhase) -> Dict:
        """Get current status of a specific phase"""
        with self._lock:
            if phase.value not in self.phase_metrics:
                return {"status": "not_found"}
            
            metrics = self.phase_metrics[phase.value]
            return {
                "phase": phase.value,
                "status": metrics.status,
                "start_time": metrics.start_time.isoformat() if metrics.start_time else None,
                "duration_seconds": metrics.duration_seconds,
                "items_processed": metrics.items_processed,
                "progress_percentage": (metrics.items_succeeded / metrics.items_processed * 100) 
                                     if metrics.items_processed > 0 else 0
            }
    
    def get_active_workflows(self) -> List[Dict]:
        """Get list of active workflows"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cycle_id, status, start_time, 
                   securities_scanned, patterns_detected, 
                   signals_generated, trades_executed
            FROM workflow_metrics
            WHERE status = 'running'
            ORDER BY start_time DESC
        ''')
        
        workflows = []
        for row in cursor.fetchall():
            workflows.append({
                "cycle_id": row[0],
                "status": row[1],
                "start_time": row[2],
                "securities_scanned": row[3],
                "patterns_detected": row[4],
                "signals_generated": row[5],
                "trades_executed": row[6]
            })
        
        conn.close()
        return workflows
    
    def get_workflow_history(self, limit: int = 10) -> List[Dict]:
        """Get workflow execution history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cycle_id, status, start_time, end_time,
                   total_duration_seconds, success_rate, error_count,
                   securities_scanned, patterns_detected, 
                   signals_generated, trades_executed
            FROM workflow_metrics
            ORDER BY start_time DESC
            LIMIT ?
        ''', (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "cycle_id": row[0],
                "status": row[1],
                "start_time": row[2],
                "end_time": row[3],
                "duration_seconds": row[4],
                "success_rate": row[5],
                "error_count": row[6],
                "metrics": {
                    "securities_scanned": row[7],
                    "patterns_detected": row[8],
                    "signals_generated": row[9],
                    "trades_executed": row[10]
                }
            })
        
        conn.close()
        return history
    
    def get_phase_performance_stats(self) -> Dict:
        """Get performance statistics for each phase"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        for phase in WorkflowPhase:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_runs,
                    AVG(duration_seconds) as avg_duration,
                    MIN(duration_seconds) as min_duration,
                    MAX(duration_seconds) as max_duration,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_count,
                    AVG(items_processed) as avg_items_processed,
                    AVG(CASE WHEN items_processed > 0 
                        THEN CAST(items_succeeded AS FLOAT) / items_processed 
                        ELSE 0 END) as avg_success_rate
                FROM workflow_tracking
                WHERE phase = ?
                AND status IN ('completed', 'failed')
            ''', (phase.value,))
            
            row = cursor.fetchone()
            if row and row[0] > 0:
                stats[phase.value] = {
                    "total_runs": row[0],
                    "avg_duration_seconds": row[1],
                    "min_duration_seconds": row[2],
                    "max_duration_seconds": row[3],
                    "success_rate": row[4] / row[0] if row[0] > 0 else 0,
                    "avg_items_processed": row[5] or 0,
                    "avg_item_success_rate": row[6] or 0
                }
        
        conn.close()
        return stats
    
    def check_service_health(self) -> Dict[str, bool]:
        """Check health of all trading services"""
        health_status = {}
        
        for service, endpoint in self.service_endpoints.items():
            try:
                response = requests.get(f"{endpoint}/health", timeout=2)
                health_status[service] = response.status_code == 200
            except:
                health_status[service] = False
        
        return health_status
    
    def _save_phase_metrics(self, phase_name: str):
        """Save phase metrics to database"""
        metrics = self.phase_metrics.get(phase_name)
        if not metrics:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO workflow_tracking
            (cycle_id, phase, status, start_time, end_time, duration_seconds,
             items_processed, items_succeeded, items_failed, error_message,
             retry_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.current_cycle,
            metrics.phase,
            metrics.status,
            metrics.start_time.isoformat() if metrics.start_time else None,
            metrics.end_time.isoformat() if metrics.end_time else None,
            metrics.duration_seconds,
            metrics.items_processed,
            metrics.items_succeeded,
            metrics.items_failed,
            metrics.error_message,
            metrics.retry_count,
            json.dumps(metrics.metadata) if metrics.metadata else None
        ))
        
        conn.commit()
        conn.close()
    
    def _save_workflow_metrics(self):
        """Save workflow metrics to database"""
        if not self.workflow_metrics:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO workflow_metrics
            (cycle_id, status, start_time, end_time, total_duration_seconds,
             securities_scanned, patterns_detected, signals_generated,
             trades_executed, success_rate, error_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.workflow_metrics.cycle_id,
            self.workflow_metrics.status,
            self.workflow_metrics.start_time.isoformat(),
            self.workflow_metrics.end_time.isoformat() if self.workflow_metrics.end_time else None,
            self.workflow_metrics.total_duration_seconds,
            self.workflow_metrics.securities_scanned,
            self.workflow_metrics.patterns_detected,
            self.workflow_metrics.signals_generated,
            self.workflow_metrics.trades_executed,
            self.workflow_metrics.success_rate,
            self.workflow_metrics.error_count
        ))
        
        conn.commit()
        conn.close()
    
    def _update_workflow_metrics_for_phase(self, phase: WorkflowPhase, metrics: PhaseMetrics):
        """Update workflow metrics based on phase completion"""
        if not self.workflow_metrics:
            return
        
        if phase == WorkflowPhase.SECURITY_SELECTION:
            self.workflow_metrics.securities_scanned = metrics.items_processed
        elif phase == WorkflowPhase.PATTERN_ANALYSIS:
            self.workflow_metrics.patterns_detected = metrics.items_succeeded
        elif phase == WorkflowPhase.SIGNAL_GENERATION:
            self.workflow_metrics.signals_generated = metrics.items_succeeded
        elif phase == WorkflowPhase.TRADE_EXECUTION:
            self.workflow_metrics.trades_executed = metrics.items_succeeded
        
        self._save_workflow_metrics()
    
    def _log_event(self, cycle_id: str, phase: str, event_type: str, event_data: Dict = None):
        """Log workflow event to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflow_events (cycle_id, phase, event_type, event_data)
            VALUES (?, ?, ?, ?)
        ''', (
            cycle_id,
            phase,
            event_type,
            json.dumps(event_data) if event_data else None
        ))
        
        conn.commit()
        conn.close()


# Example usage for integration with coordination service
if __name__ == "__main__":
    # Initialize tracker
    tracker = TradingWorkflowTracker()
    
    # Example: Start tracking a new workflow
    cycle_id = f"CYCLE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    tracker.start_workflow(cycle_id)
    
    # Example: Track security selection phase
    tracker.start_phase(WorkflowPhase.SECURITY_SELECTION)
    tracker.update_phase_progress(
        WorkflowPhase.SECURITY_SELECTION,
        items_processed=100,
        items_succeeded=15,
        items_failed=0
    )
    tracker.complete_phase(WorkflowPhase.SECURITY_SELECTION)
    
    # Get workflow summary
    summary = tracker.get_workflow_summary()
    print(json.dumps(summary, indent=2))

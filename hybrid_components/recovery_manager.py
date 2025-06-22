"""
Name of Service: TRADING SYSTEM HYBRID ARCHITECTURE - RECOVERY MANAGER
Version: 3.0.0
Last Updated: 2025-06-15
REVISION HISTORY:
v3.0.0 (2025-06-15) - Initial recovery manager implementation
"""

import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class RecoveryManager:
    """Handles checkpoints and recovery for Colab disconnections"""
    
    def __init__(self, manager):
        self.manager = manager
        self.logger = logging.getLogger('RecoveryManager')
        
        # Checkpoint paths
        checkpoint_dir = manager.config.get_paths()['checkpoint_dir']
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.latest_checkpoint = self.checkpoint_dir / 'checkpoint_latest.json'
        self.checkpoint_count = 0
        self.last_checkpoint_time = None
    
    def create_checkpoint(self) -> Dict:
        """Create a checkpoint of current system state"""
        checkpoint = {
            'version': '3.0.0',
            'timestamp': datetime.now().isoformat(),
            'system_state': {
                'uptime': self.manager.get_uptime(),
                'start_time': self.manager.start_time.isoformat() if self.manager.start_time else None,
                'services': {}
            },
            'service_metrics': {},
            'configuration': self.manager.config.to_dict()
        }
        
        # Get state of each service
        for service_name in self.manager.services:
            service_status = self.manager.lifecycle.get_service_status(service_name)
            checkpoint['system_state']['services'][service_name] = {
                'status': service_status['status'],
                'pid': service_status['pid'],
                'port': service_status['port'],
                'started_at': service_status['started_at'],
                'restart_count': service_status['restart_count']
            }
            
            # Add metrics if available
            checkpoint['service_metrics'][service_name] = {
                'uptime_seconds': service_status['uptime'],
                'health_checks_passed': service_status['is_healthy'],
                'last_health_check': service_status['last_health_check']
            }
        
        return checkpoint
    
    def save_checkpoint(self) -> bool:
        """Save checkpoint to disk"""
        try:
            checkpoint = self.create_checkpoint()
            
            # Save to latest checkpoint file
            with open(self.latest_checkpoint, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            # Also save timestamped backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.checkpoint_dir / f'checkpoint_{timestamp}.json'
            shutil.copy2(self.latest_checkpoint, backup_file)
            
            # Save daily backup
            daily_file = self.checkpoint_dir / f'checkpoint_daily_{datetime.now().strftime("%Y%m%d")}.json'
            shutil.copy2(self.latest_checkpoint, daily_file)
            
            # Clean old checkpoints (keep last 10)
            self._cleanup_old_checkpoints()
            
            self.checkpoint_count += 1
            self.last_checkpoint_time = datetime.now()
            
            self.logger.info(f"Checkpoint saved successfully (#{self.checkpoint_count})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving checkpoint: {str(e)}")
            return False
    
    def restore_from_checkpoint(self, checkpoint_path: Optional[Path] = None) -> bool:
        """Restore system from checkpoint"""
        try:
            # Use provided checkpoint or latest
            checkpoint_file = checkpoint_path or self.latest_checkpoint
            
            if not checkpoint_file.exists():
                self.logger.warning("No checkpoint found to restore from")
                return False
            
            # Load checkpoint
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            self.logger.info(f"Restoring from checkpoint: {checkpoint['timestamp']}")
            
            # Restore configuration if different
            saved_config = checkpoint.get('configuration', {})
            if saved_config:
                self.manager.config.update_from_dict(saved_config)
            
            # Restore services that were running
            services_to_start = []
            for service_name, service_state in checkpoint['system_state']['services'].items():
                if service_state['status'] in ['running', 'starting']:
                    services_to_start.append(service_name)
            
            # Run database migration first
            self.manager._run_database_migration()
            
            # Start services
            self.logger.info(f"Restarting {len(services_to_start)} services from checkpoint")
            for service_name in services_to_start:
                success = self.manager.lifecycle.start_service(service_name)
                if not success:
                    self.logger.warning(f"Failed to restore service: {service_name}")
            
            self.logger.info("System restored from checkpoint")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring from checkpoint: {str(e)}")
            return False
    
    def save_final_state(self):
        """Save final state before shutdown"""
        try:
            # Create final checkpoint
            checkpoint = self.create_checkpoint()
            checkpoint['shutdown_time'] = datetime.now().isoformat()
            checkpoint['shutdown_type'] = 'graceful'
            
            # Save to special file
            final_state_file = self.checkpoint_dir / 'final_state.json'
            with open(final_state_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            self.logger.info("Final state saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving final state: {str(e)}")
    
    def checkpoint_exists(self) -> bool:
        """Check if a checkpoint exists"""
        return self.latest_checkpoint.exists()
    
    def get_last_checkpoint_time(self) -> Optional[str]:
        """Get timestamp of last checkpoint"""
        if self.last_checkpoint_time:
            return self.last_checkpoint_time.isoformat()
        
        # Check file modification time
        if self.latest_checkpoint.exists():
            mtime = datetime.fromtimestamp(self.latest_checkpoint.stat().st_mtime)
            return mtime.isoformat()
        
        return None
    
    def get_checkpoint_count(self) -> int:
        """Get number of checkpoints saved in this session"""
        return self.checkpoint_count
    
    def list_available_checkpoints(self) -> list:
        """List all available checkpoint files"""
        checkpoints = []
        
        for checkpoint_file in self.checkpoint_dir.glob('checkpoint_*.json'):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                
                checkpoints.append({
                    'filename': checkpoint_file.name,
                    'path': str(checkpoint_file),
                    'timestamp': data.get('timestamp'),
                    'version': data.get('version'),
                    'service_count': len(data.get('system_state', {}).get('services', {}))
                })
            except:
                pass
        
        return sorted(checkpoints, key=lambda x: x['timestamp'], reverse=True)
    
    def _cleanup_old_checkpoints(self):
        """Remove old checkpoint files, keeping the most recent ones"""
        try:
            # Get all timestamped checkpoints
            checkpoint_files = list(self.checkpoint_dir.glob('checkpoint_20*.json'))
            
            # Sort by modification time
            checkpoint_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the 10 most recent
            for old_file in checkpoint_files[10:]:
                old_file.unlink()
                self.logger.debug(f"Removed old checkpoint: {old_file.name}")
                
        except Exception as e:
            self.logger.warning(f"Error cleaning up old checkpoints: {str(e)}")

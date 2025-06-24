"""
Name of Service: TRADING SYSTEM HYBRID ARCHITECTURE - CONFIGURATION MANAGER
Version: 3.0.1
Last Updated: 2025-06-15
REVISION HISTORY:
v3.0.1 (2025-06-15) - Added dashboard service to DEFAULT_SERVICES
v3.0.0 (2025-06-15) - Initial configuration manager implementation
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List

class ConfigurationManager:
    """Manages system and service configurations"""
    
    # Default service registry matching v2.0 architecture
    DEFAULT_SERVICES = {
        "coordination": {
            "file": "coordination_service.py",
            "port": 5000,
            "health_endpoint": "/health",
            "startup_delay": 2,
            "critical": True,
            "dependencies": []
        },
        "scanner": {
            "file": "security_scanner.py",
            "port": 5001,
            "health_endpoint": "/health",
            "startup_delay": 2,
            "critical": True,
            "dependencies": ["coordination"]
        },
        "pattern": {
            "file": "pattern_analysis.py",
            "port": 5002,
            "health_endpoint": "/health",
            "startup_delay": 2,
            "critical": False,
            "dependencies": ["coordination"]
        },
        "technical": {
            "file": "technical_analysis.py",
            "port": 5003,
            "health_endpoint": "/health",
            "startup_delay": 2,
            "critical": True,
            "dependencies": ["coordination"]
        },
        "trading": {
            "file": "paper_trading.py",
            "port": 5005,
            "health_endpoint": "/health",
            "startup_delay": 3,
            "critical": False,
            "dependencies": ["coordination", "technical"]
        },
        "pattern_rec": {
            "file": "pattern_recognition_service.py",
            "port": 5006,
            "health_endpoint": "/health",
            "startup_delay": 2,
            "critical": False,
            "dependencies": []
        },
        "news": {
            "file": "news_service.py",
            "port": 5008,
            "health_endpoint": "/health",
            "startup_delay": 2,
            "critical": False,
            "dependencies": []
        },
        "reporting": {
            "file": "reporting_service.py",
            "port": 5009,
            "health_endpoint": "/health",
            "startup_delay": 2,
            "critical": False,
            "dependencies": ["coordination"]
        },
        "dashboard": {
            "file": "web_dashboard_service.py",
            "port": 5010,
            "health_endpoint": "/health",
            "startup_delay": 2,
            "critical": False,
            "dependencies": ["coordination", "trading", "reporting"]
        }
    }
    
    # Default system configuration
    DEFAULT_SYSTEM_CONFIG = {
        "checkpoint_interval": 300,  # 5 minutes
        "health_check_interval": 30,  # 30 seconds
        "max_restart_attempts": 3,
        "restart_backoff_base": 10,  # seconds
        "enable_auto_restart": True,
        "enable_checkpoints": True,
        "log_level": "INFO"
    }
    
    # Default paths
    DEFAULT_PATHS = {
        "services_dir": ".",
        "logs_dir": "./logs",
        "checkpoint_dir": "./checkpoints",
        "backup_dir": "./backups",
        "database_path": "./trading_system.db"
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager"""
        self.logger = logging.getLogger('ConfigurationManager')
        self.config_file = config_file
        
        # Initialize with defaults
        self.services = self.DEFAULT_SERVICES.copy()
        self.system_config = self.DEFAULT_SYSTEM_CONFIG.copy()
        self.paths = self.DEFAULT_PATHS.copy()
        
        # Load custom configuration if provided
        if config_file:
            self.load_config(config_file)
        
        # Ensure directories exist
        self._ensure_directories()
    
    def load_config(self, config_file: str) -> bool:
        """Load configuration from file"""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                self.logger.warning(f"Config file not found: {config_file}")
                return False
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update configurations
            if 'services' in config:
                self.services.update(config['services'])
            
            if 'system' in config:
                self.system_config.update(config['system'])
            
            if 'paths' in config:
                self.paths.update(config['paths'])
            
            self.logger.info(f"Configuration loaded from {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return False
    
    def save_config(self, config_file: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        try:
            config_path = Path(config_file or self.config_file or 'hybrid_config.json')
            
            config = {
                'version': '3.0.1',
                'services': self.services,
                'system': self.system_config,
                'paths': self.paths
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            return False
    
    def get_services(self) -> Dict:
        """Get service configurations"""
        return self.services
    
    def get_service_config(self, service_name: str) -> Optional[Dict]:
        """Get configuration for specific service"""
        return self.services.get(service_name)
    
    def get_system_config(self) -> Dict:
        """Get system configuration"""
        return self.system_config
    
    def get_paths(self) -> Dict:
        """Get path configurations"""
        return self.paths
    
    def update_service_config(self, service_name: str, config: Dict):
        """Update configuration for a specific service"""
        if service_name in self.services:
            self.services[service_name].update(config)
            self.logger.info(f"Updated configuration for service: {service_name}")
    
    def update_system_config(self, config: Dict):
        """Update system configuration"""
        self.system_config.update(config)
        self.logger.info("Updated system configuration")
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            'services': self.services,
            'system': self.system_config,
            'paths': self.paths
        }
    
    def update_from_dict(self, config: Dict):
        """Update configuration from dictionary"""
        if 'services' in config:
            self.services.update(config['services'])
        if 'system' in config:
            self.system_config.update(config['system'])
        if 'paths' in config:
            self.paths.update(config['paths'])
    
    def validate_config(self) -> bool:
        """Validate configuration integrity"""
        try:
            # Check required fields for each service
            required_fields = ['file', 'port', 'health_endpoint']
            for service_name, service_config in self.services.items():
                for field in required_fields:
                    if field not in service_config:
                        self.logger.error(f"Missing required field '{field}' for service '{service_name}'")
                        return False
            
            # Check for port conflicts
            ports = [s['port'] for s in self.services.values()]
            if len(ports) != len(set(ports)):
                self.logger.error("Port conflict detected in service configuration")
                return False
            
            # Validate system config values
            if self.system_config['checkpoint_interval'] < 60:
                self.logger.warning("Checkpoint interval is very short (< 60s)")
            
            if self.system_config['health_check_interval'] < 10:
                self.logger.warning("Health check interval is very short (< 10s)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {str(e)}")
            return False
    
    def _ensure_directories(self):
        """Ensure all configured directories exist"""
        for path_name, path_value in self.paths.items():
            if path_name.endswith('_dir'):
                try:
                    Path(path_value).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.logger.warning(f"Could not create directory {path_value}: {str(e)}")
    
    def get_service_command(self, service_name: str) -> List[str]:
        """Get command to start a service"""
        service_config = self.services.get(service_name)
        if not service_config:
            return []
        
        service_file = Path(self.paths['services_dir']) / service_config['file']
        return ['python', '-u', str(service_file)]
    
    def get_service_dependencies(self, service_name: str) -> List[str]:
        """Get dependencies for a service"""
        service_config = self.services.get(service_name)
        if not service_config:
            return []
        
        return service_config.get('dependencies', [])
    
    def is_critical_service(self, service_name: str) -> bool:
        """Check if a service is critical"""
        service_config = self.services.get(service_name)
        if not service_config:
            return False
        
        return service_config.get('critical', False)

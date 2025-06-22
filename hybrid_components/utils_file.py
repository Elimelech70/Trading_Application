"""
Name of Service: TRADING SYSTEM HYBRID ARCHITECTURE - UTILITIES
Version: 3.0.0
Last Updated: 2025-06-15
REVISION HISTORY:
v3.0.0 (2025-06-15) - Initial utilities implementation
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

def setup_logging(component_name: str, log_level: str = 'INFO') -> logging.Logger:
    """Set up logging for a component"""
    # Ensure log directory exists
    log_dir = Path('/content/logs')
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(component_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # File handler
    log_file = log_dir / f'{component_name.lower()}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def print_banner():
    """Print the hybrid manager banner"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║          TRADING SYSTEM HYBRID ARCHITECTURE v3.0.0         ║
║                                                            ║
║  • 8 Microservices with REST APIs                         ║
║  • Automated Lifecycle Management                          ║
║  • Checkpoint/Recovery for Colab                          ║
║  • Health Monitoring & Auto-Restart                       ║
╚════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_status(status: Dict):
    """Print formatted system status"""
    print("\n" + "="*60)
    print(f"System Status: {status['system_status'].upper()}")
    print(f"Uptime: {format_duration(status.get('uptime_seconds', 0))}")
    print("="*60)
    
    # Service status table
    print("\nSERVICE STATUS:")
    print("-"*60)
    print(f"{'Service':<15} {'Status':<12} {'Port':<8} {'PID':<8} {'Uptime':<15}")
    print("-"*60)
    
    for service_name, service_info in status['services'].items():
        uptime_str = format_duration(service_info.get('uptime', 0))
        print(f"{service_name:<15} {service_info['status']:<12} "
              f"{service_info.get('port', 'N/A'):<8} "
              f"{service_info.get('pid', 'N/A'):<8} {uptime_str:<15}")
    
    print("-"*60)
    
    # Monitoring info
    if 'monitoring' in status:
        print(f"\nMonitoring: {'Enabled' if status['monitoring']['enabled'] else 'Disabled'}")
        print(f"Health Checks: {status['monitoring']['checks_performed']}")
    
    # Recovery info
    if 'recovery' in status:
        print(f"\nCheckpoints Saved: {status['recovery']['checkpoints_saved']}")
        if status['recovery']['last_checkpoint']:
            print(f"Last Checkpoint: {format_timestamp(status['recovery']['last_checkpoint'])}")
    
    print("="*60)

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to human readable string"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def ensure_google_drive_mounted() -> bool:
    """Ensure Google Drive is mounted in Colab"""
    drive_path = Path('/content/drive')
    
    if drive_path.exists() and any(drive_path.iterdir()):
        return True
    
    try:
        # Try to mount Google Drive
        from google.colab import drive
        drive.mount('/content/drive')
        return True
    except ImportError:
        # Not running in Colab
        return False
    except Exception as e:
        print(f"Error mounting Google Drive: {str(e)}")
        return False

def get_service_logs(service_name: str, lines: int = 50) -> Optional[str]:
    """Get recent logs from a service"""
    log_file = Path(f'/content/logs/{service_name}_service.log')
    
    if not log_file.exists():
        return None
    
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except Exception:
        return None

def check_system_requirements() -> Dict[str, bool]:
    """Check if system requirements are met"""
    requirements = {}
    
    # Check Python version
    import sys
    requirements['python_3.10+'] = sys.version_info >= (3, 10)
    
    # Check required directories
    requirements['logs_directory'] = Path('/content/logs').exists()
    requirements['services_directory'] = Path('/content/trading_system').exists()
    
    # Check Google Drive (optional but recommended)
    requirements['google_drive'] = Path('/content/drive').exists()
    
    # Check for database
    requirements['database'] = Path('/content/trading_system.db').exists()
    
    # Check for service files
    service_files = [
        'coordination_service.py',
        'security_scanner.py',
        'pattern_analysis.py',
        'technical_analysis.py',
        'paper_trading.py',
        'pattern_recognition_service.py',
        'news_service.py',
        'reporting_service.py'
    ]
    
    all_services_exist = all(
        Path(f'/conten./{f}').exists() 
        for f in service_files
    )
    requirements['all_services'] = all_services_exist
    
    return requirements

def create_directory_structure():
    """Create required directory structure"""
    directories = [
        '/content/logs',
        '/content/trading_system',
        '/content/drive/MyDrive/TradingBot/checkpoints',
        '/content/drive/MyDrive/TradingBot/backups',
        '/content/drive/MyDrive/TradingBot/logs'
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create {directory}: {str(e)}")

def get_system_info() -> Dict:
    """Get system information"""
    info = {}
    
    # Memory info
    try:
        import psutil
        memory = psutil.virtual_memory()
        info['memory'] = {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'percent_used': memory.percent
        }
        
        # CPU info
        info['cpu'] = {
            'count': psutil.cpu_count(),
            'percent': psutil.cpu_percent(interval=1)
        }
        
        # Disk info
        disk = psutil.disk_usage('/')
        info['disk'] = {
            'total_gb': round(disk.total / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'percent_used': disk.percent
        }
    except ImportError:
        info['error'] = 'psutil not available'
    
    return info

def cleanup_old_logs(days: int = 7):
    """Clean up log files older than specified days"""
    log_dir = Path('/content/logs')
    if not log_dir.exists():
        return
    
    cutoff_time = datetime.now() - timedelta(days=days)
    
    for log_file in log_dir.glob('*.log'):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff_time:
                log_file.unlink()
                print(f"Removed old log: {log_file.name}")
        except Exception:
            pass

# Service health check utilities
async def check_service_health_async(service_name: str, port: int, 
                                   endpoint: str = '/health') -> bool:
    """Async health check for a service"""
    import aiohttp
    
    url = f"http://localhost:{port}{endpoint}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
    except:
        return False

def format_service_table(services: Dict) -> str:
    """Format service information as a table"""
    lines = []
    lines.append("┌" + "─"*15 + "┬" + "─"*12 + "┬" + "─"*8 + "┬" + "─"*15 + "┐")
    lines.append(f"│{'Service':<15}│{'Status':<12}│{'Port':<8}│{'Health':<15}│")
    lines.append("├" + "─"*15 + "┼" + "─"*12 + "┼" + "─"*8 + "┼" + "─"*15 + "┤")
    
    for name, info in services.items():
        health = "✓ Healthy" if info.get('is_healthy') else "✗ Unhealthy"
        lines.append(f"│{name:<15}│{info['status']:<12}│{info['port']:<8}│{health:<15}│")
    
    lines.append("└" + "─"*15 + "┴" + "─"*12 + "┴" + "─"*8 + "┴" + "─"*15 + "┘")
    
    return "\n".join(lines)

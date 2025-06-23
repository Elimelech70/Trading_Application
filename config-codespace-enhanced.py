#!/usr/bin/env python3
"""
Enhanced Setup script for GitHub Codespaces
Configures the Trading Application environment and fixes all compatibility issues
Version: 2.0.0
Last Updated: 2025-06-23

This script:
1. Updates all service paths from Google Colab (/content/) to relative paths
2. Fixes port configuration mismatches
3. Creates comprehensive requirements.txt
4. Initializes database
5. Creates startup and health check scripts
6. Updates documentation folder references
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
import shutil
import json
from datetime import datetime

class CodespaceConfigurator:
    def __init__(self):
        self.root_path = Path('.')
        self.backup_dir = self.root_path / 'config_backups'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.issues_found = []
        self.fixes_applied = []
        self.services_list = [
            'coordination_service.py',
            'security_scanner.py', 
            'pattern_analysis.py',
            'technical_analysis.py',
            'paper_trading.py',
            'pattern_recognition_service.py',
            'news_service.py',
            'reporting_service.py',
            'web_dashboard_service.py',
            'hybrid_manager.py',
            'database_migration.py',
            'diagnostic_toolkit.py',
            'database_utils.py',
            'google_drive_service.py',
            'trading_scheduler.py',
            'coordination_service_v105.py'
        ]
        
    def print_header(self):
        """Print script header"""
        print("\n" + "="*60)
        print("🔧 GitHub Codespaces Configuration Tool v2.0")
        print("="*60)
        print(f"Timestamp: {self.timestamp}")
        print("="*60)
        
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            'logs',
            'backups', 
            'Documentation',
            'Documentation/implementation_plans',
            'Documentation/change_diaries',
            'Documentation/specifications',
            'Documentation/archive',
            'updates',
            '.update_state',
            'config_backups'
        ]
        
        print("\n📁 Creating directory structure...")
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {directory}/")

    def backup_file(self, filepath):
        """Create backup of a file before modification"""
        if Path(filepath).exists():
            backup_subdir = self.backup_dir / self.timestamp
            backup_subdir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_subdir / f"{filepath}.backup"
            shutil.copy2(filepath, backup_path)
            return True
        return False

    def update_service_paths(self):
        """Update paths in service files from Colab to Codespace format"""
        print("\n🔧 Updating service file paths...")
        
        # Comprehensive path replacements
        replacements = [
            # Database paths - order matters!
            ("db_path='/content/trading_system.db'", "db_path='./trading_system.db'"),
            ("db_path = '/content/trading_system.db'", "db_path = './trading_system.db'"),
            ('db_path="/content/trading_system.db"', 'db_path="./trading_system.db"'),
            ("DEFAULT_DB_PATH = '/content/trading_system.db'", "DEFAULT_DB_PATH = './trading_system.db'"),
            ('/content/trading_system.db', './trading_system.db'),
            ("'/content/trading_database.db'", "'./trading_system.db'"),
            ('"/content/trading_database.db"', '"./trading_system.db"'),
            
            # Log paths
            ("'/content/logs/'", "'./logs/'"),
            ('"/content/logs/"', '"./logs/"'),
            ("'/content/logs'", "'./logs'"),
            ('"/content/logs"', '"./logs"'),
            ('/content/logs/', './logs/'),
            ('/content/logs', './logs'),
            
            # Backup paths
            ("'/content/backups/'", "'./backups/'"),
            ('"/content/backups/"', '"./backups/"'),
            ("'/content/backups'", "'./backups'"),
            ('"/content/backups"', '"./backups"'),
            ('/content/backups/', './backups/'),
            ('/content/backups', './backups'),
            
            # Documentation paths
            ('project_documentation/', 'Documentation/'),
            ('project_documentation\\\\', 'Documentation\\\\'),
            ('"project_documentation"', '"Documentation"'),
            ("'project_documentation'", "'Documentation'"),
            
            # General content paths - do these last
            ("'/content/'", "'./'"),
            ('"/content/"', '"./"'),
            ("'/content'", "'.'"),
            ('"/content"', '"."'),
            ('/content/', './'),
        ]
        
        updated_count = 0
        
        for service in self.services_list:
            if Path(service).exists():
                try:
                    # Backup file first
                    self.backup_file(service)
                    
                    with open(service, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    changes_made = []
                    
                    # Apply replacements
                    for old_path, new_path in replacements:
                        if old_path in content:
                            count = content.count(old_path)
                            content = content.replace(old_path, new_path)
                            changes_made.append(f"    - {old_path} → {new_path} ({count}x)")
                            self.issues_found.append(f"{service}: Found {old_path}")
                    
                    # Fix specific issues per service
                    if service == 'hybrid_manager.py':
                        # Fix port mismatch
                        if '"port": 8080' in content:
                            content = content.replace('"port": 8080', '"port": 5010')
                            changes_made.append("    - Port 8080 → 5010 (dashboard)")
                            self.issues_found.append(f"{service}: Port mismatch")
                    
                    if service == 'database_migration.py':
                        # Fix hardcoded db path in __init__
                        lines = content.split('\n')
                        new_lines = []
                        for i, line in enumerate(lines):
                            if 'self.db_path = ' in line and i > 0:
                                # Check if we're in __init__ method
                                if any('def __init__' in lines[j] for j in range(max(0, i-10), i)):
                                    if "db_path" in lines[i-1] or "db_path" in lines[i-2]:
                                        new_lines.append("        self.db_path = db_path")
                                        changes_made.append("    - Fixed hardcoded db_path in __init__")
                                    else:
                                        new_lines.append(line)
                                else:
                                    new_lines.append(line)
                            else:
                                new_lines.append(line)
                        content = '\n'.join(new_lines)
                    
                    # Remove Google Colab imports
                    lines = content.split('\n')
                    filtered_lines = []
                    for line in lines:
                        if 'from google.colab import' in line or 'import google.colab' in line:
                            filtered_lines.append(f"# {line}  # Removed for Codespace")
                            changes_made.append(f"    - Removed: {line.strip()}")
                            self.issues_found.append(f"{service}: Google Colab import")
                        else:
                            filtered_lines.append(line)
                    
                    content = '\n'.join(filtered_lines)
                    
                    # Write updated content if changed
                    if content != original_content:
                        with open(service, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"\n  ✓ Updated {service}")
                        if changes_made:
                            print("    Changes:")
                            for change in changes_made:
                                print(change)
                        self.fixes_applied.append(f"{service}: {len(changes_made)} changes")
                        updated_count += 1
                        
                except Exception as e:
                    print(f"  ⚠️  Error updating {service}: {e}")
                    self.issues_found.append(f"{service}: Error - {e}")
        
        print(f"\n  Summary: Updated {updated_count} files")

    def create_requirements_file(self):
        """Create comprehensive requirements.txt with all dependencies"""
        print("\n📦 Creating requirements.txt...")
        
        requirements_content = """# Trading Application Requirements
# Generated by Config_Codespace.py
# Last Updated: """ + self.timestamp + """

# Core Web Framework
flask==3.0.0
flask-cors==4.0.0
flask-socketio==5.3.5
waitress==2.1.2

# HTTP and Networking
requests==2.31.0
urllib3==2.0.7

# Data Processing
pandas==2.1.4
numpy==1.26.2

# Machine Learning
scikit-learn==1.3.2

# Trading and Market Data
yfinance==0.2.33
alpaca-py==0.21.1

# Technical Analysis (Optional - comment out if TA-Lib install fails)
# TA-Lib==0.4.28

# Natural Language Processing
textblob==0.17.1
nltk==3.8.1

# Web Scraping
beautifulsoup4==4.12.2
lxml==4.9.3

# System Monitoring
psutil==5.9.6

# Date/Time Handling
python-dateutil==2.8.2
pytz==2023.3

# Environment Configuration
python-dotenv==1.0.0

# Development Tools (optional)
# ipython==8.17.2
# jupyter==1.0.0

# Testing (optional)
# pytest==7.4.3
# pytest-cov==4.1.0
"""
        
        # Backup existing requirements.txt if it exists
        if Path('requirements.txt').exists():
            self.backup_file('requirements.txt')
            
        with open('requirements.txt', 'w') as f:
            f.write(requirements_content)
        
        print("  ✓ Created comprehensive requirements.txt")
        self.fixes_applied.append("Created requirements.txt with all dependencies")

    def initialize_database(self):
        """Initialize the database using database_migration.py"""
        print("\n🗄️  Initializing database...")
        
        if Path('database_migration.py').exists():
            try:
                result = subprocess.run(
                    [sys.executable, 'database_migration.py'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    print("  ✓ Database initialized successfully")
                    self.fixes_applied.append("Database initialized")
                    
                    # Verify database exists
                    if Path('./trading_system.db').exists():
                        size = Path('./trading_system.db').stat().st_size
                        print(f"  ✓ Database created: trading_system.db ({size:,} bytes)")
                else:
                    print(f"  ⚠️  Database initialization warning:")
                    print(f"    {result.stderr}")
                    self.issues_found.append(f"Database initialization: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("  ⚠️  Database initialization timed out")
                self.issues_found.append("Database initialization timeout")
            except Exception as e:
                print(f"  ⚠️  Database initialization error: {e}")
                self.issues_found.append(f"Database initialization error: {e}")
        else:
            print("  ⚠️  database_migration.py not found")
            self.issues_found.append("database_migration.py not found")

    def create_startup_scripts(self):
        """Create startup and utility scripts"""
        print("\n🚀 Creating startup scripts...")
        
        # 1. Bash startup script
        startup_bash = """#!/bin/bash
# Trading Application Startup Script for GitHub Codespaces
# Generated by Config_Codespace.py

echo "🚀 Starting Trading Application..."
echo "================================"

# Colors for output
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt

# Initialize database if needed
if [ ! -f "./trading_system.db" ]; then
    echo -e "${YELLOW}Initializing database...${NC}"
    python database_migration.py
fi

# Start the trading system
echo -e "${GREEN}Starting Trading System...${NC}"
python hybrid_manager.py start

echo "================================"
echo -e "${GREEN}✅ Trading Application Started!${NC}"
echo -e "${GREEN}📊 Dashboard: http://localhost:5010${NC}"
echo "================================"
"""
        
        with open('start_trading.sh', 'w') as f:
            f.write(startup_bash)
        os.chmod('start_trading.sh', 0o755)
        print("  ✓ Created start_trading.sh")

        # 2. Health check script
        health_check = '''#!/usr/bin/env python3
"""
Health Check Script for Trading Application
Verifies all services are running correctly
"""
import requests
import time
import sys
from datetime import datetime

SERVICES = {
    'Coordination Service': 5000,
    'Security Scanner': 5001,
    'Pattern Analysis': 5002,
    'Technical Analysis': 5003,
    'Paper Trading': 5005,
    'Pattern Recognition': 5006,
    'News Service': 5008,
    'Reporting Service': 5009,
    'Web Dashboard': 5010
}

def check_service(name, port, timeout=2):
    """Check if a service is responding"""
    try:
        response = requests.get(f'http://localhost:{port}/health', timeout=timeout)
        if response.status_code == 200:
            return True, "OK", response.json() if response.text else {}
        else:
            return False, f"HTTP {response.status_code}", {}
    except requests.exceptions.Timeout:
        return False, "Timeout", {}
    except requests.exceptions.ConnectionError:
        return False, "Connection refused", {}
    except Exception as e:
        return False, str(e), {}

def main():
    """Run health checks on all services"""
    print("\\n" + "="*60)
    print("🏥 Trading Application Health Check")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    all_healthy = True
    healthy_count = 0
    
    # Table header
    print(f"\\n{'Service':<25} {'Port':<6} {'Status':<20} {'Details'}")
    print("-"*70)
    
    for name, port in SERVICES.items():
        is_healthy, status, details = check_service(name, port)
        
        # Status icon
        icon = "✅" if is_healthy else "❌"
        
        # Format details
        detail_str = ""
        if details:
            if 'service' in details:
                detail_str = f"[{details['service']}]"
        
        print(f"{icon} {name:<23} {port:<6} {status:<20} {detail_str}")
        
        if is_healthy:
            healthy_count += 1
        else:
            all_healthy = False
    
    print("-"*70)
    print(f"\\nSummary: {healthy_count}/{len(SERVICES)} services healthy")
    
    if all_healthy:
        print("\\n✅ All services are healthy!")
        return 0
    else:
        print("\\n⚠️  Some services are not responding")
        print("\\nTroubleshooting:")
        print("1. Check if services are started: python hybrid_manager.py status")
        print("2. Check logs in ./logs/ directory")
        print("3. Try restarting services: python hybrid_manager.py restart")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open('health_check.py', 'w') as f:
            f.write(health_check)
        os.chmod('health_check.py', 0o755)
        print("  ✓ Created health_check.py")

        # 3. Quick test script
        quick_test = '''#!/usr/bin/env python3
"""
Quick Test Script - Validates basic functionality
"""
import subprocess
import time
import sys

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Success")
            if result.stdout:
                print(f"  Output: {result.stdout.strip()[:100]}...")
            return True
        else:
            print(f"  ❌ Failed")
            if result.stderr:
                print(f"  Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False

def main():
    print("🧪 Running Quick Tests...")
    print("="*50)
    
    tests = [
        ("python --version", "Checking Python"),
        ("ls -la trading_system.db 2>/dev/null || echo 'Database not found'", "Checking database"),
        ("ls -la logs/ 2>/dev/null || echo 'Logs directory not found'", "Checking logs directory"),
        ("pip show flask requests pandas", "Checking key packages"),
    ]
    
    passed = 0
    for cmd, desc in tests:
        if run_command(cmd, desc):
            passed += 1
    
    print(f"\\n{'='*50}")
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open('quick_test.py', 'w') as f:
            f.write(quick_test)
        os.chmod('quick_test.py', 0o755)
        print("  ✓ Created quick_test.py")
        
        self.fixes_applied.append("Created startup scripts: start_trading.sh, health_check.py, quick_test.py")

    def create_config_module(self):
        """Create unified configuration module"""
        print("\n⚙️  Creating trading_config.py...")
        
        config_content = '''"""
Unified Configuration for Trading Application
Handles paths and settings across different environments
Generated by Config_Codespace.py
"""
import os
from pathlib import Path

# Environment Detection
IS_COLAB = 'google.colab' in sys.modules
IS_CODESPACE = os.environ.get('CODESPACES', 'false').lower() == 'true'
IS_DOCKER = os.path.exists('/.dockerenv')

# Base Paths
if IS_COLAB:
    BASE_PATH = Path('/content')
elif IS_CODESPACE:
    # In Codespaces, we're in /workspaces/[repo-name]
    BASE_PATH = Path.cwd()
else:
    BASE_PATH = Path('.')

# Directory Paths
DB_PATH = str(BASE_PATH / 'trading_system.db')
LOG_DIR = str(BASE_PATH / 'logs')
BACKUP_DIR = str(BASE_PATH / 'backups')
UPDATE_DIR = str(BASE_PATH / 'updates')
DOC_DIR = str(BASE_PATH / 'Documentation')

# Service Configuration
SERVICES = {
    'coordination': {
        'name': 'Coordination Service',
        'port': 5000,
        'file': 'coordination_service.py',
        'critical': True
    },
    'scanner': {
        'name': 'Security Scanner',
        'port': 5001,
        'file': 'security_scanner.py',
        'critical': True
    },
    'pattern': {
        'name': 'Pattern Analysis',
        'port': 5002,
        'file': 'pattern_analysis.py',
        'critical': True
    },
    'technical': {
        'name': 'Technical Analysis',
        'port': 5003,
        'file': 'technical_analysis.py',
        'critical': True
    },
    'trading': {
        'name': 'Paper Trading',
        'port': 5005,
        'file': 'paper_trading.py',
        'critical': True
    },
    'pattern_rec': {
        'name': 'Pattern Recognition',
        'port': 5006,
        'file': 'pattern_recognition_service.py',
        'critical': False
    },
    'news': {
        'name': 'News Service',
        'port': 5008,
        'file': 'news_service.py',
        'critical': False
    },
    'reporting': {
        'name': 'Reporting Service',
        'port': 5009,
        'file': 'reporting_service.py',
        'critical': False
    },
    'dashboard': {
        'name': 'Web Dashboard',
        'port': 5010,
        'file': 'web_dashboard_service.py',
        'critical': False
    }
}

# Trading Configuration
TRADING_CONFIG = {
    'market_hours': {
        'start': '09:30',
        'end': '16:00',
        'timezone': 'America/New_York',
        'trading_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    },
    'risk_management': {
        'max_position_size': 0.1,      # 10% of portfolio per position
        'max_portfolio_risk': 0.02,     # 2% total portfolio risk
        'stop_loss_percent': 0.02,      # 2% stop loss
        'take_profit_percent': 0.06,    # 6% take profit
        'daily_loss_limit': 0.05,       # 5% daily loss limit
        'max_positions': 10             # Maximum concurrent positions
    },
    'scanning': {
        'min_price': 10.0,
        'max_price': 500.0,
        'min_volume': 1000000,
        'scan_interval_minutes': 30
    }
}

# Database Configuration
DATABASE_CONFIG = {
    'path': DB_PATH,
    'pragma': {
        'journal_mode': 'WAL',
        'synchronous': 'NORMAL',
        'cache_size': -64000,  # 64MB
        'foreign_keys': 'ON',
        'temp_store': 'MEMORY'
    },
    'pool_size': 5,
    'timeout': 30.0
}

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{LOG_DIR}/trading_system.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}

# Create necessary directories
for directory in [LOG_DIR, BACKUP_DIR, UPDATE_DIR, DOC_DIR]:
    Path(directory).mkdir(exist_ok=True)

def get_service_url(service_key):
    """Get the URL for a service"""
    if service_key in SERVICES:
        return f"http://localhost:{SERVICES[service_key]['port']}"
    return None

def get_db_connection():
    """Get a database connection with proper configuration"""
    import sqlite3
    
    conn = sqlite3.connect(DATABASE_CONFIG['path'], timeout=DATABASE_CONFIG['timeout'])
    conn.row_factory = sqlite3.Row
    
    # Apply PRAGMA settings
    for pragma, value in DATABASE_CONFIG['pragma'].items():
        conn.execute(f"PRAGMA {pragma} = {value}")
    
    return conn

# Environment info
print(f"Trading Config Loaded: BASE_PATH = {BASE_PATH}")
if IS_CODESPACE:
    print("Running in GitHub Codespaces")
elif IS_COLAB:
    print("Running in Google Colab")
else:
    print("Running in Local Environment")
'''
        
        with open('trading_config.py', 'w') as f:
            f.write(config_content)
        
        print("  ✓ Created trading_config.py")
        self.fixes_applied.append("Created unified configuration module")

    def create_gitignore(self):
        """Create or update .gitignore file"""
        print("\n📝 Creating .gitignore...")
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv/

# Virtual Environments
bin/
include/
lib/
lib64/
share/
pyvenv.cfg

# Trading Application
logs/
*.log
trading_system.db
trading_system.db-journal
trading_system.db-wal
backups/
config_backups/
update_backups/
*.backup
.update_state/
update_state.json

# Sensitive Data
.env
.env.local
.env.*.local
config.ini
credentials.json
*.key
*.pem

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.project
.pydevproject

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Jupyter/IPython
.ipynb_checkpoints/
*.ipynb

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/
.nox/
coverage.xml
*.cover
.hypothesis/

# Documentation builds
docs/_build/
docs/_static/
docs/_templates/

# Temporary files
*.tmp
*.temp
*.bak
tmp/
temp/

# Package files
*.egg
*.egg-info/
dist/
build/
eggs/
parts/
sdist/
wheels/
pip-wheel-metadata/
"""
        
        # Backup existing .gitignore if it exists
        if Path('.gitignore').exists():
            self.backup_file('.gitignore')
            
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        
        print("  ✓ Created .gitignore")
        self.fixes_applied.append("Created comprehensive .gitignore")

    def generate_report(self):
        """Generate configuration report"""
        print("\n" + "="*60)
        print("📊 Configuration Report")
        print("="*60)
        
        # Issues found
        if self.issues_found:
            print(f"\n🔍 Issues Found ({len(self.issues_found)}):")
            # Group by type
            path_issues = [i for i in self.issues_found if '/content' in i]
            import_issues = [i for i in self.issues_found if 'Colab import' in i]
            other_issues = [i for i in self.issues_found if i not in path_issues and i not in import_issues]
            
            if path_issues:
                print(f"\n  Path Issues ({len(path_issues)}):")
                for issue in path_issues[:5]:
                    print(f"    - {issue}")
                if len(path_issues) > 5:
                    print(f"    ... and {len(path_issues) - 5} more")
                    
            if import_issues:
                print(f"\n  Import Issues ({len(import_issues)}):")
                for issue in import_issues[:3]:
                    print(f"    - {issue}")
                if len(import_issues) > 3:
                    print(f"    ... and {len(import_issues) - 3} more")
                    
            if other_issues:
                print(f"\n  Other Issues ({len(other_issues)}):")
                for issue in other_issues:
                    print(f"    - {issue}")
        else:
            print("\n✅ No issues found!")
        
        # Fixes applied
        if self.fixes_applied:
            print(f"\n🔧 Fixes Applied ({len(self.fixes_applied)}):")
            for fix in self.fixes_applied:
                print(f"  ✓ {fix}")
        
        # File status
        print("\n📋 File Status:")
        important_files = [
            ('requirements.txt', 'Package dependencies'),
            ('trading_config.py', 'Unified configuration'),
            ('start_trading.sh', 'Startup script'),
            ('health_check.py', 'Service health checker'),
            ('quick_test.py', 'Quick test script'),
            ('.gitignore', 'Git ignore rules'),
            ('trading_system.db', 'Database'),
            ('logs/', 'Logs directory'),
            ('Documentation/', 'Documentation directory')
        ]
        
        for file, description in important_files:
            exists = "✅" if Path(file).exists() else "❌"
            print(f"  {exists} {file:<25} - {description}")
        
        # Save report to file
        report_path = self.backup_dir / f"configuration_report_{self.timestamp}.txt"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"GitHub Codespaces Configuration Report\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Issues Found: {len(self.issues_found)}\n")
            f.write(f"Fixes Applied: {len(self.fixes_applied)}\n")
            f.write(f"\nBackup Location: {self.backup_dir}\n")
            
            if self.issues_found:
                f.write(f"\n\nDetailed Issues:\n")
                for issue in self.issues_found:
                    f.write(f"- {issue}\n")
                    
            if self.fixes_applied:
                f.write(f"\n\nDetailed Fixes:\n")
                for fix in self.fixes_applied:
                    f.write(f"- {fix}\n")
        
        print(f"\n📄 Detailed report saved to: {report_path}")

    def main(self):
        """Main configuration process"""
        self.print_header()
        
        # Check if in correct directory
        service_files = [f for f in self.services_list if Path(f).exists()]
        if len(service_files) == 0:
            print("\n⚠️  Warning: No trading application service files found!")
            print("Make sure you're in the Trading_Application repository root.")
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                print("❌ Configuration cancelled")
                return
        else:
            print(f"\n✅ Found {len(service_files)} service files")
        
        # Run configuration steps
        try:
            self.create_directories()
            self.update_service_paths()
            self.create_requirements_file()
            self.create_config_module()
            self.create_startup_scripts()
            self.create_gitignore()
            self.initialize_database()
            self.generate_report()
            
            print("\n" + "="*60)
            print("✅ Configuration Complete!")
            print("="*60)
            
            print("\n📋 Next Steps:")
            print("1. Install dependencies:")
            print("   pip install -r requirements.txt")
            print("\n2. Run quick test:")
            print("   python quick_test.py")
            print("\n3. Check service health:")
            print("   python health_check.py") 
            print("\n4. Start services:")
            print("   ./start_trading.sh")
            print("   OR: python hybrid_manager.py start")
            print("\n💡 Web Dashboard: http://localhost:5010")
            print("\n📚 Documentation: ./Documentation/")
            
        except KeyboardInterrupt:
            print("\n\n❌ Configuration interrupted")
        except Exception as e:
            print(f"\n❌ Configuration failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    configurator = CodespaceConfigurator()
    configurator.main()

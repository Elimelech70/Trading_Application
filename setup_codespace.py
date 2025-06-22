#!/usr/bin/env python3
"""
Setup script for GitHub Codespace
Configures the Trading Application environment
"""
import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'backups',
        'project_documentation',
        'updates',
        '.update_state'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created {directory}/")

def update_service_paths():
    """Update paths in service files from Colab to Codespace format"""
    services = [
        'coordination_service.py',
        'security_scanner.py',
        'pattern_analysis.py',
        'technical_analysis.py',
        'paper_trading.py',
        'pattern_recognition_service.py',
        'news_service.py',
        'reporting_service.py',
        'web_dashboard.py',
        'hybrid_manager.py',
        'database_migration.py',
        'diagnostic_toolkit.py'
    ]
    
    replacements = [
        ('./trading_system.db', './trading_system.db'),
        ('./logs/', './logs/'),
        ('./backups/', './backups/'),
        ('/conten./', './'),
        ('./', './')
    ]
    
    for service in services:
        if Path(service).exists():
            with open(service, 'r') as f:
                content = f.read()
            
            original_content = content
            for old_path, new_path in replacements:
                content = content.replace(old_path, new_path)
            
            # Remove Colab-specific imports
            lines = content.split('\n')
            filtered_lines = []
            for line in lines:
                if 'from google.colab import' not in line and 'import google.colab' not in line:
                    filtered_lines.append(line)
                else:
                    filtered_lines.append(f"# {line}  # Removed for Codespace")
            
            content = '\n'.join(filtered_lines)
            
            if content != original_content:
                with open(service, 'w') as f:
                    f.write(content)
                print(f"✓ Updated paths in {service}")

def initialize_database():
    """Initialize the database"""
    if Path('database_migration.py').exists():
        print("\n🔧 Initializing database...")
        result = subprocess.run([sys.executable, 'database_migration.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Database initialized successfully")
        else:
            print(f"⚠️  Database initialization warning: {result.stderr}")
    else:
        print("⚠️  database_migration.py not found")

def create_requirements_file():
    """Create requirements.txt if it doesn't exist"""
    if not Path('requirements.txt').exists():
        requirements = """flask==3.0.0
requests==2.31.0
pandas==2.1.4
numpy==1.26.2
scikit-learn==1.3.2
yfinance==0.2.33
alpaca-py==0.21.1
psutil==5.9.6
python-dateutil==2.8.2
pytz==2023.3
beautifulsoup4==4.12.2
"""
        with open('requirements.txt', 'w') as f:
            f.write(requirements)
        print("✓ Created requirements.txt")

def create_startup_script():
    """Create a quick startup script"""
    startup_content = """#!/bin/bash
# Quick startup script for Trading Application

echo "🚀 Starting Trading Application Services..."
python hybrid_manager.py
"""
    
    with open('start_trading.sh', 'w') as f:
        f.write(startup_content)
    
    os.chmod('start_trading.sh', 0o755)
    print("✓ Created start_trading.sh")

def main():
    print("🔧 Setting up Trading Application for GitHub Codespaces\n")
    
    # Check if we're in the right directory
    if not any(Path(f).exists() for f in ['coordination_service.py', 'hybrid_manager.py']):
        print("⚠️  Warning: Trading application files not found in current directory")
        print("   Make sure you're in the root of your Trading_Application repository")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    create_directories()
    create_requirements_file()
    update_service_paths()
    initialize_database()
    create_startup_script()
    
    print("\n✅ Codespace setup complete!")
    print("\n📋 Next steps:")
    print("1. Install requirements: pip install -r requirements.txt")
    print("2. Run diagnostic check: python diagnostic_toolkit.py --report")
    print("3. Start services: python hybrid_manager.py")
    print("   OR use: ./start_trading.sh")
    print("\n💡 Tip: The web dashboard will be available at port 8080")

if __name__ == "__main__":
    main()
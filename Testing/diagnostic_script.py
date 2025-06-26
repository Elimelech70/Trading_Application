#!/usr/bin/env python3
"""
Technical Analysis Service Diagnostic Script
Checks common issues and provides troubleshooting guidance
"""

import sys
import os
import sqlite3
import importlib
import subprocess
import requests
from pathlib import Path

def check_python_dependencies():
    """Check if required Python packages are available"""
    print("🔍 Checking Python Dependencies...")
    
    required_packages = [
        'numpy', 'pandas', 'flask', 'requests', 'yfinance', 'scikit-learn'
    ]
    
    missing_packages = []
    available_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            available_packages.append(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required dependencies available")
    return True

def check_database_setup():
    """Check database file and schema"""
    print("\n🔍 Checking Database Setup...")
    
    db_paths = [
        './trading_system.db',
        '/workspaces/trading-system/trading_system.db',
        './trading_system.db'
    ]
    
    db_found = False
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_found = True
            db_path = path
            print(f"  ✅ Database found: {path}")
            break
    
    if not db_found:
        print("  ❌ Database file not found")
        print("  💡 Run database migration first:")
        print("     python database_migration.py")
        return False, None
    
    # Check database schema
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        
        # Check if technical_indicators table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='technical_indicators'
        """)
        
        if cursor.fetchone():
            print("  ✅ technical_indicators table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(technical_indicators)")
            columns = [row[1] for row in cursor.fetchall()]
            expected_columns = [
                'id', 'symbol', 'indicator_name', 'indicator_value', 
                'signal', 'timeframe', 'calculation_timestamp', 
                'metadata', 'created_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                print(f"  ⚠️  Missing columns: {missing_columns}")
            else:
                print("  ✅ Table schema is correct")
        else:
            print("  ❌ technical_indicators table missing")
            print("  💡 Run database migration to create tables")
            
        # Check WAL mode
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        print(f"  📊 Journal mode: {journal_mode}")
        
        conn.close()
        return True, db_path
        
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        return False, db_path

def check_port_availability():
    """Check if port 5003 is available"""
    print("\n🔍 Checking Port Availability...")
    
    try:
        # Try to connect to port 5003
        response = requests.get("http://localhost:5003/health", timeout=2)
        print(f"  ⚠️  Port 5003 already in use (status: {response.status_code})")
        print("  💡 Stop existing service or use different port")
        return False
    except requests.exceptions.ConnectionError:
        print("  ✅ Port 5003 is available")
        return True
    except Exception as e:
        print(f"  ❓ Port check inconclusive: {e}")
        return True

def check_coordination_service():
    """Check if coordination service is running"""
    print("\n🔍 Checking Coordination Service...")
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code == 200:
            print("  ✅ Coordination service is running")
            return True
        else:
            print(f"  ⚠️  Coordination service responding with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ❌ Coordination service not running")
        print("  💡 Start coordination service first:")
        print("     python coordination_service.py")
        return False
    except Exception as e:
        print(f"  ❌ Error connecting to coordination service: {e}")
        return False

def check_file_permissions():
    """Check file and directory permissions"""
    print("\n🔍 Checking File Permissions...")
    
    # Check if logs directory exists and is writable
    logs_dir = Path('./logs')
    if not logs_dir.exists():
        try:
            logs_dir.mkdir(exist_ok=True)
            print("  ✅ Created logs directory")
        except Exception as e:
            print(f"  ❌ Cannot create logs directory: {e}")
            return False
    
    if os.access(logs_dir, os.W_OK):
        print("  ✅ Logs directory is writable")
    else:
        print("  ❌ Logs directory is not writable")
        return False
    
    # Check current directory permissions
    if os.access('.', os.W_OK):
        print("  ✅ Current directory is writable")
    else:
        print("  ❌ Current directory is not writable")
        return False
    
    return True

def test_import_technical_analysis():
    """Try to import the technical analysis service"""
    print("\n🔍 Testing Service Import...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, '.')
        
        # Try to import the service
        from technical_analysis_v105 import TechnicalAnalysisService
        print("  ✅ Service imports successfully")
        
        # Try to create instance (without starting server)
        try:
            service = TechnicalAnalysisService(db_path='./trading_system.db')
            print("  ✅ Service instance created successfully")
            return True
        except Exception as e:
            print(f"  ❌ Service initialization failed: {e}")
            return False
            
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def check_system_resources():
    """Check basic system resources"""
    print("\n🔍 Checking System Resources...")
    
    # Check available disk space
    try:
        disk_usage = os.statvfs('.')
        free_space = disk_usage.f_frsize * disk_usage.f_availf
        free_gb = free_space / (1024**3)
        print(f"  📊 Available disk space: {free_gb:.2f} GB")
        
        if free_gb < 1:
            print("  ⚠️  Low disk space!")
            return False
        else:
            print("  ✅ Sufficient disk space")
            
    except Exception as e:
        print(f"  ❓ Could not check disk space: {e}")
    
    return True

def main():
    """Run all diagnostic checks"""
    print("🚀 Technical Analysis Service Diagnostics")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        check_python_dependencies,
        check_file_permissions,
        check_system_resources,
        check_database_setup,
        check_port_availability,
        check_coordination_service,
        test_import_technical_analysis
    ]
    
    for check in checks:
        try:
            result = check()
            if isinstance(result, tuple):
                result = result[0]  # For database check
            if not result:
                all_checks_passed = False
        except Exception as e:
            print(f"  ❌ Check failed with error: {e}")
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("✅ All diagnostics passed! Service should work.")
        print("\n💡 To start the service:")
        print("   python technical_analysis_v105.py")
    else:
        print("❌ Some issues found. Please fix the problems above.")
        print("\n💡 Common solutions:")
        print("   1. Install missing packages: pip install numpy pandas flask requests yfinance scikit-learn")
        print("   2. Run database migration: python database_migration.py")
        print("   3. Start coordination service: python coordination_service.py")
        print("   4. Check file permissions and available disk space")

if __name__ == "__main__":
    main()

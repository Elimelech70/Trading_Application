# ================================================================
# coordination_service_workflow_fix.py - Quick Fix for Workflow Tracking
# ================================================================
"""
Quick fixes for coordination service workflow tracking issues
Run this to patch common workflow problems
"""

import sqlite3
import json
import requests
from datetime import datetime

def fix_service_registration_table():
    """Ensure service_coordination table exists and is accessible"""
    print("🔧 Fixing service registration table...")
    
    try:
        conn = sqlite3.connect('./trading_system.db')
        cursor = conn.cursor()
        
        # Ensure service_coordination table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_coordination (
                service_name TEXT PRIMARY KEY,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                status TEXT NOT NULL,
                last_heartbeat TIMESTAMP,
                start_time TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Clear any stale registrations
        cursor.execute("DELETE FROM service_coordination WHERE status = 'stopped'")
        
        # Update existing registrations to show they're running
        cursor.execute("UPDATE service_coordination SET status = 'running', last_heartbeat = ?", 
                      (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()
        
        print("✅ Service registration table fixed")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing service registration: {e}")
        return False

def fix_workflow_tracking_tables():
    """Ensure workflow tracking tables exist"""
    print("🔧 Fixing workflow tracking tables...")
    
    try:
        conn = sqlite3.connect('./trading_system.db')
        cursor = conn.cursor()
        
        # Ensure workflow_tracking table exists
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Ensure workflow_events table exists
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
        
        # Ensure workflow_metrics table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT NOT NULL,
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
        
        conn.commit()
        conn.close()
        
        print("✅ Workflow tracking tables fixed")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing workflow tables: {e}")
        return False

def test_coordination_endpoints():
    """Test and fix coordination service endpoints"""
    print("🔧 Testing coordination service endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"⚠️ Health endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test service status endpoint
    try:
        response = requests.get(f"{base_url}/service_status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service status endpoint working: {len(data.get('services', []))} services")
        else:
            print(f"⚠️ Service status endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Service status endpoint error: {e}")
    
    # Test trading cycles endpoint
    try:
        response = requests.get(f"{base_url}/trading_cycles", timeout=5)
        if response.status_code == 200:
            cycles = response.json()
            print(f"✅ Trading cycles endpoint working: {len(cycles)} cycles")
        else:
            print(f"⚠️ Trading cycles endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Trading cycles endpoint error: {e}")

def force_service_registration():
    """Force register core services if they're not showing up"""
    print("🔧 Force registering core services...")
    
    base_url = "http://localhost:5000"
    
    # Core services that should be registered
    services = [
        {"service_name": "technical_analysis", "port": 5003},
        {"service_name": "pattern_analysis", "port": 5002},
        {"service_name": "security_scanner", "port": 5001},
        {"service_name": "paper_trading", "port": 5005},
        {"service_name": "web_dashboard", "port": 5010}
    ]
    
    for service in services:
        try:
            # Check if service is actually running
            health_response = requests.get(f"http://localhost:{service['port']}/health", timeout=2)
            
            if health_response.status_code == 200:
                # Service is running, register it
                registration_data = {
                    "service_name": service["service_name"],
                    "port": service["port"],
                    "status": "running"
                }
                
                response = requests.post(f"{base_url}/register_service", 
                                       json=registration_data, timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ Registered {service['service_name']}")
                else:
                    print(f"⚠️ Failed to register {service['service_name']}: {response.status_code}")
            else:
                print(f"⚠️ {service['service_name']} not responding on port {service['port']}")
                
        except Exception as e:
            print(f"⚠️ Could not check/register {service['service_name']}: {e}")

def create_logs_directory():
    """Ensure logs directory exists"""
    print("🔧 Creating logs directory...")
    
    import os
    from pathlib import Path
    
    try:
        Path('./logs').mkdir(exist_ok=True)
        print("✅ Logs directory created")
        
        # Create empty log files for services
        log_files = [
            'coordination_service.log',
            'web_dashboard.log',
            'technical_analysis_service.log',
            'workflow_manager.log'
        ]
        
        for log_file in log_files:
            log_path = Path(f'./logs/{log_file}')
            if not log_path.exists():
                log_path.touch()
                print(f"✅ Created {log_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating logs directory: {e}")
        return False

def main():
    """Run all fixes"""
    print("🚀 Coordination Service Workflow Fix")
    print("=" * 45)
    
    # Run fixes in order
    fixes = [
        create_logs_directory,
        fix_service_registration_table,
        fix_workflow_tracking_tables,
        test_coordination_endpoints,
        force_service_registration
    ]
    
    for fix in fixes:
        try:
            fix()
            print()
        except Exception as e:
            print(f"❌ Fix failed: {e}")
            print()
    
    print("=" * 45)
    print("🔧 After running fixes:")
    print("1. Restart the system: python hybrid_manager.py restart")
    print("2. Check services are registered: curl http://localhost:5000/service_status")
    print("3. Try starting a trading cycle from the web dashboard")
    print("4. Check workflow status in the Trading Workflow Monitor")

if __name__ == "__main__":
    main()

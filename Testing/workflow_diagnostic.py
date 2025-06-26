#!/usr/bin/env python3
"""
Trading Workflow Monitor Diagnostic Script
Checks database tables and service status for workflow issues
"""

import sqlite3
import json
import requests
from datetime import datetime
from pathlib import Path

def check_database_tables():
    """Check workflow-related database tables"""
    print("🔍 Checking Workflow Database Tables...")
    
    db_paths = ['./trading_system.db', '/workspaces/trading-system/trading_system.db']
    db_path = None
    
    for path in db_paths:
        if Path(path).exists():
            db_path = path
            break
    
    if not db_path:
        print("❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check trading_schedule_config
        print("\n📅 Trading Schedule Config:")
        cursor.execute("SELECT * FROM trading_schedule_config")
        schedule_rows = cursor.fetchall()
        if schedule_rows:
            for row in schedule_rows:
                config_data = json.loads(row[1]) if len(row) > 1 else {}
                print(f"  ✅ Config found: {config_data}")
        else:
            print("  ❌ No schedule configuration found")
        
        # Check trading_cycles
        print("\n🔄 Trading Cycles:")
        cursor.execute("""
            SELECT cycle_id, status, start_time, end_time, securities_scanned, 
                   patterns_found, trades_executed, error_count 
            FROM trading_cycles 
            ORDER BY start_time DESC LIMIT 5
        """)
        cycle_rows = cursor.fetchall()
        if cycle_rows:
            for row in cycle_rows:
                print(f"  📊 Cycle: {row[0]} | Status: {row[1]} | Started: {row[2]}")
                print(f"      Securities: {row[4]} | Patterns: {row[5]} | Trades: {row[6]} | Errors: {row[7]}")
        else:
            print("  ❌ No trading cycles found")
        
        # Check workflow_tracking
        print("\n🏃 Workflow Tracking:")
        cursor.execute("""
            SELECT cycle_id, phase, status, start_time, end_time, 
                   items_processed, items_succeeded, items_failed
            FROM workflow_tracking 
            ORDER BY start_time DESC LIMIT 10
        """)
        tracking_rows = cursor.fetchall()
        if tracking_rows:
            for row in tracking_rows:
                print(f"  🎯 {row[0]} | Phase: {row[1]} | Status: {row[2]}")
                print(f"      Processed: {row[5]} | Success: {row[6]} | Failed: {row[7]}")
        else:
            print("  ❌ No workflow tracking records found")
        
        # Check workflow_events
        print("\n📝 Workflow Events:")
        cursor.execute("""
            SELECT cycle_id, phase, event_type, timestamp
            FROM workflow_events 
            ORDER BY timestamp DESC LIMIT 10
        """)
        event_rows = cursor.fetchall()
        if event_rows:
            for row in event_rows:
                print(f"  📅 {row[0]} | {row[1]} | {row[2]} | {row[3]}")
        else:
            print("  ❌ No workflow events found")
        
        # Check service_coordination
        print("\n🤝 Service Coordination:")
        cursor.execute("SELECT service_name, status, last_heartbeat FROM service_coordination")
        service_rows = cursor.fetchall()
        if service_rows:
            for row in service_rows:
                print(f"  🔧 {row[0]} | Status: {row[1]} | Last seen: {row[2]}")
        else:
            print("  ❌ No registered services found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def check_coordination_service():
    """Check if coordination service is responding"""
    print("\n🔍 Checking Coordination Service...")
    
    try:
        # Health check
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ Coordination service is healthy")
            health_data = response.json()
            print(f"      Version: {health_data.get('version', 'unknown')}")
        else:
            print(f"  ⚠️ Coordination service returned status {response.status_code}")
    except Exception as e:
        print(f"  ❌ Cannot reach coordination service: {e}")
    
    try:
        # Service status
        response = requests.get("http://localhost:5000/service_status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print(f"  📊 Registered services: {len(status_data.get('services', []))}")
        else:
            print(f"  ⚠️ Service status returned {response.status_code}")
    except Exception as e:
        print(f"  ❌ Cannot get service status: {e}")

def check_web_dashboard():
    """Check if web dashboard is responding"""
    print("\n🔍 Checking Web Dashboard...")
    
    try:
        response = requests.get("http://localhost:5010/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ Web dashboard is healthy")
        else:
            print(f"  ⚠️ Web dashboard returned status {response.status_code}")
    except Exception as e:
        print(f"  ❌ Cannot reach web dashboard: {e}")

def test_workflow_endpoints():
    """Test specific workflow endpoints"""
    print("\n🔍 Testing Workflow Endpoints...")
    
    # Test trading cycles endpoint
    try:
        response = requests.get("http://localhost:5000/trading_cycles", timeout=5)
        if response.status_code == 200:
            cycles = response.json()
            print(f"  ✅ Trading cycles endpoint working: {len(cycles)} cycles")
        else:
            print(f"  ❌ Trading cycles endpoint returned {response.status_code}")
    except Exception as e:
        print(f"  ❌ Trading cycles endpoint error: {e}")
    
    # Test schedule config (if it exists)
    try:
        response = requests.get("http://localhost:5010/api/schedule_status", timeout=5)
        if response.status_code == 200:
            schedule = response.json()
            print(f"  ✅ Schedule status endpoint working")
            print(f"      Enabled: {schedule.get('enabled', 'unknown')}")
        else:
            print(f"  ❌ Schedule status endpoint returned {response.status_code}")
    except Exception as e:
        print(f"  ❌ Schedule status endpoint error: {e}")

def check_recent_logs():
    """Check recent log entries"""
    print("\n🔍 Checking Recent Logs...")
    
    log_files = [
        './logs/coordination_service.log',
        './logs/web_dashboard.log',
        './logs/workflow_manager.log'
    ]
    
    for log_file in log_files:
        if Path(log_file).exists():
            print(f"\n📄 Recent entries from {log_file}:")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Get last 5 lines
                    for line in lines[-5:]:
                        print(f"    {line.strip()}")
            except Exception as e:
                print(f"    ❌ Error reading log: {e}")
        else:
            print(f"  ❌ Log file not found: {log_file}")

def main():
    """Run all diagnostics"""
    print("🚀 Trading Workflow Monitor Diagnostics")
    print("=" * 50)
    
    check_database_tables()
    check_coordination_service()
    check_web_dashboard()
    test_workflow_endpoints()
    check_recent_logs()
    
    print("\n" + "=" * 50)
    print("🔧 Common Issues and Solutions:")
    print("1. Schedule not saving → Check web dashboard POST endpoints")
    print("2. Workflow not showing → Check coordination service workflow tracking")
    print("3. Database not updating → Check service database connections")
    print("4. Missing workflow records → Check if workflow_tracking table exists")

if __name__ == "__main__":
    main()

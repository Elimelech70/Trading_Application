#!/usr/bin/env python3
"""
Fix Database Persistence Issues
Forces coordination service to sync in-memory data to database
"""

import sqlite3
import json
import requests
from datetime import datetime

def sync_services_to_database():
    """Sync in-memory service registry to database"""
    print("🔄 Syncing services from memory to database...")
    
    try:
        # Get services from coordination service API
        response = requests.get("http://localhost:5000/service_status", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Could not get service status: {response.status_code}")
            return False
        
        service_data = response.json()
        services = service_data.get('services', [])
        
        print(f"📊 Found {len(services)} services in memory")
        
        if not services:
            print("⚠️ No services found in memory")
            return False
        
        # Connect to database
        conn = sqlite3.connect('./trading_system.db')
        cursor = conn.cursor()
        
        # Clear existing registrations
        cursor.execute("DELETE FROM service_coordination")
        
        # Insert each service
        for service in services:
            cursor.execute('''
                INSERT INTO service_coordination 
                (service_name, host, port, status, last_heartbeat, start_time, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                service.get('service_name', service.get('name', 'unknown')),
                service.get('host', 'localhost'),
                service.get('port', 0),
                service.get('status', 'running'),
                datetime.now().isoformat(),
                service.get('start_time', datetime.now().isoformat()),
                json.dumps(service)
            ))
            
            print(f"  ✅ Synced {service.get('service_name', service.get('name'))}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully synced {len(services)} services to database")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing services: {e}")
        return False

def sync_trading_cycles_to_database():
    """Sync trading cycles from API to database"""
    print("\n🔄 Syncing trading cycles to database...")
    
    try:
        # Get trading cycles from API
        response = requests.get("http://localhost:5000/trading_cycles", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Could not get trading cycles: {response.status_code}")
            return False
        
        cycles = response.json()
        print(f"📊 Found {len(cycles)} cycles in API")
        
        if not cycles:
            print("⚠️ No trading cycles found in API")
            return True  # Not an error, just empty
        
        # Connect to database  
        conn = sqlite3.connect('./trading_system.db')
        cursor = conn.cursor()
        
        # Clear existing cycles (if this is a sync operation)
        # cursor.execute("DELETE FROM trading_cycles")
        
        # Insert or update each cycle
        for cycle in cycles:
            cursor.execute('''
                INSERT OR REPLACE INTO trading_cycles 
                (cycle_id, status, start_time, end_time, securities_scanned, 
                 patterns_found, trades_executed, error_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cycle.get('cycle_id', f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                cycle.get('status', 'unknown'),
                cycle.get('start_time', datetime.now().isoformat()),
                cycle.get('end_time'),
                cycle.get('securities_scanned', 0),
                cycle.get('patterns_found', 0),
                cycle.get('trades_executed', 0),
                cycle.get('error_count', 0),
                cycle.get('created_at', datetime.now().isoformat())
            ))
            
            print(f"  ✅ Synced cycle {cycle.get('cycle_id')}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully synced {len(cycles)} cycles to database")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing cycles: {e}")
        return False

def create_missing_workflow_tables():
    """Ensure all workflow tables exist"""
    print("\n🔧 Creating missing workflow tables...")
    
    try:
        conn = sqlite3.connect('./trading_system.db')
        cursor = conn.cursor()
        
        # Create workflow_tracking if missing
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
        
        # Create workflow_events if missing
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
        
        conn.commit()
        conn.close()
        
        print("✅ Workflow tables verified/created")
        return True
        
    except Exception as e:
        print(f"❌ Error creating workflow tables: {e}")
        return False

def test_database_sync():
    """Test if database sync worked"""
    print("\n🧪 Testing database sync results...")
    
    try:
        conn = sqlite3.connect('./trading_system.db')
        cursor = conn.cursor()
        
        # Check service_coordination
        cursor.execute("SELECT COUNT(*) FROM service_coordination")
        service_count = cursor.fetchone()[0]
        print(f"  📊 Services in database: {service_count}")
        
        # Check trading_cycles
        cursor.execute("SELECT COUNT(*) FROM trading_cycles")
        cycle_count = cursor.fetchone()[0]
        print(f"  📊 Cycles in database: {cycle_count}")
        
        # Show some service details
        if service_count > 0:
            cursor.execute("SELECT service_name, port, status FROM service_coordination LIMIT 5")
            services = cursor.fetchall()
            print("  📋 Sample services:")
            for service in services:
                print(f"    - {service[0]} (port {service[1]}) - {service[2]}")
        
        conn.close()
        
        success = service_count > 0
        if success:
            print("✅ Database sync successful!")
        else:
            print("❌ Database sync failed")
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing sync: {e}")
        return False

def main():
    """Run all database sync fixes"""
    print("🚀 Database Persistence Fix")
    print("=" * 35)
    
    # Step 1: Create missing tables
    create_missing_workflow_tables()
    
    # Step 2: Sync services to database
    sync_services_to_database()
    
    # Step 3: Sync trading cycles to database
    sync_trading_cycles_to_database()
    
    # Step 4: Test results
    test_database_sync()
    
    print("\n" + "=" * 35)
    print("🔧 Next steps:")
    print("1. Run: python workflow_diagnostic.py")
    print("2. Check Trading Workflow Monitor in web dashboard")
    print("3. Try starting a new trading cycle")

if __name__ == "__main__":
    main()

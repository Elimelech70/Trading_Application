#!/usr/bin/env python3
"""
Fix Trading System Issues
Fixes database schema mismatch and service configuration issues
"""
import sqlite3
import subprocess
import time
from pathlib import Path

def fix_database_schema():
    """Fix the service_coordination table schema"""
    print("🔧 Fixing database schema...")
    
    try:
        conn = sqlite3.connect('./trading_system.db')
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(service_coordination)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        if 'service_url' not in columns and 'host' in columns:
            print("Schema is correct (uses 'host' column)")
            
            # Update coordination_service.py to use 'host' instead of 'service_url'
            if Path('coordination_service.py').exists():
                with open('coordination_service.py', 'r') as f:
                    content = f.read()
                
                # Replace service_url with host
                content = content.replace('service_url', 'host')
                
                # Backup and update
                Path('coordination_service.py.backup').write_text(
                    Path('coordination_service.py').read_text()
                )
                
                with open('coordination_service.py', 'w') as f:
                    f.write(content)
                    
                print("✅ Updated coordination_service.py to use 'host' column")
        
        elif 'service_url' not in columns:
            # Add service_url column if neither exists
            print("Adding service_url column...")
            cursor.execute('''
                ALTER TABLE service_coordination 
                ADD COLUMN service_url TEXT
            ''')
            conn.commit()
            print("✅ Added service_url column")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        return False
    
    return True

def add_trading_scheduler_to_hybrid_manager():
    """Add trading scheduler to hybrid manager service list"""
    print("\n🔧 Adding trading scheduler to hybrid manager...")
    
    try:
        with open('hybrid_manager.py', 'r') as f:
            content = f.read()
        
        # Find the services list
        if 'trading_scheduler' not in content:
            # Look for the services array
            services_start = content.find('self.services = [')
            if services_start != -1:
                # Find the end of the array
                services_end = content.find(']', services_start)
                
                # Insert trading scheduler before the last service
                insert_pos = content.rfind('},', services_start, services_end) + 2
                
                new_service = '''
            {"name": "trading_scheduler", "port": 5011, "process": None, "status": "Stopped", "critical": False, "startup_delay": 3},'''
                
                # Insert the new service
                new_content = content[:insert_pos] + new_service + '\n' + content[insert_pos:]
                
                # Backup and update
                Path('hybrid_manager.py.backup').write_text(content)
                
                with open('hybrid_manager.py', 'w') as f:
                    f.write(new_content)
                    
                print("✅ Added trading scheduler to service list")
                return True
            else:
                print("❌ Could not find services array in hybrid_manager.py")
                return False
        else:
            print("✅ Trading scheduler already in hybrid manager")
            return True
            
    except Exception as e:
        print(f"❌ Failed to update hybrid manager: {e}")
        return False

def check_scanner_endpoints():
    """Check security scanner endpoints"""
    print("\n🔍 Checking security scanner endpoints...")
    
    try:
        # Look for the scan endpoint in security_scanner.py
        if Path('security_scanner.py').exists():
            with open('security_scanner.py', 'r') as f:
                content = f.read()
            
            # Look for scan endpoints
            if '/scan' in content:
                print("Found scan endpoints in security_scanner.py:")
                
                # Extract route definitions
                import re
                routes = re.findall(r'@.*\.route\([\'"]([^\'"]+)[\'"].*methods=\[([^\]]+)\]', content)
                for route, methods in routes:
                    if 'scan' in route:
                        print(f"  - {route} [{methods}]")
                        
            # Common endpoint names
            if '/scan_securities' not in content:
                print("⚠️  /scan_securities endpoint not found")
                print("  The endpoint might be named differently (e.g., /scan, /start_scan)")
                
    except Exception as e:
        print(f"❌ Error checking scanner: {e}")

def restart_services():
    """Restart affected services"""
    print("\n🔄 Restarting services...")
    
    try:
        # Stop all services
        print("Stopping all services...")
        subprocess.run(['python', 'hybrid_manager.py', 'stop'], capture_output=True)
        time.sleep(2)
        
        # Start all services
        print("Starting all services...")
        result = subprocess.run(['python', 'hybrid_manager.py', 'start'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Services restarted successfully")
            return True
        else:
            print(f"⚠️  Service restart had issues: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to restart services: {e}")
        return False

def main():
    print("🚀 Trading System Issue Fixer")
    print("="*50)
    
    # Fix database schema
    if not fix_database_schema():
        print("\n⚠️  Database fix failed, but continuing...")
    
    # Add trading scheduler
    if not add_trading_scheduler_to_hybrid_manager():
        print("\n⚠️  Could not add trading scheduler, but continuing...")
    
    # Check scanner endpoints
    check_scanner_endpoints()
    
    # Ask before restarting
    print("\n" + "="*50)
    response = input("\nRestart all services now? (y/n): ")
    
    if response.lower() == 'y':
        restart_services()
        
        print("\n✅ Fixes applied!")
        print("\nNext steps:")
        print("1. Check dashboard: http://127.0.0.1:5010")
        print("2. If trading cycle still fails, check logs/security_scanner.log")
        print("3. The scanner endpoint might be /scan instead of /scan_securities")
    else:
        print("\nFixes applied. Restart services manually:")
        print("  python hybrid_manager.py restart")

if __name__ == "__main__":
    main()

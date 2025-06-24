#!/usr/bin/env python3
"""
TRADING SYSTEM PHASE 1
Service: fix_coordination_service.py
Version: 1.0.0
Last Updated: 2025-06-22

PURPOSE:
Script to properly stop old coordination service and start the fixed version
"""

import os
import sys
import time
import subprocess
import psutil
from pathlib import Path

def kill_coordination_service():
    """Kill all running instances of coordination service"""
    print("🛑 Stopping all coordination service instances...")
    
    killed_count = 0
    
    # Method 1: Using psutil to find and kill processes
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('coordination_service' in str(arg) for arg in cmdline):
                    print(f"  Found process: PID {proc.info['pid']}")
                    proc.terminate()
                    killed_count += 1
                    time.sleep(0.5)
                    if proc.is_running():
                        proc.kill()  # Force kill if still running
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        print("  psutil not available, trying alternative method...")
    
    # Method 2: Using pkill command
    try:
        subprocess.run(['pkill', '-f', 'coordination_service'], capture_output=True)
        print("  Executed pkill command")
    except:
        pass
    
    # Method 3: Find processes on port 5000
    try:
        result = subprocess.run(['lsof', '-ti:5000'], capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        subprocess.run(['kill', '-9', pid], capture_output=True)
                        print(f"  Killed process on port 5000: PID {pid}")
                        killed_count += 1
                    except:
                        pass
    except:
        pass
    
    if killed_count > 0:
        print(f"✅ Stopped {killed_count} coordination service instance(s)")
    else:
        print("ℹ️  No running coordination service instances found")
    
    # Wait for port to be released
    time.sleep(2)
    
def check_port_availability(port=5000):
    """Check if port is available"""
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result == 0:
        print(f"❌ Port {port} is still in use")
        return False
    else:
        print(f"✅ Port {port} is available")
        return True

def backup_old_service():
    """Backup old coordination service"""
    old_file = Path('coordination_service.py')
    if old_file.exists():
        backup_name = f'coordination_service_backup_{time.strftime("%Y%m%d_%H%M%S")}.py'
        old_file.rename(backup_name)
        print(f"📦 Backed up old service to: {backup_name}")

def apply_fixed_version():
    """Copy the fixed version to coordination_service.py"""
    fixed_file = Path('coordination_service_v105.py')
    target_file = Path('coordination_service.py')
    
    if not fixed_file.exists():
        print("❌ Fixed version (coordination_service_v105.py) not found!")
        print("   Please ensure you've created the fixed version first.")
        return False
    
    # Copy the fixed version
    target_file.write_text(fixed_file.read_text())
    print("✅ Applied fixed version of coordination service")
    return True

def verify_fix():
    """Verify the fix is applied by checking the file content"""
    service_file = Path('coordination_service.py')
    
    if not service_file.exists():
        print("❌ coordination_service.py not found!")
        return False
    
    content = service_file.read_text()
    
    # Check for the old problematic code
    if 'service_url, service_port' in content:
        print("❌ Old version still in place - fix not applied!")
        return False
    
    # Check for the fixed code
    if 'host, port, status' in content:
        print("✅ Fixed version verified - correct schema references found")
        return True
    
    print("⚠️  Cannot verify fix - please check manually")
    return False

def start_fixed_service():
    """Start the fixed coordination service"""
    print("\n🚀 Starting fixed coordination service...")
    
    # Start in background using subprocess
    try:
        process = subprocess.Popen(
            [sys.executable, 'coordination_service.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment to see if it starts successfully
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Coordination service started successfully")
            print(f"   Process PID: {process.pid}")
            
            # Check if it's responding
            time.sleep(2)
            try:
                import requests
                response = requests.get('http://localhost:5000/health', timeout=5)
                if response.status_code == 200:
                    print("✅ Service is responding to health checks")
                else:
                    print("⚠️  Service started but not responding properly")
            except:
                print("⚠️  Cannot verify service health - check logs")
                
            return True
        else:
            print("❌ Service failed to start")
            stdout, stderr = process.communicate()
            if stderr:
                print(f"   Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start service: {e}")
        return False

def check_logs():
    """Display recent log entries"""
    log_file = Path('/content/logs/coordination_service.log')
    
    if log_file.exists():
        print("\n📋 Recent log entries:")
        try:
            # Get last 10 lines of log
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-10:] if len(lines) > 10 else lines
                for line in recent_lines:
                    print(f"   {line.strip()}")
        except:
            print("   Could not read log file")
    else:
        print("\n📋 No log file found yet")

def main():
    """Main execution flow"""
    print("=" * 60)
    print("COORDINATION SERVICE FIX SCRIPT")
    print("=" * 60)
    
    # Step 1: Kill existing services
    kill_coordination_service()
    
    # Step 2: Check port availability
    if not check_port_availability():
        print("\n⚠️  Port 5000 is still in use. Waiting 5 seconds...")
        time.sleep(5)
        kill_coordination_service()  # Try again
        
    # Step 3: Backup old service
    backup_old_service()
    
    # Step 4: Apply fixed version
    if not apply_fixed_version():
        print("\n❌ Failed to apply fix. Exiting.")
        sys.exit(1)
    
    # Step 5: Verify fix
    if not verify_fix():
        print("\n⚠️  Warning: Could not verify fix was applied correctly")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Step 6: Start fixed service
    if start_fixed_service():
        print("\n✅ SUCCESS: Fixed coordination service is running!")
        
        # Step 7: Check logs
        check_logs()
        
        print("\n📌 Next steps:")
        print("   1. Monitor logs: tail -f /content/logs/coordination_service.log")
        print("   2. Check health: curl http://localhost:5000/health")
        print("   3. Verify services: curl http://localhost:5000/services")
    else:
        print("\n❌ FAILED: Could not start fixed service")
        print("   Check the logs for more information")
        check_logs()

if __name__ == "__main__":
    # Install psutil if not available
    try:
        import psutil
    except ImportError:
        print("Installing psutil for better process management...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'psutil', '-q'], capture_output=True)
        
    main()
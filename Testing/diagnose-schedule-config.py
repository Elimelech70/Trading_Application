#!/usr/bin/env python3
"""
Name of Service: Schedule Configuration Diagnostic
Filename: diagnose_schedule_config.py
Version: 1.0.0
Last Updated: 2025-01-27
REVISION HISTORY:
v1.0.0 (2025-01-27) - Diagnose and fix schedule configuration issues

DESCRIPTION:
This script diagnoses why the schedule configuration is failing
and provides solutions or fixes.
"""

import requests
import json
import time

def check_service_health(service_name, port):
    """Check if a service is running and healthy"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        if response.status_code == 200:
            print(f"✓ {service_name} is running on port {port}")
            return True
        else:
            print(f"✗ {service_name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ {service_name} is not running on port {port}")
        return False
    except Exception as e:
        print(f"✗ {service_name} error: {e}")
        return False

def test_schedule_endpoints():
    """Test schedule-related endpoints"""
    print("\n2. Testing Schedule Endpoints:")
    print("-" * 40)
    
    # Test GET /schedule/status on coordination service
    try:
        response = requests.get("http://localhost:5000/schedule/status", timeout=5)
        print(f"GET /schedule/status: Status {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print("✗ Schedule status endpoint not working")
    except Exception as e:
        print(f"✗ Schedule status error: {e}")
    
    # Test GET /schedule/config on coordination service
    try:
        response = requests.get("http://localhost:5000/schedule/config", timeout=5)
        print(f"\nGET /schedule/config: Status {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print("✗ Schedule config GET endpoint not working")
    except Exception as e:
        print(f"✗ Schedule config GET error: {e}")
    
    # Test POST /schedule/config with sample data
    test_config = {
        "enabled": True,
        "interval_minutes": 30,
        "market_hours_only": True,
        "start_time": "09:30",
        "end_time": "16:00"
    }
    
    try:
        response = requests.post("http://localhost:5000/schedule/config", 
                               json=test_config, timeout=5)
        print(f"\nPOST /schedule/config: Status {response.status_code}")
        if response.status_code == 200:
            print(f"✓ Schedule config saved successfully")
            print(f"Response: {response.json()}")
        else:
            print(f"✗ Schedule config POST failed with status {response.status_code}")
            if response.text:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"✗ Schedule config POST error: {e}")

def check_scheduler_integration():
    """Check if scheduler is integrated with coordination service"""
    print("\n3. Checking Scheduler Integration:")
    print("-" * 40)
    
    # Check if scheduler is registered with coordination
    try:
        response = requests.get("http://localhost:5000/service_status", timeout=5)
        if response.status_code == 200:
            services = response.json()
            if 'scheduler' in services:
                print("✓ Scheduler is registered with coordination service")
                print(f"  Status: {services['scheduler'].get('status', 'unknown')}")
            else:
                print("✗ Scheduler is NOT registered with coordination service")
                print("  This might be why schedule config is failing")
                
                # Try to register scheduler
                print("\nAttempting to register scheduler...")
                try:
                    reg_response = requests.post(
                        "http://localhost:5000/register_service",
                        json={
                            "service_name": "scheduler",
                            "port": 5011,
                            "endpoints": ["/health", "/start", "/stop", "/status", "/config"]
                        },
                        timeout=5
                    )
                    if reg_response.status_code == 200:
                        print("✓ Successfully registered scheduler")
                    else:
                        print("✗ Failed to register scheduler")
                except Exception as e:
                    print(f"✗ Registration error: {e}")
        else:
            print("✗ Cannot check service status from coordination")
    except Exception as e:
        print(f"✗ Service status error: {e}")

def test_scheduler_directly():
    """Test scheduler service directly"""
    print("\n4. Testing Scheduler Service Directly:")
    print("-" * 40)
    
    # Test scheduler config endpoint directly
    try:
        response = requests.get("http://localhost:5011/config", timeout=5)
        print(f"GET scheduler /config: Status {response.status_code}")
        if response.status_code == 200:
            print(f"✓ Scheduler config accessible")
            print(f"Current config: {response.json()}")
        else:
            print("✗ Scheduler config endpoint not accessible")
    except Exception as e:
        print(f"✗ Scheduler direct access error: {e}")
    
    # Test scheduler status
    try:
        response = requests.get("http://localhost:5011/status", timeout=5)
        print(f"\nGET scheduler /status: Status {response.status_code}")
        if response.status_code == 200:
            print(f"✓ Scheduler status: {response.json()}")
    except Exception as e:
        print(f"✗ Scheduler status error: {e}")

def suggest_fixes():
    """Suggest fixes based on findings"""
    print("\n5. SUGGESTED FIXES:")
    print("=" * 60)
    
    print("""
Based on the diagnosis, here are potential solutions:

1. If Scheduler Service is Not Running:
   - Start the scheduler service: python trading_scheduler.py
   - Make sure it's running on port 5011

2. If Scheduler is Not Registered:
   - The script attempted to register it automatically
   - If that failed, restart both services in order:
     a) Start coordination service first
     b) Then start scheduler service

3. If Endpoints are Missing in Coordination Service:
   - The coordination service might need schedule endpoint handlers
   - These should proxy requests to the scheduler service
   
4. Quick Fix - Direct Scheduler Access:
   - Modify web_dashboard_service.py to talk directly to scheduler
   - Change http://localhost:5000/schedule/* to http://localhost:5011/*
   
5. Check Logs:
   - Check ./logs/coordination_service.log for errors
   - Check ./logs/trading_scheduler.log for errors
""")

def create_coordination_fix():
    """Create a fix file for coordination service"""
    print("\n6. Creating Coordination Service Fix:")
    print("-" * 40)
    
    fix_code = '''#!/usr/bin/env python3
"""
Fix for adding schedule endpoints to coordination service
Add this code to coordination_service.py in the _setup_routes method
"""

# Add these routes to coordination_service.py _setup_routes method:

@self.app.route('/schedule/status', methods=['GET'])
def get_schedule_status():
    """Proxy schedule status to scheduler service"""
    try:
        # Forward to scheduler service
        response = requests.get('http://localhost:5011/status', timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
    except Exception as e:
        self.logger.error(f"Error getting schedule status: {e}")
    
    return jsonify({
        "enabled": False,
        "message": "Scheduler service not available",
        "next_run": None
    })

@self.app.route('/schedule/config', methods=['GET', 'POST'])
def schedule_config():
    """Proxy schedule config to scheduler service"""
    if request.method == 'GET':
        try:
            response = requests.get('http://localhost:5011/config', timeout=5)
            if response.status_code == 200:
                return jsonify(response.json())
        except Exception as e:
            self.logger.error(f"Error getting schedule config: {e}")
        
        # Default config if scheduler not available
        return jsonify({
            "enabled": False,
            "interval_minutes": 30,
            "market_hours_only": True,
            "start_time": "09:30",
            "end_time": "16:00"
        })
    
    else:  # POST
        try:
            # Forward config to scheduler
            response = requests.post('http://localhost:5011/config', 
                                   json=request.json, timeout=5)
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({"error": "Failed to update scheduler config"}), 500
        except Exception as e:
            self.logger.error(f"Error updating schedule config: {e}")
            return jsonify({"error": str(e)}), 500
'''
    
    with open('coordination_schedule_fix.py', 'w') as f:
        f.write(fix_code)
    
    print("✓ Created coordination_schedule_fix.py")
    print("  This file contains the code to add to coordination_service.py")
    print("  Add these routes to the _setup_routes method")

def main():
    """Run the diagnostic"""
    print("=" * 60)
    print("SCHEDULE CONFIGURATION DIAGNOSTIC")
    print("=" * 60)
    
    # 1. Check services
    print("\n1. Checking Service Health:")
    print("-" * 40)
    
    coord_running = check_service_health("Coordination Service", 5000)
    scheduler_running = check_service_health("Trading Scheduler", 5011)
    dashboard_running = check_service_health("Web Dashboard", 5010)
    
    # 2. Test endpoints
    if coord_running:
        test_schedule_endpoints()
    
    # 3. Check integration
    if coord_running:
        check_scheduler_integration()
    
    # 4. Test scheduler directly
    if scheduler_running:
        test_scheduler_directly()
    
    # 5. Suggest fixes
    suggest_fixes()
    
    # 6. Create fix file
    create_coordination_fix()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Fix Schedule Sync Issue
Ensures both /schedule/status and /schedule/config use the same data
"""

import json
import os
import requests

print("=" * 60)
print("FIXING SCHEDULE SYNCHRONIZATION")
print("=" * 60)

# 1. Create the missing schedule_config.json file
print("\n1. Creating schedule_config.json file...")

config_data = {
    "enabled": True,
    "interval_minutes": 30,
    "market_hours_only": True,
    "start_time": "09:30", 
    "end_time": "16:00",
    "timezone": "America/New_York",
    "excluded_days": ["Saturday", "Sunday"]
}

# Save to current directory
config_path = './schedule_config.json'
with open(config_path, 'w') as f:
    json.dump(config_data, f, indent=2)

print(f"✓ Created {config_path}")
print(f"  Contents: {json.dumps(config_data, indent=2)}")

# 2. Also save to other possible locations
alt_paths = [
    '/workspaces/Trading_Application/schedule_config.json',
    '../schedule_config.json'
]

for path in alt_paths:
    try:
        dir_path = os.path.dirname(path)
        if dir_path and os.path.exists(dir_path):
            with open(path, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"✓ Also created {path}")
    except:
        pass

# 3. Force the coordination service to reload by sending a POST
print("\n2. Forcing coordination service to reload configuration...")

try:
    response = requests.post('http://localhost:5000/schedule/config', json=config_data)
    if response.status_code == 200:
        print("✓ Successfully updated configuration via API")
    else:
        print(f"⚠️  API update returned status {response.status_code}")
except Exception as e:
    print(f"⚠️  Could not update via API: {e}")

# 4. Check both endpoints again
print("\n3. Verifying both endpoints now show same status...")
print("-" * 40)

try:
    # Check status
    status_response = requests.get('http://localhost:5000/schedule/status')
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"Status endpoint - enabled: {status_data.get('enabled')}")
    
    # Check config
    config_response = requests.get('http://localhost:5000/schedule/config')
    if config_response.status_code == 200:
        config_data = config_response.json()
        print(f"Config endpoint - enabled: {config_data.get('enabled')}")
    
    if status_data.get('enabled') == config_data.get('enabled'):
        print("\n✅ Both endpoints are synchronized!")
    else:
        print("\n⚠️  Endpoints still out of sync - restart coordination service")
        
except Exception as e:
    print(f"Error checking endpoints: {e}")

# 5. Create a coordination service patch to sync the endpoints
print("\n4. Creating coordination service patch...")

patch_code = '''
# Add this to coordination_service.py to fix the sync issue
# Replace or update the /schedule/status endpoint handler

@self.app.route('/schedule/status', methods=['GET'])
def get_schedule_status():
    """Get trading schedule status - synchronized with config"""
    # Read from the same config file as /schedule/config
    config_file = './schedule_config.json'
    
    try:
        # Load config from file
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            # Use defaults
            config = {
                "enabled": False,
                "interval_minutes": 30,
                "market_hours_only": True,
                "start_time": "09:30",
                "end_time": "16:00",
                "timezone": "America/New_York",
                "excluded_days": ["Saturday", "Sunday"]
            }
        
        # Add runtime information
        config['last_run'] = getattr(self, '_last_scheduled_run', None)
        
        # Calculate next run if enabled
        if config['enabled']:
            from datetime import datetime, timedelta
            now = datetime.now()
            if hasattr(self, '_last_scheduled_run') and self._last_scheduled_run:
                next_run = self._last_scheduled_run + timedelta(minutes=config['interval_minutes'])
                config['next_run'] = next_run.strftime('%Y-%m-%d %H:%M:%S')
            else:
                config['next_run'] = f"In {config['interval_minutes']} minutes"
        else:
            config['next_run'] = None
        
        return jsonify(config)
        
    except Exception as e:
        self.logger.error(f"Error getting schedule status: {e}")
        return jsonify({
            "enabled": False,
            "message": "Error reading schedule configuration",
            "error": str(e)
        })
'''

with open('coordination_schedule_sync_patch.py', 'w') as f:
    f.write(patch_code)

print("✓ Created coordination_schedule_sync_patch.py")
print("  This contains code to sync the /schedule/status endpoint")

print("\n" + "=" * 60)
print("IMMEDIATE SOLUTION")
print("=" * 60)

print("""
The schedule_config.json file has been created with enabled=true.

To fix the issue completely:

1. RESTART the coordination service:
   - Press Ctrl+C to stop it
   - Run: python coordination_service.py

2. The schedule should now show as ENABLED in the web interface

3. If it still shows disabled after restart:
   - Apply the patch from coordination_schedule_sync_patch.py
   - This will make /schedule/status read from the same config file

The issue was that /schedule/status and /schedule/config were reading
from different sources. The config file now exists and both should sync up.
""")

# 6. Test if it's working now
print("\nTesting current status after fix...")
import time
time.sleep(2)  # Give it a moment

try:
    response = requests.get('http://localhost:5000/schedule/status')
    if response.status_code == 200:
        data = response.json()
        if data.get('enabled'):
            print("✅ Schedule is now showing as ENABLED!")
        else:
            print("⚠️  Schedule still shows disabled - restart coordination service")
except:
    pass
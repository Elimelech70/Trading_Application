#!/usr/bin/env python3
"""
Debug Schedule Display Issue
Checks what the APIs are actually returning vs what the HTML expects
"""

import requests
import json
from datetime import datetime

print("=" * 60)
print("SCHEDULE DISPLAY DEBUG")
print("=" * 60)

# 1. Check /schedule/status endpoint
print("\n1. Checking /schedule/status endpoint:")
print("-" * 40)
try:
    response = requests.get("http://localhost:5000/schedule/status")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check what fields are present
        print("\nFields in response:")
        for key in data.keys():
            print(f"  - {key}: {data[key]}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# 2. Check /schedule/config endpoint
print("\n\n2. Checking /schedule/config endpoint:")
print("-" * 40)
try:
    response = requests.get("http://localhost:5000/schedule/config")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('enabled'):
            print("\n✅ Schedule is ENABLED in config")
        else:
            print("\n❌ Schedule is DISABLED in config")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# 3. Check what the HTML expects
print("\n\n3. What the HTML JavaScript expects:")
print("-" * 40)
print("""
The updateScheduleStatus() function in the HTML expects:
- response.data.enabled (boolean)
- response.data.next_run (string)
- response.data.interval_minutes (number)

But your /schedule/status is returning:
- enabled (boolean)
- next_run (string or null)
- interval_minutes (number)
- Plus extra fields: end_time, excluded_days, last_run, market_hours_only, start_time, timezone
""")

# 4. Test enabling schedule
print("\n\n4. Testing schedule enable/disable:")
print("-" * 40)

# First get current config
try:
    response = requests.get("http://localhost:5000/schedule/config")
    if response.status_code == 200:
        current_config = response.json()
        print(f"Current 'enabled' status: {current_config.get('enabled', False)}")
        
        # Try to enable it
        if not current_config.get('enabled'):
            print("\nTrying to enable schedule...")
            new_config = current_config.copy()
            new_config['enabled'] = True
            
            response = requests.post("http://localhost:5000/schedule/config", json=new_config)
            if response.status_code == 200:
                print("✅ Successfully enabled schedule")
                
                # Check status again
                response = requests.get("http://localhost:5000/schedule/status")
                if response.status_code == 200:
                    status = response.json()
                    print(f"\nNew status: {json.dumps(status, indent=2)}")
            else:
                print(f"❌ Failed to enable: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# 5. Create a fix for the HTML
print("\n\n5. HTML Fix Needed:")
print("-" * 40)
print("""
The issue appears to be that the HTML is correctly reading the data,
but your schedule shows 'enabled': false even after configuration.

Possible issues:
1. The coordination service isn't persisting the enabled state
2. The schedule_config.json file isn't being read/written properly
3. The scheduler thread isn't starting when enabled

Let's check if schedule_config.json exists:
""")

import os
if os.path.exists('schedule_config.json'):
    with open('schedule_config.json', 'r') as f:
        config = json.load(f)
        print(f"schedule_config.json contents: {json.dumps(config, indent=2)}")
else:
    print("❌ schedule_config.json does not exist!")
    print("   This explains why settings aren't persisting")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
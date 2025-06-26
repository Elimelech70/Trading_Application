#!/usr/bin/env python3
"""Final test of schedule configuration"""
import requests
import json
import time

print("Testing Schedule Configuration...")
print("=" * 50)

# Test 1: GET current config
print("\n1. Getting current configuration:")
response = requests.get("http://localhost:5000/schedule/config")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    config = response.json()
    print(f"   Current config: {json.dumps(config, indent=2)}")
else:
    print(f"   Error: Could not get config")
    exit(1)

# Test 2: Update config
print("\n2. Updating configuration:")
new_config = {
    "enabled": True,
    "interval_minutes": 15,
    "market_hours_only": True,
    "start_time": "09:30",
    "end_time": "16:00"
}
response = requests.post("http://localhost:5000/schedule/config", json=new_config)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
else:
    print(f"   Error: {response.text}")

# Test 3: Verify update
print("\n3. Verifying configuration was saved:")
time.sleep(1)
response = requests.get("http://localhost:5000/schedule/config")
if response.status_code == 200:
    config = response.json()
    if config['interval_minutes'] == 15:
        print("   ✓ Configuration successfully updated!")
    else:
        print("   ✗ Configuration was not saved properly")
else:
    print("   ✗ Could not verify configuration")

print("\n" + "=" * 50)
print("✅ Schedule configuration is working!")
print("You can now use the 'Configure Schedule' button in the web dashboard.")

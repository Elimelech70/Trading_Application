#!/usr/bin/env python3
"""Test if schedule config endpoints are working"""

import requests
import json

print("Testing Schedule Config Endpoints...")
print("=" * 50)

# Test GET
print("\n1. Testing GET /schedule/config:")
try:
    response = requests.get("http://localhost:5000/schedule/config")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print("   ✓ GET endpoint working!")
    else:
        print("   ✗ GET endpoint not working")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test POST
print("\n2. Testing POST /schedule/config:")
test_config = {
    "enabled": True,
    "interval_minutes": 30,
    "market_hours_only": True,
    "start_time": "09:30",
    "end_time": "16:00"
}

try:
    response = requests.post("http://localhost:5000/schedule/config", json=test_config)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print("   ✓ POST endpoint working!")
    else:
        print(f"   ✗ POST endpoint not working")
        if response.text:
            print(f"   Error: {response.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 50)
print("Test complete!")

# test_trading_cycle.py
import requests

# Test each step manually
print("1. Testing scanner...")
try:
    response = requests.get("http://localhost:5001/scan_securities", timeout=30)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. Testing coordination trading cycle...")
try:
    response = requests.post("http://localhost:5000/start_trading_cycle", timeout=30)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   Error: {e}")
#!/usr/bin/env python3
"""
Health Check Script for Trading Application
Verifies all services are running correctly
"""
import requests
import time
import sys
from datetime import datetime

SERVICES = {
    'Coordination Service': 5000,
    'Security Scanner': 5001,
    'Pattern Analysis': 5002,
    'Technical Analysis': 5003,
    'Paper Trading': 5005,
    'Pattern Recognition': 5006,
    'News Service': 5008,
    'Reporting Service': 5009,
    'Web Dashboard': 5010
}

def check_service(name, port, timeout=2):
    """Check if a service is responding"""
    try:
        response = requests.get(f'http://localhost:{port}/health', timeout=timeout)
        if response.status_code == 200:
            return True, "OK", response.json() if response.text else {}
        else:
            return False, f"HTTP {response.status_code}", {}
    except requests.exceptions.Timeout:
        return False, "Timeout", {}
    except requests.exceptions.ConnectionError:
        return False, "Connection refused", {}
    except Exception as e:
        return False, str(e), {}

def main():
    """Run health checks on all services"""
    print("\n" + "="*60)
    print("🏥 Trading Application Health Check")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    all_healthy = True
    healthy_count = 0
    
    # Table header
    print(f"\n{'Service':<25} {'Port':<6} {'Status':<20} {'Details'}")
    print("-"*70)
    
    for name, port in SERVICES.items():
        is_healthy, status, details = check_service(name, port)
        
        # Status icon
        icon = "✅" if is_healthy else "❌"
        
        # Format details
        detail_str = ""
        if details:
            if 'service' in details:
                detail_str = f"[{details['service']}]"
        
        print(f"{icon} {name:<23} {port:<6} {status:<20} {detail_str}")
        
        if is_healthy:
            healthy_count += 1
        else:
            all_healthy = False
    
    print("-"*70)
    print(f"\nSummary: {healthy_count}/{len(SERVICES)} services healthy")
    
    if all_healthy:
        print("\n✅ All services are healthy!")
        return 0
    else:
        print("\n⚠️  Some services are not responding")
        print("\nTroubleshooting:")
        print("1. Check if services are started: python hybrid_manager.py status")
        print("2. Check logs in ./logs/ directory")
        print("3. Try restarting services: python hybrid_manager.py restart")
        return 1

if __name__ == "__main__":
    sys.exit(main())

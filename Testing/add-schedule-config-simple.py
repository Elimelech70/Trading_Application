#!/usr/bin/env python3
"""
Name of Service: Add Schedule Config Endpoints
Filename: add_schedule_config_endpoints.py
Version: 1.0.0
Last Updated: 2025-01-27
REVISION HISTORY:
v1.0.0 (2025-01-27) - Add missing /schedule/config endpoints

DESCRIPTION:
Simple script to add the missing /schedule/config endpoints to coordination service.
This is a minimal fix that works with your existing schedule implementation.
"""

import os
import json

def create_schedule_config_patch():
    """Create a patch file with the missing endpoints"""
    
    patch_code = '''
# Add this code to coordination_service.py in the _setup_routes method
# Place it right after the existing /schedule/status route

        @self.app.route('/schedule/config', methods=['GET', 'POST'])
        def schedule_config():
            """Get or set trading schedule configuration"""
            if request.method == 'GET':
                # Return current schedule configuration
                try:
                    # Get config from scheduler state or file
                    config = {
                        "enabled": self.scheduler_enabled,
                        "interval_minutes": self.schedule_interval,
                        "market_hours_only": getattr(self, 'market_hours_only', True),
                        "start_time": getattr(self, 'market_start', '09:30'),
                        "end_time": getattr(self, 'market_end', '16:00'),
                        "timezone": getattr(self, 'timezone', 'America/New_York'),
                        "excluded_days": getattr(self, 'excluded_days', ['Saturday', 'Sunday'])
                    }
                    return jsonify(config)
                except Exception as e:
                    self.logger.error(f"Error getting schedule config: {e}")
                    return jsonify({
                        "enabled": False,
                        "interval_minutes": 30,
                        "market_hours_only": True,
                        "start_time": "09:30",
                        "end_time": "16:00"
                    })
            
            else:  # POST - Update configuration
                try:
                    config = request.json
                    
                    # Update scheduler configuration
                    self.scheduler_enabled = config.get('enabled', False)
                    self.schedule_interval = config.get('interval_minutes', 30)
                    self.market_hours_only = config.get('market_hours_only', True)
                    self.market_start = config.get('start_time', '09:30')
                    self.market_end = config.get('end_time', '16:00')
                    
                    # Save configuration to file for persistence
                    config_file = './schedule_config.json'
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    # If scheduler is being enabled, start it
                    if self.scheduler_enabled:
                        if hasattr(self, '_start_scheduler'):
                            self._start_scheduler()
                        else:
                            # If no _start_scheduler method, just log
                            self.logger.info("Schedule enabled - scheduler will start on next check")
                    else:
                        # If scheduler is being disabled
                        if hasattr(self, '_stop_scheduler'):
                            self._stop_scheduler()
                        else:
                            self.logger.info("Schedule disabled")
                    
                    self.logger.info(f"Schedule configuration updated: {config}")
                    
                    return jsonify({
                        "status": "success",
                        "message": "Schedule configuration updated",
                        "config": config
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error updating schedule config: {e}")
                    return jsonify({"error": str(e)}), 500

# Also add this initialization code to the __init__ method of CoordinationService:
# (Add after self.logger is initialized)

        # Load schedule configuration
        self._load_schedule_config()

# And add this helper method to the class:

    def _load_schedule_config(self):
        """Load schedule configuration from file"""
        config_file = './schedule_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.scheduler_enabled = config.get('enabled', False)
                    self.schedule_interval = config.get('interval_minutes', 30)
                    self.market_hours_only = config.get('market_hours_only', True)
                    self.market_start = config.get('start_time', '09:30')
                    self.market_end = config.get('end_time', '16:00')
                    self.logger.info(f"Loaded schedule config: {config}")
            except Exception as e:
                self.logger.error(f"Error loading schedule config: {e}")
                self._set_default_schedule_config()
        else:
            self._set_default_schedule_config()
    
    def _set_default_schedule_config(self):
        """Set default schedule configuration"""
        self.scheduler_enabled = False
        self.schedule_interval = 30
        self.market_hours_only = True
        self.market_start = '09:30'
        self.market_end = '16:00'
'''
    
    with open('schedule_config_patch.py', 'w') as f:
        f.write(patch_code)
    
    print("✓ Created schedule_config_patch.py")
    print("\nThis file contains the code to add to coordination_service.py")

def create_manual_instructions():
    """Create manual instructions for applying the fix"""
    
    instructions = """
MANUAL INSTRUCTIONS TO FIX SCHEDULE CONFIGURATION
================================================

Since your coordination service already has some scheduling functionality
(as evidenced by the working /schedule/status endpoint), here are the
manual steps to add the missing /schedule/config endpoints:

1. Open coordination_service.py in your editor

2. Find the /schedule/status route in the _setup_routes method

3. Add the /schedule/config route right after it (see schedule_config_patch.py)

4. In the __init__ method, add:
   - self._load_schedule_config() after logger initialization

5. Add the helper methods at the class level:
   - _load_schedule_config()
   - _set_default_schedule_config()

6. Save the file and restart the coordination service

The patch code handles:
- GET /schedule/config - Returns current configuration
- POST /schedule/config - Updates and saves configuration
- Persistence via schedule_config.json file
- Integration with existing scheduler_enabled flag

After applying these changes:
1. Stop the coordination service (Ctrl+C)
2. Start it again: python coordination_service.py
3. The "Configure Schedule" button should now work!
"""
    
    with open('schedule_fix_instructions.txt', 'w') as f:
        f.write(instructions)
    
    print("\n✓ Created schedule_fix_instructions.txt")
    print("  This file contains step-by-step manual instructions")

def create_test_script():
    """Create a script to test if the fix worked"""
    
    test_code = '''#!/usr/bin/env python3
"""Test if schedule config endpoints are working"""

import requests
import json

print("Testing Schedule Config Endpoints...")
print("=" * 50)

# Test GET
print("\\n1. Testing GET /schedule/config:")
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
print("\\n2. Testing POST /schedule/config:")
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

print("\\n" + "=" * 50)
print("Test complete!")
'''
    
    with open('test_schedule_config.py', 'w') as f:
        f.write(test_code)
    
    os.chmod('test_schedule_config.py', 0o755)
    print("\n✓ Created test_schedule_config.py")
    print("  Run this after applying the fix to verify it works")

def main():
    """Main execution"""
    print("=" * 60)
    print("CREATING SCHEDULE CONFIG FIX")
    print("=" * 60)
    
    print("\nBased on the diagnostic results:")
    print("- /schedule/status endpoint exists and works ✓")
    print("- /schedule/config endpoints are missing ✗")
    print("\nCreating fix files...")
    
    # Create the patch file
    create_schedule_config_patch()
    
    # Create manual instructions
    create_manual_instructions()
    
    # Create test script
    create_test_script()
    
    print("\n" + "=" * 60)
    print("FIX FILES CREATED")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Review schedule_config_patch.py for the code to add")
    print("2. Follow schedule_fix_instructions.txt to apply the fix")
    print("3. Restart the coordination service")
    print("4. Run test_schedule_config.py to verify the fix")
    
    print("\nAlternatively, if you prefer an automated fix:")
    print("- Run: python fix_coordination_schedule_endpoints.py")
    print("  (This will automatically modify your coordination_service.py)")

if __name__ == "__main__":
    main()

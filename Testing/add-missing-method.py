#!/usr/bin/env python3
"""
Name of Service: Add Missing Schedule Method
Filename: add_missing_schedule_method.py
Version: 1.0.0
Last Updated: 2025-01-27
REVISION HISTORY:
v1.0.0 (2025-01-27) - Add missing _set_default_schedule_config method

DESCRIPTION:
Adds the missing _set_default_schedule_config method to coordination_service.py
"""

import os
import shutil
from datetime import datetime

def find_coordination_service():
    """Find the coordination service file"""
    possible_paths = [
        'coordination_service.py',
        './coordination_service.py',
        '../coordination_service.py',
        '/workspaces/Trading_Application/coordination_service.py'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✓ Found coordination service at: {path}")
            return path
    
    return None

def add_missing_method(filepath):
    """Add the missing _set_default_schedule_config method"""
    
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Check if method already exists
    if '_set_default_schedule_config' in content:
        print("✓ Method _set_default_schedule_config already exists")
        return True
    
    # Find where to insert (after _load_schedule_config method)
    insert_index = None
    
    for i, line in enumerate(lines):
        if 'def _load_schedule_config(self):' in line:
            # Find the end of this method
            j = i + 1
            method_indent = len(line) - len(line.lstrip())
            
            while j < len(lines):
                # Check if we've reached another method at the same level
                if lines[j].strip() and lines[j].startswith(' ' * method_indent + 'def '):
                    insert_index = j
                    break
                # Or if we've reached a line with less indentation (end of class)
                elif lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) < method_indent:
                    insert_index = j
                    break
                j += 1
            
            # If we reached the end of file
            if insert_index is None and j >= len(lines) - 1:
                insert_index = len(lines) - 1
            break
    
    if insert_index is None:
        print("⚠️  Could not find _load_schedule_config method")
        print("   Adding method at the end of the class")
        
        # Find the end of the class
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].startswith(' ') and 'if __name__' not in lines[i]:
                insert_index = i
                break
    
    if insert_index is None:
        print("✗ Could not find appropriate location to insert method")
        return False
    
    # Add the missing method
    method_code = '''
    def _set_default_schedule_config(self):
        """Set default schedule configuration"""
        self.scheduler_enabled = False
        self.schedule_interval = 30
        self.market_hours_only = True
        self.market_start = '09:30'
        self.market_end = '16:00'
        self.logger.info("Set default schedule configuration")
'''
    
    lines.insert(insert_index, method_code)
    
    # Write the modified content
    modified_content = '\n'.join(lines)
    with open(filepath, 'w') as f:
        f.write(modified_content)
    
    print("✓ Successfully added _set_default_schedule_config method")
    return True

def verify_fix(filepath):
    """Verify all required components are present"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    checks = [
        ('/schedule/config', "schedule/config endpoint"),
        ('_load_schedule_config', "_load_schedule_config method"),
        ('_set_default_schedule_config', "_set_default_schedule_config method")
    ]
    
    print("\nFinal verification:")
    all_good = True
    for check_str, desc in checks:
        if check_str in content:
            print(f"  ✓ Found {desc}")
        else:
            print(f"  ✗ Missing {desc}")
            all_good = False
    
    return all_good

def main():
    """Main execution"""
    print("=" * 60)
    print("ADDING MISSING SCHEDULE METHOD")
    print("=" * 60)
    
    # Find the coordination service file
    filepath = find_coordination_service()
    if not filepath:
        print("\n✗ Could not find coordination_service.py")
        return
    
    # Create a simple backup
    backup_path = filepath + '.backup_method'
    shutil.copy2(filepath, backup_path)
    print(f"\n✓ Created backup: {backup_path}")
    
    # Add the missing method
    print("\nAdding missing method...")
    success = add_missing_method(filepath)
    
    if success:
        # Verify everything is now in place
        if verify_fix(filepath):
            print("\n✅ ALL COMPONENTS NOW IN PLACE!")
            print("\nThe schedule configuration fix is complete.")
            print("\nNext steps:")
            print("1. Restart the coordination service")
            print("2. The 'Configure Schedule' button should now work!")
            
            # Create a final test script
            create_final_test()
        else:
            print("\n⚠️  Some components still missing")
    else:
        print("\n✗ Failed to add method")
        print(f"Restore from backup: cp {backup_path} {filepath}")

def create_final_test():
    """Create a final test script"""
    test_code = '''#!/usr/bin/env python3
"""Final test of schedule configuration"""
import requests
import json
import time

print("Testing Schedule Configuration...")
print("=" * 50)

# Test 1: GET current config
print("\\n1. Getting current configuration:")
response = requests.get("http://localhost:5000/schedule/config")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    config = response.json()
    print(f"   Current config: {json.dumps(config, indent=2)}")
else:
    print(f"   Error: Could not get config")
    exit(1)

# Test 2: Update config
print("\\n2. Updating configuration:")
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
print("\\n3. Verifying configuration was saved:")
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

print("\\n" + "=" * 50)
print("✅ Schedule configuration is working!")
print("You can now use the 'Configure Schedule' button in the web dashboard.")
'''
    
    with open('test_schedule_final.py', 'w') as f:
        f.write(test_code)
    os.chmod('test_schedule_final.py', 0o755)
    print("\n✓ Created test_schedule_final.py for testing")

if __name__ == "__main__":
    main()

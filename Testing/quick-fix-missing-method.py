#!/usr/bin/env python3
"""
Quick fix to add the missing _set_default_schedule_config method
"""

import os

# The method code to add
METHOD_TO_ADD = '''
    def _set_default_schedule_config(self):
        """Set default schedule configuration"""
        self.scheduler_enabled = False
        self.schedule_interval = 30
        self.market_hours_only = True
        self.market_start = '09:30'
        self.market_end = '16:00'
        if hasattr(self, 'logger'):
            self.logger.info("Set default schedule configuration")
'''

def main():
    # Find coordination_service.py
    filepath = None
    for path in ['coordination_service.py', '../coordination_service.py', '/workspaces/Trading_Application/coordination_service.py']:
        if os.path.exists(path):
            filepath = path
            break
    
    if not filepath:
        print("❌ Cannot find coordination_service.py")
        print("Please run this script from your project directory")
        return
    
    print(f"✓ Found: {filepath}")
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if method already exists
    if '_set_default_schedule_config' in content:
        print("✓ Method _set_default_schedule_config already exists!")
        print("The schedule configuration should be working.")
        return
    
    # Find where to add it (look for _load_schedule_config)
    lines = content.split('\n')
    insert_line = None
    
    # Find _load_schedule_config method
    for i, line in enumerate(lines):
        if 'def _load_schedule_config(self):' in line:
            # Find the end of this method
            j = i + 1
            indent = len(line) - len(line.lstrip())
            while j < len(lines):
                current_line = lines[j]
                if current_line.strip():  # Non-empty line
                    current_indent = len(current_line) - len(current_line.lstrip())
                    if current_indent <= indent and current_line.strip() != '':
                        # Found the end of the method
                        insert_line = j
                        break
                j += 1
            break
    
    if insert_line is None:
        # If we couldn't find _load_schedule_config, add at the end of class
        print("⚠️  Adding method at end of file")
        insert_line = len(lines) - 1
        # Find the last line before if __name__ == '__main__'
        for i in range(len(lines) - 1, -1, -1):
            if 'if __name__' in lines[i]:
                insert_line = i - 1
                break
    
    # Insert the method
    lines.insert(insert_line, METHOD_TO_ADD)
    
    # Save the file
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))
    
    print("✓ Added _set_default_schedule_config method")
    
    # Verify
    with open(filepath, 'r') as f:
        new_content = f.read()
    
    if '_set_default_schedule_config' in new_content:
        print("✅ SUCCESS! Method added successfully")
        print("\nNext steps:")
        print("1. Restart coordination service:")
        print("   - Press Ctrl+C to stop it")
        print("   - Run: python coordination_service.py")
        print("2. The schedule configuration should now work!")
    else:
        print("❌ Failed to add method")

if __name__ == "__main__":
    main()

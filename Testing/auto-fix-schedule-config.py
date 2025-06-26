#!/usr/bin/env python3
"""
Name of Service: Auto Fix Schedule Config
Filename: auto_fix_schedule_config.py
Version: 1.0.0
Last Updated: 2025-01-27
REVISION HISTORY:
v1.0.0 (2025-01-27) - Automatically add schedule/config endpoints

DESCRIPTION:
This script automatically adds the missing /schedule/config endpoints
to your coordination_service.py file.
"""

import os
import re
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
    
    # If not found, ask user
    print("Could not find coordination_service.py automatically.")
    user_path = input("Please enter the path to coordination_service.py: ").strip()
    if os.path.exists(user_path):
        return user_path
    
    return None

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_dir = os.path.dirname(filepath) or '.'
    backup_name = f"coordination_service_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    backup_path = os.path.join(backup_dir, backup_name)
    shutil.copy2(filepath, backup_path)
    print(f"✓ Created backup: {backup_path}")
    return backup_path

def add_schedule_config_endpoint(filepath):
    """Add the schedule/config endpoint to the coordination service"""
    
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Find where to insert the route (after /schedule/status)
    insert_index = None
    indent_level = None
    
    for i, line in enumerate(lines):
        if '/schedule/status' in line and '@self.app.route' in line:
            # Find the end of this route definition
            j = i
            while j < len(lines) - 1:
                j += 1
                # Look for the next route or method definition
                if lines[j].strip() and (
                    '@self.app.route' in lines[j] or 
                    (lines[j].strip().startswith('def ') and not lines[j].strip().startswith('def get_schedule_status'))
                ):
                    insert_index = j
                    # Get indentation from the @self.app.route line
                    indent_level = len(lines[i]) - len(lines[i].lstrip())
                    break
            break
    
    if insert_index is None:
        print("⚠️  Could not find /schedule/status endpoint")
        print("   Adding schedule/config at the end of _setup_routes method")
        
        # Find _setup_routes method
        for i, line in enumerate(lines):
            if 'def _setup_routes(self):' in line:
                # Find the end of this method
                j = i + 1
                method_indent = len(lines[j]) - len(lines[j].lstrip()) if j < len(lines) and lines[j].strip() else 8
                
                while j < len(lines) - 1:
                    j += 1
                    if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= len(line) - len(line.lstrip()):
                        # Found the end of the method
                        insert_index = j - 1
                        indent_level = method_indent
                        break
                break
    
    if insert_index is None or indent_level is None:
        print("✗ Could not find appropriate location to insert route")
        return False
    
    # Create the schedule/config route code
    indent = ' ' * indent_level
    route_code = f'''
{indent}@self.app.route('/schedule/config', methods=['GET', 'POST'])
{indent}def schedule_config():
{indent}    """Get or set trading schedule configuration"""
{indent}    if request.method == 'GET':
{indent}        # Return current schedule configuration
{indent}        try:
{indent}            config = {{
{indent}                "enabled": self.scheduler_enabled,
{indent}                "interval_minutes": self.schedule_interval,
{indent}                "market_hours_only": getattr(self, 'market_hours_only', True),
{indent}                "start_time": getattr(self, 'market_start', '09:30'),
{indent}                "end_time": getattr(self, 'market_end', '16:00'),
{indent}                "timezone": getattr(self, 'timezone', 'America/New_York'),
{indent}                "excluded_days": getattr(self, 'excluded_days', ['Saturday', 'Sunday'])
{indent}            }}
{indent}            return jsonify(config)
{indent}        except Exception as e:
{indent}            self.logger.error(f"Error getting schedule config: {{e}}")
{indent}            return jsonify({{
{indent}                "enabled": False,
{indent}                "interval_minutes": 30,
{indent}                "market_hours_only": True,
{indent}                "start_time": "09:30",
{indent}                "end_time": "16:00"
{indent}            }})
{indent}    
{indent}    else:  # POST - Update configuration
{indent}        try:
{indent}            config = request.json
{indent}            
{indent}            # Update scheduler configuration
{indent}            self.scheduler_enabled = config.get('enabled', False)
{indent}            self.schedule_interval = config.get('interval_minutes', 30)
{indent}            self.market_hours_only = config.get('market_hours_only', True)
{indent}            self.market_start = config.get('start_time', '09:30')
{indent}            self.market_end = config.get('end_time', '16:00')
{indent}            
{indent}            # Save configuration to file for persistence
{indent}            config_file = './schedule_config.json'
{indent}            with open(config_file, 'w') as f:
{indent}                json.dump(config, f, indent=2)
{indent}            
{indent}            # Log the update
{indent}            self.logger.info(f"Schedule configuration updated: {{config}}")
{indent}            
{indent}            # Restart scheduler if needed
{indent}            if self.scheduler_enabled and hasattr(self, 'scheduler_thread'):
{indent}                self.logger.info("Restarting scheduler with new configuration")
{indent}            
{indent}            return jsonify({{
{indent}                "status": "success",
{indent}                "message": "Schedule configuration updated",
{indent}                "config": config
{indent}            }})
{indent}            
{indent}        except Exception as e:
{indent}            self.logger.error(f"Error updating schedule config: {{e}}")
{indent}            return jsonify({{"error": str(e)}}), 500
'''
    
    # Insert the route code
    lines.insert(insert_index, route_code)
    
    # Check if we need to add the _load_schedule_config call in __init__
    init_modified = False
    for i, line in enumerate(lines):
        if 'def __init__' in line and 'self' in line:
            # Find where to add the load config call (after logger initialization)
            j = i + 1
            while j < len(lines):
                if 'self.logger' in lines[j] and '=' in lines[j]:
                    # Add load config after logger
                    k = j + 1
                    while k < len(lines) and lines[k].strip() == '':
                        k += 1
                    
                    init_indent = len(lines[j]) - len(lines[j].lstrip())
                    lines.insert(k, f"{' ' * init_indent}# Load schedule configuration")
                    lines.insert(k + 1, f"{' ' * init_indent}self._load_schedule_config()")
                    lines.insert(k + 2, "")
                    init_modified = True
                    break
                j += 1
            break
    
    # Add helper methods if they don't exist
    if '_load_schedule_config' not in content:
        # Find the end of the class to add helper methods
        class_end = len(lines) - 1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].startswith(' ') and not lines[i].startswith('\t'):
                if i > 0:
                    class_end = i
                break
        
        helper_code = '''
    def _load_schedule_config(self):
        """Load schedule configuration from file"""
        config_file = './schedule_config.json'
        if os.path.exists(config_file):
            try:
                import json
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
        
        lines.insert(class_end, helper_code)
    
    # Add json import if not present
    import_added = False
    for i, line in enumerate(lines[:20]):  # Check first 20 lines
        if 'import json' in line:
            import_added = True
            break
    
    if not import_added:
        # Add after other imports
        for i, line in enumerate(lines[:30]):
            if line.startswith('import ') or line.startswith('from '):
                continue
            elif line.strip() == '':
                continue
            else:
                # Found the end of imports
                lines.insert(i - 1, 'import json')
                break
    
    # Write the modified content
    modified_content = '\n'.join(lines)
    with open(filepath, 'w') as f:
        f.write(modified_content)
    
    print("✓ Successfully added /schedule/config endpoint")
    return True

def verify_fix(filepath):
    """Verify the fix was applied correctly"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    checks = [
        ('/schedule/config', "schedule/config endpoint"),
        ('_load_schedule_config', "_load_schedule_config method"),
        ('_set_default_schedule_config', "_set_default_schedule_config method")
    ]
    
    print("\nVerifying changes:")
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
    print("AUTO FIX SCHEDULE CONFIGURATION")
    print("=" * 60)
    
    # Find the coordination service file
    filepath = find_coordination_service()
    if not filepath:
        print("\n✗ Could not find coordination_service.py")
        print("Please make sure you're running this from the project directory")
        return
    
    # Create backup
    print("\nCreating backup...")
    backup_path = backup_file(filepath)
    
    # Apply the fix
    print("\nApplying fix...")
    success = add_schedule_config_endpoint(filepath)
    
    if success:
        # Verify the fix
        if verify_fix(filepath):
            print("\n✓ Fix applied successfully!")
            print("\nNext steps:")
            print("1. Restart the coordination service")
            print("2. Test the schedule configuration in the web dashboard")
            print("\nTo test manually:")
            print("   python test_schedule_config.py")
            
            if backup_path:
                print(f"\nIf you need to revert:")
                print(f"   cp {backup_path} {filepath}")
        else:
            print("\n⚠️  Fix partially applied - please check the file manually")
    else:
        print("\n✗ Failed to apply fix")
        print(f"Restore from backup: cp {backup_path} {filepath}")

if __name__ == "__main__":
    main()

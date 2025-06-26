#!/usr/bin/env python3
"""
Name of Service: Fix Coordination Schedule Endpoints
Filename: fix_coordination_schedule_endpoints.py
Version: 1.0.0
Last Updated: 2025-01-27
REVISION HISTORY:
v1.0.0 (2025-01-27) - Add missing schedule endpoints to coordination service

DESCRIPTION:
This script adds the missing schedule configuration endpoints to the
coordination service by modifying the file directly.
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✓ Created backup: {backup_path}")
    return backup_path

def find_coordination_service():
    """Find the coordination service file"""
    possible_paths = [
        'coordination_service.py',
        './coordination_service.py',
        '../coordination_service.py'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def add_schedule_endpoints(filepath):
    """Add schedule endpoints to coordination service"""
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Find where to insert the new routes (after _setup_routes definition)
    insert_index = None
    indent_level = None
    
    for i, line in enumerate(lines):
        if 'def _setup_routes(self):' in line:
            # Find the last route definition in this method
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith('def ') and not lines[j].strip().startswith('def health'):
                    # Found the end of _setup_routes
                    insert_index = j - 1
                    # Find a route definition to match indentation
                    for k in range(i + 1, j):
                        if '@self.app.route' in lines[k]:
                            indent_level = len(lines[k]) - len(lines[k].lstrip())
                            break
                    break
            break
    
    if insert_index is None or indent_level is None:
        print("✗ Could not find appropriate location to insert routes")
        return False
    
    # Create the new routes code
    indent = ' ' * indent_level
    new_routes = f'''
{indent}# Schedule Management Routes
{indent}@self.app.route('/schedule/status', methods=['GET'])
{indent}def get_schedule_status():
{indent}    """Get trading schedule status"""
{indent}    schedule_config = self._get_schedule_config()
{indent}    
{indent}    if schedule_config['enabled']:
{indent}        # Calculate next run time
{indent}        from datetime import datetime, timedelta
{indent}        now = datetime.now()
{indent}        interval = schedule_config['interval_minutes']
{indent}        
{indent}        # Simple next run calculation
{indent}        if hasattr(self, '_last_cycle_time'):
{indent}            next_run = self._last_cycle_time + timedelta(minutes=interval)
{indent}            next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S')
{indent}        else:
{indent}            next_run_str = f"In {interval} minutes"
{indent}        
{indent}        return jsonify({{
{indent}            "enabled": True,
{indent}            "interval_minutes": interval,
{indent}            "next_run": next_run_str,
{indent}            "message": "Automated trading is active"
{indent}        }})
{indent}    else:
{indent}        return jsonify({{
{indent}            "enabled": False,
{indent}            "message": "Automated trading is disabled",
{indent}            "next_run": None
{indent}        }})

{indent}@self.app.route('/schedule/config', methods=['GET', 'POST'])
{indent}def schedule_config():
{indent}    """Get or set trading schedule configuration"""
{indent}    if request.method == 'GET':
{indent}        return jsonify(self._get_schedule_config())
{indent}    else:  # POST
{indent}        try:
{indent}            config = request.json
{indent}            self._save_schedule_config(config)
{indent}            
{indent}            # Start or stop scheduler based on config
{indent}            if config.get('enabled'):
{indent}                self._start_scheduler(config)
{indent}            else:
{indent}                self._stop_scheduler()
{indent}            
{indent}            return jsonify({{
{indent}                "status": "success",
{indent}                "message": "Schedule configuration updated",
{indent}                "config": config
{indent}            }})
{indent}        except Exception as e:
{indent}            self.logger.error(f"Error updating schedule config: {{e}}")
{indent}            return jsonify({{"error": str(e)}}), 500
'''
    
    # Insert the new routes
    lines.insert(insert_index, new_routes)
    
    # Now add the helper methods at the class level
    # Find the end of the class
    class_end_index = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() and not lines[i].startswith(' ') and not lines[i].startswith('\t'):
            class_end_index = i
            break
    
    if class_end_index is None:
        class_end_index = len(lines) - 1
    
    # Add helper methods
    helper_methods = '''
    def _get_schedule_config(self):
        """Get schedule configuration"""
        # Default configuration
        default_config = {
            "enabled": False,
            "interval_minutes": 30,
            "market_hours_only": True,
            "start_time": "09:30",
            "end_time": "16:00"
        }
        
        # Try to load from file or database
        config_file = './schedule_config.json'
        if os.path.exists(config_file):
            try:
                import json
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return default_config
    
    def _save_schedule_config(self, config):
        """Save schedule configuration"""
        import json
        config_file = './schedule_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        self.logger.info(f"Schedule configuration saved: {config}")
    
    def _start_scheduler(self, config):
        """Start the automated trading scheduler"""
        if hasattr(self, '_scheduler_thread') and self._scheduler_thread and self._scheduler_thread.is_alive():
            self.logger.info("Scheduler already running")
            return
        
        import threading
        
        def scheduler_loop():
            import time
            from datetime import datetime, timedelta
            
            while getattr(self, '_scheduler_running', False):
                try:
                    now = datetime.now()
                    current_time = now.strftime('%H:%M')
                    
                    # Check if within market hours
                    if config.get('market_hours_only', True):
                        if current_time < config.get('start_time', '09:30') or \\
                           current_time > config.get('end_time', '16:00'):
                            time.sleep(60)  # Check every minute
                            continue
                    
                    # Check if it's time to run
                    if not hasattr(self, '_last_scheduled_run') or \\
                       (now - self._last_scheduled_run).total_seconds() >= config['interval_minutes'] * 60:
                        
                        self.logger.info("Executing scheduled trading cycle")
                        try:
                            # Start a trading cycle
                            response = requests.post(f"http://localhost:{self.port}/start_trading_cycle")
                            if response.status_code == 200:
                                self._last_scheduled_run = now
                                self.logger.info("Scheduled trading cycle started successfully")
                            else:
                                self.logger.error("Failed to start scheduled trading cycle")
                        except Exception as e:
                            self.logger.error(f"Error in scheduled cycle: {e}")
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    self.logger.error(f"Error in scheduler loop: {e}")
                    time.sleep(60)
        
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        self.logger.info("Trading scheduler started")
    
    def _stop_scheduler(self):
        """Stop the automated trading scheduler"""
        self._scheduler_running = False
        if hasattr(self, '_scheduler_thread') and self._scheduler_thread:
            self.logger.info("Trading scheduler stopped")
'''
    
    # Insert helper methods before the class end
    lines.insert(class_end_index, helper_methods)
    
    # Write the modified content
    modified_content = '\n'.join(lines)
    
    # Save to file
    with open(filepath, 'w') as f:
        f.write(modified_content)
    
    print("✓ Successfully added schedule endpoints to coordination service")
    return True

def verify_changes(filepath):
    """Verify the changes were applied correctly"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    checks = [
        ('/schedule/status', "schedule/status endpoint"),
        ('/schedule/config', "schedule/config endpoint"),
        ('_get_schedule_config', "_get_schedule_config method"),
        ('_save_schedule_config', "_save_schedule_config method"),
        ('_start_scheduler', "_start_scheduler method"),
        ('_stop_scheduler', "_stop_scheduler method")
    ]
    
    all_good = True
    for check_str, desc in checks:
        if check_str in content:
            print(f"✓ Found {desc}")
        else:
            print(f"✗ Missing {desc}")
            all_good = False
    
    return all_good

def main():
    """Main execution"""
    print("=" * 60)
    print("FIXING COORDINATION SERVICE SCHEDULE ENDPOINTS")
    print("=" * 60)
    
    # Find coordination service file
    filepath = find_coordination_service()
    if not filepath:
        print("\n✗ Could not find coordination_service.py")
        print("Please run this script from the project directory")
        return
    
    print(f"\n✓ Found coordination service: {filepath}")
    
    # Create backup
    backup_path = backup_file(filepath)
    
    # Apply changes
    print("\nAdding schedule endpoints...")
    success = add_schedule_endpoints(filepath)
    
    if success:
        print("\nVerifying changes...")
        if verify_changes(filepath):
            print("\n✓ All changes applied successfully!")
            print("\nNext steps:")
            print("1. Restart the coordination service")
            print("2. The schedule configuration should now work")
            print("\nIf there are any issues, restore from backup:")
            print(f"   cp {backup_path} {filepath}")
        else:
            print("\n⚠️  Some changes may not have been applied correctly")
            print("Check the file manually or restore from backup")
    else:
        print("\n✗ Failed to apply changes")
        print(f"Restore from backup: cp {backup_path} {filepath}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FIX EXTRA DATETIME IN COORDINATION SERVICE
Service: Remove duplicate datetime.now()
Version: 1.0.0
Last Updated: 2025-06-24

Removes the extra datetime.now() that's causing parameter count mismatch
"""

from pathlib import Path
from datetime import datetime

def fix_extra_datetime():
    """Remove the extra datetime.now() from coordination_service.py"""
    
    print("="*60)
    print("FIX EXTRA DATETIME IN COORDINATION SERVICE")
    print("="*60)
    
    coord_file = Path('coordination_service.py')
    
    if not coord_file.exists():
        print("❌ coordination_service.py not found!")
        return
    
    # Read the file
    with open(coord_file, 'r') as f:
        content = f.read()
    
    # Backup
    backup_path = f"coordination_service.py.datetime_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"✓ Created backup: {backup_path}")
    
    print("\nFixing the duplicate datetime.now()...")
    
    # Look for the pattern with two datetime.now() calls
    old_pattern = """'active',
                    datetime.now(),
                    datetime.now()
                ))"""
    
    new_pattern = """'active',
                    datetime.now()
                ))"""
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("✅ Found and fixed the duplicate datetime.now()")
        
        # Write back
        with open(coord_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Fixed! The INSERT now has:")
        print("  - 5 columns: service_name, host, port, status, last_heartbeat")
        print("  - 5 values: service_name, 'localhost', port, 'active', datetime.now()")
        
    else:
        # Try alternative spacing
        print("Trying alternative pattern...")
        
        # Look for any occurrence of two datetime.now() in a row
        import re
        pattern = r'datetime\.now\(\),\s*datetime\.now\(\)'
        
        matches = list(re.finditer(pattern, content))
        if matches:
            print(f"Found {len(matches)} occurrences of duplicate datetime.now()")
            # Replace with single datetime.now()
            content = re.sub(pattern, 'datetime.now()', content)
            
            # Write back
            with open(coord_file, 'w') as f:
                f.write(content)
            
            print("✅ Fixed all duplicate datetime.now() calls")
        else:
            print("❌ Could not find duplicate datetime.now() pattern")
            print("\nManual fix required:")
            print("1. Open coordination_service.py")
            print("2. Find the _persist_service_registration method")
            print("3. In the cursor.execute, change:")
            print("   FROM: datetime.now(), datetime.now()")
            print("   TO:   datetime.now()")
    
    print("\nRestart the coordination service after this fix:")
    print("1. pkill -f coordination_service")
    print("2. python coordination_service.py &")

if __name__ == "__main__":
    fix_extra_datetime()

#!/usr/bin/env python3
"""
FIX COORDINATION SERVICE PARAMETER COUNT
Service: Fix SQL Parameter Mismatch
Version: 1.0.0
Last Updated: 2025-06-24

Fixes the "Incorrect number of bindings supplied" error in coordination_service.py
"""

from pathlib import Path
from datetime import datetime

def fix_coordination_parameters():
    """Fix parameter count mismatch in coordination_service.py"""
    
    print("="*60)
    print("FIX COORDINATION SERVICE PARAMETER COUNT")
    print("="*60)
    
    coord_file = Path('coordination_service.py')
    
    if not coord_file.exists():
        print("❌ coordination_service.py not found!")
        return
    
    # Read the file
    with open(coord_file, 'r') as f:
        content = f.read()
    
    # Backup
    backup_path = f"coordination_service.py.params_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"✓ Created backup: {backup_path}")
    
    print("\nSearching for the INSERT statement...")
    
    # Find the _persist_service_registration method
    method_start = content.find("def _persist_service_registration")
    if method_start == -1:
        print("❌ Could not find _persist_service_registration method")
        return
    
    # Find the INSERT statement within this method
    insert_start = content.find("INSERT OR REPLACE INTO service_coordination", method_start)
    if insert_start == -1:
        print("❌ Could not find INSERT statement")
        return
    
    # Find the end of the execute statement
    execute_end = content.find("))", insert_start) + 2
    
    # Extract the current INSERT block
    current_block = content[insert_start:execute_end]
    print("\nCurrent INSERT block:")
    print("-"*40)
    print(current_block)
    print("-"*40)
    
    # Count placeholders and values
    placeholders = current_block.count("?")
    
    # Count commas in the values tuple (approximate)
    values_start = current_block.find("(", current_block.find("VALUES"))
    values_end = current_block.rfind(")")
    if values_start != -1 and values_end != -1:
        values_section = current_block[values_start:values_end]
        value_commas = values_section.count(",")
        estimated_values = value_commas + 1
        
        print(f"\nFound {placeholders} placeholders (?) and approximately {estimated_values} values")
    
    # Replace with the correct INSERT statement
    # Based on the schema: service_name, host, port, status, last_heartbeat
    new_insert_template = '''INSERT OR REPLACE INTO service_coordination 
                    (service_name, host, port, status, last_heartbeat)
                    VALUES (?, ?, ?, ?, ?)'''
    
    # Find and replace the entire execute block
    # Look for pattern: cursor.execute(''' ... ))
    import re
    
    # Pattern to match the entire cursor.execute block
    pattern = r'cursor\.execute\(\'\'\'\s*INSERT OR REPLACE INTO service_coordination[^)]+\)\)'
    
    match = re.search(pattern, content[method_start:], re.DOTALL)
    if match:
        old_execute = match.group(0)
        
        # Build the new execute statement
        new_execute = """cursor.execute('''
                    INSERT OR REPLACE INTO service_coordination 
                    (service_name, host, port, status, last_heartbeat)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    service_name,
                    'localhost',
                    port,
                    'active',
                    datetime.now()
                ))"""
        
        # Replace in content
        content = content[:method_start] + content[method_start:].replace(old_execute, new_execute, 1)
        
        print("\n✅ Fixed INSERT statement!")
        print("\nNew INSERT statement:")
        print("-"*40)
        print(new_execute)
        print("-"*40)
        
        # Write back
        with open(coord_file, 'w') as f:
            f.write(content)
        
        print("\n✅ coordination_service.py has been fixed!")
        print("\nThe INSERT now has:")
        print("  - 5 columns: service_name, host, port, status, last_heartbeat")
        print("  - 5 values: service_name, 'localhost', port, 'active', datetime.now()")
        print("\nRestart the coordination service for changes to take effect.")
    else:
        print("\n❌ Could not find the exact INSERT pattern to replace")
        print("You may need to manually fix the _persist_service_registration method")
        print("\nMake sure the INSERT has the same number of columns and values:")
        print("  Columns: (service_name, host, port, status, last_heartbeat)")
        print("  Values: (service_name, 'localhost', port, 'active', datetime.now())")

if __name__ == "__main__":
    fix_coordination_parameters()
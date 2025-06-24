#!/usr/bin/env python3
"""
FIX COORDINATION SERVICE COLUMN NAMES
Service: Coordination Service Database Fix
Version: 1.1.0
Last Updated: 2025-06-24

This script fixes the coordination_service.py to use the correct column names
that actually exist in the service_coordination table.
"""

from pathlib import Path
from datetime import datetime

def fix_coordination_service():
    """Fix column names in coordination_service.py"""
    
    print("="*60)
    print("FIX COORDINATION SERVICE COLUMN NAMES")
    print("="*60)
    
    coord_file = Path('coordination_service.py')
    
    if not coord_file.exists():
        print("❌ coordination_service.py not found!")
        return
    
    # Read the file
    with open(coord_file, 'r') as f:
        content = f.read()
    
    # Backup original
    backup_path = f"coordination_service.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"✓ Created backup: {backup_path}")
    
    print("\nApplying fixes...")
    original_content = content
    changes_made = []
    
    # Simple replacements - do ALL occurrences
    replacements = [
        # Column name fixes
        ('service_url', 'host'),
        ('service_port', 'port'),
        ('updated_at', 'last_heartbeat'),  # or remove it
        
        # Fix the URL construction
        ('f"http://localhost:{port}"', "'localhost'"),  # Just store hostname
        ("f'http://localhost:{port}'", "'localhost'"),
        
        # Fix any remaining references
        ('row[1]', 'row[1]'),  # This stays the same but we need to construct URL differently
    ]
    
    # Apply replacements and track what was changed
    for old, new in replacements:
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            changes_made.append(f"{old} → {new} ({count} occurrences)")
    
    # Special handling for the service registry URL construction
    # After SELECT, we need to construct the URL from host and port
    if "'url': row[1]," in content:
        # This means it's expecting a URL directly from the database
        # But we store host and port separately, so construct it
        old_block = """self.service_registry[row[0]] = {
                    'url': row[1],
                    'port': row[2],
                    'status': row[3],
                    'last_heartbeat': row[4]
                }"""
        
        new_block = """self.service_registry[row[0]] = {
                    'url': f"http://{row[1]}:{row[2]}",
                    'port': row[2],
                    'status': row[3],
                    'last_heartbeat': row[4]
                }"""
        
        if old_block in content:
            content = content.replace(old_block, new_block)
            changes_made.append("Fixed URL construction in service registry")
    
    # Remove any CREATE TABLE with wrong columns (coordination service shouldn't create tables)
    # The database_migration.py should handle this
    if "CREATE TABLE IF NOT EXISTS service_coordination" in content:
        # Find and comment out the entire CREATE TABLE block
        create_start = content.find("cursor.execute('''")
        if create_start != -1:
            create_end = content.find("''')", create_start) + 4
            if create_end > create_start:
                create_block = content[create_start:create_end]
                if "service_coordination" in create_block:
                    content = content[:create_start] + "# Table creation handled by database_migration.py\n" + content[create_end:]
                    changes_made.append("Removed CREATE TABLE statement (should use database_migration.py)")
    
    # Fix the INSERT statement specifically
    # Look for the _persist_service_registration method
    if "_persist_service_registration" in content:
        # Find the INSERT statement
        if "(service_name, host, port, status, last_heartbeat, last_heartbeat)" in content:
            # Fix duplicate last_heartbeat
            content = content.replace(
                "(service_name, host, port, status, last_heartbeat, last_heartbeat)",
                "(service_name, host, port, status, last_heartbeat)"
            )
            content = content.replace(
                "VALUES (?, ?, ?, ?, ?, ?)",
                "VALUES (?, ?, ?, ?, ?)"
            )
            changes_made.append("Fixed duplicate column in INSERT")
    
    # Write the fixed content
    if content != original_content:
        with open(coord_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Applied the following changes:")
        for change in changes_made:
            print(f"  - {change}")
        
        print(f"\nTotal changes: {len(changes_made)}")
        print("\n✅ coordination_service.py has been fixed!")
        
        # Show a sample of what was changed
        print("\n📋 Sample changes:")
        lines_original = original_content.split('\n')
        lines_new = content.split('\n')
        
        changes_shown = 0
        for i, (old_line, new_line) in enumerate(zip(lines_original, lines_new)):
            if old_line != new_line and changes_shown < 5:
                print(f"\n  Line {i+1}:")
                print(f"  OLD: {old_line.strip()}")
                print(f"  NEW: {new_line.strip()}")
                changes_shown += 1
        
    else:
        print("\n⚠️  No changes were needed or the patterns didn't match exactly.")
        print("\nYou may need to manually fix:")
        print("  - Change all 'service_url' to 'host'")
        print("  - Change all 'service_port' to 'port'") 
        print("  - Remove all 'updated_at' references")
        print("  - Change f'http://localhost:{port}' to just 'localhost'")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    fix_coordination_service()
#!/usr/bin/env python3
"""
Quick fix script to add missing time import to security_scanner.py
Run this from the repository root: python fix_security_scanner_import.py
"""

import os
import re
from pathlib import Path

def fix_security_scanner():
    """Add missing time import to security_scanner.py"""
    
    # Find the security_scanner.py file
    scanner_file = Path('security_scanner.py')
    
    if not scanner_file.exists():
        print("❌ security_scanner.py not found in current directory")
        return False
    
    print(f"📄 Found {scanner_file}")
    
    # Read the file
    with open(scanner_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if time is already imported
    if re.search(r'^import time\s*$', content, re.MULTILINE):
        print("✅ 'import time' already exists")
        return True
    
    if re.search(r'^from time import', content, re.MULTILINE):
        print("✅ time module already imported (using from time import ...)")
        return True
    
    # Find where to insert the import
    # Look for the first import statement
    import_match = re.search(r'^(import|from)\s+\w+', content, re.MULTILINE)
    
    if import_match:
        # Find all standard library imports
        lines = content.split('\n')
        import_section_start = None
        import_section_end = None
        
        for i, line in enumerate(lines):
            if re.match(r'^(import|from)\s+\w+', line):
                if import_section_start is None:
                    import_section_start = i
                import_section_end = i
        
        # Insert after other standard library imports
        if import_section_start is not None:
            # Check if we're in the standard library section
            insert_line = import_section_start
            
            # Look for a good place to insert (after other standard imports like os, sys, etc.)
            for i in range(import_section_start, min(import_section_end + 1, len(lines))):
                if re.match(r'^import (os|sys|json|logging|threading|traceback)', lines[i]):
                    insert_line = i + 1
            
            # Insert the import
            lines.insert(insert_line, 'import time')
            
            # Write back
            new_content = '\n'.join(lines)
            
            # Backup original
            backup_file = scanner_file.with_suffix('.py.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📋 Created backup: {backup_file}")
            
            # Write fixed version
            with open(scanner_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Added 'import time' to security_scanner.py")
            return True
    else:
        # No imports found, add at the beginning after docstring/comments
        lines = content.split('\n')
        insert_pos = 0
        
        # Skip shebang, docstrings, and initial comments
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#') and not line.startswith('"""') and not line.startswith("'''"):
                insert_pos = i
                break
        
        lines.insert(insert_pos, 'import time\n')
        
        # Write back
        new_content = '\n'.join(lines)
        
        # Backup original
        backup_file = scanner_file.with_suffix('.py.backup')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📋 Created backup: {backup_file}")
        
        # Write fixed version
        with open(scanner_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Added 'import time' at the beginning of security_scanner.py")
        return True
    
    return False

def verify_fix():
    """Verify the fix worked"""
    print("\n🔍 Verifying fix...")
    
    try:
        # Try to import and check
        import importlib.util
        spec = importlib.util.spec_from_file_location("security_scanner", "security_scanner.py")
        module = importlib.util.module_from_spec(spec)
        
        # This will fail if there are import errors
        spec.loader.exec_module(module)
        
        # Check if time is available
        if hasattr(module, 'time') or 'time' in dir(module):
            print("✅ Verification passed - time module is available")
            return True
        else:
            print("⚠️  Warning: time module might not be properly imported")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    print("🔧 Security Scanner Import Fixer")
    print("=" * 50)
    
    if fix_security_scanner():
        verify_fix()
        print("\n✅ Fix complete! Try running the security scanner again.")
        print("\nTo restart the service:")
        print("  python hybrid_manager.py restart scanner")
        print("  # or restart all services:")
        print("  python hybrid_manager.py restart")
    else:
        print("\n❌ Fix failed. Please check security_scanner.py manually.")

if __name__ == "__main__":
    main()
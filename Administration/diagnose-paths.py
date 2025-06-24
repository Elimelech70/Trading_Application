#!/usr/bin/env python3
"""
Diagnose and fix path issues in Trading Application
"""
import os
import re
from pathlib import Path

def find_path_issues():
    """Find all files with path issues"""
    print("🔍 Scanning for path issues...\n")
    
    issues_found = []
    
    # Common problematic patterns
    patterns = [
        r'["\']\.?/?trading_system/',  # ./trading_system/ or /trading_system/
        r'["\']\.?/?content/',          # ../ or ./
        r'trading_system\.db',          # database references
    ]
    
    # Scan all Python files
    for py_file in Path('.').glob('*.py'):
        with open(py_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        file_issues = []
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    file_issues.append({
                        'line_num': i,
                        'line': line.strip(),
                        'pattern': pattern
                    })
        
        if file_issues:
            issues_found.append({
                'file': str(py_file),
                'issues': file_issues
            })
    
    return issues_found

def show_issues(issues):
    """Display found issues"""
    if not issues:
        print("✅ No path issues found!")
        return
    
    print(f"❌ Found path issues in {len(issues)} files:\n")
    
    for file_info in issues:
        print(f"\n📄 {file_info['file']}:")
        for issue in file_info['issues']:
            print(f"   Line {issue['line_num']}: {issue['line']}")

def suggest_fixes(issues):
    """Suggest fixes for found issues"""
    if not issues:
        return
    
    print("\n" + "="*60)
    print("🔧 SUGGESTED FIXES:")
    print("="*60)
    
    print("\nThe issue is that your files are looking for a 'trading_system' subdirectory")
    print("that doesn't exist. Your files are in the current directory.\n")
    
    print("Run these commands to fix:\n")
    
    # Generate sed commands for each file
    fixed_files = set()
    for file_info in issues:
        filename = file_info['file']
        if filename not in fixed_files:
            print(f"# Fix {filename}")
            print(f"sed -i 's|trading_system/||g' {filename}")
            print(f"sed -i 's|./|./|g' {filename}")
            fixed_files.add(filename)
    
    print("\n# Or fix all at once:")
    print("for f in *.py; do")
    print("  sed -i 's|trading_system/||g' \"$f\"")
    print("  sed -i 's|./|./|g' \"$f\"")
    print("done")

def main():
    print("🏥 Trading Application Path Diagnostic Tool\n")
    
    # Find issues
    issues = find_path_issues()
    
    # Show what was found
    show_issues(issues)
    
    # Suggest fixes
    suggest_fixes(issues)
    
    # Show current directory structure
    print("\n" + "="*60)
    print("📁 YOUR CURRENT DIRECTORY STRUCTURE:")
    print("="*60)
    print(f"Current directory: {os.getcwd()}")
    print("\nFiles in current directory:")
    for item in sorted(os.listdir('.')):
        if not item.startswith('.'):
            print(f"  - {item}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
FIND GOOGLE COLAB PATHS
Service: Google Colab Path Finder
Version: 1.1.0
Last Updated: 2025-06-24

This script finds all instances of Google Colab paths (/content/) in Python service files.
It reports the filename and line number for each occurrence.
"""

import os
from pathlib import Path

def find_colab_paths():
    """Find all instances of Google Colab paths in Python files"""
    
    # Paths to search for - expanded list
    wrong_paths = [
        '/content/trading_system.db',
        '/content/trading_database.db',
        '/content/trading_system',
        '/content/logs',
        '/content/drive/MyDrive/TradingBot',
        '/content/drive/MyDrive/trading_bot',
        '/content/drive/MyDrive',
        '/content/backups',
        '/content/'
    ]
    
    # Find all Python files in current directory and subdirectories
    # Exclude common directories that shouldn't be searched
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'env', '.env', 'node_modules', '.idea', '.vscode'}
    
    python_files = []
    for py_file in Path('.').rglob('*.py'):
        # Check if any part of the path contains excluded directories
        if not any(excluded in py_file.parts for excluded in exclude_dirs):
            python_files.append(py_file)
    
    print("="*80)
    print("GOOGLE COLAB PATH REPORT")
    print("="*80)
    print(f"Searching {len(python_files)} Python files for Google Colab paths (/content/)...")
    print("="*80)
    print()
    
    total_issues = 0
    files_with_issues = 0
    
    for py_file in sorted(python_files):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            file_issues = []
            
            for line_num, line in enumerate(lines, 1):
                for wrong_path in wrong_paths:
                    if wrong_path in line:
                        file_issues.append({
                            'line_num': line_num,
                            'path': wrong_path,
                            'line': line.strip()
                        })
            
            if file_issues:
                files_with_issues += 1
                
                for issue in file_issues:
                    print(f"File: {py_file}, Line {issue['line_num']}")
                    print(f"  Found: {issue['path']}")
                    print(f"  Code: {issue['line']}")
                    print()
                    total_issues += 1
                
        except Exception as e:
            print(f"⚠️  Error reading {py_file}: {e}")
            print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Files checked: {len(python_files)}")
    print(f"Files with issues: {files_with_issues}")
    print(f"Total issues found: {total_issues}")
    print("="*80)
    
    if total_issues > 0:
        print("\nTo fix these issues, replace:")
        print("  '/content/trading_system.db' → './trading_system.db'")
        print("  '/content/trading_database.db' → './trading_system.db'")
        print("  '/content/trading_system' → '.'")
        print("  '/content/logs' → './logs'")
        print("  '/content/backups' → './backups'")
        print("  '/content/drive/MyDrive/TradingBot/checkpoints' → './checkpoints'")
        print("  '/content/drive/MyDrive/TradingBot/backups' → './backups'")
        print("  '/content/' → './'")
        print("\nNote: Remove leading '/' from paths like '/./logs' → './logs'")

if __name__ == "__main__":
    find_colab_paths()
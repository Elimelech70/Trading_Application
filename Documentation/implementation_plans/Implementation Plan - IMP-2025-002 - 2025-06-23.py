#!/usr/bin/env python3
"""
Update Documentation Folder References
Version: 1.0.0
Purpose: Updates all references from 'project_documentation' to 'Documentation' across the project

This script will:
1. Rename the actual folder if it exists
2. Update all references in Python files
3. Update all references in markdown files
4. Update all references in configuration files
5. Create backups before making changes
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import re

class DocumentationFolderUpdater:
    def __init__(self):
        self.old_folder_name = "project_documentation"
        self.new_folder_name = "Documentation"
        self.backup_dir = Path("update_backups") / f"doc_folder_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.changes_made = []
        self.files_checked = []
        self.files_updated = []
        
    def create_backup_directory(self):
        """Create backup directory for this update"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created backup directory: {self.backup_dir}")
        
    def backup_file(self, file_path):
        """Create a backup of a file before modifying it"""
        try:
            relative_path = Path(file_path).relative_to(".")
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            print(f"⚠️  Warning: Could not backup {file_path}: {e}")
            return False
    
    def rename_folder(self):
        """Rename the actual folder if it exists"""
        old_path = Path(self.old_folder_name)
        new_path = Path(self.new_folder_name)
        
        if old_path.exists() and old_path.is_dir():
            if new_path.exists():
                print(f"⚠️  Warning: {self.new_folder_name} already exists. Folder not renamed.")
                return False
            
            try:
                # Backup the entire folder structure
                backup_folder_path = self.backup_dir / self.old_folder_name
                shutil.copytree(old_path, backup_folder_path)
                
                # Rename the folder
                old_path.rename(new_path)
                self.changes_made.append(f"Renamed folder: {self.old_folder_name} → {self.new_folder_name}")
                print(f"✓ Renamed folder: {self.old_folder_name} → {self.new_folder_name}")
                return True
            except Exception as e:
                print(f"❌ Error renaming folder: {e}")
                return False
        else:
            print(f"ℹ️  Folder '{self.old_folder_name}' not found, skipping rename")
            return False
    
    def update_file_content(self, file_path):
        """Update references in a single file"""
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # Define replacement patterns
            replacements = [
                # Basic replacements
                ('project_documentation/', f'{self.new_folder_name}/'),
                ('project_documentation\\\\', f'{self.new_folder_name}\\\\'),
                ('"project_documentation"', f'"{self.new_folder_name}"'),
                ("'project_documentation'", f"'{self.new_folder_name}'"),
                ('`project_documentation`', f'`{self.new_folder_name}`'),
                
                # Path-specific replacements
                ('./project_documentation/', f'./{self.new_folder_name}/'),
                ('../project_documentation/', f'../{self.new_folder_name}/'),
                ('project_documentation/implementation_plans', f'{self.new_folder_name}/implementation_plans'),
                ('project_documentation/change_diaries', f'{self.new_folder_name}/change_diaries'),
                ('project_documentation/specifications', f'{self.new_folder_name}/specifications'),
                ('project_documentation/archive', f'{self.new_folder_name}/archive'),
                
                # Variable and string replacements
                ('PROJECT_DOCUMENTATION', 'DOCUMENTATION'),
                ('Project Documentation', 'Documentation'),
            ]
            
            # Apply replacements
            changes_in_file = []
            for old_text, new_text in replacements:
                if old_text in content:
                    count = content.count(old_text)
                    content = content.replace(old_text, new_text)
                    changes_in_file.append(f"  - Replaced '{old_text}' ({count} occurrences)")
            
            # Check if content changed
            if content != original_content:
                # Backup the file
                if self.backup_file(file_path):
                    # Write updated content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.files_updated.append(str(file_path))
                    self.changes_made.extend([f"\n{file_path}:"] + changes_in_file)
                    return True
                else:
                    print(f"⚠️  Skipped updating {file_path} (backup failed)")
                    return False
                    
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
            return False
        
        return False
    
    def get_files_to_update(self):
        """Get list of files that should be checked for updates"""
        extensions = ['.py', '.md', '.txt', '.json', '.yml', '.yaml', '.sh', '.bat']
        exclude_dirs = {'venv', 'env', '.git', '__pycache__', 'node_modules', 
                       '.idea', '.vscode', 'update_backups', 'config_backups'}
        
        files_to_check = []
        
        for root, dirs, files in os.walk('.'):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip this script
                if file == os.path.basename(__file__):
                    continue
                
                # Check if file has relevant extension
                if any(str(file_path).endswith(ext) for ext in extensions):
                    files_to_check.append(file_path)
                    
                # Also check specific files without extensions
                if file in ['Dockerfile', 'Makefile', 'requirements', '.gitignore', '.env.example']:
                    files_to_check.append(file_path)
        
        return files_to_check
    
    def generate_report(self):
        """Generate a report of all changes made"""
        report_path = self.backup_dir / "update_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Documentation Folder Update Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Old folder name: {self.old_folder_name}\n")
            f.write(f"New folder name: {self.new_folder_name}\n")
            f.write(f"\nFiles checked: {len(self.files_checked)}\n")
            f.write(f"Files updated: {len(self.files_updated)}\n")
            f.write(f"\nBackup location: {self.backup_dir}\n")
            f.write("\n" + "=" * 50 + "\n")
            
            if self.files_updated:
                f.write("\nFiles Updated:\n")
                for file in sorted(self.files_updated):
                    f.write(f"  - {file}\n")
            
            if self.changes_made:
                f.write("\nDetailed Changes:\n")
                for change in self.changes_made:
                    f.write(f"{change}\n")
        
        print(f"\n📄 Report saved to: {report_path}")
    
    def run(self):
        """Execute the update process"""
        print("\n🔄 Documentation Folder Update Tool")
        print("=" * 50)
        print(f"This will update all references from '{self.old_folder_name}' to '{self.new_folder_name}'")
        
        # Confirm with user
        response = input("\nProceed with update? (y/n): ")
        if response.lower() != 'y':
            print("❌ Update cancelled")
            return
        
        print("\n🚀 Starting update process...")
        
        # Create backup directory
        self.create_backup_directory()
        
        # Step 1: Rename the actual folder
        print("\n📁 Step 1: Checking for folder rename...")
        self.rename_folder()
        
        # Step 2: Get files to update
        print("\n📝 Step 2: Scanning for files to update...")
        files_to_check = self.get_files_to_update()
        print(f"Found {len(files_to_check)} files to check")
        
        # Step 3: Update file contents
        print("\n✏️  Step 3: Updating file contents...")
        for file_path in files_to_check:
            self.files_checked.append(str(file_path))
            self.update_file_content(file_path)
        
        # Step 4: Generate report
        print("\n📊 Step 4: Generating report...")
        self.generate_report()
        
        # Summary
        print("\n✅ Update Complete!")
        print(f"Files checked: {len(self.files_checked)}")
        print(f"Files updated: {len(self.files_updated)}")
        print(f"Backup location: {self.backup_dir}")
        
        if self.files_updated:
            print("\n📋 Updated files:")
            for file in sorted(self.files_updated)[:10]:  # Show first 10
                print(f"  - {file}")
            if len(self.files_updated) > 10:
                print(f"  ... and {len(self.files_updated) - 10} more")
        
        print("\n💡 To rollback changes, restore files from the backup directory")
        print(f"   Backup location: {self.backup_dir}")

def main():
    """Main entry point"""
    updater = DocumentationFolderUpdater()
    
    try:
        updater.run()
    except KeyboardInterrupt:
        print("\n\n❌ Update interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
TRADING SYSTEM PHASE 1
Service: TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py
Version: 2.0.1
Last Updated: 2025-01-11

REVISION HISTORY:
- v2.0.1 (2025-01-11) - Integrated with google_drive_service_v101.py
- v2.0.0 (2025-06-19) - Full compliance with Project Methodology v3.0.2
  - Added implementation plan reading functionality
  - Implemented proper Change Diary naming with Implementation ID
  - Added What's Next Task List after each phase
  - Implemented all required command line options
  - Added Implementation ID tracking throughout lifecycle
- v1.0.0 (2025-06-19) - Initial automated update process

PURPOSE:
Automated update process for Trading System with full Google Drive integration.
Executes implementation plans following the 6-phase methodology.
"""

import os
import sys
import json
import shutil
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Import the Google Drive service
from google_drive_service_v101 import get_drive_service

@dataclass
class ImplementationPlan:
    """Represents an approved implementation plan"""
    implementation_id: str
    plan_name: str
    date_created: str
    phases: List[Dict]
    files_to_update: List[Dict]
    risk_level: str = "MEDIUM"
    rollback_strategy: Dict = field(default_factory=dict)
    raw_content: str = ""
    
    @classmethod
    def from_drive_content(cls, plan_name: str, content: str) -> 'ImplementationPlan':
        """Load implementation plan from Google Drive content"""
        # Extract Implementation ID from filename
        # Format: "Implementation Plan - [ID] - [DATE].md"
        parts = plan_name.replace("Implementation Plan - ", "").replace(".md", "").split(" - ")
        implementation_id = parts[0] if parts else "UNKNOWN"
        
        # Parse content to extract files to update
        files_to_update = []
        lines = content.split('\n')
        in_files_section = False
        
        for line in lines:
            if 'Files to Update' in line or 'Files to Deliver' in line:
                in_files_section = True
                continue
            if in_files_section and line.strip().startswith('-'):
                # Extract filename from various formats
                # - news_service_v105.py
                # - `news_service_v105.py` → `news_service.py`
                if '→' in line or '->' in line:
                    parts = line.replace('→', '->').split('->')
                    source = parts[0].strip().strip('-').strip().strip('`')
                    target = parts[1].strip().strip('`')
                else:
                    source = line.strip().strip('-').strip().strip('`')
                    target = source.replace('_v', '_').split('_')[0] + '.py'
                
                if source.endswith('.py'):
                    files_to_update.append({
                        'filename': source,
                        'target': target,
                        'action': 'update'
                    })
        
        # Extract risk level if present
        risk_level = "MEDIUM"
        for line in lines:
            if 'Risk Level:' in line:
                if 'HIGH' in line.upper():
                    risk_level = "HIGH"
                elif 'LOW' in line.upper():
                    risk_level = "LOW"
                break
        
        return cls(
            implementation_id=implementation_id,
            plan_name=plan_name,
            date_created=datetime.now().strftime("%Y-%m-%d"),
            phases=[
                {"name": "Discovery", "description": "Scan for updates"},
                {"name": "Documentation", "description": "Create change records"},
                {"name": "Preparation", "description": "Backup system"},
                {"name": "Implementation", "description": "Apply updates"},
                {"name": "Testing", "description": "Verify functionality"},
                {"name": "Completion", "description": "Finalize update"}
            ],
            files_to_update=files_to_update,
            risk_level=risk_level,
            raw_content=content
        )


class WhatsNextTaskList:
    """Generate What's Next Task List based on phase and status"""
    
    @staticmethod
    def generate(phase_name: str, phase_status: str, context: Dict) -> str:
        """Generate task list for the current situation"""
        task_list = [
            "=== WHAT'S NEXT TASK LIST ===",
            f"Phase: {phase_name} - {phase_status} {'✓' if phase_status == 'COMPLETED' else '✗'}",
            ""
        ]
        
        # Determine if in Jupyter/Colab
        python_cmd = "!python" if 'ipykernel' in sys.modules else "python"
        
        if phase_status == "COMPLETED":
            # Success path
            if "Discovery" in phase_name:
                update_count = context.get('update_count', 0)
                task_list.extend([
                    f"✅ Found {update_count} updates to process",
                    "",
                    "Actions Required:",
                    "1. Review discovered updates in Change Diary",
                    f"2. Continue with: {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --continue",
                    "3. Monitor progress in Change Diary"
                ])
                
            elif "Documentation" in phase_name:
                task_list.extend([
                    "✅ Change documentation created",
                    "",
                    "Actions Required:",
                    "1. Review impact analysis in Change Diary",
                    f"2. Continue with: {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --continue",
                    "3. Ensure system is ready for backup"
                ])
                
            elif "Preparation" in phase_name:
                backup_path = context.get('backup_path', './backups/backup_[timestamp]')
                task_list.extend([
                    "✅ System prepared and backed up",
                    "",
                    "Actions Required:",
                    "1. Review Preparation results in Change Diary",
                    f"2. Continue with: {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --continue",
                    f"3. Verify backup completion in: {backup_path}",
                    "4. Confirm all services have been stopped"
                ])
                
            elif "Implementation" in phase_name:
                applied_count = context.get('applied_count', 0)
                task_list.extend([
                    f"✅ Applied {applied_count} updates successfully",
                    "",
                    "Actions Required:",
                    "1. Review implementation results in Change Diary",
                    f"2. Continue with: {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --continue",
                    "3. Prepare for system testing"
                ])
                
            elif "Testing" in phase_name:
                task_list.extend([
                    "✅ All tests passed",
                    "",
                    "Actions Required:",
                    "1. Review test results in Change Diary",
                    f"2. Continue with: {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --continue",
                    "3. Prepare for final completion"
                ])
                
            elif "Completion" in phase_name:
                task_list.extend([
                    "✅ Update process completed successfully!",
                    "",
                    "Post-Implementation Tasks:",
                    "1. Review final Change Diary",
                    "2. Verify all services are operational",
                    "3. Archive implementation plan",
                    "4. Monitor system for 24 hours"
                ])
                
        elif phase_status == "FAILED":
            # Failure path
            task_list.extend([
                "Phase FAILED - Intervention Required",
                "",
                "Diagnostic Steps:",
                f"1. Run: {python_cmd} diagnostic_toolkit.py --report",
                "2. Review error details in Change Diary",
                "3. Check Google Drive connectivity",
                "",
                "Recovery Options:",
                f"- Fix issue and retry: {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --retry",
                f"- Rollback changes: {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --rollback",
                "- Get help: Review Implementation Plan for troubleshooting steps"
            ])
            
            if context.get('error'):
                task_list.extend([
                    "",
                    f"Error Details: {context['error']}"
                ])
                
        return "\n".join(task_list)


class ChangeManagementDiary:
    """Enhanced Change Management Diary with Google Drive integration"""
    
    def __init__(self, implementation_id: str, plan_name: str, drive_service):
        self.implementation_id = implementation_id
        self.plan_name = plan_name
        self.drive_service = drive_service
        self.start_time = datetime.now()
        
        # Create diary filename with proper naming convention
        date_str = self.start_time.strftime("%Y-%m-%d")
        self.diary_filename = f"Change Diary - {implementation_id} - {date_str}.md"
        
        self.phases = {
            "Phase 1": {"name": "Discovery and Verification", "status": "PENDING"},
            "Phase 2": {"name": "Change Management Documentation", "status": "PENDING"},
            "Phase 3": {"name": "Pre-Update Preparation", "status": "PENDING"},
            "Phase 4": {"name": "Implementation", "status": "PENDING"},
            "Phase 5": {"name": "Testing and Validation", "status": "PENDING"},
            "Phase 6": {"name": "Completion or Rollback", "status": "PENDING"}
        }
        self.current_phase = None
        self.detailed_progress = []
        self.phase_metadata = {}
        self.last_task_list = ""
        self._initialize_diary()
        
    def _initialize_diary(self):
        """Create initial diary with proper header format"""
        header = f"""# {self.diary_filename.replace('.md', '')}

**Document**: Change Diary
**Implementation ID**: {self.implementation_id}
**Related Implementation Plan**: {self.plan_name}
**Date Created**: {self.start_time.strftime("%Y-%m-%d")}
**Author**: Trading System Development Team

## Implementation Summary
Automated update process executing approved implementation plan.

## Phase Progress
"""
        
        # Add phase checkboxes
        for phase_id, phase_info in self.phases.items():
            header += f"- [ ] {phase_id}: {phase_info['name']}\n"
            
        header += "\n## Current Status\n**Active Phase**: Starting\n"
        header += f"**Status**: INITIALIZING\n"
        header += f"**Last Updated**: {datetime.now().isoformat()}\n\n"
        header += "## What's Next Task List\nInitializing...\n\n"
        header += "## Detailed Progress\n\n"
        
        self._write_diary(header)
        
    def _write_diary(self, content: str):
        """Write content to diary file in Google Drive"""
        self.drive_service.write_file(
            self.diary_filename,
            content.encode('utf-8'),
            'project_documentation',
            mime_type='text/markdown'
        )
        
    def _update_diary(self):
        """Update the diary with current state"""
        content = f"""# {self.diary_filename.replace('.md', '')}

**Document**: Change Diary
**Implementation ID**: {self.implementation_id}
**Related Implementation Plan**: {self.plan_name}
**Date Created**: {self.start_time.strftime("%Y-%m-%d")}
**Author**: Trading System Development Team

## Implementation Summary
Automated update process executing approved implementation plan.

## Phase Progress
"""
        
        # Update phase checkboxes
        for phase_id, phase_info in self.phases.items():
            status = phase_info.get('status', 'PENDING')
            checkbox = "[x]" if status in ['COMPLETE', 'COMPLETED'] else "[ ]"
            content += f"- {checkbox} {phase_id}: {phase_info['name']}"
            if status not in ['PENDING', 'COMPLETE', 'COMPLETED']:
                content += f" ({status})"
            content += "\n"
            
        # Current status
        content += f"\n## Current Status\n"
        content += f"**Active Phase**: {self.current_phase or 'None'}\n"
        content += f"**Status**: {self._get_overall_status()}\n"
        content += f"**Last Updated**: {datetime.now().isoformat()}\n"
        content += f"**Duration**: {(datetime.now() - self.start_time).total_seconds():.1f} seconds\n\n"
        
        # Add What's Next Task List
        content += "## What's Next Task List\n"
        content += self.last_task_list + "\n\n"
        
        # Detailed progress
        content += "## Detailed Progress\n\n"
        content += "\n".join(self.detailed_progress)
        
        self._write_diary(content)
    
    def start_phase(self, phase_name: str, metadata: Optional[Dict] = None):
        """Start a new phase"""
        self.current_phase = phase_name
        
        # Update phase status
        for phase_key, phase_info in self.phases.items():
            if phase_info['name'] == phase_name or phase_name in phase_key:
                self.phases[phase_key]['status'] = 'IN_PROGRESS'
                self.phases[phase_key]['start_time'] = datetime.now().isoformat()
                break
                
        # Store metadata
        if metadata:
            self.phase_metadata[phase_name] = metadata
            
        # Add to detailed progress
        entry = f"### {phase_name}\n"
        entry += f"**Started**: {datetime.now().isoformat()}\n"
        entry += f"**Status**: IN PROGRESS\n"
        
        if metadata:
            for key, value in metadata.items():
                entry += f"**{key.replace('_', ' ').title()}**: {value}\n"
                
        self.detailed_progress.append(entry)
        self._update_diary()
        
    def complete_phase(self, phase_name: str, status: str, message: str, 
                      context: Optional[Dict] = None):
        """Complete a phase with status"""
        # Update phase status
        for phase_key, phase_info in self.phases.items():
            if phase_info['name'] == phase_name or phase_name in phase_key:
                self.phases[phase_key]['status'] = status
                self.phases[phase_key]['end_time'] = datetime.now().isoformat()
                self.phases[phase_key]['message'] = message
                
        # Find the last entry for this phase and update it
        for i in range(len(self.detailed_progress) - 1, -1, -1):
            if phase_name in self.detailed_progress[i]:
                self.detailed_progress[i] += f"\n**Completed**: {datetime.now().isoformat()}\n"
                self.detailed_progress[i] += f"**Final Status**: {status}\n"
                self.detailed_progress[i] += f"**Message**: {message}\n"
                break
                
        # Generate What's Next Task List
        task_context = context or {}
        task_context['error'] = message if status == 'FAILED' else None
        self.last_task_list = WhatsNextTaskList.generate(phase_name, status, task_context)
        
        self._update_diary()
        
    def _get_overall_status(self) -> str:
        """Determine overall implementation status"""
        if all(p.get('status') in ['COMPLETE', 'COMPLETED'] for p in self.phases.values()):
            return 'COMPLETE'
        elif any(p.get('status') == 'FAILED' for p in self.phases.values()):
            return 'FAILED'
        elif any(p.get('status') == 'ROLLED_BACK' for p in self.phases.values()):
            return 'ROLLED_BACK'
        else:
            return 'IN_PROGRESS'


class TradingSystemUpdater:
    """Enhanced automated update process with Google Drive integration"""
    
    def __init__(self, implementation_plan: ImplementationPlan):
        self.plan = implementation_plan
        self.drive_service = get_drive_service()
        self.logger = logging.getLogger('TradingSystemUpdater')
        
        # Setup logging
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Service mapping for correct target names
        self.service_mapping = {
            'coordination': 'coordination_service.py',
            'security_scanner': 'security_scanner.py',
            'pattern_analysis': 'pattern_analysis.py',
            'technical_analysis': 'technical_analysis.py',
            'paper_trading': 'paper_trading.py',
            'pattern_recognition': 'pattern_recognition_service.py',
            'news_service': 'news_service.py',
            'reporting': 'reporting_service.py',
            'web_dashboard': 'web_dashboard.py',
            'database_migration': 'database_migration.py',
            'diagnostic_toolkit': 'diagnostic_toolkit.py',
            'hybrid_manager': 'hybrid_manager.py'
        }
        
        # Initialize Change Diary
        self.diary = ChangeManagementDiary(
            implementation_plan.implementation_id,
            implementation_plan.plan_name,
            self.drive_service
        )
        
        self.logger.info(f"✅ Initialized updater for Implementation ID: {self.plan.implementation_id}")
        
    def load_state(self) -> Optional[Dict]:
        """Load saved state from Google Drive"""
        return self.drive_service.load_json('.update_state.json', 'coordination')
        
    def save_state(self, phase: str, status: str):
        """Save current state to Google Drive"""
        state = {
            'implementation_id': self.plan.implementation_id,
            'plan_name': self.plan.plan_name,
            'current_phase': phase,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        self.drive_service.save_json('.update_state.json', state, 'coordination')
        
    def execute_update(self, continue_from: Optional[str] = None) -> bool:
        """Execute the complete update process"""
        try:
            self.logger.info(f"🚀 Starting update process for: {self.plan.implementation_id}")
            
            # Define phases
            phases = [
                ("Discovery", self._discover_updates),
                ("Documentation", self._document_changes),
                ("Preparation", self._prepare_system),
                ("Implementation", self._implement_updates),
                ("Testing", self._test_system),
                ("Completion", self._complete_update)
            ]
            
            # Determine starting point
            start_index = 0
            if continue_from:
                for i, (phase_name, _) in enumerate(phases):
                    if phase_name == continue_from:
                        start_index = i
                        break
                        
            # Execute phases
            context = {}
            for phase_name, phase_func in phases[start_index:]:
                self.save_state(phase_name, "IN_PROGRESS")
                
                try:
                    result = phase_func(context)
                    if not result.get('success', False):
                        # Phase failed
                        self.diary.complete_phase(phase_name, "FAILED", 
                                                result.get('error', 'Unknown error'),
                                                context)
                        self.save_state(phase_name, "FAILED")
                        return False
                        
                    # Phase succeeded
                    self.diary.complete_phase(phase_name, "COMPLETED", 
                                            result.get('message', 'Success'),
                                            context)
                    self.save_state(phase_name, "COMPLETED")
                    
                    # Update context for next phase
                    context.update(result.get('context', {}))
                    
                except Exception as e:
                    self.logger.error(f"Phase {phase_name} failed: {str(e)}")
                    self.diary.complete_phase(phase_name, "FAILED", str(e), context)
                    self.save_state(phase_name, "FAILED")
                    return False
                    
            # All phases completed
            self.diary.complete_phase("Update Process", "COMPLETED", 
                                    "All phases completed successfully")
            self.drive_service.delete_file('.update_state.json', 'coordination')
            return True
            
        except Exception as e:
            self.logger.error(f"Update process failed: {str(e)}")
            self.diary.complete_phase("Error", "FAILED", str(e))
            return False
            
    def _discover_updates(self, context: Dict) -> Dict:
        """Phase 1: Discover available updates"""
        self.diary.start_phase("Phase 1: Discovery and Verification")
        
        updates = []
        
        # Check updates folder in Google Drive
        update_files = self.drive_service.list_files('updates')
        
        # Also check for files specified in implementation plan
        if self.plan.files_to_update:
            # Look for these specific files
            for file_info in self.plan.files_to_update:
                filename = file_info['filename']
                
                # Check in updates folder
                found = False
                for update_file in update_files:
                    if update_file['name'] == filename:
                        updates.append({
                            'filename': filename,
                            'target': file_info['target'],
                            'file_id': update_file['id'],
                            'size': update_file.get('size', 0),
                            'modified': update_file.get('modifiedTime')
                        })
                        found = True
                        break
                
                if not found:
                    self.logger.warning(f"Update file not found: {filename}")
        else:
            # Auto-discover Python files in updates folder
            for update_file in update_files:
                if update_file['name'].endswith('.py'):
                    target = self._determine_target_name(update_file['name'])
                    updates.append({
                        'filename': update_file['name'],
                        'target': target,
                        'file_id': update_file['id'],
                        'size': update_file.get('size', 0),
                        'modified': update_file.get('modifiedTime')
                    })
        
        if not updates:
            return {
                'success': False,
                'error': 'No updates found in Google Drive updates folder'
            }
        
        self.diary.start_phase("Phase 1: Discovery and Verification", {
            'update_count': len(updates),
            'update_files': [u['filename'] for u in updates]
        })
        
        self.logger.info(f"✅ Discovered {len(updates)} updates")
        
        return {
            'success': True,
            'message': f"Found {len(updates)} updates",
            'context': {
                'updates': updates,
                'update_count': len(updates)
            }
        }
        
    def _determine_target_name(self, source_filename: str) -> str:
        """Remove version suffix from filename"""
        import re
        base_name = re.sub(r'_v\d+', '', source_filename.replace('.py', ''))
        
        # Map to correct service name
        for service_key, target_name in self.service_mapping.items():
            if base_name in service_key:
                return target_name
                
        # Default: just remove version
        return base_name + '.py'
        
    def _document_changes(self, context: Dict) -> Dict:
        """Phase 2: Create change management documentation"""
        updates = context.get('updates', [])
        
        self.diary.start_phase("Phase 2: Change Management Documentation", {
            'files_to_update': len(updates),
            'update_list': [u['filename'] for u in updates]
        })
        
        # Analyze impact based on implementation plan
        impact_analysis = {
            'risk_level': self.plan.risk_level,
            'expected_downtime': f"{len(updates) * 30} seconds",
            'services_affected': len(updates),
            'database_changes': any('database' in u['filename'] for u in updates),
            'api_changes': any('api' in u['filename'] or 'service' in u['filename'] for u in updates)
        }
        
        self.logger.info(f"Impact Analysis: {impact_analysis}")
        
        return {
            'success': True,
            'message': f"Documented {len(updates)} changes, Risk Level: {impact_analysis['risk_level']}",
            'context': {'impact_analysis': impact_analysis}
        }
        
    def _prepare_system(self, context: Dict) -> Dict:
        """Phase 3: Prepare system for update"""
        self.diary.start_phase("Phase 3: Pre-Update Preparation")
        
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{self.plan.implementation_id}_{timestamp}"
        
        try:
            # Get list of all service files
            service_files = []
            main_files = self.drive_service.list_files()
            
            for file in main_files:
                if file['name'].endswith('.py') and any(
                    svc in file['name'] for svc in ['service', 'manager', 'toolkit', 'migration']
                ):
                    service_files.append(file)
            
            # Create backup folder and copy files
            backup_folder_id = self.drive_service._find_or_create_folder(
                backup_name,
                self.drive_service.get_subfolder_id('backups')
            )
            
            # Copy each service file to backup
            for file_info in service_files:
                try:
                    copy_metadata = {
                        'name': file_info['name'],
                        'parents': [backup_folder_id]
                    }
                    self.drive_service.service.files().copy(
                        fileId=file_info['id'],
                        body=copy_metadata
                    ).execute()
                except Exception as e:
                    self.logger.warning(f"Failed to backup {file_info['name']}: {e}")
            
            self.logger.info(f"✅ Created backup: {backup_name}")
            
            # Stop running services (simulate)
            self.logger.info("Stopping services...")
            
            return {
                'success': True,
                'message': f"System prepared, backup created: {backup_name}",
                'context': {
                    'backup_name': backup_name,
                    'backup_path': f"backups/{backup_name}",
                    'files_backed_up': len(service_files)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Preparation failed: {str(e)}"
            }
            
    def _implement_updates(self, context: Dict) -> Dict:
        """Phase 4: Apply updates to system"""
        self.diary.start_phase("Phase 4: Implementation")
        
        updates = context.get('updates', [])
        applied_updates = []
        
        try:
            for update in updates:
                # Read update file from updates folder
                update_content = self.drive_service.read_file(
                    update['filename'], 
                    'updates'
                )
                
                # Write to main directory (replacing existing)
                self.drive_service.write_file(
                    update['target'],
                    update_content,
                    None,  # Main directory
                    mime_type='text/x-python'
                )
                
                self.logger.info(f"✅ Applied: {update['filename']} → {update['target']}")
                
                applied_updates.append({
                    'source': update['filename'],
                    'target': update['target'],
                    'timestamp': datetime.now().isoformat()
                })
                
            return {
                'success': True,
                'message': f"Applied {len(applied_updates)} updates",
                'context': {
                    'applied_updates': applied_updates,
                    'applied_count': len(applied_updates)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Implementation failed: {str(e)}"
            }
            
    def _test_system(self, context: Dict) -> Dict:
        """Phase 5: Test the updated system"""
        self.diary.start_phase("Phase 5: Testing and Validation")
        
        test_results = []
        all_passed = True
        
        # Run basic validation tests
        tests = [
            ('File Integrity', self._test_file_integrity),
            ('Python Syntax', self._test_python_syntax),
            ('Service Dependencies', self._test_dependencies),
            ('Database Connectivity', self._test_database)
        ]
        
        for test_name, test_func in tests:
            try:
                passed, message = test_func(context)
                test_results.append({
                    'test': test_name,
                    'passed': passed,
                    'message': message
                })
                
                if passed:
                    self.logger.info(f"✅ {test_name}: {message}")
                else:
                    self.logger.error(f"❌ {test_name}: {message}")
                    all_passed = False
                    
            except Exception as e:
                test_results.append({
                    'test': test_name,
                    'passed': False,
                    'message': f"Exception: {str(e)}"
                })
                all_passed = False
        
        if not all_passed:
            return {
                'success': False,
                'error': 'One or more tests failed',
                'context': {'test_results': test_results}
            }
            
        return {
            'success': True,
            'message': f"All {len(test_results)} tests passed",
            'context': {'test_results': test_results}
        }
        
    def _test_file_integrity(self, context: Dict) -> Tuple[bool, str]:
        """Test that all updated files exist"""
        applied_updates = context.get('applied_updates', [])
        
        for update in applied_updates:
            file_id = self.drive_service._find_file(update['target'])
            if not file_id:
                return False, f"File not found: {update['target']}"
        
        return True, f"All {len(applied_updates)} files verified"
        
    def _test_python_syntax(self, context: Dict) -> Tuple[bool, str]:
        """Test Python syntax of updated files"""
        applied_updates = context.get('applied_updates', [])
        
        for update in applied_updates:
            if update['target'].endswith('.py'):
                try:
                    content = self.drive_service.read_file(update['target'])
                    compile(content, update['target'], 'exec')
                except SyntaxError as e:
                    return False, f"Syntax error in {update['target']}: {e}"
                except Exception as e:
                    return False, f"Error checking {update['target']}: {e}"
        
        return True, "All Python files have valid syntax"
        
    def _test_dependencies(self, context: Dict) -> Tuple[bool, str]:
        """Test that required dependencies are available"""
        try:
            required = ['flask', 'requests', 'pandas', 'numpy', 'googleapiclient']
            missing = []
            
            for module in required:
                try:
                    __import__(module.split('.')[0])
                except ImportError:
                    missing.append(module)
            
            if missing:
                return False, f"Missing dependencies: {', '.join(missing)}"
                
            return True, "All dependencies available"
            
        except Exception as e:
            return False, f"Dependency check failed: {str(e)}"
        
    def _test_database(self, context: Dict) -> Tuple[bool, str]:
        """Test database connectivity"""
        try:
            db_info = self.drive_service.get_database_info()
            if db_info['exists']:
                return True, f"Database exists: {db_info['size']} bytes"
            else:
                return False, "Database not found"
        except Exception as e:
            return False, f"Database check failed: {str(e)}"
            
    def _complete_update(self, context: Dict) -> Dict:
        """Phase 6: Complete the update process"""
        self.diary.start_phase("Phase 6: Completion")
        
        # Archive processed update files
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_folder = f"archive_{self.plan.implementation_id}_{timestamp}"
            
            # Create archive folder
            archive_folder_id = self.drive_service._find_or_create_folder(
                archive_folder,
                self.drive_service.get_subfolder_id('updates')
            )
            
            # Move update files to archive
            updates = context.get('updates', [])
            for update in updates:
                try:
                    # Move file to archive folder
                    self.drive_service.service.files().update(
                        fileId=update['file_id'],
                        addParents=archive_folder_id,
                        removeParents=self.drive_service.get_subfolder_id('updates')
                    ).execute()
                except Exception as e:
                    self.logger.warning(f"Failed to archive {update['filename']}: {e}")
            
            # Update system version info
            version_info = {
                'last_update': datetime.now().isoformat(),
                'implementation_id': self.plan.implementation_id,
                'applied_updates': context.get('applied_updates', []),
                'update_count': len(context.get('applied_updates', [])),
                'archive_folder': archive_folder
            }
            
            self.drive_service.save_json(
                'last_update_info.json',
                version_info,
                'coordination'
            )
            
            self.logger.info(f"✅ Update process completed, files archived to: {archive_folder}")
            
            return {
                'success': True,
                'message': 'Update process completed successfully',
                'context': {
                    'archive_folder': archive_folder,
                    'completion_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Completion failed: {str(e)}'
            }
            
    def rollback(self, backup_name: str) -> bool:
        """Rollback to a previous backup"""
        try:
            self.logger.info(f"🔄 Starting rollback to: {backup_name}")
            
            # Find backup folder
            backup_files = self.drive_service.list_files('backups')
            backup_folder = None
            
            for file in backup_files:
                if file['name'] == backup_name and file['mimeType'] == 'application/vnd.google-apps.folder':
                    backup_folder = file
                    break
            
            if not backup_folder:
                self.logger.error(f"Backup not found: {backup_name}")
                return False
            
            # List files in backup
            backup_contents = self.drive_service.service.files().list(
                q=f"parents in '{backup_folder['id']}' and trashed=false",
                fields="files(id, name)"
            ).execute().get('files', [])
            
            # Restore each file
            for file_info in backup_contents:
                try:
                    # Read backup file
                    request = self.drive_service.service.files().get_media(
                        fileId=file_info['id']
                    )
                    content = io.BytesIO()
                    downloader = MediaIoBaseDownload(content, request)
                    
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                    
                    # Write to main directory
                    self.drive_service.write_file(
                        file_info['name'],
                        content.getvalue(),
                        None,  # Main directory
                        mime_type='text/x-python'
                    )
                    
                    self.logger.info(f"✅ Restored: {file_info['name']}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to restore {file_info['name']}: {e}")
            
            self.logger.info("✅ Rollback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False


def main():
    """Main entry point with enhanced command line interface"""
    # Detect if running in Jupyter/Colab
    in_jupyter = 'ipykernel' in sys.modules
    python_cmd = "!python" if in_jupyter else "python"
    
    parser = argparse.ArgumentParser(
        description='Trading System Automated Update Process v2.0.1',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Execute an implementation plan
  {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --plan "Implementation Plan - NEWS-FIX - 2025-06-19.md"
  
  # Continue from interruption
  {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --continue
  
  # Check current status
  {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --status
  
  # Rollback failed implementation
  {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --rollback
  
  # Check for updates only
  {python_cmd} TRADING_SYSTEM_AUTOMATED_UPDATE_PROCESS.py --check-only
        """
    )
    
    parser.add_argument('--plan', type=str, 
                       help='Execute specified implementation plan')
    parser.add_argument('--continue', action='store_true',
                       help='Continue from last checkpoint')
    parser.add_argument('--status', action='store_true',
                       help='Check current implementation status')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback to previous state')
    parser.add_argument('--check-only', action='store_true',
                       help='Check for updates without applying')
    parser.add_argument('--retry', action='store_true',
                       help='Retry the last failed phase')
    
    # Use parse_known_args for Jupyter compatibility
    args, unknown = parser.parse_known_args()
    
    try:
        # Initialize Google Drive service
        drive_service = get_drive_service()
        
        # Handle different command options
        if args.status:
            # Check status
            state = drive_service.load_json('.update_state.json', 'coordination')
            if state:
                print(f"\n📊 IMPLEMENTATION STATUS")
                print(f"   Implementation ID: {state['implementation_id']}")
                print(f"   Plan: {state['plan_name']}")
                print(f"   Current Phase: {state['current_phase']}")
                print(f"   Status: {state['status']}")
                print(f"   Last Updated: {state['timestamp']}")
            else:
                print("ℹ️ No implementation currently in progress")
                
        elif args.check_only:
            # Check for updates
            print("🔍 Checking for updates in Google Drive...")
            updates = drive_service.list_files('updates')
            python_updates = [f for f in updates if f['name'].endswith('.py')]
            
            if python_updates:
                print(f"\n📦 Found {len(python_updates)} updates:")
                for update in python_updates:
                    print(f"   - {update['name']} ({update.get('size', 0)} bytes)")
            else:
                print("✅ No updates found")
                
        elif args.plan:
            # Execute implementation plan
            print(f"📋 Loading implementation plan: {args.plan}")
            
            # Load plan from Google Drive
            plan_content = drive_service.read_file(args.plan, 'project_documentation')
            if not plan_content:
                print(f"❌ Implementation plan not found: {args.plan}")
                sys.exit(1)
                
            plan = ImplementationPlan.from_drive_content(
                args.plan,
                plan_content.decode('utf-8')
            )
            
            print(f"✅ Loaded plan: {plan.implementation_id}")
            
            # Execute update
            updater = TradingSystemUpdater(plan)
            success = updater.execute_update()
            
            sys.exit(0 if success else 1)
            
        elif args.continue or args.retry:
            # Continue or retry from saved state
            state = drive_service.load_json('.update_state.json', 'coordination')
            if not state:
                print("❌ No implementation in progress to continue")
                sys.exit(1)
                
            # Reload implementation plan
            plan_content = drive_service.read_file(state['plan_name'], 'project_documentation')
            if not plan_content:
                print(f"❌ Original plan not found: {state['plan_name']}")
                sys.exit(1)
                
            plan = ImplementationPlan.from_drive_content(
                state['plan_name'],
                plan_content.decode('utf-8')
            )
            
            print(f"✅ Resuming implementation: {plan.implementation_id}")
            
            # Continue from saved phase
            updater = TradingSystemUpdater(plan)
            
            if args.retry and state['status'] == 'FAILED':
                # Retry the failed phase
                success = updater.execute_update(continue_from=state['current_phase'])
            else:
                # Continue from next phase
                phases = ["Discovery", "Documentation", "Preparation", 
                         "Implementation", "Testing", "Completion"]
                current_index = phases.index(state['current_phase'])
                if current_index < len(phases) - 1:
                    success = updater.execute_update(continue_from=phases[current_index + 1])
                else:
                    print("✅ Implementation already completed")
                    success = True
                    
            sys.exit(0 if success else 1)
            
        elif args.rollback:
            # Rollback implementation
            state = drive_service.load_json('.update_state.json', 'coordination')
            if not state:
                print("❌ No implementation in progress to rollback")
                # Check for recent backups
                backups = drive_service.list_files('backups')
                if backups:
                    print("\n📁 Available backups:")
                    for backup in backups[:5]:  # Show last 5
                        print(f"   - {backup['name']}")
                sys.exit(1)
                
            # Find backup for this implementation
            backup_prefix = f"backup_{state['implementation_id']}_"
            backups = drive_service.list_files('backups')
            matching_backup = None
            
            for backup in backups:
                if backup['name'].startswith(backup_prefix):
                    matching_backup = backup['name']
                    break
                    
            if not matching_backup:
                print(f"❌ No backup found for implementation: {state['implementation_id']}")
                sys.exit(1)
                
            print(f"🔄 Rolling back to: {matching_backup}")
            
            # Create minimal updater for rollback
            plan = ImplementationPlan(
                implementation_id=state['implementation_id'],
                plan_name=state['plan_name'],
                date_created=datetime.now().strftime("%Y-%m-%d"),
                phases=[],
                files_to_update=[]
            )
            
            updater = TradingSystemUpdater(plan)
            success = updater.rollback(matching_backup)
            
            if success:
                # Clear state
                drive_service.delete_file('.update_state.json', 'coordination')
                print("✅ Rollback completed successfully")
            else:
                print("❌ Rollback failed")
                
            sys.exit(0 if success else 1)
            
        else:
            # No arguments - show help
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

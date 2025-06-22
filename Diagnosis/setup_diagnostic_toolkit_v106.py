#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM DIAGNOSTIC TOOLKIT SETUP - ENHANCED VERSION
Version: 1.0.6
Last Updated: 2025-06-19
REVISION HISTORY:
v1.0.6 (2025-06-19) - Enhanced with automatic report generation, better analysis display, and quick issue detection
v1.0.5 (2025-06-17) - Incorporated v1.0.3 Jupyter/Colab notebook execution fix + v1.0.4 report generation fixes
v1.0.4 (2025-06-17) - Fixed report generation feedback and verification
v1.0.3 (2025-06-17) - Enhanced error handling and path detection + Fixed Jupyter/Colab notebook execution error
v1.0.2 (2025-06-17) - Initial setup script for diagnostic toolkit
v1.0.1 (2025-06-17) - Fixed import paths for Google Drive deployment
v1.0.0 (2025-06-17) - Initial diagnostic toolkit orchestrator

This enhanced version:
1. Automatically runs with report generation
2. Displays key findings immediately
3. Provides quick access to common troubleshooting tasks
4. Shows real-time analysis of critical issues
"""

import os
import sys
import shutil
import subprocess
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

# Configuration
GOOGLE_DRIVE_SOURCE = '/content/drive/MyDrive/Business/Trade/software/Code/Diagnosis'
COLAB_DIAGNOSTIC_DIR = '/content/diagnostic_toolkit'
COLAB_TRADING_DIR = '/content/trading_system'
REPORTS_DIR = '/content/diagnostic_reports'

# Diagnostic files to copy
DIAGNOSTIC_FILES = [
    'diagnostic_toolkit.py',
    'diagnostic_service_integration.py',
    'diagnostic_log_analysis.py',
    'diagnostic_process_ports.py'
]

# Required Python packages for diagnostics
REQUIRED_PACKAGES = [
    'psutil',
    'tabulate',
    'requests'
]

# ANSI color codes for better output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_banner():
    """Print enhanced setup banner"""
    banner = f"""
{Colors.HEADER}╔════════════════════════════════════════════════════════════╗
║     TRADING SYSTEM DIAGNOSTIC TOOLKIT v1.0.6 - ENHANCED    ║
║                                                            ║
║  Features:                                                 ║
║  • Automatic report generation                             ║
║  • Real-time issue detection                              ║
║  • Quick troubleshooting options                          ║
║  • Enhanced analysis display                              ║
╚════════════════════════════════════════════════════════════╝{Colors.ENDC}
    """
    print(banner)

def mount_google_drive():
    """Mount Google Drive in Colab"""
    print(f"\n{Colors.OKBLUE}📁 Mounting Google Drive...{Colors.ENDC}")
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=False)
        print(f"{Colors.OKGREEN}✅ Google Drive mounted successfully{Colors.ENDC}")
        return True
    except ImportError:
        print(f"{Colors.FAIL}❌ Not running in Google Colab environment{Colors.ENDC}")
        return False
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error mounting Google Drive: {str(e)}{Colors.ENDC}")
        return False

def create_directory_structure():
    """Create required directories"""
    print(f"\n{Colors.OKBLUE}📂 Creating directory structure...{Colors.ENDC}")
    
    directories = [
        COLAB_DIAGNOSTIC_DIR,
        REPORTS_DIR,
        '/content/logs'
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {directory}")
        except Exception as e:
            print(f"  {Colors.FAIL}✗ Error creating {directory}: {str(e)}{Colors.ENDC}")

def copy_diagnostic_files():
    """Copy diagnostic files from Google Drive to Colab"""
    print(f"\n{Colors.OKBLUE}📋 Copying diagnostic files from Google Drive...{Colors.ENDC}")
    
    # Check both possible path formats
    possible_paths = [
        Path(GOOGLE_DRIVE_SOURCE),
        Path('/content/drive/My Drive/Business/Trade/software/Code/Diagnosis')
    ]
    
    source_path = None
    for path in possible_paths:
        if path.exists():
            source_path = path
            break
    
    if source_path is None:
        print(f"{Colors.FAIL}❌ Source directory not found{Colors.ENDC}")
        return False
    
    print(f"{Colors.OKGREEN}✅ Found source directory: {source_path}{Colors.ENDC}")
    
    copied_count = 0
    for file_name in DIAGNOSTIC_FILES:
        source_file = source_path / file_name
        dest_path = Path(COLAB_DIAGNOSTIC_DIR) / file_name
        
        if source_file.exists():
            try:
                shutil.copy2(source_file, dest_path)
                print(f"  ✓ Copied: {file_name}")
                copied_count += 1
            except Exception as e:
                print(f"  {Colors.FAIL}✗ Error copying {file_name}: {str(e)}{Colors.ENDC}")
        else:
            print(f"  {Colors.WARNING}⚠ Not found: {file_name}{Colors.ENDC}")
    
    print(f"\n📊 Copied {copied_count}/{len(DIAGNOSTIC_FILES)} files")
    return copied_count > 0

def install_dependencies():
    """Install required Python packages"""
    print(f"\n{Colors.OKBLUE}📦 Installing diagnostic dependencies...{Colors.ENDC}")
    
    for package in REQUIRED_PACKAGES:
        print(f"  Installing {package}...", end='', flush=True)
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', package], 
                         check=True, capture_output=True)
            print(" ✓")
        except subprocess.CalledProcessError:
            print(f" {Colors.FAIL}✗{Colors.ENDC}")

def run_diagnostic_with_analysis(args):
    """Run diagnostic and analyze results"""
    print(f"\n{Colors.HEADER}🏥 Running Comprehensive Diagnostic...{Colors.ENDC}")
    print("=" * 70)
    
    try:
        os.chdir(COLAB_DIAGNOSTIC_DIR)
        
        # Always run with report generation
        cmd = [sys.executable, 'diagnostic_toolkit.py', '--report']
        
        # Add additional arguments if specified
        if args.quick:
            cmd.append('--quick')
        if args.service:
            cmd.extend(['--service', args.service])
        if args.errors_only:
            cmd.append('--errors-only')
        if args.last_minutes:
            cmd.extend(['--last-minutes', str(args.last_minutes)])
        
        # Run diagnostic
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Display output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"{Colors.FAIL}{result.stderr}{Colors.ENDC}")
        
        # Analyze results
        if result.returncode == 0:
            print(f"\n{Colors.OKGREEN}✅ Diagnostic completed successfully!{Colors.ENDC}")
            return analyze_diagnostic_results()
        else:
            print(f"\n{Colors.FAIL}❌ Diagnostic failed with return code: {result.returncode}{Colors.ENDC}")
            return False
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error running diagnostic: {str(e)}{Colors.ENDC}")
        return False

def analyze_diagnostic_results():
    """Analyze the generated diagnostic results"""
    print(f"\n{Colors.HEADER}📊 Analyzing Diagnostic Results...{Colors.ENDC}")
    print("-" * 50)
    
    # Find the latest JSON report
    reports_dir = Path(REPORTS_DIR)
    json_reports = list(reports_dir.glob('trading_system_diagnostic_*.json'))
    
    if not json_reports:
        print(f"{Colors.FAIL}❌ No diagnostic reports found{Colors.ENDC}")
        return False
    
    latest_report = max(json_reports, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest_report, 'r') as f:
            data = json.load(f)
        
        # Extract key information
        comprehensive = data.get('comprehensive_analysis', {})
        process_analysis = data.get('process_analysis', {})
        log_analysis = data.get('log_analysis', {})
        
        # Overall health
        overall_health = comprehensive.get('overall_system_health', 'unknown')
        system_score = comprehensive.get('system_scores', {}).get('overall', 0)
        
        # Color code the health status
        if overall_health == 'excellent':
            health_color = Colors.OKGREEN
        elif overall_health == 'good':
            health_color = Colors.OKCYAN
        elif overall_health == 'fair':
            health_color = Colors.WARNING
        else:
            health_color = Colors.FAIL
        
        print(f"\n{Colors.BOLD}System Health Summary:{Colors.ENDC}")
        print(f"  Overall Health: {health_color}{overall_health.upper()}{Colors.ENDC} ({system_score:.0f}/100)")
        
        # Service status
        services_total = process_analysis.get('services_total', 0)
        services_responding = process_analysis.get('services_responding', 0)
        print(f"  Services Responding: {services_responding}/{services_total}")
        
        # Critical issues
        critical_issues = comprehensive.get('critical_issues', [])
        if critical_issues:
            print(f"\n{Colors.FAIL}🚨 Critical Issues Found:{Colors.ENDC}")
            for issue in critical_issues:
                print(f"     • {issue}")
        
        # Log errors
        total_errors = log_analysis.get('summary', {}).get('total_errors', 0)
        if total_errors > 0:
            print(f"\n{Colors.WARNING}⚠️  Log Errors: {total_errors} errors detected{Colors.ENDC}")
            
            # Show top error services
            service_analyses = log_analysis.get('service_analyses', {})
            error_services = []
            for service, analysis in service_analyses.items():
                error_count = analysis.get('error_counts', {}).get('error', 0)
                if error_count > 0:
                    error_services.append((service, error_count))
            
            if error_services:
                error_services.sort(key=lambda x: x[1], reverse=True)
                print("     Top error services:")
                for service, count in error_services[:3]:
                    print(f"       - {service}: {count} errors")
        
        # Recommendations
        recommendations = comprehensive.get('recommendations', [])
        if recommendations:
            print(f"\n{Colors.OKBLUE}💡 Recommendations:{Colors.ENDC}")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"     {i}. {rec}")
        
        # Report location
        print(f"\n{Colors.OKGREEN}📄 Full Reports Generated:{Colors.ENDC}")
        print(f"     • HTML Report: {reports_dir}/diagnostic_report_latest.html")
        print(f"     • JSON Data: {latest_report.name}")
        
        # Quick actions based on findings
        print(f"\n{Colors.HEADER}🔧 Quick Actions:{Colors.ENDC}")
        
        if total_errors > 0 and 'database is locked' in str(data):
            print(f"     1. {Colors.WARNING}Database locking detected{Colors.ENDC} - Run: fix_database_locking()")
        
        if 'pattern analysis' in str(critical_issues).lower():
            print(f"     2. {Colors.WARNING}Pattern analysis issues{Colors.ENDC} - Run: check_pattern_service()")
        
        if total_errors > 10:
            print(f"     3. {Colors.WARNING}High error count{Colors.ENDC} - Run: analyze_service_logs()")
        
        return True
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error analyzing results: {str(e)}{Colors.ENDC}")
        return False

def show_quick_commands():
    """Display quick diagnostic commands"""
    print(f"\n{Colors.HEADER}📚 Quick Diagnostic Commands:{Colors.ENDC}")
    print("-" * 50)
    
    commands = [
        ("Full diagnostic with report", "!python setup_diagnostic_toolkit_v106.py"),
        ("Quick health check", "!python setup_diagnostic_toolkit_v106.py --quick"),
        ("Check specific service", "!python setup_diagnostic_toolkit_v106.py --service pattern"),
        ("Analyze recent logs only", "!python setup_diagnostic_toolkit_v106.py --last-minutes 5"),
        ("Show errors only", "!python setup_diagnostic_toolkit_v106.py --errors-only"),
    ]
    
    for desc, cmd in commands:
        print(f"  {desc:.<35} {Colors.OKCYAN}{cmd}{Colors.ENDC}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Enhanced Trading System Diagnostic Toolkit Setup',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Diagnostic options
    parser.add_argument('--quick', action='store_true', 
                       help='Quick health check (skip detailed analysis)')
    parser.add_argument('--service', 
                       help='Focus on specific service')
    parser.add_argument('--errors-only', action='store_true',
                       help='Show only errors in analysis')
    parser.add_argument('--last-minutes', type=int,
                       help='Analyze only last N minutes')
    
    # Setup options
    parser.add_argument('--skip-mount', action='store_true',
                       help='Skip Google Drive mounting')
    parser.add_argument('--skip-deps', action='store_true',
                       help='Skip dependency installation')
    parser.add_argument('--skip-copy', action='store_true',
                       help='Skip file copying (use existing files)')
    
    return parser.parse_args()

def main(args=None):
    """Main setup and execution function"""
    if args is None:
        args = parse_arguments()
    
    print_banner()
    
    # Setup steps
    if not args.skip_mount:
        if not mount_google_drive():
            print(f"\n{Colors.FAIL}❌ Setup failed: Could not mount Google Drive{Colors.ENDC}")
            return False
    
    create_directory_structure()
    
    if not args.skip_copy:
        if not copy_diagnostic_files():
            print(f"\n{Colors.FAIL}❌ Setup failed: Could not copy diagnostic files{Colors.ENDC}")
            return False
    
    if not args.skip_deps:
        install_dependencies()
    
    # Run diagnostic with analysis
    success = run_diagnostic_with_analysis(args)
    
    if success:
        show_quick_commands()
    
    return success

if __name__ == "__main__":
    # Check if running in notebook
    try:
        __IPYTHON__
        in_notebook = True
    except NameError:
        in_notebook = False
    
    if in_notebook:
        # Notebook execution - create simple args object
        class Args:
            def __init__(self):
                self.quick = False
                self.service = None
                self.errors_only = False
                self.last_minutes = None
                self.skip_mount = False
                self.skip_deps = False
                self.skip_copy = False
        
        args = Args()
        
        # Check if user wants quick mode
        print("🔧 Running Enhanced Diagnostic Toolkit Setup")
        print("\nOptions:")
        print("1. Full diagnostic (recommended)")
        print("2. Quick health check")
        print("3. Skip setup, run diagnostic only")
        
        choice = input("\nEnter choice (1-3) or press Enter for option 1: ").strip()
        
        if choice == "2":
            args.quick = True
        elif choice == "3":
            args.skip_mount = True
            args.skip_copy = True
            args.skip_deps = True
        
        success = main(args)
    else:
        # Command line execution
        success = main()
    
    if not success:
        sys.exit(1)

#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM DIAGNOSTIC - LOG ANALYSIS
Version: 1.0.0
Last Updated: 2025-06-17
REVISION HISTORY:
v1.0.0 (2025-06-17) - Initial diagnostic script for log analysis and error detection

USAGE: python diagnostic_log_analysis.py [--service SERVICE_NAME] [--errors-only] [--last-minutes N]
PURPOSE: Analyze service logs for errors, patterns, and performance issues
"""

import os
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class LogAnalysisDiagnostic:
    """Analyze trading system service logs for issues and patterns"""
    
    def __init__(self):
        self.log_dir = Path('/content/logs')
        self.log_files = {
            'coordination': 'coordination_service.log',
            'scanner': 'security_scanner.log',
            'pattern': 'pattern_analysis_service.log', 
            'technical': 'technical_analysis_service.log',
            'trading': 'paper_trading_service.log',
            'pattern_rec': 'pattern_recognition_service.log',
            'news': 'news_service.log',
            'reporting': 'reporting_service.log',
            'dashboard': 'web_dashboard_service.log'
        }
        
        # Error patterns to look for
        self.error_patterns = {
            'critical': [
                r'CRITICAL',
                r'FATAL',
                r'Exception.*not.*serializable',
                r'Connection refused',
                r'Database.*error',
                r'Failed to start'
            ],
            'error': [
                r'ERROR',
                r'Exception',
                r'Traceback',
                r'Failed',
                r'Could not',
                r'Unable to'
            ],
            'warning': [
                r'WARNING',
                r'WARN',
                r'deprecated',
                r'timeout',
                r'retry'
            ],
            'performance': [
                r'slow',
                r'timeout',
                r'took.*\d+.*seconds',
                r'response.*time.*\d+ms'
            ]
        }
    
    def run_full_analysis(self, service_filter: Optional[str] = None, 
                         errors_only: bool = False, 
                         last_minutes: Optional[int] = None) -> Dict:
        """Run complete log analysis"""
        print("📋 TRADING SYSTEM LOG ANALYSIS")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if service_filter:
            print(f"Service Filter: {service_filter}")
        if errors_only:
            print("Mode: Errors only")
        if last_minutes:
            print(f"Time Filter: Last {last_minutes} minutes")
        
        results = {}
        
        # 1. Check log file status
        file_status = self.check_log_files()
        results["file_status"] = file_status
        
        # 2. Analyze each service's logs
        service_analyses = {}
        services_to_analyze = [service_filter] if service_filter else self.log_files.keys()
        
        for service in services_to_analyze:
            if service in self.log_files:
                analysis = self.analyze_service_log(service, errors_only, last_minutes)
                service_analyses[service] = analysis
        
        results["service_analyses"] = service_analyses
        
        # 3. Cross-service analysis
        cross_analysis = self.cross_service_analysis(service_analyses)
        results["cross_analysis"] = cross_analysis
        
        # 4. Generate summary
        summary = self.generate_summary(results)
        results["summary"] = summary
        
        return results
    
    def check_log_files(self) -> Dict:
        """Check status of all log files"""
        print(f"\n📁 LOG FILE STATUS:")
        print("-" * 30)
        
        file_status = {}
        
        if not self.log_dir.exists():
            print("❌ Log directory does not exist!")
            return {"error": "Log directory missing"}
        
        for service, filename in self.log_files.items():
            log_path = self.log_dir / filename
            
            if log_path.exists():
                try:
                    stat = log_path.stat()
                    size_kb = stat.st_size / 1024
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    age_minutes = (datetime.now() - modified).total_seconds() / 60
                    
                    file_status[service] = {
                        "exists": True,
                        "size_kb": round(size_kb, 1),
                        "last_modified": modified.strftime('%Y-%m-%d %H:%M:%S'),
                        "age_minutes": round(age_minutes, 1)
                    }
                    
                    age_indicator = "🟢" if age_minutes < 5 else "🟡" if age_minutes < 60 else "🔴"
                    print(f"{age_indicator} {service:12}: {size_kb:6.1f}KB, {age_minutes:4.1f}min ago")
                
                except Exception as e:
                    file_status[service] = {"exists": True, "error": str(e)}
                    print(f"❌ {service:12}: Error reading file - {e}")
            
            else:
                file_status[service] = {"exists": False}
                print(f"❌ {service:12}: Log file not found")
        
        return file_status
    
    def analyze_service_log(self, service: str, errors_only: bool = False, 
                           last_minutes: Optional[int] = None) -> Dict:
        """Analyze a single service's log file"""
        log_path = self.log_dir / self.log_files[service]
        
        analysis = {
            "service": service,
            "log_file": str(log_path),
            "total_lines": 0,
            "error_counts": defaultdict(int),
            "recent_errors": [],
            "performance_issues": [],
            "patterns": defaultdict(int),
            "status": "unknown"
        }
        
        if not log_path.exists():
            analysis["status"] = "no_log_file"
            return analysis
        
        try:
            # Calculate time filter
            time_filter = None
            if last_minutes:
                time_filter = datetime.now() - timedelta(minutes=last_minutes)
            
            with open(log_path, 'r') as f:
                lines = f.readlines()
            
            analysis["total_lines"] = len(lines)
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Parse timestamp if available
                log_time = self.parse_log_timestamp(line)
                
                # Apply time filter
                if time_filter and log_time and log_time < time_filter:
                    continue
                
                # Skip non-error lines if errors_only is True
                if errors_only and not any(re.search(pattern, line, re.IGNORECASE) 
                                         for patterns in self.error_patterns.values() 
                                         for pattern in patterns):
                    continue
                
                # Categorize the line
                for category, patterns in self.error_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            analysis["error_counts"][category] += 1
                            
                            # Store recent critical errors and errors
                            if category in ['critical', 'error'] and len(analysis["recent_errors"]) < 10:
                                analysis["recent_errors"].append({
                                    "line_number": line_num,
                                    "timestamp": log_time.isoformat() if log_time else "unknown",
                                    "category": category,
                                    "message": line
                                })
                            
                            # Store performance issues
                            if category == 'performance' and len(analysis["performance_issues"]) < 5:
                                analysis["performance_issues"].append({
                                    "line_number": line_num,
                                    "timestamp": log_time.isoformat() if log_time else "unknown",
                                    "message": line
                                })
                            
                            break
                
                # Look for specific patterns
                if "JSON serializable" in line:
                    analysis["patterns"]["json_serialization_errors"] += 1
                elif "websockets" in line.lower():
                    analysis["patterns"]["websockets_issues"] += 1
                elif "alpaca" in line.lower():
                    analysis["patterns"]["alpaca_mentions"] += 1
                elif "yfinance" in line.lower():
                    analysis["patterns"]["yfinance_mentions"] += 1
            
            # Determine status
            if analysis["error_counts"]["critical"] > 0:
                analysis["status"] = "critical_errors"
            elif analysis["error_counts"]["error"] > 0:
                analysis["status"] = "errors_found" 
            elif analysis["error_counts"]["warning"] > 0:
                analysis["status"] = "warnings_only"
            else:
                analysis["status"] = "clean"
        
        except Exception as e:
            analysis["status"] = "analysis_error"
            analysis["error"] = str(e)
        
        return analysis
    
    def parse_log_timestamp(self, line: str) -> Optional[datetime]:
        """Parse timestamp from log line"""
        # Common log timestamp patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',  # 2025-06-17 14:30:45
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # 2025-06-17T14:30:45
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    timestamp_str = match.group(1)
                    if 'T' in timestamp_str:
                        return datetime.fromisoformat(timestamp_str)
                    else:
                        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    continue
        
        return None
    
    def cross_service_analysis(self, service_analyses: Dict) -> Dict:
        """Analyze patterns across services"""
        print(f"\n🔍 CROSS-SERVICE ANALYSIS:")
        print("-" * 35)
        
        cross_analysis = {
            "total_errors": 0,
            "total_warnings": 0,
            "common_issues": defaultdict(int),
            "error_correlation": {},
            "service_health_ranking": []
        }
        
        # Aggregate error counts
        for service, analysis in service_analyses.items():
            if "error_counts" in analysis:
                cross_analysis["total_errors"] += analysis["error_counts"].get("error", 0)
                cross_analysis["total_errors"] += analysis["error_counts"].get("critical", 0)
                cross_analysis["total_warnings"] += analysis["error_counts"].get("warning", 0)
        
        # Find common patterns
        for service, analysis in service_analyses.items():
            if "patterns" in analysis:
                for pattern, count in analysis["patterns"].items():
                    cross_analysis["common_issues"][pattern] += count
        
        # Rank services by health
        service_scores = []
        for service, analysis in service_analyses.items():
            if "error_counts" in analysis:
                error_score = (analysis["error_counts"].get("critical", 0) * 3 + 
                             analysis["error_counts"].get("error", 0) * 2 + 
                             analysis["error_counts"].get("warning", 0) * 1)
                service_scores.append((service, error_score, analysis["status"]))
        
        service_scores.sort(key=lambda x: x[1])  # Sort by error score (lower is better)
        cross_analysis["service_health_ranking"] = service_scores
        
        print(f"Total Errors: {cross_analysis['total_errors']}")
        print(f"Total Warnings: {cross_analysis['total_warnings']}")
        
        if cross_analysis["common_issues"]:
            print("Common Issues:")
            for issue, count in sorted(cross_analysis["common_issues"].items(), 
                                     key=lambda x: x[1], reverse=True):
                print(f"   {issue}: {count}")
        
        print("Service Health Ranking (best to worst):")
        for service, score, status in service_scores:
            status_icon = "✅" if status == "clean" else "⚠️" if status == "warnings_only" else "❌"
            print(f"   {status_icon} {service}: {status} (score: {score})")
        
        return cross_analysis
    
    def generate_summary(self, results: Dict) -> Dict:
        """Generate overall summary and recommendations"""
        print(f"\n📊 LOG ANALYSIS SUMMARY:")
        print("=" * 30)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "overall_log_health": "unknown",
            "services_analyzed": len(results.get("service_analyses", {})),
            "total_errors": results.get("cross_analysis", {}).get("total_errors", 0),
            "total_warnings": results.get("cross_analysis", {}).get("total_warnings", 0),
            "critical_issues": [],
            "recommendations": []
        }
        
        # Determine overall health
        total_errors = summary["total_errors"]
        total_warnings = summary["total_warnings"]
        
        if total_errors == 0 and total_warnings == 0:
            summary["overall_log_health"] = "excellent"
            print("🎉 LOG HEALTH: EXCELLENT (No errors or warnings)")
        elif total_errors == 0 and total_warnings < 5:
            summary["overall_log_health"] = "good"
            print(f"✅ LOG HEALTH: GOOD ({total_warnings} warnings only)")
        elif total_errors < 5:
            summary["overall_log_health"] = "fair"
            print(f"🟡 LOG HEALTH: FAIR ({total_errors} errors, {total_warnings} warnings)")
        else:
            summary["overall_log_health"] = "poor"
            print(f"❌ LOG HEALTH: POOR ({total_errors} errors, {total_warnings} warnings)")
        
        # Generate specific recommendations
        service_analyses = results.get("service_analyses", {})
        
        for service, analysis in service_analyses.items():
            if analysis.get("status") == "critical_errors":
                summary["critical_issues"].append(f"{service}_has_critical_errors")
                summary["recommendations"].append(f"Investigate {service} critical errors immediately")
            
            # Check for specific patterns
            patterns = analysis.get("patterns", {})
            if patterns.get("json_serialization_errors", 0) > 0:
                summary["critical_issues"].append(f"{service}_json_serialization_errors")
                summary["recommendations"].append(f"Fix JSON serialization in {service}")
            
            if patterns.get("websockets_issues", 0) > 0:
                summary["recommendations"].append(f"Check websockets dependency in {service}")
        
        # Common issues recommendations
        common_issues = results.get("cross_analysis", {}).get("common_issues", {})
        if common_issues.get("json_serialization_errors", 0) > 0:
            summary["recommendations"].append("Apply JSON serialization fix across services")
        
        if common_issues.get("websockets_issues", 0) > 0:
            summary["recommendations"].append("Apply websockets import fix across services")
        
        # Show top recommendations
        if summary["recommendations"]:
            print("Top Recommendations:")
            for i, rec in enumerate(summary["recommendations"][:3], 1):
                print(f"   {i}. {rec}")
        
        return summary

def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description='Analyze trading system logs')
    parser.add_argument('--service', help='Analyze specific service only')
    parser.add_argument('--errors-only', action='store_true', help='Show only error lines')
    parser.add_argument('--last-minutes', type=int, help='Analyze only last N minutes')
    
    args = parser.parse_args()
    
    diagnostic = LogAnalysisDiagnostic()
    results = diagnostic.run_full_analysis(
        service_filter=args.service,
        errors_only=args.errors_only,
        last_minutes=args.last_minutes
    )
    
    return results

if __name__ == "__main__":
    main()
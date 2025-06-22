#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM DIAGNOSTIC TOOLKIT - MAIN ORCHESTRATOR
Version: 1.0.0
Last Updated: 2025-06-17
REVISION HISTORY:
v1.0.0 (2025-06-17) - Initial diagnostic toolkit orchestrator

USAGE: 
  python diagnostic_toolkit.py                    # Full comprehensive diagnostic
  python diagnostic_toolkit.py --quick           # Quick health check only
  python diagnostic_toolkit.py --logs-only       # Log analysis only
  python diagnostic_toolkit.py --integration     # Service integration test only
  python diagnostic_toolkit.py --processes       # Process/port check only
  python diagnostic_toolkit.py --service NAME    # Single service focus
  python diagnostic_toolkit.py --report          # Generate detailed report

PURPOSE: Unified diagnostic toolkit for comprehensive Trading System health analysis
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import diagnostic modules
try:
    from diagnostic_service_integration import ServiceIntegrationDiagnostic
    from diagnostic_log_analysis import LogAnalysisDiagnostic  
    from diagnostic_process_ports import ProcessPortDiagnostic
except ImportError as e:
    print(f"❌ Error importing diagnostic modules: {e}")
    print("   Ensure all diagnostic scripts are in the same directory")
    sys.exit(1)

class TradingSystemDiagnosticToolkit:
    """Comprehensive diagnostic toolkit orchestrator"""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.results = {}
        
        # Initialize diagnostic modules
        self.integration_diagnostic = ServiceIntegrationDiagnostic()
        self.log_diagnostic = LogAnalysisDiagnostic()
        self.process_diagnostic = ProcessPortDiagnostic()
        
        # Output directory
        self.output_dir = Path('./diagnostic_reports')
        self.output_dir.mkdir(exist_ok=True)
    
    def run_comprehensive_diagnostic(self, options: Dict) -> Dict:
        """Run complete comprehensive diagnostic"""
        print("🏥 TRADING SYSTEM COMPREHENSIVE DIAGNOSTIC TOOLKIT")
        print("=" * 70)
        print(f"Started: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'Quick' if options.get('quick') else 'Comprehensive'}")
        
        if options.get('service_filter'):
            print(f"Service Focus: {options['service_filter']}")
        
        comprehensive_results = {
            "diagnostic_metadata": {
                "timestamp": self.timestamp.isoformat(),
                "version": "1.0.0",
                "mode": "quick" if options.get('quick') else "comprehensive",
                "service_filter": options.get('service_filter'),
                "modules_run": []
            }
        }
        
        # 1. Process and Port Analysis (Always run first)
        if not options.get('logs_only') and not options.get('integration_only'):
            print(f"\n{'='*20} PHASE 1: PROCESS & PORT ANALYSIS {'='*20}")
            try:
                process_results = self.process_diagnostic.run_full_diagnostic()
                comprehensive_results["process_analysis"] = process_results
                comprehensive_results["diagnostic_metadata"]["modules_run"].append("process_ports")
            except Exception as e:
                print(f"❌ Process analysis failed: {e}")
                comprehensive_results["process_analysis"] = {"error": str(e)}
        
        # 2. Service Integration Testing
        if not options.get('logs_only') and not options.get('processes_only'):
            print(f"\n{'='*20} PHASE 2: SERVICE INTEGRATION TESTING {'='*18}")
            try:
                integration_results = self.integration_diagnostic.run_full_diagnostic()
                comprehensive_results["integration_analysis"] = integration_results
                comprehensive_results["diagnostic_metadata"]["modules_run"].append("service_integration")
            except Exception as e:
                print(f"❌ Integration analysis failed: {e}")
                comprehensive_results["integration_analysis"] = {"error": str(e)}
        
        # 3. Log Analysis (Skip in quick mode unless specifically requested)
        if not options.get('quick') or options.get('logs_only'):
            if not options.get('integration_only') and not options.get('processes_only'):
                print(f"\n{'='*20} PHASE 3: LOG ANALYSIS {'='*31}")
                try:
                    log_results = self.log_diagnostic.run_full_analysis(
                        service_filter=options.get('service_filter'),
                        errors_only=options.get('errors_only', False),
                        last_minutes=options.get('last_minutes')
                    )
                    comprehensive_results["log_analysis"] = log_results
                    comprehensive_results["diagnostic_metadata"]["modules_run"].append("log_analysis")
                except Exception as e:
                    print(f"❌ Log analysis failed: {e}")
                    comprehensive_results["log_analysis"] = {"error": str(e)}
        
        # 4. Comprehensive Analysis and Recommendations
        print(f"\n{'='*20} PHASE 4: COMPREHENSIVE ANALYSIS {'='*23}")
        comprehensive_analysis = self.generate_comprehensive_analysis(comprehensive_results)
        comprehensive_results["comprehensive_analysis"] = comprehensive_analysis
        
        # 5. Save Report (if requested)
        if options.get('save_report'):
            report_path = self.save_diagnostic_report(comprehensive_results)
            comprehensive_results["report_path"] = str(report_path)
        
        return comprehensive_results
    
    def generate_comprehensive_analysis(self, results: Dict) -> Dict:
        """Generate unified analysis across all diagnostic modules"""
        print("🧠 COMPREHENSIVE SYSTEM ANALYSIS")
        print("-" * 40)
        
        analysis = {
            "overall_system_health": "unknown",
            "confidence_level": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
            "system_scores": {},
            "health_indicators": {},
            "summary": {}
        }
        
        # Collect health indicators from each module
        process_health = self.extract_process_health(results.get("process_analysis", {}))
        integration_health = self.extract_integration_health(results.get("integration_analysis", {}))
        log_health = self.extract_log_health(results.get("log_analysis", {}))
        
        analysis["health_indicators"] = {
            "process_health": process_health,
            "integration_health": integration_health,
            "log_health": log_health
        }
        
        # Calculate weighted system scores
        scores = []
        weights = []
        
        if process_health.get("score") is not None:
            scores.append(process_health["score"])
            weights.append(0.4)  # Process health is most important
        
        if integration_health.get("score") is not None:
            scores.append(integration_health["score"])
            weights.append(0.4)  # Integration health is equally important
        
        if log_health.get("score") is not None:
            scores.append(log_health["score"])
            weights.append(0.2)  # Log health is supporting indicator
        
        # Calculate overall score
        if scores and weights:
            overall_score = sum(score * weight for score, weight in zip(scores, weights)) / sum(weights)
            analysis["system_scores"]["overall"] = round(overall_score, 1)
        else:
            overall_score = 0
        
        # Determine overall health
        if overall_score >= 90:
            analysis["overall_system_health"] = "excellent"
            analysis["confidence_level"] = "high"
            print("🎉 OVERALL SYSTEM HEALTH: EXCELLENT")
        elif overall_score >= 75:
            analysis["overall_system_health"] = "good"
            analysis["confidence_level"] = "high"
            print("✅ OVERALL SYSTEM HEALTH: GOOD")
        elif overall_score >= 60:
            analysis["overall_system_health"] = "fair"
            analysis["confidence_level"] = "medium"
            print("🟡 OVERALL SYSTEM HEALTH: FAIR")
        elif overall_score >= 40:
            analysis["overall_system_health"] = "poor"
            analysis["confidence_level"] = "high"
            print("⚠️ OVERALL SYSTEM HEALTH: POOR")
        else:
            analysis["overall_system_health"] = "critical"
            analysis["confidence_level"] = "high"
            print("🚨 OVERALL SYSTEM HEALTH: CRITICAL")
        
        print(f"System Score: {overall_score:.1f}/100")
        
        # Collect issues and recommendations from all modules
        self.collect_unified_issues_and_recommendations(results, analysis)
        
        # Generate summary
        analysis["summary"] = {
            "total_services": 9,
            "services_healthy": process_health.get("services_responding", 0),
            "workflow_functional": integration_health.get("workflow_works", False),
            "log_errors": log_health.get("total_errors", 0),
            "critical_issues_count": len(analysis["critical_issues"]),
            "recommendations_count": len(analysis["recommendations"])
        }
        
        # Display key findings
        print(f"\nKey Findings:")
        print(f"   Services Responding: {analysis['summary']['services_healthy']}/9")
        print(f"   Workflow Functional: {'Yes' if analysis['summary']['workflow_functional'] else 'No'}")
        print(f"   Log Errors: {analysis['summary']['log_errors']}")
        print(f"   Critical Issues: {analysis['summary']['critical_issues_count']}")
        
        return analysis
    
    def extract_process_health(self, process_results: Dict) -> Dict:
        """Extract health indicators from process analysis"""
        if not process_results or "error" in process_results:
            return {"score": None, "status": "unavailable"}
        
        services_total = process_results.get("services_total", 9)
        services_responding = process_results.get("services_responding", 0)
        
        # Calculate score based on service availability
        score = (services_responding / services_total) * 100 if services_total > 0 else 0
        
        return {
            "score": round(score, 1),
            "status": process_results.get("overall_status", "unknown"),
            "services_responding": services_responding,
            "services_total": services_total,
            "hybrid_manager_running": process_results.get("hybrid_manager", {}).get("status") == "running"
        }
    
    def extract_integration_health(self, integration_results: Dict) -> Dict:
        """Extract health indicators from integration analysis"""
        if not integration_results or "error" in integration_results:
            return {"score": None, "status": "unavailable"}
        
        summary = integration_results.get("summary", {})
        health_score_map = {"excellent": 100, "good": 80, "fair": 60, "poor": 30}
        
        score = health_score_map.get(summary.get("overall_health"), 0)
        workflow_result = integration_results.get("workflow", {})
        workflow_works = workflow_result.get("status") == "completed"
        
        return {
            "score": score,
            "status": summary.get("overall_health", "unknown"),
            "workflow_works": workflow_works,
            "services_functional": summary.get("services_functional", 0)
        }
    
    def extract_log_health(self, log_results: Dict) -> Dict:
        """Extract health indicators from log analysis"""
        if not log_results or "error" in log_results:
            return {"score": None, "status": "unavailable"}
        
        summary = log_results.get("summary", {})
        health_score_map = {"excellent": 100, "good": 85, "fair": 60, "poor": 20}
        
        score = health_score_map.get(summary.get("overall_log_health"), 50)
        
        return {
            "score": score,
            "status": summary.get("overall_log_health", "unknown"),
            "total_errors": summary.get("total_errors", 0),
            "total_warnings": summary.get("total_warnings", 0)
        }
    
    def collect_unified_issues_and_recommendations(self, results: Dict, analysis: Dict):
        """Collect and unify issues and recommendations from all modules"""
        # Process issues
        process_analysis = results.get("process_analysis", {})
        if process_analysis.get("issues"):
            analysis["critical_issues"].extend(process_analysis["issues"])
        if process_analysis.get("recommendations"):
            analysis["recommendations"].extend(process_analysis["recommendations"])
        
        # Integration issues
        integration_summary = results.get("integration_analysis", {}).get("summary", {})
        if integration_summary.get("critical_issues"):
            analysis["critical_issues"].extend(integration_summary["critical_issues"])
        if integration_summary.get("recommendations"):
            analysis["recommendations"].extend(integration_summary["recommendations"])
        
        # Log issues
        log_summary = results.get("log_analysis", {}).get("summary", {})
        if log_summary.get("critical_issues"):
            analysis["critical_issues"].extend(log_summary["critical_issues"])
        if log_summary.get("recommendations"):
            analysis["recommendations"].extend(log_summary["recommendations"])
        
        # Remove duplicates while preserving order
        analysis["critical_issues"] = list(dict.fromkeys(analysis["critical_issues"]))
        analysis["recommendations"] = list(dict.fromkeys(analysis["recommendations"]))
        
        # Add unified recommendations based on patterns
        if "json_serialization" in str(analysis["critical_issues"]):
            analysis["recommendations"].insert(0, "Apply JSON serialization fix to pattern_analysis.py")
        
        if "hybrid_manager_not_running" in analysis["critical_issues"]:
            analysis["recommendations"].insert(0, "Start system: python hybrid_manager.py start")
    
    def save_diagnostic_report(self, results: Dict) -> Path:
        """Save comprehensive diagnostic report to file"""
        timestamp_str = self.timestamp.strftime('%Y%m%d_%H%M%S')
        report_filename = f"trading_system_diagnostic_{timestamp_str}.json"
        report_path = self.output_dir / report_filename
        
        try:
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n💾 Diagnostic report saved: {report_path}")
            
            # Also create a summary text report
            summary_path = self.output_dir / f"diagnostic_summary_{timestamp_str}.txt"
            self.create_text_summary(results, summary_path)
            
            return report_path
            
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return None
    
    def create_text_summary(self, results: Dict, summary_path: Path):
        """Create human-readable text summary"""
        try:
            with open(summary_path, 'w') as f:
                f.write("TRADING SYSTEM DIAGNOSTIC SUMMARY\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Overall health
                comp_analysis = results.get("comprehensive_analysis", {})
                f.write(f"Overall Health: {comp_analysis.get('overall_system_health', 'unknown').upper()}\n")
                f.write(f"System Score: {comp_analysis.get('system_scores', {}).get('overall', 'N/A')}/100\n\n")
                
                # Key metrics
                summary = comp_analysis.get("summary", {})
                f.write("Key Metrics:\n")
                f.write(f"  Services Responding: {summary.get('services_healthy', 0)}/9\n")
                f.write(f"  Workflow Functional: {'Yes' if summary.get('workflow_functional') else 'No'}\n")
                f.write(f"  Log Errors: {summary.get('log_errors', 0)}\n")
                f.write(f"  Critical Issues: {summary.get('critical_issues_count', 0)}\n\n")
                
                # Critical issues
                critical_issues = comp_analysis.get("critical_issues", [])
                if critical_issues:
                    f.write("Critical Issues:\n")
                    for issue in critical_issues:
                        f.write(f"  - {issue}\n")
                    f.write("\n")
                
                # Top recommendations
                recommendations = comp_analysis.get("recommendations", [])
                if recommendations:
                    f.write("Top Recommendations:\n")
                    for i, rec in enumerate(recommendations[:5], 1):
                        f.write(f"  {i}. {rec}\n")
                
            print(f"📄 Text summary saved: {summary_path}")
            
        except Exception as e:
            print(f"❌ Error saving text summary: {e}")
    
    def run_quick_health_check(self) -> Dict:
        """Run quick health check (process + integration only)"""
        print("⚡ QUICK HEALTH CHECK")
        print("-" * 30)
        
        return self.run_comprehensive_diagnostic({"quick": True})

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Trading System Diagnostic Toolkit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python diagnostic_toolkit.py                    # Full comprehensive diagnostic
  python diagnostic_toolkit.py --quick           # Quick health check
  python diagnostic_toolkit.py --logs-only       # Log analysis only
  python diagnostic_toolkit.py --service scanner # Focus on scanner service
  python diagnostic_toolkit.py --report          # Save detailed report
        """
    )
    
    parser.add_argument('--quick', action='store_true', 
                       help='Quick health check (skip log analysis)')
    parser.add_argument('--logs-only', action='store_true',
                       help='Run log analysis only')
    parser.add_argument('--integration-only', action='store_true',
                       help='Run integration tests only')
    parser.add_argument('--processes-only', action='store_true',
                       help='Run process/port checks only')
    parser.add_argument('--service', 
                       help='Focus on specific service')
    parser.add_argument('--errors-only', action='store_true',
                       help='Show only errors in log analysis')
    parser.add_argument('--last-minutes', type=int,
                       help='Analyze only last N minutes of logs')
    parser.add_argument('--report', action='store_true',
                       help='Save detailed diagnostic report')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Convert args to options dict
    options = {
        'quick': args.quick,
        'logs_only': args.logs_only,
        'integration_only': args.integration_only,
        'processes_only': args.processes_only,
        'service_filter': args.service,
        'errors_only': args.errors_only,
        'last_minutes': args.last_minutes,
        'save_report': args.report
    }
    
    # Initialize toolkit
    toolkit = TradingSystemDiagnosticToolkit()
    
    try:
        # Run diagnostic
        if args.quick:
            results = toolkit.run_quick_health_check()
        else:
            results = toolkit.run_comprehensive_diagnostic(options)
        
        # Print completion message
        print(f"\n🏁 DIAGNOSTIC COMPLETED")
        print("=" * 30)
        
        comp_analysis = results.get("comprehensive_analysis", {})
        overall_health = comp_analysis.get("overall_system_health", "unknown")
        
        if overall_health in ["excellent", "good"]:
            print("✅ Your trading system is healthy and ready for operation!")
        elif overall_health == "fair":
            print("🟡 Your trading system has minor issues but is operational.")
        else:
            print("❌ Your trading system has significant issues requiring attention.")
        
        # Show next steps
        recommendations = comp_analysis.get("recommendations", [])
        if recommendations:
            print(f"\n🎯 Next Steps:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. {rec}")
        
        return results
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Diagnostic interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        return None

if __name__ == "__main__":
    main()
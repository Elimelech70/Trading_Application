#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM DIAGNOSTIC - PROCESS AND PORT STATUS
Version: 1.0.0
Last Updated: 2025-06-17
REVISION HISTORY:
v1.0.0 (2025-06-17) - Initial diagnostic script for process and port monitoring

USAGE: python diagnostic_process_ports.py
PURPOSE: Accurate diagnosis of service processes and port status
"""

import subprocess
import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple

class ProcessPortDiagnostic:
    """Accurate process and port diagnostic for trading system services"""
    
    def __init__(self):
        self.services = {
            "coordination": {"file": "coordination_service.py", "port": 5000},
            "scanner": {"file": "security_scanner.py", "port": 5001},
            "pattern": {"file": "pattern_analysis.py", "port": 5002},
            "technical": {"file": "technical_analysis.py", "port": 5003},
            "trading": {"file": "paper_trading.py", "port": 5005},
            "pattern_rec": {"file": "pattern_recognition_service.py", "port": 5006},
            "news": {"file": "news_service.py", "port": 5008},
            "reporting": {"file": "reporting_service.py", "port": 5009},
            "dashboard": {"file": "web_dashboard_service.py", "port": 5010}
        }
        
        self.hybrid_manager_file = "hybrid_manager.py"
    
    def run_full_diagnostic(self):
        """Run complete process and port diagnostic"""
        print("🔍 TRADING SYSTEM PROCESS & PORT DIAGNOSTIC")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Check hybrid manager
        hybrid_status = self.check_hybrid_manager()
        
        # 2. Check individual service processes
        process_results = self.check_service_processes()
        
        # 3. Check port responses
        port_results = self.check_port_responses()
        
        # 4. Cross-reference and analyze
        analysis = self.analyze_results(hybrid_status, process_results, port_results)
        
        # 5. Generate summary and recommendations
        self.generate_summary(analysis)
        
        return analysis
    
    def check_hybrid_manager(self) -> Dict:
        """Check hybrid manager process status"""
        print(f"\n🤖 HYBRID MANAGER STATUS:")
        print("-" * 30)
        
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            hybrid_processes = []
            
            for line in result.stdout.split('\n'):
                if self.hybrid_manager_file in line and 'python' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        command = ' '.join(parts[10:]) if len(parts) >= 11 else line
                        hybrid_processes.append((pid, command))
            
            if hybrid_processes:
                for pid, command in hybrid_processes:
                    print(f"✅ Hybrid Manager: PID {pid}")
                return {"status": "running", "processes": hybrid_processes}
            else:
                print("❌ Hybrid Manager: NOT FOUND")
                return {"status": "not_running", "processes": []}
                
        except Exception as e:
            print(f"❌ Error checking hybrid manager: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_service_processes(self) -> Dict:
        """Check individual service processes with multiple detection methods"""
        print(f"\n📊 SERVICE PROCESS STATUS:")
        print("-" * 30)
        
        results = {}
        
        try:
            # Get all Python processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            all_processes = result.stdout.split('\n')
            
            for service_name, config in self.services.items():
                service_file = config["file"]
                port = config["port"]
                
                # Method 1: Look for exact filename match
                exact_matches = []
                for line in all_processes:
                    if service_file in line and 'python' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[1]
                            exact_matches.append(pid)
                
                # Method 2: Look for port binding
                port_binding = self.check_port_binding(port)
                
                # Method 3: HTTP health check
                http_responsive = self.quick_health_check(port)
                
                results[service_name] = {
                    "file": service_file,
                    "port": port,
                    "process_pids": exact_matches,
                    "port_bound": port_binding,
                    "http_responsive": http_responsive,
                    "status": self.determine_process_status(exact_matches, port_binding, http_responsive)
                }
                
                # Display result
                status = results[service_name]["status"]
                if status == "running":
                    pids_str = ", ".join(exact_matches) if exact_matches else "Unknown PID"
                    print(f"✅ {service_name:12}: Running (PID: {pids_str})")
                elif status == "responding":
                    print(f"🟡 {service_name:12}: Responding (No PID found, but HTTP works)")
                else:
                    print(f"❌ {service_name:12}: Not running")
        
        except Exception as e:
            print(f"❌ Error checking service processes: {e}")
            results["error"] = str(e)
        
        return results
    
    def check_port_responses(self) -> Dict:
        """Check HTTP responses on all service ports"""
        print(f"\n🌐 PORT RESPONSE STATUS:")
        print("-" * 30)
        
        results = {}
        
        for service_name, config in self.services.items():
            port = config["port"]
            
            try:
                start_time = time.time()
                response = requests.get(f'http://localhost:{port}/health', timeout=5)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        service_status = data.get('status', 'unknown')
                        service_type = data.get('service', 'unknown')
                        
                        results[service_name] = {
                            "port": port,
                            "status": "responding",
                            "http_code": response.status_code,
                            "response_time": round(response_time * 1000, 1),
                            "service_status": service_status,
                            "service_type": service_type
                        }
                        
                        print(f"✅ {service_name:12} (port {port}): {service_status} ({response_time*1000:.1f}ms)")
                    
                    except json.JSONDecodeError:
                        results[service_name] = {
                            "port": port,
                            "status": "responding_no_json",
                            "http_code": response.status_code,
                            "response_time": round(response_time * 1000, 1)
                        }
                        print(f"🟡 {service_name:12} (port {port}): Responding but no JSON")
                
                else:
                    results[service_name] = {
                        "port": port,
                        "status": "http_error",
                        "http_code": response.status_code,
                        "response_time": round(response_time * 1000, 1)
                    }
                    print(f"⚠️ {service_name:12} (port {port}): HTTP {response.status_code}")
            
            except requests.exceptions.ConnectionError:
                results[service_name] = {
                    "port": port,
                    "status": "connection_refused",
                    "error": "Connection refused"
                }
                print(f"❌ {service_name:12} (port {port}): Connection refused")
            
            except requests.exceptions.Timeout:
                results[service_name] = {
                    "port": port,
                    "status": "timeout",
                    "error": "Request timeout"
                }
                print(f"⏱️ {service_name:12} (port {port}): Timeout")
            
            except Exception as e:
                results[service_name] = {
                    "port": port,
                    "status": "error",
                    "error": str(e)
                }
                print(f"❌ {service_name:12} (port {port}): {type(e).__name__}")
        
        return results
    
    def check_port_binding(self, port: int) -> bool:
        """Check if a port is bound using lsof"""
        try:
            result = subprocess.run(['lsof', '-i', f':{port}'], 
                                  capture_output=True, text=True)
            return str(port) in result.stdout
        except:
            return False
    
    def quick_health_check(self, port: int) -> bool:
        """Quick HTTP health check"""
        try:
            response = requests.get(f'http://localhost:{port}/health', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def determine_process_status(self, pids: List[str], port_bound: bool, http_responsive: bool) -> str:
        """Determine overall process status from multiple indicators"""
        if pids and port_bound and http_responsive:
            return "running"  # Full confirmation
        elif http_responsive:
            return "responding"  # Service works but PID detection failed
        elif port_bound:
            return "bound_not_responding"  # Port occupied but not responding
        else:
            return "not_running"  # Definitely not running
    
    def analyze_results(self, hybrid_status: Dict, process_results: Dict, port_results: Dict) -> Dict:
        """Analyze all results and provide insights"""
        print(f"\n🧠 ANALYSIS & INSIGHTS:")
        print("-" * 30)
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "hybrid_manager": hybrid_status,
            "overall_status": "unknown",
            "services_running": 0,
            "services_responding": 0,
            "services_total": len(self.services),
            "issues": [],
            "recommendations": []
        }
        
        # Count running and responding services
        for service_name in self.services:
            process_status = process_results.get(service_name, {}).get("status", "unknown")
            port_status = port_results.get(service_name, {}).get("status", "unknown")
            
            if process_status == "running":
                analysis["services_running"] += 1
            
            if port_status == "responding":
                analysis["services_responding"] += 1
        
        # Overall system status assessment
        if analysis["services_responding"] == analysis["services_total"]:
            analysis["overall_status"] = "fully_operational"
            print("🎉 SYSTEM STATUS: FULLY OPERATIONAL")
            print(f"   All {analysis['services_total']} services responding")
        
        elif analysis["services_responding"] >= analysis["services_total"] - 1:
            analysis["overall_status"] = "mostly_operational"
            print("🟡 SYSTEM STATUS: MOSTLY OPERATIONAL")
            print(f"   {analysis['services_responding']}/{analysis['services_total']} services responding")
        
        elif analysis["services_responding"] >= analysis["services_total"] // 2:
            analysis["overall_status"] = "degraded"
            print("⚠️ SYSTEM STATUS: DEGRADED")
            print(f"   Only {analysis['services_responding']}/{analysis['services_total']} services responding")
        
        else:
            analysis["overall_status"] = "critical"
            print("🚨 SYSTEM STATUS: CRITICAL")
            print(f"   Only {analysis['services_responding']}/{analysis['services_total']} services responding")
        
        # Identify specific issues
        if hybrid_status["status"] != "running":
            analysis["issues"].append("hybrid_manager_not_running")
            analysis["recommendations"].append("Start hybrid manager: python hybrid_manager.py start")
        
        # Check for PID detection issues
        pid_detection_issues = 0
        for service_name in self.services:
            process_status = process_results.get(service_name, {}).get("status", "unknown")
            port_status = port_results.get(service_name, {}).get("status", "unknown")
            
            if process_status != "running" and port_status == "responding":
                pid_detection_issues += 1
        
        if pid_detection_issues > 0:
            analysis["issues"].append(f"pid_detection_inaccurate_{pid_detection_issues}_services")
            analysis["recommendations"].append("PID detection has issues - trust port responses over process detection")
        
        return analysis
    
    def generate_summary(self, analysis: Dict):
        """Generate diagnostic summary and recommendations"""
        print(f"\n📋 DIAGNOSTIC SUMMARY:")
        print("=" * 30)
        
        print(f"Overall Status: {analysis['overall_status']}")
        print(f"Services Responding: {analysis['services_responding']}/{analysis['services_total']}")
        print(f"Hybrid Manager: {analysis['hybrid_manager']['status']}")
        
        if analysis["issues"]:
            print(f"\n⚠️ Issues Found:")
            for issue in analysis["issues"]:
                print(f"   - {issue}")
        
        if analysis["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in analysis["recommendations"]:
                print(f"   - {rec}")
        
        print(f"\n🕐 Diagnostic completed at: {analysis['timestamp']}")

def main():
    """Main entry point"""
    diagnostic = ProcessPortDiagnostic()
    analysis = diagnostic.run_full_diagnostic()
    return analysis

if __name__ == "__main__":
    main()
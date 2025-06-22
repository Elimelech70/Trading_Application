#!/usr/bin/env python3
"""
Name of Service: TRADING SYSTEM DIAGNOSTIC - SERVICE INTEGRATION & HEALTH
Version: 1.0.0
Last Updated: 2025-06-17
REVISION HISTORY:
v1.0.0 (2025-06-17) - Initial diagnostic script for service integration testing

USAGE: python diagnostic_service_integration.py
PURPOSE: Test service endpoints, inter-service communication, and functional health
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class ServiceIntegrationDiagnostic:
    """Test service integration and functional health"""
    
    def __init__(self):
        self.base_urls = {
            "coordination": "http://localhost:5000",
            "scanner": "http://localhost:5001", 
            "pattern": "http://localhost:5002",
            "technical": "http://localhost:5003",
            "trading": "http://localhost:5005",
            "pattern_rec": "http://localhost:5006",
            "news": "http://localhost:5008",
            "reporting": "http://localhost:5009",
            "dashboard": "http://localhost:5010"
        }
        
        self.test_symbol = "AAPL"
        self.timeout = 10
    
    def run_full_diagnostic(self):
        """Run complete service integration diagnostic"""
        print("🔗 TRADING SYSTEM SERVICE INTEGRATION DIAGNOSTIC")
        print("=" * 65)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {}
        
        # 1. Test individual service health endpoints
        health_results = self.test_health_endpoints()
        results["health_endpoints"] = health_results
        
        # 2. Test service-specific functionality
        functionality_results = self.test_service_functionality()
        results["functionality"] = functionality_results
        
        # 3. Test inter-service communication
        integration_results = self.test_service_integration()
        results["integration"] = integration_results
        
        # 4. Test complete workflow
        workflow_results = self.test_complete_workflow()
        results["workflow"] = workflow_results
        
        # 5. Analyze and summarize
        summary = self.analyze_and_summarize(results)
        results["summary"] = summary
        
        return results
    
    def test_health_endpoints(self) -> Dict:
        """Test /health endpoints for all services"""
        print(f"\n💊 HEALTH ENDPOINT TESTS:")
        print("-" * 40)
        
        results = {}
        
        for service_name, base_url in self.base_urls.items():
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}/health", timeout=self.timeout)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        status = data.get('status', 'unknown')
                        service_type = data.get('service', 'unknown')
                        
                        results[service_name] = {
                            "status": "healthy",
                            "response_time": round(response_time * 1000, 1),
                            "service_status": status,
                            "service_type": service_type,
                            "additional_info": self.extract_additional_health_info(data)
                        }
                        
                        print(f"✅ {service_name:12}: {status} ({response_time*1000:.1f}ms)")
                        
                        # Show important additional info
                        if service_name == "pattern" and "yfinance_available" in data:
                            yf_status = "✅" if data["yfinance_available"] else "⚠️ "
                            print(f"   └─ yfinance: {yf_status}")
                        
                        if service_name == "trading" and "alpaca_connected" in data:
                            alpaca_status = "✅" if data["alpaca_connected"] else "⚠️ "
                            trading_mode = data.get("trading_mode", "unknown")
                            print(f"   └─ alpaca: {alpaca_status} ({trading_mode})")
                    
                    except json.JSONDecodeError:
                        results[service_name] = {
                            "status": "responding_invalid_json",
                            "response_time": round(response_time * 1000, 1),
                            "http_code": response.status_code
                        }
                        print(f"🟡 {service_name:12}: Responding but invalid JSON")
                
                else:
                    results[service_name] = {
                        "status": "http_error",
                        "response_time": round(response_time * 1000, 1),
                        "http_code": response.status_code
                    }
                    print(f"❌ {service_name:12}: HTTP {response.status_code}")
            
            except requests.exceptions.Timeout:
                results[service_name] = {"status": "timeout"}
                print(f"⏱️ {service_name:12}: Timeout ({self.timeout}s)")
            
            except requests.exceptions.ConnectionError:
                results[service_name] = {"status": "connection_error"}
                print(f"❌ {service_name:12}: Connection refused")
            
            except Exception as e:
                results[service_name] = {"status": "error", "error": str(e)}
                print(f"❌ {service_name:12}: {type(e).__name__}")
        
        return results
    
    def test_service_functionality(self) -> Dict:
        """Test key functionality endpoints for each service"""
        print(f"\n⚙️ SERVICE FUNCTIONALITY TESTS:")
        print("-" * 40)
        
        results = {}
        
        # Test Scanner
        print("🔍 Testing Scanner...")
        try:
            response = requests.get(f"{self.base_urls['scanner']}/scan_securities", timeout=self.timeout)
            if response.status_code == 200:
                securities = response.json()
                count = len(securities) if isinstance(securities, list) else 0
                results["scanner"] = {"status": "working", "securities_found": count}
                print(f"   ✅ Found {count} securities")
            else:
                results["scanner"] = {"status": "error", "http_code": response.status_code}
                print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            results["scanner"] = {"status": "error", "error": str(e)}
            print(f"   ❌ {type(e).__name__}: {e}")
        
        # Test Pattern Analysis
        print("📊 Testing Pattern Analysis...")
        try:
            response = requests.get(f"{self.base_urls['pattern']}/analyze_patterns/{self.test_symbol}", timeout=self.timeout)
            if response.status_code == 200:
                patterns = response.json()
                pattern_count = len(patterns.get('patterns', []))
                confidence = patterns.get('confidence_score', 0)
                results["pattern"] = {
                    "status": "working", 
                    "patterns_found": pattern_count,
                    "confidence": confidence
                }
                print(f"   ✅ Found {pattern_count} patterns (confidence: {confidence:.3f})")
            else:
                results["pattern"] = {"status": "error", "http_code": response.status_code}
                print(f"   ❌ HTTP {response.status_code}")
                # Try to get error details
                try:
                    error_text = response.text[:200]
                    print(f"   └─ Error: {error_text}")
                except:
                    pass
        except Exception as e:
            results["pattern"] = {"status": "error", "error": str(e)}
            print(f"   ❌ {type(e).__name__}: {e}")
        
        # Test Technical Analysis
        print("📈 Testing Technical Analysis...")
        try:
            test_data = {"securities": [{"symbol": self.test_symbol, "patterns": []}]}
            response = requests.post(f"{self.base_urls['technical']}/generate_signals", 
                                   json=test_data, timeout=self.timeout)
            if response.status_code == 200:
                signals = response.json()
                signal_count = len(signals) if isinstance(signals, list) else 0
                results["technical"] = {"status": "working", "signals_generated": signal_count}
                print(f"   ✅ Generated {signal_count} signals")
            else:
                results["technical"] = {"status": "error", "http_code": response.status_code}
                print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            results["technical"] = {"status": "error", "error": str(e)}
            print(f"   ❌ {type(e).__name__}: {e}")
        
        # Test News Service
        print("📰 Testing News Service...")
        try:
            response = requests.get(f"{self.base_urls['news']}/news_sentiment/{self.test_symbol}", timeout=self.timeout)
            if response.status_code == 200:
                sentiment = response.json()
                sentiment_score = sentiment.get('sentiment_score', 0)
                news_count = sentiment.get('news_count', 0)
                results["news"] = {
                    "status": "working", 
                    "sentiment_score": sentiment_score,
                    "news_count": news_count
                }
                print(f"   ✅ Sentiment: {sentiment_score:.3f} ({news_count} articles)")
            else:
                results["news"] = {"status": "error", "http_code": response.status_code}
                print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            results["news"] = {"status": "error", "error": str(e)}
            print(f"   ❌ {type(e).__name__}: {e}")
        
        # Test Paper Trading
        print("💰 Testing Paper Trading...")
        try:
            response = requests.get(f"{self.base_urls['trading']}/account", timeout=self.timeout)
            if response.status_code == 200:
                account = response.json()
                buying_power = account.get('buying_power', 0)
                trading_mode = account.get('mode', 'unknown')
                results["trading"] = {
                    "status": "working",
                    "buying_power": buying_power,
                    "trading_mode": trading_mode
                }
                print(f"   ✅ Account: ${buying_power:,.2f} ({trading_mode})")
            else:
                results["trading"] = {"status": "error", "http_code": response.status_code}
                print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            results["trading"] = {"status": "error", "error": str(e)}
            print(f"   ❌ {type(e).__name__}: {e}")
        
        # Test Reporting
        print("📋 Testing Reporting...")
        try:
            response = requests.get(f"{self.base_urls['reporting']}/daily_summary", timeout=self.timeout)
            if response.status_code == 200:
                summary = response.json()
                trades = summary.get('trading_performance', {}).get('total_trades', 0)
                results["reporting"] = {"status": "working", "daily_trades": trades}
                print(f"   ✅ Daily summary: {trades} trades")
            else:
                results["reporting"] = {"status": "error", "http_code": response.status_code}
                print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            results["reporting"] = {"status": "error", "error": str(e)}
            print(f"   ❌ {type(e).__name__}: {e}")
        
        return results
    
    def test_service_integration(self) -> Dict:
        """Test communication between services"""
        print(f"\n🔗 INTER-SERVICE COMMUNICATION TESTS:")
        print("-" * 45)
        
        results = {}
        
        # Test Coordination -> Scanner
        print("🤝 Testing Coordination ↔ Scanner...")
        try:
            response = requests.get(f"{self.base_urls['coordination']}/service_status", timeout=self.timeout)
            if response.status_code == 200:
                status = response.json()
                registered_services = len(status)
                results["coordination_registry"] = {
                    "status": "working",
                    "registered_services": registered_services
                }
                print(f"   ✅ Service registry: {registered_services} services")
            else:
                results["coordination_registry"] = {"status": "error", "http_code": response.status_code}
                print(f"   ❌ Service registry: HTTP {response.status_code}")
        except Exception as e:
            results["coordination_registry"] = {"status": "error", "error": str(e)}
            print(f"   ❌ Service registry: {type(e).__name__}")
        
        # Test Pattern -> Pattern Recognition integration
        print("🤝 Testing Pattern ↔ Pattern Recognition...")
        try:
            response = requests.get(f"{self.base_urls['pattern_rec']}/detect_advanced_patterns/{self.test_symbol}", timeout=self.timeout)
            if response.status_code == 200:
                advanced_patterns = response.json()
                pattern_score = advanced_patterns.get('overall_pattern_score', 0)
                results["pattern_integration"] = {
                    "status": "working",
                    "pattern_score": pattern_score
                }
                print(f"   ✅ Advanced patterns: score {pattern_score:.3f}")
            else:
                results["pattern_integration"] = {"status": "error", "http_code": response.status_code}
                print(f"   ❌ Advanced patterns: HTTP {response.status_code}")
        except Exception as e:
            results["pattern_integration"] = {"status": "error", "error": str(e)}
            print(f"   ❌ Advanced patterns: {type(e).__name__}")
        
        return results
    
    def test_complete_workflow(self) -> Dict:
        """Test the complete trading workflow"""
        print(f"\n🔄 COMPLETE WORKFLOW TEST:")
        print("-" * 35)
        
        try:
            print("🚀 Starting trading cycle...")
            start_time = time.time()
            
            response = requests.post(f"{self.base_urls['coordination']}/start_trading_cycle", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                cycle_time = time.time() - start_time
                
                workflow_result = {
                    "status": "completed",
                    "cycle_time": round(cycle_time, 1),
                    "cycle_id": result.get('cycle_id', 'N/A'),
                    "securities_scanned": result.get('securities_scanned', 0),
                    "patterns_analyzed": result.get('patterns_analyzed', 0),
                    "signals_generated": result.get('signals_generated', 0),
                    "trades_executed": result.get('trades_executed', 0)
                }
                
                print(f"   ✅ Workflow completed in {cycle_time:.1f}s")
                print(f"   📊 Securities: {workflow_result['securities_scanned']}")
                print(f"   📈 Patterns: {workflow_result['patterns_analyzed']}")
                print(f"   📡 Signals: {workflow_result['signals_generated']}")
                print(f"   💰 Trades: {workflow_result['trades_executed']}")
                
                return workflow_result
            
            else:
                print(f"   ❌ Workflow failed: HTTP {response.status_code}")
                return {"status": "failed", "http_code": response.status_code}
        
        except Exception as e:
            print(f"   ❌ Workflow error: {type(e).__name__}")
            return {"status": "error", "error": str(e)}
    
    def extract_additional_health_info(self, health_data: Dict) -> Dict:
        """Extract additional useful info from health endpoint"""
        additional = {}
        
        # Common additional fields
        for key in ["yfinance_available", "alpaca_connected", "trading_mode", 
                   "ml_available", "data_source", "implementation"]:
            if key in health_data:
                additional[key] = health_data[key]
        
        return additional
    
    def analyze_and_summarize(self, results: Dict) -> Dict:
        """Analyze all test results and provide summary"""
        print(f"\n📊 INTEGRATION DIAGNOSTIC SUMMARY:")
        print("=" * 40)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "unknown",
            "services_healthy": 0,
            "services_functional": 0,
            "workflow_status": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Count healthy services
        health_results = results.get("health_endpoints", {})
        for service, health in health_results.items():
            if health.get("status") == "healthy":
                summary["services_healthy"] += 1
        
        # Count functional services
        func_results = results.get("functionality", {})
        for service, func in func_results.items():
            if func.get("status") == "working":
                summary["services_functional"] += 1
        
        # Workflow status
        workflow = results.get("workflow", {})
        summary["workflow_status"] = workflow.get("status", "unknown")
        
        # Determine overall health
        total_services = len(self.base_urls)
        if summary["services_healthy"] == total_services and summary["workflow_status"] == "completed":
            summary["overall_health"] = "excellent"
            print("🎉 OVERALL HEALTH: EXCELLENT")
        elif summary["services_healthy"] >= total_services - 1 and summary["workflow_status"] == "completed":
            summary["overall_health"] = "good"
            print("✅ OVERALL HEALTH: GOOD")
        elif summary["services_healthy"] >= total_services // 2:
            summary["overall_health"] = "fair"
            print("🟡 OVERALL HEALTH: FAIR")
        else:
            summary["overall_health"] = "poor"
            print("❌ OVERALL HEALTH: POOR")
        
        print(f"Healthy Services: {summary['services_healthy']}/{total_services}")
        print(f"Functional Services: {summary['services_functional']}/{len(func_results)}")
        print(f"Workflow: {summary['workflow_status']}")
        
        # Generate recommendations
        if summary["workflow_status"] != "completed":
            summary["critical_issues"].append("Trading workflow not completing")
            summary["recommendations"].append("Check coordination service and inter-service communication")
        
        if summary["services_healthy"] < total_services:
            unhealthy_count = total_services - summary["services_healthy"]
            summary["warnings"].append(f"{unhealthy_count} services not responding to health checks")
        
        # Service-specific recommendations
        pattern_func = func_results.get("pattern", {})
        if pattern_func.get("status") == "error":
            summary["critical_issues"].append("Pattern analysis not working")
            summary["recommendations"].append("Check pattern analysis logs for JSON serialization errors")
        
        return summary

def main():
    """Main entry point"""
    diagnostic = ServiceIntegrationDiagnostic()
    results = diagnostic.run_full_diagnostic()
    return results

if __name__ == "__main__":
    main()
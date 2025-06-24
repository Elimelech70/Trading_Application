#!/usr/bin/env python3
"""
WEB DASHBOARD DATA INVESTIGATION
Service: Web Dashboard Data Source Analysis
Version: 1.0.1
Last Updated: 2025-06-24

REVISION HISTORY:
- v1.0.1 (2025-06-24) - Fixed syntax error in print statement
- v1.0.0 (2025-06-24) - Initial investigation tool
  - Checks all potential sources of dashboard data
  - Identifies what "completed trades" might refer to
  - Examines trading_cycles vs workflow_metrics

This tool investigates what data the web dashboard might be showing
when it displays "completed trades".
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import json
import glob

class WebDashboardDataInvestigation:
    def __init__(self, db_path='./trading_system.db'):
        self.db_path = db_path
        
    def investigate(self):
        """Run complete investigation"""
        print("\n" + "="*80)
        print("🔍 WEB DASHBOARD DATA INVESTIGATION")
        print("="*80)
        print(f"Database: {self.db_path}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        if not Path(self.db_path).exists():
            print(f"❌ Database not found at {self.db_path}")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # 1. Check trading_cycles table (older system)
            print("\n📊 TRADING_CYCLES TABLE (Original System)")
            print("-"*60)
            self.check_trading_cycles(conn)
            
            # 2. Check workflow_metrics table (newer system)
            print("\n📊 WORKFLOW_METRICS TABLE (Workflow Tracker)")
            print("-"*60)
            self.check_workflow_metrics(conn)
            
            # 3. Check for any JSON files that might store trades
            print("\n📄 CHECKING FOR JSON DATA FILES")
            print("-"*60)
            self.check_json_files()
            
            # 4. Check web dashboard configuration
            print("\n🌐 WEB DASHBOARD ANALYSIS")
            print("-"*60)
            self.analyze_web_dashboard()
            
            # 5. Check for simulated/mock data
            print("\n🎭 CHECKING FOR MOCK/SIMULATED DATA")
            print("-"*60)
            self.check_for_mock_data(conn)
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error during investigation: {e}")
            import traceback
            traceback.print_exc()
    
    def check_trading_cycles(self, conn):
        """Check the original trading_cycles table"""
        cursor = conn.cursor()
        
        # Get all data from trading_cycles
        cursor.execute("""
            SELECT 
                id,
                cycle_id,
                status,
                start_time,
                end_time,
                securities_scanned,
                patterns_found,
                trades_executed,
                error_count,
                created_at
            FROM trading_cycles
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"Total cycles in trading_cycles: {len(rows)}")
            
            # Summary statistics
            total_trades_reported = sum(row['trades_executed'] for row in rows)
            cycles_with_trades = sum(1 for row in rows if row['trades_executed'] > 0)
            
            print(f"Total 'trades_executed' reported: {total_trades_reported}")
            print(f"Cycles claiming to have trades: {cycles_with_trades}")
            
            print("\nRecent cycles:")
            print(f"{'ID':<4} {'Cycle ID':<25} {'Status':<12} {'Trades':<8} {'Patterns':<10} {'Securities':<12} {'Date'}")
            print("-"*90)
            
            for row in rows[:10]:  # Show first 10
                cycle_id = row['cycle_id'][:25] if row['cycle_id'] else 'None'
                print(f"{row['id']:<4} {cycle_id:<25} {row['status']:<12} "
                      f"{row['trades_executed']:<8} {row['patterns_found']:<10} "
                      f"{row['securities_scanned']:<12} {row['created_at'][:10]}")
            
            # Check if any cycles actually executed trades
            if total_trades_reported == 0:
                print("\n⚠️  All cycles show 0 trades_executed")
                print("   The 'completed trades' in dashboard might refer to completed cycles, not actual trades")
        else:
            print("No records in trading_cycles table")
    
    def check_workflow_metrics(self, conn):
        """Check the newer workflow_metrics table"""
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM workflow_metrics")
        count = cursor.fetchone()['count']
        
        print(f"Total records in workflow_metrics: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT * FROM workflow_metrics
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            print("\nSample workflow metrics:")
            for row in rows:
                print(f"  Cycle: {row['cycle_id']}, Trades: {row['trades_executed']}")
    
    def check_json_files(self):
        """Check for JSON files that might contain trade data"""
        json_patterns = [
            "*.json",
            "trades/*.json",
            "data/*.json",
            "logs/*.json",
            "backups/*.json"
        ]
        
        found_files = []
        for pattern in json_patterns:
            found_files.extend(glob.glob(pattern, recursive=False))
        
        if found_files:
            print(f"Found {len(found_files)} JSON files:")
            for file in found_files[:10]:  # Show first 10
                size = Path(file).stat().st_size
                print(f"  - {file} ({size} bytes)")
                
                # Check if file might contain trade data
                try:
                    with open(file, 'r') as f:
                        content = f.read(1000)  # Read first 1000 chars
                        if any(word in content.lower() for word in ['trade', 'order', 'execution', 'position']):
                            print(f"    └─ May contain trade data!")
                except:
                    pass
        else:
            print("No JSON files found")
    
    def analyze_web_dashboard(self):
        """Analyze what the web dashboard might be showing"""
        # Check if web_dashboard_service.py exists
        dashboard_files = [
            "web_dashboard_service.py",
            "web_dashboard.py",
            "dashboard.py",
            "app.py"
        ]
        
        found_dashboard = None
        for file in dashboard_files:
            if Path(file).exists():
                found_dashboard = file
                break
        
        if found_dashboard:
            print(f"Found dashboard file: {found_dashboard}")
            
            # Read file to understand what it's displaying
            try:
                with open(found_dashboard, 'r') as f:
                    content = f.read()
                
                # Look for database queries
                if "trading_cycles" in content:
                    print("✓ Dashboard queries trading_cycles table")
                if "workflow_metrics" in content:
                    print("✓ Dashboard queries workflow_metrics table")
                if "trades" in content and "trades_executed" not in content:
                    print("✓ Dashboard queries trades table")
                
                # Look for mock data
                if "mock" in content.lower() or "sample" in content.lower() or "demo" in content.lower():
                    print("⚠️  Dashboard might be using mock/sample data")
                
                # Look for what "completed trades" refers to
                print("\n🔍 Analyzing 'completed trades' reference:")
                
                # Check if it's showing completed cycles as "trades"
                if "cycles" in content and "completed" in content:
                    print("  - Dashboard might be showing 'completed cycles' as 'completed trades'")
                
                # Check if trades_executed field is being displayed
                if "trades_executed" in content:
                    print("  - Dashboard is showing the trades_executed count from cycles")
                    print("    (This is just a number, not actual trade records)")
                
            except Exception as e:
                print(f"Error reading dashboard file: {e}")
        else:
            print("No dashboard file found in current directory")
    
    def check_for_mock_data(self, conn):
        """Check if there's any mock or test data"""
        cursor = conn.cursor()
        
        # Check for test/demo/mock indicators in data
        tables_to_check = ['trading_cycles', 'trades', 'orders']
        
        for table in tables_to_check:
            try:
                # Build query based on table
                if table == 'trading_cycles':
                    query = f"""
                        SELECT COUNT(*) as count
                        FROM {table}
                        WHERE cycle_id LIKE '%test%'
                           OR cycle_id LIKE '%demo%'
                           OR cycle_id LIKE '%mock%'
                    """
                elif table in ['trades', 'orders']:
                    query = f"""
                        SELECT COUNT(*) as count
                        FROM {table}
                        WHERE symbol LIKE '%TEST%'
                           OR symbol LIKE '%DEMO%'
                    """
                else:
                    continue
                
                cursor.execute(query)
                count = cursor.fetchone()['count']
                if count > 0:
                    print(f"Found {count} potential test/mock records in {table}")
            except Exception as e:
                # Table might not exist or have these columns
                pass
        
        # Check configuration
        try:
            cursor.execute("SELECT * FROM trading_schedule_config")
            config_row = cursor.fetchone()
            if config_row:
                config = json.loads(config_row['config'])
                print(f"\nTrading schedule config:")
                print(f"  - Enabled: {config.get('enabled', 'Unknown')}")
                print(f"  - Last run: {config.get('last_run', 'Never')}")
                
                if not config.get('enabled'):
                    print("  ⚠️  Trading is DISABLED - this might explain no real trades")
        except Exception as e:
            print(f"Could not check trading schedule config: {e}")

def main():
    """Main function"""
    investigator = WebDashboardDataInvestigation()
    investigator.investigate()
    
    print("\n" + "="*80)
    print("💡 CONCLUSION")
    print("="*80)
    print("The 'completed trades' shown in the web dashboard likely refers to:")
    print("1. The COUNT of completed trading CYCLES (not actual trades)")
    print("2. The 'trades_executed' field which is just a counter, not real trades")
    print("3. Mock/simulated data for demonstration purposes")
    print("\nTo see actual trades, the paper_trading service needs to:")
    print("1. Actually execute trades (not just count them)")
    print("2. Save trade records to the 'trades' table")
    print("3. Update both the workflow tracker AND the trades table")
    print("="*80)

if __name__ == "__main__":
    main()

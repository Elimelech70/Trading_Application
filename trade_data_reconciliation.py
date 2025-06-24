#!/usr/bin/env python3
"""
TRADE DATA RECONCILIATION TOOL
Service: Database Trade Data Reconciliation
Version: 1.0.0
Last Updated: 2025-06-24

REVISION HISTORY:
- v1.0.0 (2025-06-24) - Initial reconciliation tool
  - Compares workflow metrics trade counts with actual trade records
  - Identifies discrepancies between reported and actual trades
  - Provides recommendations for data consistency

This tool reconciles the trade counts shown in workflow metrics
with actual trade records in the trades table.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import json

class TradeDataReconciliation:
    def __init__(self, db_path='./trading_system.db'):
        self.db_path = db_path
        self.discrepancies = []
        
    def run_reconciliation(self):
        """Run complete trade data reconciliation"""
        print("\n" + "="*80)
        print("🔍 TRADE DATA RECONCILIATION REPORT")
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
            
            # 1. Check workflow metrics for trade counts
            print("\n📊 WORKFLOW METRICS - REPORTED TRADES")
            print("-"*60)
            self.check_workflow_metrics(conn)
            
            # 2. Check actual trades table
            print("\n📈 TRADES TABLE - ACTUAL TRADE RECORDS")
            print("-"*60)
            self.check_trades_table(conn)
            
            # 3. Check orders table
            print("\n📋 ORDERS TABLE - ORDER RECORDS")
            print("-"*60)
            self.check_orders_table(conn)
            
            # 4. Check for trade-related data in other tables
            print("\n🔎 SEARCHING FOR TRADE DATA IN OTHER TABLES")
            print("-"*60)
            self.search_for_trade_data(conn)
            
            # 5. Reconciliation summary
            print("\n⚖️ RECONCILIATION SUMMARY")
            print("-"*60)
            self.print_reconciliation_summary()
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error during reconciliation: {e}")
            import traceback
            traceback.print_exc()
    
    def check_workflow_metrics(self, conn):
        """Check workflow metrics for reported trade counts"""
        cursor = conn.cursor()
        
        # Get total trades executed from workflow metrics
        cursor.execute("""
            SELECT 
                cycle_id,
                status,
                start_time,
                end_time,
                trades_executed,
                securities_scanned,
                patterns_detected,
                signals_generated
            FROM workflow_metrics
            WHERE trades_executed > 0
            ORDER BY start_time DESC
            LIMIT 20
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            total_reported_trades = sum(row['trades_executed'] for row in rows)
            print(f"Total trades reported in workflow_metrics: {total_reported_trades}")
            print("\nRecent cycles with trades:")
            print(f"{'Cycle ID':<30} {'Status':<12} {'Trades':<8} {'Signals':<8} {'Date'}")
            print("-"*80)
            
            for row in rows:
                cycle_id = row['cycle_id'][:30]
                print(f"{cycle_id:<30} {row['status']:<12} {row['trades_executed']:<8} "
                      f"{row['signals_generated']:<8} {row['start_time'][:10]}")
            
            self.discrepancies.append({
                'type': 'workflow_metrics',
                'total_reported': total_reported_trades,
                'cycles_with_trades': len(rows)
            })
        else:
            print("No trades reported in workflow_metrics table")
            self.discrepancies.append({
                'type': 'workflow_metrics',
                'total_reported': 0,
                'cycles_with_trades': 0
            })
        
        # Check all workflow metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_cycles,
                SUM(trades_executed) as total_trades,
                SUM(signals_generated) as total_signals,
                SUM(patterns_detected) as total_patterns,
                SUM(securities_scanned) as total_securities
            FROM workflow_metrics
        """)
        
        summary = cursor.fetchone()
        print(f"\n📊 Overall Workflow Statistics:")
        print(f"  - Total cycles: {summary['total_cycles']}")
        print(f"  - Total trades executed: {summary['total_trades'] or 0}")
        print(f"  - Total signals generated: {summary['total_signals'] or 0}")
        print(f"  - Total patterns detected: {summary['total_patterns'] or 0}")
        print(f"  - Total securities scanned: {summary['total_securities'] or 0}")
    
    def check_trades_table(self, conn):
        """Check actual trades in trades table"""
        cursor = conn.cursor()
        
        # Count trades
        cursor.execute("SELECT COUNT(*) as count FROM trades")
        trade_count = cursor.fetchone()['count']
        
        print(f"Total trades in trades table: {trade_count}")
        
        if trade_count > 0:
            # Get trade details
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM trades
                GROUP BY status
            """)
            
            print("\nTrade status breakdown:")
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]}")
            
            # Get sample trades
            cursor.execute("""
                SELECT 
                    id, symbol, signal_type, status, 
                    entry_price, exit_price, profit_loss,
                    created_at
                FROM trades
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            sample_trades = cursor.fetchall()
            if sample_trades:
                print("\nSample trades:")
                for trade in sample_trades:
                    print(f"  ID: {trade['id']}, Symbol: {trade['symbol']}, "
                          f"Type: {trade['signal_type']}, Status: {trade['status']}, "
                          f"Date: {trade['created_at']}")
        
        self.discrepancies.append({
            'type': 'trades_table',
            'actual_trades': trade_count
        })
    
    def check_orders_table(self, conn):
        """Check orders table"""
        cursor = conn.cursor()
        
        # Count orders
        cursor.execute("SELECT COUNT(*) as count FROM orders")
        order_count = cursor.fetchone()['count']
        
        print(f"Total orders in orders table: {order_count}")
        
        if order_count > 0:
            # Get order status breakdown
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM orders
                GROUP BY status
            """)
            
            print("\nOrder status breakdown:")
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]}")
        
        self.discrepancies.append({
            'type': 'orders_table',
            'order_count': order_count
        })
    
    def search_for_trade_data(self, conn):
        """Search for trade-related data in other tables"""
        cursor = conn.cursor()
        
        # Tables that might contain trade information
        potential_tables = [
            'strategy_evaluations',
            'technical_indicators',
            'pattern_analysis',
            'ml_predictions',
            'scanning_results'
        ]
        
        for table in potential_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                
                if count > 0:
                    print(f"  {table}: {count} records")
                    
                    # Check for recent activity
                    cursor.execute(f"""
                        SELECT COUNT(*) as recent_count 
                        FROM {table} 
                        WHERE created_at >= datetime('now', '-7 days')
                    """)
                    recent = cursor.fetchone()['recent_count']
                    if recent > 0:
                        print(f"    └─ Recent (7d): {recent} records")
            except:
                # Table might not exist
                pass
    
    def print_reconciliation_summary(self):
        """Print reconciliation summary and recommendations"""
        # Extract counts
        workflow_trades = 0
        actual_trades = 0
        order_count = 0
        
        for disc in self.discrepancies:
            if disc['type'] == 'workflow_metrics':
                workflow_trades = disc['total_reported']
            elif disc['type'] == 'trades_table':
                actual_trades = disc['actual_trades']
            elif disc['type'] == 'orders_table':
                order_count = disc['order_count']
        
        # Calculate discrepancy
        discrepancy = workflow_trades - actual_trades
        
        print(f"Trades reported in workflow_metrics: {workflow_trades}")
        print(f"Actual trades in trades table: {actual_trades}")
        print(f"Orders in orders table: {order_count}")
        print(f"Discrepancy: {discrepancy} trades")
        
        # Analysis and recommendations
        print("\n💡 ANALYSIS & RECOMMENDATIONS")
        print("-"*60)
        
        if discrepancy > 0:
            print(f"⚠️  ISSUE FOUND: {discrepancy} trades are reported in workflow metrics")
            print("   but not found in the trades table.")
            print("\nPossible causes:")
            print("1. The paper_trading service is counting trades but not saving them")
            print("2. Trade records are being saved to a different location")
            print("3. Database writes are failing silently")
            print("4. The trades are being simulated but not persisted")
            
            print("\n🔧 Recommended actions:")
            print("1. Check paper_trading.py for database insert operations")
            print("2. Review logs for any database errors")
            print("3. Verify paper_trading service has correct database path")
            print("4. Check if trades are being saved with different status values")
            print("5. Look for any transaction rollbacks in the code")
            
        elif actual_trades > workflow_trades:
            print("ℹ️  More trades in database than reported in workflow metrics.")
            print("   This might indicate manual trades or incomplete workflow tracking.")
            
        else:
            print("✅ Trade counts match between workflow metrics and trades table.")
        
        # Additional checks
        print("\n📝 Additional observations:")
        
        if workflow_trades > 0 and actual_trades == 0:
            print("- Workflow metrics show trade execution but trades table is empty")
            print("- This strongly suggests trades are not being persisted")
            print("- Check paper_trading.py method: _save_trade_record()")
            
        if order_count > 0 and actual_trades == 0:
            print("- Orders exist but no trades, suggesting order creation works")
            print("- but trade execution records are not being saved")

def main():
    """Main function"""
    reconciler = TradeDataReconciliation()
    reconciler.run_reconciliation()
    
    print("\n" + "="*80)
    print("📌 Next steps:")
    print("1. Review paper_trading.py to ensure trades are being saved")
    print("2. Check if database path is consistent across services")
    print("3. Look for any try/except blocks that might be hiding errors")
    print("4. Verify the paper trading service is actually executing trades")
    print("="*80)

if __name__ == "__main__":
    main()

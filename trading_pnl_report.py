#!/usr/bin/env python3
"""
TRADING P&L REPORT SERVICE
Service: Trading Profit & Loss Reporting
Version: 2.0.0
Last Updated: 2025-06-24

REVISION HISTORY:
- v2.0.0 (2025-06-24) - Complete rewrite for actual database schema
  - Added support for trades and orders tables
  - Implemented portfolio value estimation
  - Added system activity metrics
  - Enhanced reporting with win rates and statistics
- v1.0.0 (2025-06-24) - Initial version with basic P&L calculations

This script generates comprehensive P&L reports from the trading system database.
It provides:
- Portfolio summary with total value and available cash
- Trading statistics including win rates and averages
- Open positions tracking
- Closed trades history with realized P&L
- Best and worst trade identification
- Recent system activity metrics
- CSV export functionality
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
import json

class TradingPnLReport:
    def __init__(self, db_path='./trading_system.db', initial_capital=100000):
        self.db_path = db_path
        self.initial_capital = initial_capital
        self.conn = None
        
    def connect(self):
        """Connect to the trading database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_all_trades(self):
        """Get all trades from the trades table"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    symbol,
                    signal_type,
                    quantity,
                    entry_price,
                    exit_price,
                    confidence,
                    trade_reason,
                    alpaca_order_id,
                    status,
                    profit_loss,
                    created_at,
                    closed_at
                FROM trades
                ORDER BY 
                    CASE WHEN status = 'pending' OR exit_price IS NULL THEN 0 ELSE 1 END,
                    created_at DESC
            """)
            
            trades = cursor.fetchall()
            return [dict(trade) for trade in trades]
            
        except Exception as e:
            print(f"❌ Error getting trades: {e}")
            return []
    
    def get_orders_summary(self):
        """Get summary of orders from orders table"""
        try:
            cursor = self.conn.cursor()
            
            # Get order statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN status = 'filled' THEN 1 END) as filled_orders,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_orders
                FROM orders
            """)
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            print(f"⚠️  Error getting orders summary: {e}")
            return None
    
    def calculate_portfolio_metrics(self, trades):
        """Calculate portfolio metrics from trades"""
        if not trades:
            return {
                'total_trades': 0,
                'open_trades': 0,
                'closed_trades': 0,
                'total_realized_pnl': 0,
                'total_unrealized_pnl': 0,
                'estimated_portfolio_value': self.initial_capital,
                'available_cash': self.initial_capital,
                'positions_value': 0
            }
        
        # Separate open and closed trades
        open_trades = []
        closed_trades = []
        
        for trade in trades:
            if trade['exit_price'] is None or trade['status'] == 'pending':
                open_trades.append(trade)
            else:
                closed_trades.append(trade)
        
        # Calculate realized P&L
        total_realized_pnl = 0
        for trade in closed_trades:
            if trade['profit_loss'] is not None:
                total_realized_pnl += trade['profit_loss']
            elif trade['exit_price'] and trade['entry_price']:
                # Calculate P&L if not stored
                pnl = (trade['exit_price'] - trade['entry_price']) * trade['quantity']
                if trade['signal_type'] == 'SELL':
                    pnl = -pnl  # Reverse for short positions
                total_realized_pnl += pnl
        
        # Calculate unrealized P&L and positions value
        total_unrealized_pnl = 0
        positions_value = 0
        
        # For open trades, we need current prices (not available in trades table)
        # So we'll calculate based on entry prices as an estimate
        for trade in open_trades:
            if trade['entry_price'] and trade['quantity']:
                position_value = trade['entry_price'] * trade['quantity']
                positions_value += position_value
        
        # Estimate available cash
        # Start with initial capital, add realized P&L, subtract value locked in open positions
        cash_used_in_positions = sum(
            trade['entry_price'] * trade['quantity'] 
            for trade in open_trades 
            if trade['entry_price'] and trade['quantity']
        )
        
        available_cash = self.initial_capital + total_realized_pnl - cash_used_in_positions
        estimated_portfolio_value = available_cash + positions_value
        
        return {
            'total_trades': len(trades),
            'open_trades': len(open_trades),
            'closed_trades': len(closed_trades),
            'total_realized_pnl': total_realized_pnl,
            'total_unrealized_pnl': total_unrealized_pnl,
            'estimated_portfolio_value': estimated_portfolio_value,
            'available_cash': available_cash,
            'positions_value': positions_value,
            'winning_trades': len([t for t in closed_trades if t.get('profit_loss', 0) > 0]),
            'losing_trades': len([t for t in closed_trades if t.get('profit_loss', 0) < 0])
        }
    
    def get_recent_activity(self):
        """Get recent trading activity from various tables"""
        activity = {}
        
        try:
            cursor = self.conn.cursor()
            
            # Recent trading cycles
            cursor.execute("""
                SELECT COUNT(*) as total_cycles,
                       COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_cycles,
                       MAX(start_time) as last_cycle_time
                FROM trading_cycles
            """)
            activity['cycles'] = dict(cursor.fetchone())
            
            # Recent patterns detected
            cursor.execute("""
                SELECT COUNT(*) as total_patterns,
                       COUNT(DISTINCT symbol) as unique_symbols
                FROM pattern_analysis
                WHERE created_at >= datetime('now', '-7 days')
            """)
            activity['patterns'] = dict(cursor.fetchone())
            
            # Recent signals
            cursor.execute("""
                SELECT COUNT(*) as total_indicators,
                       COUNT(DISTINCT symbol) as symbols_analyzed
                FROM technical_indicators
                WHERE created_at >= datetime('now', '-7 days')
            """)
            activity['indicators'] = dict(cursor.fetchone())
            
        except Exception as e:
            print(f"⚠️  Error getting recent activity: {e}")
        
        return activity
    
    def format_currency(self, value):
        """Format currency values"""
        if value is None:
            return "$0.00"
        return f"${value:,.2f}"
    
    def format_percentage(self, value):
        """Format percentage values"""
        if value is None:
            return "0.00%"
        return f"{value:.2f}%"
    
    def print_report(self):
        """Generate and print the complete trading report"""
        print("\n" + "="*80)
        print("📊 TRADING P&L REPORT")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Initial Capital: {self.format_currency(self.initial_capital)}")
        print("="*80)
        
        # Get trades
        trades = self.get_all_trades()
        
        if not trades:
            print("\n⚠️  No trades found in the database.")
            
            # Show recent activity even if no trades
            activity = self.get_recent_activity()
            if activity:
                print("\n📈 RECENT SYSTEM ACTIVITY")
                print("-"*40)
                if 'cycles' in activity:
                    print(f"Trading Cycles: {activity['cycles']['total_cycles']} total, "
                          f"{activity['cycles']['completed_cycles']} completed")
                    if activity['cycles']['last_cycle_time']:
                        print(f"Last Cycle: {activity['cycles']['last_cycle_time']}")
                if 'patterns' in activity:
                    print(f"Patterns (7d): {activity['patterns']['total_patterns']} detected in "
                          f"{activity['patterns']['unique_symbols']} symbols")
                if 'indicators' in activity:
                    print(f"Indicators (7d): {activity['indicators']['total_indicators']} calculated for "
                          f"{activity['indicators']['symbols_analyzed']} symbols")
            return
        
        # Calculate metrics
        metrics = self.calculate_portfolio_metrics(trades)
        
        # Print portfolio summary
        print("\n💰 PORTFOLIO SUMMARY")
        print("-"*40)
        print(f"Estimated Portfolio Value: {self.format_currency(metrics['estimated_portfolio_value'])}")
        print(f"Available Cash:           {self.format_currency(metrics['available_cash'])}")
        print(f"Positions Value:          {self.format_currency(metrics['positions_value'])}")
        print(f"Total Realized P&L:       {self.format_currency(metrics['total_realized_pnl'])}")
        
        # Calculate return percentage
        total_return = ((metrics['estimated_portfolio_value'] - self.initial_capital) / 
                       self.initial_capital * 100)
        print(f"Total Return:             {self.format_percentage(total_return)}")
        
        # Print trading statistics
        print("\n📈 TRADING STATISTICS")
        print("-"*40)
        print(f"Total Trades:        {metrics['total_trades']}")
        print(f"Open Positions:      {metrics['open_trades']}")
        print(f"Closed Trades:       {metrics['closed_trades']}")
        
        if metrics['closed_trades'] > 0:
            win_rate = (metrics['winning_trades'] / metrics['closed_trades'] * 100)
            print(f"Winning Trades:      {metrics['winning_trades']} ({self.format_percentage(win_rate)})")
            print(f"Losing Trades:       {metrics['losing_trades']}")
            
            # Calculate average win/loss
            closed_trades = [t for t in trades if t['exit_price'] is not None]
            if metrics['winning_trades'] > 0:
                avg_win = sum(t.get('profit_loss', 0) for t in closed_trades if t.get('profit_loss', 0) > 0) / metrics['winning_trades']
                print(f"Average Win:         {self.format_currency(avg_win)}")
            if metrics['losing_trades'] > 0:
                avg_loss = sum(t.get('profit_loss', 0) for t in closed_trades if t.get('profit_loss', 0) < 0) / metrics['losing_trades']
                print(f"Average Loss:        {self.format_currency(avg_loss)}")
        
        # Get orders summary
        orders_summary = self.get_orders_summary()
        if orders_summary and orders_summary['total_orders'] > 0:
            print(f"\nOrder Statistics:")
            print(f"Total Orders:        {orders_summary['total_orders']}")
            print(f"Filled:              {orders_summary['filled_orders']}")
            print(f"Pending:             {orders_summary['pending_orders']}")
            print(f"Cancelled:           {orders_summary['cancelled_orders']}")
        
        # Print open positions
        open_trades = [t for t in trades if t['exit_price'] is None or t['status'] == 'pending']
        if open_trades:
            print("\n🔵 OPEN POSITIONS")
            print("-"*80)
            print(f"{'Symbol':<10} {'Type':<6} {'Qty':>8} {'Entry':>12} {'Value':>12} {'Date':<12}")
            print("-"*80)
            
            for trade in open_trades:
                position_value = (trade['entry_price'] * trade['quantity']) if trade['entry_price'] else 0
                print(f"{trade['symbol']:<10} "
                      f"{trade['signal_type']:<6} "
                      f"{trade['quantity']:>8} "
                      f"{self.format_currency(trade['entry_price']):>12} "
                      f"{self.format_currency(position_value):>12} "
                      f"{trade['created_at'][:10] if trade['created_at'] else 'N/A':<12}")
        
        # Print closed trades (last 20)
        closed_trades = [t for t in trades if t['exit_price'] is not None and t['status'] != 'pending']
        if closed_trades:
            print("\n🔴 CLOSED TRADES (Last 20)")
            print("-"*80)
            print(f"{'Symbol':<10} {'Type':<6} {'Qty':>8} {'Entry':>12} {'Exit':>12} {'P&L':>12} {'Date':<12}")
            print("-"*80)
            
            for trade in closed_trades[:20]:
                # Calculate P&L if not stored
                if trade['profit_loss'] is not None:
                    pnl = trade['profit_loss']
                else:
                    pnl = (trade['exit_price'] - trade['entry_price']) * trade['quantity']
                    if trade['signal_type'] == 'SELL':
                        pnl = -pnl
                
                print(f"{trade['symbol']:<10} "
                      f"{trade['signal_type']:<6} "
                      f"{trade['quantity']:>8} "
                      f"{self.format_currency(trade['entry_price']):>12} "
                      f"{self.format_currency(trade['exit_price']):>12} "
                      f"{self.format_currency(pnl):>12} "
                      f"{trade['closed_at'][:10] if trade['closed_at'] else 'N/A':<12}")
        
        # Best and worst trades
        if closed_trades:
            trades_with_pnl = []
            for t in closed_trades:
                if t['profit_loss'] is not None:
                    pnl = t['profit_loss']
                else:
                    pnl = (t['exit_price'] - t['entry_price']) * t['quantity']
                    if t['signal_type'] == 'SELL':
                        pnl = -pnl
                trades_with_pnl.append((t, pnl))
            
            if trades_with_pnl:
                best_trade = max(trades_with_pnl, key=lambda x: x[1])
                worst_trade = min(trades_with_pnl, key=lambda x: x[1])
                
                print("\n🏆 NOTABLE TRADES")
                print("-"*40)
                print(f"Best Trade:  {best_trade[0]['symbol']} - {self.format_currency(best_trade[1])}")
                print(f"Worst Trade: {worst_trade[0]['symbol']} - {self.format_currency(worst_trade[1])}")
        
        # Show recent activity
        activity = self.get_recent_activity()
        if activity:
            print("\n📊 RECENT SYSTEM ACTIVITY")
            print("-"*40)
            if 'cycles' in activity:
                print(f"Trading Cycles: {activity['cycles']['total_cycles']} total")
            if 'patterns' in activity:
                print(f"Patterns (7d): {activity['patterns']['total_patterns']} detected")
            if 'indicators' in activity:
                print(f"Indicators (7d): {activity['indicators']['total_indicators']} calculated")
        
        print("\n" + "="*80)
        
    def export_to_csv(self, filename='trading_report.csv'):
        """Export trades to CSV file"""
        trades = self.get_all_trades()
        if trades:
            # Add calculated P&L for trades that don't have it
            for trade in trades:
                if trade['profit_loss'] is None and trade['exit_price'] and trade['entry_price']:
                    pnl = (trade['exit_price'] - trade['entry_price']) * trade['quantity']
                    if trade['signal_type'] == 'SELL':
                        pnl = -pnl
                    trade['calculated_pnl'] = pnl
                else:
                    trade['calculated_pnl'] = trade['profit_loss']
            
            df = pd.DataFrame(trades)
            df.to_csv(filename, index=False)
            print(f"\n✅ Report exported to {filename}")
        else:
            print("\n⚠️  No trades to export")

def main():
    """Main function to run P&L report generation"""
    # Check if database exists
    db_path = './trading_system.db'
    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        print("Make sure the trading system is properly initialized.")
        sys.exit(1)
    
    # Get initial capital from user or use default
    try:
        initial_capital = float(input("Enter initial capital (default: $100,000): $").strip() or "100000")
    except ValueError:
        initial_capital = 100000
    
    # Create report
    report = TradingPnLReport(db_path, initial_capital)
    
    if not report.connect():
        sys.exit(1)
    
    try:
        # Generate report
        report.print_report()
        
        # Ask if user wants to export
        response = input("\nExport report to CSV? (y/n): ")
        if response.lower() == 'y':
            filename = input("Enter filename (default: trading_report.csv): ").strip()
            if not filename:
                filename = 'trading_report.csv'
            report.export_to_csv(filename)
            
    except KeyboardInterrupt:
        print("\n\n❌ Report generation cancelled")
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
    finally:
        report.disconnect()

if __name__ == "__main__":
    main()

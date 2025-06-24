#!/usr/bin/env python3
"""
P/L Tracking Enhancement for Web Dashboard
Adds comprehensive profit/loss tracking and display
Version: 1.0.0
"""

import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import pandas as pd

# Create a Blueprint for P/L tracking routes
pl_bp = Blueprint('pl_tracking', __name__, url_prefix='/api/pl')

class PLTracker:
    """Enhanced P/L tracking functionality"""
    
    def __init__(self, db_path='./trading_system.db'):
        self.db_path = db_path
        self._ensure_pl_tables()
    
    def _ensure_pl_tables(self):
        """Ensure P/L tracking tables exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create P/L summary table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pl_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                realized_pl REAL DEFAULT 0,
                unrealized_pl REAL DEFAULT 0,
                total_pl REAL DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0,
                avg_win REAL DEFAULT 0,
                avg_loss REAL DEFAULT 0,
                largest_win REAL DEFAULT 0,
                largest_loss REAL DEFAULT 0,
                commission_paid REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        ''')
        
        # Create position P/L tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS position_pl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL,
                quantity INTEGER NOT NULL,
                side TEXT NOT NULL,
                realized_pl REAL DEFAULT 0,
                unrealized_pl REAL DEFAULT 0,
                commission REAL DEFAULT 0,
                opened_at TEXT NOT NULL,
                closed_at TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_realtime_pl(self):
        """Get real-time P/L including open positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get today's realized P/L from closed trades
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN pnl IS NOT NULL THEN pnl ELSE 0 END) as realized_pl,
                    COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades,
                    COUNT(*) as total_trades,
                    AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                    AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss,
                    MAX(pnl) as largest_win,
                    MIN(pnl) as largest_loss
                FROM trades
                WHERE DATE(completed_at) = ? AND status = 'closed'
            ''', (today,))
            
            realized_stats = cursor.fetchone()
            
            # Get unrealized P/L from open positions
            cursor.execute('''
                SELECT 
                    symbol,
                    quantity,
                    entry_price,
                    current_price,
                    side,
                    (CASE 
                        WHEN side = 'buy' THEN (current_price - entry_price) * quantity
                        WHEN side = 'sell' THEN (entry_price - current_price) * quantity
                    END) as unrealized_pl
                FROM positions
                WHERE status = 'open'
            ''')
            
            open_positions = cursor.fetchall()
            
            # Calculate totals
            realized_pl = realized_stats[0] or 0
            winning_trades = realized_stats[1] or 0
            losing_trades = realized_stats[2] or 0
            total_trades = realized_stats[3] or 0
            
            unrealized_pl = sum(pos[5] or 0 for pos in open_positions)
            total_pl = realized_pl + unrealized_pl
            
            # Position details
            positions_detail = []
            for pos in open_positions:
                positions_detail.append({
                    'symbol': pos[0],
                    'quantity': pos[1],
                    'entry_price': pos[2],
                    'current_price': pos[3],
                    'side': pos[4],
                    'unrealized_pl': pos[5] or 0,
                    'pl_percent': ((pos[3] - pos[2]) / pos[2] * 100) if pos[2] > 0 else 0
                })
            
            return {
                'summary': {
                    'realized_pl': round(realized_pl, 2),
                    'unrealized_pl': round(unrealized_pl, 2),
                    'total_pl': round(total_pl, 2),
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'total_trades': total_trades,
                    'win_rate': round((winning_trades / total_trades * 100) if total_trades > 0 else 0, 1),
                    'avg_win': round(realized_stats[4] or 0, 2),
                    'avg_loss': round(realized_stats[5] or 0, 2),
                    'largest_win': round(realized_stats[6] or 0, 2),
                    'largest_loss': round(realized_stats[7] or 0, 2)
                },
                'open_positions': positions_detail,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting realtime P/L: {e}")
            return {
                'summary': {
                    'realized_pl': 0,
                    'unrealized_pl': 0,
                    'total_pl': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_trades': 0,
                    'win_rate': 0
                },
                'open_positions': [],
                'error': str(e)
            }
        finally:
            conn.close()
    
    def get_historical_pl(self, days=30):
        """Get historical P/L data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Get daily P/L
            cursor.execute('''
                SELECT 
                    DATE(completed_at) as trade_date,
                    SUM(pnl) as daily_pl,
                    COUNT(*) as trades,
                    COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                    COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses
                FROM trades
                WHERE DATE(completed_at) >= ? AND status = 'closed'
                GROUP BY DATE(completed_at)
                ORDER BY trade_date
            ''', (start_date,))
            
            daily_data = []
            cumulative_pl = 0
            
            for row in cursor.fetchall():
                daily_pl = row[1] or 0
                cumulative_pl += daily_pl
                
                daily_data.append({
                    'date': row[0],
                    'daily_pl': round(daily_pl, 2),
                    'cumulative_pl': round(cumulative_pl, 2),
                    'trades': row[2],
                    'wins': row[3],
                    'losses': row[4],
                    'win_rate': round((row[3] / row[2] * 100) if row[2] > 0 else 0, 1)
                })
            
            return daily_data
            
        except Exception as e:
            print(f"Error getting historical P/L: {e}")
            return []
        finally:
            conn.close()
    
    def update_position_prices(self, price_updates):
        """Update current prices for positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for symbol, price in price_updates.items():
                cursor.execute('''
                    UPDATE positions
                    SET current_price = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE symbol = ? AND status = 'open'
                ''', (price, symbol))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating position prices: {e}")
            return False
        finally:
            conn.close()

# Initialize P/L tracker
pl_tracker = PLTracker()

# P/L API Routes
@pl_bp.route('/realtime')
def get_realtime_pl():
    """Get real-time P/L data"""
    return jsonify(pl_tracker.get_realtime_pl())

@pl_bp.route('/historical')
def get_historical_pl():
    """Get historical P/L data"""
    days = int(request.args.get('days', 30))
    return jsonify(pl_tracker.get_historical_pl(days))

@pl_bp.route('/update_prices', methods=['POST'])
def update_prices():
    """Update position prices"""
    price_updates = request.json
    success = pl_tracker.update_position_prices(price_updates)
    return jsonify({'success': success})

# Add this to your enhanced web_dashboard_service.py:
"""
In your web_dashboard_service.py, add:

1. Import the P/L blueprint:
from pl_tracking_enhancement import pl_bp, PLTracker

2. In your __init__ method:
# Initialize P/L tracker
self.pl_tracker = PLTracker(db_path=self.db_path)

# Register P/L blueprint
self.app.register_blueprint(pl_bp)

3. Add to your main dashboard route a P/L section
"""

# Dashboard HTML snippet for P/L display
PL_DASHBOARD_HTML = '''
<!-- Add this to your trading_workflow_dashboard.html after the metrics grid -->

<!-- P/L Summary Section -->
<div class="pl-summary">
    <h2 class="section-title">💰 Profit & Loss Summary</h2>
    <div class="pl-grid">
        <div class="pl-card">
            <div class="pl-label">Realized P/L</div>
            <div class="pl-value" id="realized-pl">$0.00</div>
            <div class="pl-subtitle">Today's Closed Trades</div>
        </div>
        <div class="pl-card">
            <div class="pl-label">Unrealized P/L</div>
            <div class="pl-value" id="unrealized-pl">$0.00</div>
            <div class="pl-subtitle">Open Positions</div>
        </div>
        <div class="pl-card">
            <div class="pl-label">Total P/L</div>
            <div class="pl-value total" id="total-pl">$0.00</div>
            <div class="pl-subtitle">Combined</div>
        </div>
        <div class="pl-card">
            <div class="pl-label">Win Rate</div>
            <div class="pl-value" id="win-rate">0%</div>
            <div class="pl-subtitle"><span id="wins">0</span>W / <span id="losses">0</span>L</div>
        </div>
    </div>
    
    <!-- Open Positions Table -->
    <div class="positions-section">
        <h3>Open Positions</h3>
        <table class="positions-table">
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Qty</th>
                    <th>Entry</th>
                    <th>Current</th>
                    <th>P/L</th>
                    <th>P/L %</th>
                </tr>
            </thead>
            <tbody id="open-positions">
                <!-- Positions will be inserted here -->
            </tbody>
        </table>
    </div>
</div>

<style>
/* P/L Styles */
.pl-summary {
    background: linear-gradient(135deg, #1a1f2e 0%, #151922 100%);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.pl-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.pl-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
}

.pl-label {
    font-size: 0.9rem;
    color: #8892a6;
    margin-bottom: 0.5rem;
}

.pl-value {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.pl-value.positive {
    color: #00ff88;
}

.pl-value.negative {
    color: #ff3366;
}

.pl-value.total {
    background: linear-gradient(45deg, #00d4ff, #0099ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.pl-subtitle {
    font-size: 0.8rem;
    color: #8892a6;
}

.positions-table {
    width: 100%;
    margin-top: 1rem;
}

.positions-table th {
    text-align: left;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    font-size: 0.85rem;
    color: #8892a6;
}

.positions-table td {
    padding: 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
}

/* Fix for black screen refresh issue */
body {
    opacity: 0;
    animation: fadeIn 0.3s ease-in forwards;
}

@keyframes fadeIn {
    to {
        opacity: 1;
    }
}
</style>

<script>
// P/L Update Function
async function updatePL() {
    try {
        const response = await fetch('/api/pl/realtime');
        const data = await response.json();
        
        // Update summary
        const summary = data.summary;
        
        // Update values with color coding
        updatePLValue('realized-pl', summary.realized_pl);
        updatePLValue('unrealized-pl', summary.unrealized_pl);
        updatePLValue('total-pl', summary.total_pl);
        
        // Update win rate
        document.getElementById('win-rate').textContent = summary.win_rate + '%';
        document.getElementById('wins').textContent = summary.winning_trades;
        document.getElementById('losses').textContent = summary.losing_trades;
        
        // Update positions table
        const tbody = document.getElementById('open-positions');
        tbody.innerHTML = data.open_positions.map(pos => `
            <tr>
                <td style="font-weight: bold;">${pos.symbol}</td>
                <td>${pos.quantity}</td>
                <td>$${pos.entry_price.toFixed(2)}</td>
                <td>$${pos.current_price.toFixed(2)}</td>
                <td class="${pos.unrealized_pl >= 0 ? 'positive' : 'negative'}">
                    $${pos.unrealized_pl.toFixed(2)}
                </td>
                <td class="${pos.pl_percent >= 0 ? 'positive' : 'negative'}">
                    ${pos.pl_percent.toFixed(2)}%
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error updating P/L:', error);
    }
}

function updatePLValue(elementId, value) {
    const element = document.getElementById(elementId);
    element.textContent = '$' + value.toFixed(2);
    
    // Color coding
    if (value > 0) {
        element.classList.add('positive');
        element.classList.remove('negative');
    } else if (value < 0) {
        element.classList.add('negative');
        element.classList.remove('positive');
    }
}

// Update P/L every 5 seconds
setInterval(updatePL, 5000);
updatePL(); // Initial load

// Fix for black screen on refresh
document.addEventListener('DOMContentLoaded', function() {
    // Smooth fade-in handled by CSS
});
</script>
'''

print("""
P/L Tracking Enhancement Created!

To integrate:
1. Save this as pl_tracking_enhancement.py
2. Update your web_dashboard_service.py to import and register the blueprint
3. Add the HTML snippet to your trading_workflow_dashboard.html

The P/L display will show:
- Real-time realized P/L (today's closed trades)
- Unrealized P/L (open positions)
- Total P/L
- Win rate with trade counts
- Detailed open positions table

The black screen refresh issue is fixed with a smooth fade-in animation.
""")

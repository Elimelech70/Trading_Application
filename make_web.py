#!/usr/bin/env python3
"""
TRADING SYSTEM PHASE 1
Service: make_web.py
Version: 1.0.1
Last Updated: 2025-06-22

REVISION HISTORY:
- v1.0.1 (2025-06-22) - Fixed CSS syntax error
- v1.0.0 (2025-06-22) - Initial version

PURPOSE:
Creates web interface for Trading Application following project standards.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def create_web_interface():
    """Create the web interface with proper CSS embedding"""
    
    # HTML template with CSS properly embedded in string
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Application</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header {
            background: #333;
            color: white;
            padding: 20px;
            margin: -20px -20px 20px -20px;
            border-radius: 10px 10px 0 0;
        }
        
        .nav {
            background: #444;
            padding: 10px;
            margin: 0 -20px 20px -20px;
        }
        
        .nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            display: inline-block;
        }
        
        .nav a:hover {
            background: #555;
        }
        
        .content {
            padding: 20px 0;
        }
        
        .status-card {
            background: #f8f9fa;
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        
        .status-healthy {
            border-left: 4px solid #28a745;
        }
        
        .status-error {
            border-left: 4px solid #dc3545;
        }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .metric {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
            text-align: center;
        }
        
        .metric h3 {
            margin: 0 0 10px 0;
            color: #495057;
        }
        
        .metric .value {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }
        
        .button {
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 5px;
        }
        
        .button:hover {
            background: #0056b3;
        }
        
        .button.success {
            background: #28a745;
        }
        
        .button.success:hover {
            background: #218838;
        }
        
        .button.danger {
            background: #dc3545;
        }
        
        .button.danger:hover {
            background: #c82333;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        
        th {
            background: #f8f9fa;
            font-weight: bold;
        }
        
        .footer {
            margin-top: 40px;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Trading Application Dashboard</h1>
            <p>Real-time trading system management</p>
        </div>
        
        <div class="nav">
            <a href="#overview">Overview</a>
            <a href="#services">Services</a>
            <a href="#trading">Trading</a>
            <a href="#performance">Performance</a>
            <a href="#logs">Logs</a>
        </div>
        
        <div class="content">
            <section id="overview">
                <h2>System Overview</h2>
                
                <div class="metrics">
                    <div class="metric">
                        <h3>System Status</h3>
                        <div class="value">Active</div>
                    </div>
                    <div class="metric">
                        <h3>Active Services</h3>
                        <div class="value">8/8</div>
                    </div>
                    <div class="metric">
                        <h3>Trading Mode</h3>
                        <div class="value">Paper</div>
                    </div>
                    <div class="metric">
                        <h3>Database Status</h3>
                        <div class="value">Connected</div>
                    </div>
                </div>
                
                <div class="status-card status-healthy">
                    <h3>Quick Actions</h3>
                    <button class="button success">Start Trading</button>
                    <button class="button">View Positions</button>
                    <button class="button">Check Performance</button>
                    <button class="button danger">Stop All Services</button>
                </div>
            </section>
            
            <section id="services">
                <h2>Service Status</h2>
                
                <table>
                    <thead>
                        <tr>
                            <th>Service</th>
                            <th>Port</th>
                            <th>Status</th>
                            <th>Uptime</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Trading Engine</td>
                            <td>5000</td>
                            <td>Running</td>
                            <td>2h 15m</td>
                            <td><button class="button">Restart</button></td>
                        </tr>
                        <tr>
                            <td>Market Data</td>
                            <td>5001</td>
                            <td>Running</td>
                            <td>2h 15m</td>
                            <td><button class="button">Restart</button></td>
                        </tr>
                        <tr>
                            <td>Pattern Analysis</td>
                            <td>5002</td>
                            <td>Running</td>
                            <td>2h 15m</td>
                            <td><button class="button">Restart</button></td>
                        </tr>
                        <tr>
                            <td>Risk Management</td>
                            <td>5003</td>
                            <td>Running</td>
                            <td>2h 15m</td>
                            <td><button class="button">Restart</button></td>
                        </tr>
                        <tr>
                            <td>News Service</td>
                            <td>5004</td>
                            <td>Running</td>
                            <td>2h 15m</td>
                            <td><button class="button">Restart</button></td>
                        </tr>
                        <tr>
                            <td>Portfolio Manager</td>
                            <td>5005</td>
                            <td>Running</td>
                            <td>2h 15m</td>
                            <td><button class="button">Restart</button></td>
                        </tr>
                        <tr>
                            <td>Scheduler</td>
                            <td>5007</td>
                            <td>Running</td>
                            <td>2h 15m</td>
                            <td><button class="button">Restart</button></td>
                        </tr>
                        <tr>
                            <td>ML Service</td>
                            <td>5009</td>
                            <td>Running</td>
                            <td>2h 15m</td>
                            <td><button class="button">Restart</button></td>
                        </tr>
                    </tbody>
                </table>
            </section>
        </div>
        
        <div class="footer">
            <p>Trading Application v1.0.1 | Last Updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write the HTML file
    output_path = Path("trading_dashboard.html")
    
    try:
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Successfully created web interface: {output_path}")
        print(f"📁 File location: {output_path.absolute()}")
        
        # If running in Colab, provide additional instructions
        if 'google.colab' in sys.modules:
            print("\n🌐 To view in Google Colab:")
            print("1. Run: from IPython.display import HTML")
            print("2. Run: HTML(filename='trading_dashboard.html')")
            
    except Exception as e:
        print(f"❌ Error creating web interface: {e}")
        return False
    
    return True

def main():
    """Main entry point"""
    print("Creating Trading Application Web Interface...")
    print("-" * 50)
    
    success = create_web_interface()
    
    if success:
        print("\n✅ Web interface created successfully!")
    else:
        print("\n❌ Failed to create web interface")
        sys.exit(1)

if __name__ == "__main__":
    main()

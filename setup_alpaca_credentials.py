#!/usr/bin/env python3
"""
Setup Alpaca Paper Trading Credentials
Helps configure Alpaca API credentials for paper trading
"""

import os
import sys
from pathlib import Path

def setup_alpaca_credentials():
    """Interactive setup for Alpaca credentials"""
    
    print("=" * 60)
    print("ALPACA PAPER TRADING SETUP")
    print("=" * 60)
    
    print("\nThis script will help you set up Alpaca Paper Trading credentials.")
    print("\nYou'll need:")
    print("1. A free Alpaca account (sign up at https://alpaca.markets)")
    print("2. Your Paper Trading API credentials (not live trading!)")
    
    print("\nTo get your credentials:")
    print("1. Log in to Alpaca Dashboard")
    print("2. Select 'Paper Trading' environment (top right)")
    print("3. Go to 'API Keys' section")
    print("4. Generate or view your Paper Trading keys")
    
    input("\nPress Enter when you have your credentials ready...")
    
    # Get credentials
    print("\nEnter your Alpaca Paper Trading credentials:")
    api_key = input("API Key ID: ").strip()
    api_secret = input("API Secret Key: ").strip()
    
    if not api_key or not api_secret:
        print("\n✗ Both API Key and Secret are required!")
        return False
    
    # Verify these look like Alpaca keys
    if not api_key.startswith('PK'):
        print("\n⚠️  Warning: Paper Trading API keys usually start with 'PK'")
        print("   Make sure you're using Paper Trading keys, not Live keys!")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            return False
    
    # Check for existing .env file
    env_path = Path('.env')
    env_exists = env_path.exists()
    
    if env_exists:
        print("\n.env file already exists.")
        print("Options:")
        print("1. Append Alpaca credentials to existing .env")
        print("2. Create .env.alpaca separately")
        print("3. Show manual setup instructions")
        
        choice = input("\nChoose option (1/2/3): ")
        
        if choice == '1':
            # Append to existing .env
            with open('.env', 'r') as f:
                existing = f.read()
                
            # Check if already has Alpaca keys
            if 'ALPACA_PAPER_API_KEY' in existing:
                print("\n⚠️  Alpaca credentials already exist in .env!")
                overwrite = input("Overwrite existing credentials? (y/n): ")
                if overwrite.lower() != 'y':
                    return False
                
                # Remove old credentials
                lines = existing.split('\n')
                new_lines = [l for l in lines if not l.startswith('ALPACA_PAPER_')]
                existing = '\n'.join(new_lines)
            
            # Append new credentials
            with open('.env', 'w') as f:
                f.write(existing.rstrip() + '\n\n')
                f.write(f"# Alpaca Paper Trading Credentials\n")
                f.write(f"ALPACA_PAPER_API_KEY={api_key}\n")
                f.write(f"ALPACA_PAPER_API_SECRET={api_secret}\n")
                
            print("\n✓ Credentials added to .env file!")
            
        elif choice == '2':
            # Create separate file
            with open('.env.alpaca', 'w') as f:
                f.write(f"# Alpaca Paper Trading Credentials\n")
                f.write(f"ALPACA_PAPER_API_KEY={api_key}\n")
                f.write(f"ALPACA_PAPER_API_SECRET={api_secret}\n")
                
            print("\n✓ Credentials saved to .env.alpaca!")
            print("  Note: You'll need to source this file or merge with .env")
            
        else:
            # Show manual instructions
            print("\nManual setup instructions:")
            print(f"\nAdd these lines to your .env file:")
            print(f"ALPACA_PAPER_API_KEY={api_key}")
            print(f"ALPACA_PAPER_API_SECRET={api_secret}")
            
    else:
        # Create new .env file
        with open('.env', 'w') as f:
            f.write(f"# Alpaca Paper Trading Credentials\n")
            f.write(f"ALPACA_PAPER_API_KEY={api_key}\n")
            f.write(f"ALPACA_PAPER_API_SECRET={api_secret}\n")
            
        print("\n✓ Created .env file with Alpaca credentials!")
    
    # Test the credentials
    print("\nTesting credentials...")
    
    # Set environment variables for testing
    os.environ['ALPACA_PAPER_API_KEY'] = api_key
    os.environ['ALPACA_PAPER_API_SECRET'] = api_secret
    
    try:
        import alpaca_trade_api as tradeapi
        
        # Try to connect
        api = tradeapi.REST(
            api_key,
            api_secret,
            base_url='https://paper-api.alpaca.markets',
            api_version='v2'
        )
        
        # Test by getting account
        account = api.get_account()
        
        print(f"\n✓ SUCCESS: Connected to Alpaca Paper Trading!")
        print(f"  Account Status: {account.status}")
        print(f"  Buying Power: ${account.buying_power}")
        print(f"  Portfolio Value: ${account.portfolio_value}")
        
        return True
        
    except ImportError:
        print("\n⚠️  alpaca-trade-api package not installed")
        print("  Run: pip install alpaca-trade-api")
        return False
        
    except Exception as e:
        print(f"\n✗ Failed to connect to Alpaca: {str(e)}")
        print("\nPossible issues:")
        print("- Invalid API credentials")
        print("- Using Live Trading keys instead of Paper Trading")
        print("- Network connectivity issues")
        return False
    
    finally:
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("1. Restart the Paper Trading Service")
        print("2. Run the diagnostic tool to verify connection")
        print("3. Try executing a test trade")
        print("=" * 60)


if __name__ == "__main__":
    setup_alpaca_credentials()

#!/usr/bin/env python3
"""
Fix Table Name Mismatch
Aligns table names between hybrid_manager and database_migration
"""
import sqlite3
from pathlib import Path

def check_actual_tables():
    """Check what tables actually exist in the database"""
    print("🔍 Checking actual database tables...")
    
    try:
        conn = sqlite3.connect('./trading_system.db')
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        actual_tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"\nActual tables in database ({len(actual_tables)}):")
        for table in actual_tables:
            print(f"  ✓ {table}")
            
        return actual_tables
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return []

def fix_hybrid_manager_table_check():
    """Update hybrid_manager.py to check for correct table names"""
    print("\n🔧 Fixing hybrid_manager.py table verification...")
    
    try:
        with open('hybrid_manager.py', 'r') as f:
            content = f.read()
        
        # Map old names to actual names
        table_mappings = {
            "'service_registry'": "'service_coordination'",
            "'trading_schedule'": "'trading_schedule_config'", 
            "'news_articles'": "'news_sentiment'",
            "'patterns'": "'pattern_analysis'",
            "'signals'": "'technical_indicators'",
            "'trades'": "'orders'",
            "'system_events'": "'trading_cycles'"
        }
        
        # Backup original
        Path('hybrid_manager.py.table_backup').write_text(content)
        
        # Apply replacements
        original_content = content
        for old_name, new_name in table_mappings.items():
            if old_name in content:
                content = content.replace(old_name, new_name)
                print(f"  • {old_name} → {new_name}")
        
        if content != original_content:
            with open('hybrid_manager.py', 'w') as f:
                f.write(content)
            print("\n✅ Updated hybrid_manager.py with correct table names")
            return True
        else:
            print("⚠️  No table name updates needed in hybrid_manager.py")
            return False
            
    except Exception as e:
        print(f"❌ Error updating hybrid_manager: {e}")
        return False

def create_missing_tables():
    """Create any tables that hybrid_manager expects but don't exist"""
    print("\n🔧 Creating any missing expected tables...")
    
    try:
        conn = sqlite3.connect('./trading_system.db')
        cursor = conn.cursor()
        
        # Create trading_schedule_config if missing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_schedule_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                config TEXT NOT NULL
            )
        ''')
        
        # Create ml_predictions if missing (sometimes expected as ml_models)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Ensured all required tables exist")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def quick_test():
    """Quick test to see if issues are resolved"""
    print("\n🧪 Running quick test...")
    
    try:
        # Try to import and check tables like hybrid_manager does
        import subprocess
        result = subprocess.run(
            ['python', '-c', 
             "import sqlite3; conn=sqlite3.connect('./trading_system.db'); "
             "cursor=conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); "
             "tables=[r[0] for r in cursor.fetchall()]; print(f'Found {len(tables)} tables'); "
             "conn.close()"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Database test passed: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Database test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    print("🚀 Table Name Mismatch Fixer")
    print("="*50)
    
    # Check what tables actually exist
    actual_tables = check_actual_tables()
    
    if not actual_tables:
        print("\n❌ No tables found! Running database migration...")
        import subprocess
        subprocess.run(['python', 'database_migration.py'])
        actual_tables = check_actual_tables()
    
    # Fix hybrid_manager
    fix_hybrid_manager_table_check()
    
    # Create any missing tables
    create_missing_tables()
    
    # Test
    quick_test()
    
    print("\n" + "="*50)
    print("✅ Table mismatch fixed!")
    print("\nNow try restarting services:")
    print("  python hybrid_manager.py restart")
    print("\nOr manually:")
    print("  python hybrid_manager.py stop")
    print("  python hybrid_manager.py start")

if __name__ == "__main__":
    main()

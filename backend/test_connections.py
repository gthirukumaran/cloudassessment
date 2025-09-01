#!/usr/bin/env python3
"""
Test script to verify database connections and table creation
Uses SQLite for local testing when PostgreSQL/Redis are not available
"""
import sys
import os
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings
from app.database import Base, init_db
from app.models import *  # Import all models

def test_postgresql_connection():
    """Test PostgreSQL database connection"""
    print("\n🔍 Testing PostgreSQL Connection...")
    print(f"Database URL: {settings.database_url.replace(settings.database_url.split('@')[0].split('//')[1], '***')}")
    
    try:
        # Create engine for testing
        engine = create_engine(settings.database_url)
        
        # Test basic connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL Connection Successful!")
            print(f"   Version: {version[:50]}...")
            
        # Test if database exists and is accessible
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database();"))
            db_name = result.fetchone()[0]
            print(f"   Connected to database: {db_name}")
            
        return True, engine
        
    except OperationalError as e:
        print(f"❌ PostgreSQL Connection Failed: {str(e)}")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False, None

def create_sqlite_fallback():
    """Create SQLite database as fallback for local testing"""
    print("\n🔄 Creating SQLite fallback database for local testing...")
    
    try:
        # Create SQLite database in backend directory
        db_path = Path(__file__).parent / "securitya_local.db"
        sqlite_url = f"sqlite:///{db_path}"
        
        print(f"   SQLite database: {db_path}")
        
        # Create engine
        engine = create_engine(sqlite_url, echo=False)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT sqlite_version();"))
            version = result.fetchone()[0]
            print(f"✅ SQLite Connection Successful!")
            print(f"   SQLite version: {version}")
        
        return True, engine
        
    except Exception as e:
        print(f"❌ SQLite setup failed: {str(e)}")
        return False, None

def test_redis_connection():
    """Test Redis cache connection"""
    print("\n🔍 Testing Redis Connection...")
    print(f"Redis URL: {settings.redis_url}")
    
    try:
        import redis
        
        # Parse Redis URL and create connection
        if hasattr(settings, 'redis_password') and settings.redis_password:
            r = redis.Redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        else:
            r = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        
        # Test connection
        r.ping()
        print("✅ Redis Connection Successful!")
        
        # Test basic operations
        r.set("test_key", "test_value", ex=60)
        value = r.get("test_key")
        if value == "test_value":
            print("   ✅ Redis read/write operations working")
            r.delete("test_key")
        
        # Get Redis info
        info = r.info()
        print(f"   Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"   Used memory: {info.get('used_memory_human', 'Unknown')}")
        
        return True
        
    except ImportError:
        print("❌ Redis package not installed")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        print("   ℹ️  This is expected if Redis is not running locally")
        return False

def check_database_tables(engine):
    """Check if required database tables exist"""
    print("\n🔍 Checking Database Tables...")
    
    try:
        # Get table inspector
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"   Found {len(existing_tables)} existing tables:")
        for table in sorted(existing_tables):
            print(f"     - {table}")
        
        # Expected tables based on models
        expected_tables = {
            'users', 'organizations', 'scans', 'scan_results', 'findings',
            'chat_sessions', 'chat_messages', 'reports', 'compliance_frameworks',
            'compliance_controls', 'custom_scan_templates'
        }
        
        missing_tables = expected_tables - set(existing_tables)
        extra_tables = set(existing_tables) - expected_tables
        
        if missing_tables:
            print(f"\n⚠️  Missing tables: {', '.join(sorted(missing_tables))}")
        else:
            print("\n✅ All expected tables exist!")
            
        if extra_tables:
            print(f"   Additional tables found: {', '.join(sorted(extra_tables))}")
        
        return len(missing_tables) == 0, missing_tables
        
    except Exception as e:
        print(f"❌ Error checking tables: {str(e)}")
        return False, set()

def create_missing_tables(engine):
    """Create missing database tables"""
    print("\n🔧 Creating missing database tables...")
    
    try:
        # Create all tables using the models
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        return False

def show_table_schemas(engine):
    """Show the schema of created tables"""
    print("\n📋 Table Schemas:")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table_name in sorted(tables):
            print(f"\n   📄 {table_name}:")
            columns = inspector.get_columns(table_name)
            for col in columns:
                col_type = str(col['type'])
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                print(f"     - {col['name']}: {col_type} {nullable}{default}")
                
    except Exception as e:
        print(f"❌ Error showing schemas: {str(e)}")

def main():
    """Main test function"""
    print("🚀 Securra Database & Cache Connection Test")
    print("=" * 50)
    
    # Test PostgreSQL first
    pg_success, pg_engine = test_postgresql_connection()
    
    # If PostgreSQL fails, try SQLite fallback
    if not pg_success:
        print("\n🔄 PostgreSQL not available, trying SQLite fallback...")
        sqlite_success, sqlite_engine = create_sqlite_fallback()
        if sqlite_success:
            engine = sqlite_engine
            db_type = "SQLite"
        else:
            print("❌ Both PostgreSQL and SQLite failed")
            return 1
    else:
        engine = pg_engine
        db_type = "PostgreSQL"
    
    # Test Redis (optional)
    redis_success = test_redis_connection()
    
    # Check and create tables
    tables_ok, missing_tables = check_database_tables(engine)
    
    if not tables_ok:
        print(f"\n🔧 Creating missing tables in {db_type}...")
        if create_missing_tables(engine):
            tables_ok, _ = check_database_tables(engine)
            if tables_ok:
                show_table_schemas(engine)
    else:
        show_table_schemas(engine)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Connection Test Summary:")
    print(f"   Database ({db_type}): {'✅ Connected' if (pg_success or sqlite_success) else '❌ Failed'}")
    print(f"   Redis Cache: {'✅ Connected' if redis_success else '⚠️  Not Available (Optional)'}")
    print(f"   Database Tables: {'✅ Ready' if tables_ok else '❌ Issues'}")
    
    if (pg_success or sqlite_success) and tables_ok:
        print(f"\n🎉 Database ({db_type}) and tables are ready!")
        if not redis_success:
            print("   ℹ️  Redis is optional and can be added later for caching")
        return 0
    else:
        print("\n⚠️  Some issues found. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
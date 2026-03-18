#!/usr/bin/env python3
"""
Setup script to initialize the database schema and import CSV data.
Run this once against your Render database:

    DATABASE_URL=your_render_url python scripts/setup_db.py

Example:
    DATABASE_URL=postgresql://user:pass@host:5432/dbname python scripts/setup_db.py
"""
import os
import sys
from sqlalchemy import create_engine, text


def setup_database():
    """Initialize database schema and load data from CSVs."""
    
    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("\nUsage:")
        print("  DATABASE_URL=your_render_url python scripts/setup_db.py")
        sys.exit(1)
    
    # Add SSL for cloud databases
    if "postgresql://" in DATABASE_URL and "sslmode" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL + "?sslmode=require"
    
    print(f"📦 Connecting to database...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    # Step 1: Create schema
    print("\n📋 Creating database schema...")
    try:
        with open("scripts/schema.sql", "r") as f:
            schema_sql = f.read()
        
        with engine.begin() as conn:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
            for stmt in statements:
                conn.execute(text(stmt))
        
        print("✅ Database schema created!")
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")
        sys.exit(1)
    
    # Step 2: Import CSV data
    print("\n📊 Importing CSV data...")
    try:
        # Set environment variable for import_core to use
        os.environ["DATABASE_URL"] = DATABASE_URL
        
        from import_core import main as import_data
        import_data(engine)
        print("✅ CSV data imported successfully!")
    except ImportError:
        print("\n⚠️  Could not import from import_core.py directly")
        print("Running import_core.py as standalone script...")
        os.system(f"DATABASE_URL={DATABASE_URL} python scripts/import_core.py")
    except Exception as e:
        print(f"❌ Failed to import CSV data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n✨ Database setup complete!")
    print("Your backend should now work properly on production.")


if __name__ == "__main__":
    setup_database()

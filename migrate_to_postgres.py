#!/usr/bin/env python3
"""
Database migration script to export SQLite data and import to PostgreSQL.
Run this script to migrate your data from SQLite to Vercel Postgres.

Usage:
    python migrate_to_postgres.py export  # Export SQLite data to SQL file
    python migrate_to_postgres.py import  # Import SQL file to PostgreSQL
"""

import sys
import asyncio
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from api.config import settings

# Database paths
SQLITE_DB_PATH = "sightings.db"
EXPORT_FILE = "sightings_export.sql"


async def export_sqlite_data():
    """Export SQLite data to SQL file."""
    print("🔄 Exporting SQLite data...")
    
    if not Path(SQLITE_DB_PATH).exists():
        print(f"❌ SQLite database not found at {SQLITE_DB_PATH}")
        return False
    
    # Connect to SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    with open(EXPORT_FILE, 'w') as f:
        f.write("-- SkyWatch API Database Export\n")
        f.write("-- Generated for PostgreSQL import\n\n")
        
        for table in tables:
            print(f"📊 Exporting table: {table}")
            
            # Get table schema (we'll recreate with SQLAlchemy)
            cursor.execute(f"SELECT * FROM {table} LIMIT 0")
            columns = [description[0] for description in cursor.description]
            
            # Get all data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if rows:
                f.write(f"-- Data for table: {table}\n")
                f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n")
                
                for i, row in enumerate(rows):
                    # Convert row to values, handling None/NULL
                    values = []
                    for value in row:
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, str):
                            # Escape single quotes
                            escaped = value.replace("'", "''")
                            values.append(f"'{escaped}'")
                        else:
                            values.append(str(value))
                    
                    # Add comma except for last row
                    comma = "," if i < len(rows) - 1 else ";"
                    f.write(f"  ({', '.join(values)}){comma}\n")
                
                f.write(f"\n-- {len(rows)} rows exported for {table}\n\n")
                print(f"  ✅ {len(rows)} rows exported")
            else:
                print(f"  📝 Table {table} is empty")
    
    conn.close()
    print(f"✅ Export complete! Data saved to {EXPORT_FILE}")
    print(f"📁 File size: {Path(EXPORT_FILE).stat().st_size / 1024 / 1024:.2f} MB")
    return True


async def import_to_postgres(database_url: str):
    """Import SQL file to PostgreSQL."""
    print("🔄 Importing data to PostgreSQL...")
    
    if not Path(EXPORT_FILE).exists():
        print(f"❌ Export file not found: {EXPORT_FILE}")
        print("   Run 'python migrate_to_postgres.py export' first")
        return False
    
    try:
        # Create tables first using SQLAlchemy
        print("📋 Creating database tables...")
        from api.database import create_tables
        
        # Temporarily update DATABASE_URL for import
        original_url = settings.DATABASE_URL
        settings.DATABASE_URL = database_url
        
        await create_tables()
        print("✅ Tables created successfully")
        
        # Connect to PostgreSQL directly for data import
        conn = await asyncpg.connect(database_url)
        
        # Read and execute SQL file
        print("📊 Importing data...")
        with open(EXPORT_FILE, 'r') as f:
            sql_content = f.read()
        
        # Split by statements and execute
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for stmt in statements:
            if stmt.strip():
                try:
                    await conn.execute(stmt)
                    print(f"  ✅ Executed: {stmt[:50]}...")
                except Exception as e:
                    print(f"  ⚠️  Failed: {stmt[:50]}... - {e}")
        
        await conn.close()
        
        # Restore original DATABASE_URL
        settings.DATABASE_URL = original_url
        
        print("✅ Import complete!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


async def test_connection(database_url: str):
    """Test PostgreSQL connection."""
    print("🔗 Testing PostgreSQL connection...")
    
    try:
        conn = await asyncpg.connect(database_url)
        result = await conn.fetchval("SELECT version()")
        await conn.close()
        print(f"✅ Connection successful!")
        print(f"📊 PostgreSQL version: {result}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migrate_to_postgres.py export")
        print("  python migrate_to_postgres.py import <postgres_url>")
        print("  python migrate_to_postgres.py test <postgres_url>")
        return
    
    command = sys.argv[1]
    
    if command == "export":
        asyncio.run(export_sqlite_data())
    
    elif command == "import":
        if len(sys.argv) < 3:
            print("❌ Please provide PostgreSQL URL")
            print("   Example: python migrate_to_postgres.py import postgresql://user:pass@host:5432/db")
            return
        
        database_url = sys.argv[2]
        asyncio.run(import_to_postgres(database_url))
    
    elif command == "test":
        if len(sys.argv) < 3:
            print("❌ Please provide PostgreSQL URL")
            return
        
        database_url = sys.argv[2]
        asyncio.run(test_connection(database_url))
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: export, import, test")


if __name__ == "__main__":
    main()
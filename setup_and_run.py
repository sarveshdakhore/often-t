#!/usr/bin/env python3
"""
Setup and Run script for the Travel Itinerary API
This script installs dependencies, runs migrations, and runs the application
"""
import os
import subprocess
import sys
import time
from sqlalchemy import text # Import text


def fix_alembic_config():
    """Fix the alembic.ini file with a proper database URL."""
    print("Checking and fixing alembic.ini...")
    alembic_ini_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alembic.ini')
    
    if not os.path.exists(alembic_ini_path):
        print("❌ alembic.ini not found. Please create it first.")
        return False
    
    with open(alembic_ini_path, 'r') as f:
        content = f.read()
    
    # Check if the file contains any problematic database URL
    if 'sqlalchemy.url = ' in content:
        print("⚠️ Updating database URL in alembic.ini...")
        # Get database URL from environment or use default local URL
        db_url = os.environ.get("DATABASE_URL", "postgresql://sarveshdakhore:@localhost:5432/postgres")
        
        # Convert asyncpg URL to standard URL for alembic if needed
        if '+asyncpg' in db_url:
            db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        # Use regex to replace the entire sqlalchemy.url line
        import re
        content = re.sub(
            r'sqlalchemy\.url\s*=\s*.*',
            f'sqlalchemy.url = {db_url}',
            content
        )
        
        with open(alembic_ini_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated alembic.ini with database URL: {db_url}")
    else:
        print("⚠️ Could not find sqlalchemy.url in alembic.ini")
    
    return True

def run_migrations():
    """Runs database migrations using manage.py apply."""
    print("\nRunning database migrations...")
    try:
        # Use sys.executable to ensure using the same python env
        # Capture output for better debugging
        process = subprocess.run(
            [sys.executable, "manage.py", "apply"],
            capture_output=True,
            text=True,
            check=False, # Don't raise exception immediately
            env=os.environ.copy() # Ensure DATABASE_URL is passed
        )
        # Print stdout/stderr regardless of success/failure
        if process.stdout:
            print("--- Migration stdout ---")
            print(process.stdout)
        if process.stderr:
            print("--- Migration stderr ---", file=sys.stderr)
            print(process.stderr, file=sys.stderr)

        if process.returncode != 0:
            print(f"❌ Migration command failed with exit code {process.returncode}.")
            return False
        else:
            print("✅ Database migrations successful!")
            # Also run status to display current migration info
            subprocess.run([sys.executable, "manage.py", "status"], env=os.environ.copy())
            return True
    except FileNotFoundError:
        print("❌ manage.py not found. Check your project structure.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred during migrations: {e}", file=sys.stderr)
        return False

def test_db_connection():
    print("Testing database connection...")
    try:
        # Import here after packages are installed
        from core.database import engine
        import asyncio

        async def test_conn():
            try:
                async with engine.connect() as conn:
                    # Wrap the query string in text()
                    result = await conn.execute(text("SELECT 1"))
                    print("✅ Database connection successful!")
                    return True
            except Exception as e:
                print(f"❌ Database connection failed: {str(e)}")
                return False

        return asyncio.run(test_conn())
    except Exception as e:
        # Catch potential import errors if sqlalchemy wasn't installed
        print(f"❌ Error testing database connection (check imports/installation): {str(e)}")
        return False

def run_application():
    """Runs the application using subprocess.run without reload."""
    print("\n🚀 Starting FastAPI application...")
    try:
        subprocess.run(
            ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            check=True, # Raise exception if uvicorn fails
            env=os.environ.copy() # Pass the current environment
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Uvicorn failed to start: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Uvicorn stopped.")

if __name__ == "__main__":
    print("=" * 50)
    print("Travel Itinerary API Setup and Run")
    print("=" * 50)

    # Fix alembic.ini before running migrations
    fix_alembic_config()

    # Run migrations before testing connection or starting app
    migrations_success = run_migrations()
    if not migrations_success:
        print("\n⚠️ Migrations failed. Attempting to continue anyway...")
        # Continue instead of exiting, in case the app can still run

    # Wait a moment to ensure DB is ready after migrations
    print("\nWaiting for database...")
    time.sleep(2)

    # Try to connect to the database
    if test_db_connection():
        run_application()
    else:
        print("\n⚠️ Database connection failed. Application cannot start.")
        sys.exit(1) # Exit if DB connection fails

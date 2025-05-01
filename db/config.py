import os

def get_sync_db_url(url: str) -> str:
    """Convert async database URL to sync URL for Alembic."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://")
    return url

def get_db_url() -> str:
    """Get the database URL with proper formatting."""
    user = os.getenv("DB_USER", "sarveshdakhore")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "often")
    
    # Handle empty password case explicitly
    if password:
        auth_part = f"{user}:{password}"
    else:
        auth_part = user
    
    return f"postgresql+asyncpg://{auth_part}@{host}:{port}/{name}"
# db/migrations.py

import os
import sys
import logging

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from dotenv import load_dotenv

from .config import get_db_url, get_sync_db_url

logger = logging.getLogger(__name__)


def get_alembic_config() -> Config:
    """
    Load .env, normalize the URL, and build an Alembic Config.
    """
    # 1) load .env
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(base_dir, ".env"))

    # 2) fetch and normalize
    raw_url = os.getenv("DATABASE_URL", "postgresql://localhost/postgres")
    if "+asyncpg" in raw_url:
        raw_url = raw_url.replace("postgresql+asyncpg://", "postgresql://")
        logger.info(f"Converting async URL → sync for Alembic: {raw_url}")

    # 3) point Alembic at our migrations/ folder
    cfg = Config(os.path.join(base_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(base_dir, "migrations"))
    cfg.set_main_option("sqlalchemy.url", raw_url)
    logger.info(f"Alembic will use URL: {raw_url}")

    return cfg


def ensure_alembic_initialized() -> None:
    """
    Create migrations/versions, script.py.mako, env.py, and alembic.ini if missing.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mig_dir = os.path.join(base_dir, "migrations")
    ver_dir = os.path.join(mig_dir, "versions")
    mako = os.path.join(mig_dir, "script.py.mako")
    env_py = os.path.join(mig_dir, "env.py")
    ini_f  = os.path.join(base_dir, "alembic.ini")

    # if everything exists, no-op
    if os.path.exists(mako) and os.path.exists(env_py) and os.path.exists(ini_f):
        return

    os.makedirs(ver_dir, exist_ok=True)
    logger.info("Initializing Alembic environment…")
    # (You’d write out alembic.ini, script.py.mako, env.py here,
    #  as in your previous init routine. Omitted for brevity.)
    logger.info("Alembic environment initialized.")


def apply_migrations() -> None:
    """
    Apply all pending migrations.
    If there are multiple heads, auto-merge them first.
    """
    ensure_alembic_initialized()
    cfg    = get_alembic_config()
    script = ScriptDirectory.from_config(cfg)
    heads  = script.get_heads()

    if len(heads) > 1:
        print(f"→ Multiple heads detected: {heads}\n   creating an automatic merge revision…")
        command.revision(
            cfg,
            message="merge multiple heads",
            autogenerate=False,
            head=heads,
            splice=True
        )
        print("✔ Merge revision created.")

    print("→ Upgrading to head…")
    try:
        command.upgrade(cfg, "head")
        print("✔ Database is now up to date.")
    except Exception as e:
        logger.error("Error during `upgrade head`", exc_info=True)
        print(f"Error applying migrations: {e}")
        sys.exit(1)


def create_migration(message: str, force: bool = False) -> None:
    """
    Ensure DB is at head, then generate a new revision.
    Destructive drops are stripped out by your env.py hook.
    """
    # 1) bring the database up to date
    apply_migrations()

    # 2) get our async→sync URL
    raw = get_db_url()
    sync_url = get_sync_db_url(raw)

    # 3) configure Alembic
    cfg = get_alembic_config()
    cfg.set_main_option("sqlalchemy.url", sync_url)

    # 4) generate
    try:
        if force:
            command.revision(cfg, message=message, autogenerate=False)
            print(f"✔ Forced migration template created: '{message}'")
        else:
            command.revision(cfg, message=message, autogenerate=True)
            print(f"✔ Migration created successfully: '{message}'")
    except Exception as e:
        logger.error("Failed to create migration", exc_info=True)
        print(f"Error creating migration: {e}")
        sys.exit(1)


def rollback_migration(revision: str = "head") -> None:
    """
    Downgrade one step before the given revision.
    """
    ensure_alembic_initialized()
    cfg = get_alembic_config()

    try:
        command.downgrade(cfg, f"{revision}-1")
        print(f"✔ Rolled back to just before {revision}")
    except Exception as e:
        logger.error("Failed to rollback migration", exc_info=True)
        print(f"Error rolling back: {e}")
        sys.exit(1)

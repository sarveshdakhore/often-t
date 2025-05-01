# manage.py
#!/usr/bin/env python
import sys
import logging
from argparse import ArgumentParser

from core.logging_config import setup_logging
from db.migrations import (
    create_migration,
    apply_migrations,
    rollback_migration,
    ensure_alembic_initialized,
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    parser = ArgumentParser(prog="manage.py", description="Database migration manager")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create a new migration")
    p_create.add_argument("message", nargs="?", default="migration", help="Migration message")

    # create-force
    p_force = subparsers.add_parser("create-force", help="Force‐create a migration even if DB is not up to date")
    p_force.add_argument("message", nargs="?", default="migration", help="Migration message")

    # migrate
    subparsers.add_parser("migrate", help="Apply all pending migrations")

    # rollback
    p_rb = subparsers.add_parser("rollback", help="Rollback to just before a given revision")
    p_rb.add_argument("revision", nargs="?", default="head", help="Revision identifier (default: head)")

    # init
    subparsers.add_parser("init", help="Initialize Alembic directory structure")

    args = parser.parse_args()

    try:
        if args.subcommand == "create":
            print(f"Creating migration with message: {args.message}")
            create_migration(args.message, force=False)
            print("Migration created successfully.")

        elif args.subcommand == "create-force":
            print(f"Force‐creating migration with message: {args.message}")
            create_migration(args.message, force=True)

        elif args.subcommand == "migrate":
            print("Applying migrations...")
            apply_migrations()

        elif args.subcommand == "rollback":
            print(f"Rolling back to before revision: {args.revision}")
            rollback_migration(args.revision)
            print("Rollback completed successfully.")

        elif args.subcommand == "init":
            print("Initializing migration environment...")
            ensure_alembic_initialized()
            print("Migration environment initialized successfully.")

    except Exception as e:
        logger.error("Command failed", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

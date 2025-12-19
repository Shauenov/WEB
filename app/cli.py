"""Simple management commands for local development."""

import argparse
import sys

from app.core.db import create_db_and_tables


def _cmd_create_tables(args: argparse.Namespace) -> None:
    create_db_and_tables(drop_existing=args.drop_existing, force=args.force)
    print("Tables created from SQLModel metadata (no migrations).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backend management commands")
    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser(
        "create-tables",
        help="Create database tables directly from models without running Alembic migrations",
    )
    create_parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop all existing tables before creating new ones",
    )
    create_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow execution when ENVIRONMENT is not 'local'",
    )
    create_parser.set_defaults(func=_cmd_create_tables)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

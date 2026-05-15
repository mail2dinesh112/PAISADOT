import argparse
import re
from pathlib import Path

from alembic import command
from alembic.config import Config


APP_DIR = Path(__file__).resolve().parents[1]
VERSIONS_DIR = APP_DIR / "migrations" / "versions"
REVISION_PREFIX = re.compile(r"^(\d+)_")


def next_revision_id() -> str:
    max_revision = 0

    for migration_file in VERSIONS_DIR.glob("*.py"):
        match = REVISION_PREFIX.match(migration_file.name)
        if match:
            max_revision = max(max_revision, int(match.group(1)))

    return f"{max_revision + 1:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a numbered Alembic migration.")
    parser.add_argument("message", help="Migration message, for example: add categories table")
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Create an empty migration instead of using autogenerate.",
    )
    args = parser.parse_args()

    config = Config(APP_DIR / "alembic.ini")
    command.revision(
        config,
        message=args.message,
        autogenerate=not args.empty,
        rev_id=next_revision_id(),
    )


if __name__ == "__main__":
    main()

"""
One-time bootstrap script to create the first Super Admin.

Not exposed over HTTP — the /pd/createsuperadmin API endpoint requires an
existing Super Admin to call it, so the very first one has to be created
this way. Run once against a fresh database:

    python scripts/seed_superadmin.py \
        --first-name Ada --email ada@paisadot.in \
        --username ada --password "change-me-now"

Refuses to run if a Super Admin already exists.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argon2 import PasswordHasher

from api.common.session import Session
from api.common.models import User, RoleType


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the first Super Admin user.")
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", default=None)
    parser.add_argument("--email", required=True)
    parser.add_argument("--phone", default=None)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    if len(args.password) < 8:
        print("Refusing to seed: password must be at least 8 characters.")
        raise SystemExit(1)

    db = Session()

    try:
        existing_superadmin = db.query(User).filter(
            User.role_type == RoleType.SUPERADMIN
        ).first()

        if existing_superadmin:
            print(
                f"Refusing to seed: a Super Admin already exists "
                f"({existing_superadmin.email}). Use POST /pd/createsuperadmin instead."
            )
            raise SystemExit(1)

        email = args.email.strip().lower()

        if db.query(User).filter(User.email == email).first():
            print(f"Refusing to seed: a user with email {email} already exists.")
            raise SystemExit(1)

        if db.query(User).filter(User.username == args.username).first():
            print(f"Refusing to seed: a user with username {args.username} already exists.")
            raise SystemExit(1)

        ph = PasswordHasher()

        superadmin = User(
            first_name=args.first_name,
            last_name=args.last_name,
            email=email,
            phone_number=args.phone,
            username=args.username,
            password_hash=ph.hash(args.password),
            role_type=RoleType.SUPERADMIN,
            account_id=None,
            is_active=True,
        )

        db.add(superadmin)
        db.commit()

        print(f"Super Admin created: {email} (username: {args.username})")

    finally:
        db.close()


if __name__ == "__main__":
    main()

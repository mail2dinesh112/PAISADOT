"""make users.account_id nullable for platform-level super admins

Revision ID: 02
Revises: 01
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "02"
down_revision: Union[str, None] = "01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "account_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "account_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=False,
    )

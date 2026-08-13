"""make categories.account_id nullable for system-wide categories

Revision ID: 03
Revises: 02
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "03"
down_revision: Union[str, None] = "02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "categories",
        "account_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "categories",
        "account_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=False,
    )

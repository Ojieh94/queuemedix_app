"""add missed appointment status

Revision ID: 399782333a14
Revises: 
Create Date: 2026-06-06 00:32:26.193267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '399782333a14'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TYPE appointment_status ADD VALUE IF NOT EXISTS 'missed';"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass

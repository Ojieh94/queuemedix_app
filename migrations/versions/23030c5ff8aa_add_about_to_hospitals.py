"""add about to hospitals

Revision ID: 23030c5ff8aa
Revises: 
Create Date: 2026-05-03 20:46:28.611377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23030c5ff8aa'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('hospitals', sa.Column('about', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('hospitals', 'about')

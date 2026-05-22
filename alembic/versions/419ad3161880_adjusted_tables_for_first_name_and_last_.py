"""adjusted tables for first name and last name

Revision ID: 419ad3161880
Revises: 1479974f5ce1
Create Date: 2026-05-21 15:47:58.621883

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '419ad3161880'


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def _index_exists(index_name: str, table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def create_table_if_not_exists(table_name: str, *args, **kwargs):
    if not _table_exists(table_name):
        op.create_table(table_name, *args, **kwargs)


def create_index_if_not_exists(index_name: str, table_name: str, *args, **kwargs):
    if not _index_exists(index_name, table_name):
        op.create_index(index_name, table_name, *args, **kwargs)


down_revision: Union[str, Sequence[str], None] = "1479974f5ce1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    target_tables = ['admins', 'doctors', 'patients', 'hospitals']

    for table in target_tables:
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        if inspector.has_table(table):
            columns = [col['name'] for col in inspector.get_columns(table)]

            if 'first_name' not in columns:
                op.add_column(table, sa.Column(
                    'first_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

            #  ADD THIS BLOCK FOR MIDDLE NAME:
            if 'middle_name' not in columns:
                op.add_column(table, sa.Column(
                    'middle_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

            if 'last_name' not in columns:
                op.add_column(table, sa.Column(
                    'last_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    target_tables = ['admins', 'doctors', 'patients', 'hospitals']

    for table in target_tables:
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        if inspector.has_table(table):
            columns = [col['name'] for col in inspector.get_columns(table)]

            if 'last_name' in columns:
                op.drop_column(table, 'last_name')
            # REMOVE MIDDLE NAME ON DOWNGRADE:
            if 'middle_name' in columns:
                op.drop_column(table, 'middle_name')
            if 'first_name' in columns:
                op.drop_column(table, 'first_name')

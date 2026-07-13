"""add_status_to_users
Revision ID: 2ef5ad183c04
Revises: f42d86dba5f9
Create Date: 2026-07-09 08:24:08.898152
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '2ef5ad183c04'
down_revision: Union[str, Sequence[str], None] = 'f42d86dba5f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('users', sa.Column('status', sa.String(), nullable=False, server_default='pending'))

def downgrade() -> None:
    op.drop_column('users', 'status')

"""merge heads

Revision ID: de9ed8d3beb0
Revises: 24484a4cb6f1
Create Date: 2026-06-17 13:56:59.344024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de9ed8d3beb0'
down_revision: Union[str, Sequence[str], None] = '24484a4cb6f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

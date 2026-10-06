"""create ai_interaction_events table

Revision ID: e6b1c4a9d7f2
Revises: b362a288d8eb
Create Date: 2026-10-06 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e6b1c4a9d7f2'
down_revision: Union[str, Sequence[str], None] = 'b362a288d8eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The model defines ai_interaction_events but no migration creates it.
    # Skipped if the table already exists.
    bind = op.get_bind()
    if "ai_interaction_events" in set(sa.inspect(bind).get_table_names()):
        return

    op.create_table(
        "ai_interaction_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("time", sa.DateTime(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("communication_type", sa.String(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", "time"),
    )
    op.execute("SELECT create_hypertable('ai_interaction_events', 'time', if_not_exists => TRUE)")


def downgrade() -> None:
    op.drop_table("ai_interaction_events")

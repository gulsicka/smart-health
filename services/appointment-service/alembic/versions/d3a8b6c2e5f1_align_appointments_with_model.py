"""align appointments table with the current model

Revision ID: d3a8b6c2e5f1
Revises: f8afc8514f36
Create Date: 2026-10-06 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd3a8b6c2e5f1'
down_revision: Union[str, Sequence[str], None] = 'f8afc8514f36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The first migration describes appointments with a slot_id and no
    # clinic/date/time columns. The model stores clinic_id, date, start_time and
    # end_time directly and enforces one appointment per provider slot.
    # Every step is conditional, so databases that already match are untouched.
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = {c["name"] for c in insp.get_columns("appointments")}

    new_columns = [
        ("clinic_id", sa.Integer(), "0"),
        ("date", sa.Date(), "1970-01-01"),
        ("start_time", sa.Time(), "00:00:00"),
        ("end_time", sa.Time(), "00:00:00"),
    ]
    for name, col_type, default in new_columns:
        if name not in columns:
            # server_default lets this work even if rows already exist
            op.add_column(
                "appointments",
                sa.Column(name, col_type, nullable=False, server_default=default),
            )
            op.alter_column("appointments", name, server_default=None)

    op.execute("ALTER TABLE appointments DROP COLUMN IF EXISTS slot_id")

    existing_uniques = {u["name"] for u in insp.get_unique_constraints("appointments")}
    if "uq_provider_slot" not in existing_uniques:
        op.create_unique_constraint(
            "uq_provider_slot", "appointments", ["provider_id", "date", "start_time"]
        )


def downgrade() -> None:
    op.drop_constraint("uq_provider_slot", "appointments", type_="unique")
    op.add_column("appointments", sa.Column("slot_id", sa.Integer(), nullable=True))
    for name in ("end_time", "start_time", "date", "clinic_id"):
        op.drop_column("appointments", name)

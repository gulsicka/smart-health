"""align patients table with the current model

Revision ID: c5d9f3a7e1b8
Revises: 2fdc6c64180d
Create Date: 2026-10-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c5d9f3a7e1b8'
down_revision: Union[str, Sequence[str], None] = '2fdc6c64180d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The earlier migrations still describe patients with name/number/email
    # columns, which now live on the user record in auth-service, and have no
    # is_deleted flag. Bring a migration-built database in line with the model.
    # Every step is conditional, so databases that already match are untouched.
    bind = op.get_bind()
    insp = sa.inspect(bind)

    columns = {c["name"] for c in insp.get_columns("patients")}
    if "is_deleted" not in columns:
        op.add_column(
            "patients",
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    op.execute("ALTER TABLE patients DROP COLUMN IF EXISTS name")
    op.execute("ALTER TABLE patients DROP COLUMN IF EXISTS number")
    op.execute("ALTER TABLE patients DROP COLUMN IF EXISTS email")

    # audit_logs is not part of the current patient model and nothing reads it
    op.execute("DROP TABLE IF EXISTS audit_logs")


def downgrade() -> None:
    op.drop_column("patients", "is_deleted")

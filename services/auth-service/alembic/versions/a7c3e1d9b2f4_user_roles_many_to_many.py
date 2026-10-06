"""users to roles many-to-many (user_roles), drop users.role_id

Revision ID: a7c3e1d9b2f4
Revises: 2ef5ad183c04
Create Date: 2026-10-06 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7c3e1d9b2f4'
down_revision: Union[str, Sequence[str], None] = '2ef5ad183c04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The earlier migrations describe a single role per user (users.role_id).
    # The application model uses a user_roles junction table instead. Bring a
    # database built from migrations up to that schema; databases that already
    # match it are left untouched.
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if "user_roles" not in set(insp.get_table_names()):
        op.create_table(
            "user_roles",
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True),
        )

    user_columns = {c["name"] for c in insp.get_columns("users")}
    if "role_id" in user_columns:
        op.execute(
            "INSERT INTO user_roles (user_id, role_id) "
            "SELECT id, role_id FROM users WHERE role_id IS NOT NULL "
            "ON CONFLICT DO NOTHING"
        )
        op.drop_column("users", "role_id")


def downgrade() -> None:
    op.add_column("users", sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=True))
    op.execute(
        "UPDATE users SET role_id = (SELECT MIN(role_id) FROM user_roles WHERE user_roles.user_id = users.id)"
    )
    op.drop_table("user_roles")

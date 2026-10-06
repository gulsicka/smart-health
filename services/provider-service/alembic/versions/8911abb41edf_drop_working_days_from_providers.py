from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '8911abb41edf'
down_revision = '92e15a12b459'
branch_labels = None
depends_on = None


def upgrade():
    # The earlier revision is empty, so on a fresh database none of the tables
    # exist yet. Create whatever is missing, then drop working_days if present.
    # Databases that already have these tables are left untouched.
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    if "departments" not in existing:
        op.create_table(
            "departments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
        )
        op.create_index("ix_departments_id", "departments", ["id"])

    if "clinics" not in existing:
        op.create_table(
            "clinics",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("address", sa.String(), nullable=False),
        )
        op.create_index("ix_clinics_id", "clinics", ["id"])

    if "clinic_departments" not in existing:
        op.create_table(
            "clinic_departments",
            sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), primary_key=True),
            sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), primary_key=True),
        )

    if "providers" not in existing:
        op.create_table(
            "providers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False, unique=True),
            sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.create_index("ix_providers_id", "providers", ["id"])

    if "provider_availability" not in existing:
        op.create_table(
            "provider_availability",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=False),
            sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
            sa.Column("schedule", postgresql.JSONB(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("provider_id", "clinic_id", name="uq_provider_clinic"),
        )
        op.create_index("ix_provider_availability_id", "provider_availability", ["id"])

    op.execute("ALTER TABLE providers DROP COLUMN IF EXISTS working_days")


def downgrade():
    op.add_column('providers', sa.Column('working_days', postgresql.ARRAY(sa.Text()), nullable=True))

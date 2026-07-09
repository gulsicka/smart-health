from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '8911abb41edf'
down_revision = '92e15a12b459'
branch_labels = None
depends_on = None

def upgrade():
    op.drop_column('providers', 'working_days')

def downgrade():
    op.add_column('providers', sa.Column('working_days', postgresql.ARRAY(sa.Text()), nullable=True))

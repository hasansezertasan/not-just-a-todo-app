"""Add server_default=func.now() to StandardMixin timestamp columns

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-10 00:50:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

# StandardMixin lives on every model; covers all 5 tables × 2 timestamp cols.
TABLES = ("sequence", "sequence_template", "task", "task_template", "user")
COLUMNS = ("date_created", "date_updated")


def upgrade():
    for table in TABLES:
        with op.batch_alter_table(table) as batch_op:
            for column in COLUMNS:
                batch_op.alter_column(
                    column,
                    existing_type=sa.DateTime(),
                    existing_nullable=False,
                    server_default=sa.func.now(),
                )


def downgrade():
    for table in TABLES:
        with op.batch_alter_table(table) as batch_op:
            for column in COLUMNS:
                batch_op.alter_column(
                    column,
                    existing_type=sa.DateTime(),
                    existing_nullable=False,
                    server_default=None,
                )

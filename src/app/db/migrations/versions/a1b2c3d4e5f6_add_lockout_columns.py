"""Add account-lockout columns to user

Revision ID: a1b2c3d4e5f6
Revises: d6b27a916acd
Create Date: 2026-05-10 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "d6b27a916acd"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(
            sa.Column(
                "failed_login_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column("locked_until", sa.DateTime(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_column("locked_until")
        batch_op.drop_column("failed_login_count")

"""add address column to events table
Revision ID: 01e42381f7ff
Revises: fdfcd5967030
Create Date: 2022-02-20 02:31:31.727254
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '01e42381f7ff'
down_revision = 'fdfcd5967030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("address", sa.Text)
    )
    pass


def downgrade() -> None:
    op.drop_column("events", "address")
    pass

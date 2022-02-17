"""hello world
Revision ID: fdfcd5967030
Revises: Init events table
Create Date: 2022-02-16 09:06:50.442279
"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic
revision = 'fdfcd5967030'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, nullable=True, primary_key=True),
        sa.Column("start_time", sa.DateTime, nullable=True, index=True),
        sa.Column("end_time", sa.DateTime, nullable=True),
        sa.Column("name", sa.Text, nullable=True),
        sa.Column("category", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("location", Geometry('POINT'), nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("organizer", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("events")

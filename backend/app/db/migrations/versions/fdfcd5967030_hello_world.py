"""hello world
Revision ID: fdfcd5967030
Revises: Init events table
Create Date: 2022-02-16 09:06:50.442279
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = 'fdfcd5967030'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("onepa_eventid", sa.Integer, nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), index=True),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("name", sa.Text),
        sa.Column("category", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("lat", sa.Float),
        sa.Column("lng", sa.Float),
        sa.Column("url", sa.Text),
        sa.Column("organizer", sa.Text),
        sa.UniqueConstraint("onepa_eventid"),
    )


def downgrade() -> None:
    op.drop_table("events")

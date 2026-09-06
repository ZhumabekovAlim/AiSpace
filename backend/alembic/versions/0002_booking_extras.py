"""booking extras: comment and amenities

Revision ID: 0002_booking_extras
Revises: 0001_initial
Create Date: 2026-09-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_booking_extras"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("comment", sa.Text(), nullable=True))
    op.add_column(
        "bookings",
        sa.Column(
            "amenities",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("bookings", "amenities")
    op.drop_column("bookings", "comment")

"""telegram fields on users and booking transfers

Revision ID: 0003_telegram_and_transfers
Revises: 0002_booking_extras
Create Date: 2026-09-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_telegram_and_transfers"
down_revision: Union[str, None] = "0002_booking_extras"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Поля пользователя: телефон и привязка Telegram ---
    op.add_column("users", sa.Column("phone", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("telegram_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "users", sa.Column("telegram_link_code", sa.String(12), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("telegram_link_expires", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_users_phone", "users", ["phone"])
    op.create_unique_constraint("uq_users_telegram_id", "users", ["telegram_id"])

    # --- Передачи броней ---
    transfer_status = postgresql.ENUM(
        "pending", "accepted", "rejected", "cancelled", name="transfer_status"
    )
    transfer_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "booking_transfers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "booking_id",
            sa.Integer,
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="transfer_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("new_title", sa.String(255), nullable=True),
        sa.Column("new_comment", sa.Text, nullable=True),
        sa.Column("new_amenities", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("new_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_booking_transfers_booking_id", "booking_transfers", ["booking_id"]
    )
    op.create_index(
        "ix_booking_transfers_status", "booking_transfers", ["status"]
    )


def downgrade() -> None:
    op.drop_table("booking_transfers")
    postgresql.ENUM(name="transfer_status").drop(op.get_bind(), checkfirst=True)
    op.drop_constraint("uq_users_telegram_id", "users", type_="unique")
    op.drop_constraint("uq_users_phone", "users", type_="unique")
    op.drop_column("users", "telegram_link_expires")
    op.drop_column("users", "telegram_link_code")
    op.drop_column("users", "telegram_id")
    op.drop_column("users", "phone")

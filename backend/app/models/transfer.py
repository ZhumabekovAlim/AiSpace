import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TransferStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class BookingTransfer(Base):
    """Запрос на передачу брони от владельца (from_user) к запросившему (to_user).

    Получатель может приложить желаемые изменения (тема/комментарий/допы/время),
    которые применятся к брони при подтверждении владельцем.
    """

    __tablename__ = "booking_transfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), index=True
    )
    from_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    to_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus, name="transfer_status"),
        default=TransferStatus.pending,
        index=True,
    )

    # Желаемые изменения получателя (все опциональны).
    new_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_amenities: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    new_start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    new_end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    booking: Mapped["Booking"] = relationship()  # noqa: F821
    from_user: Mapped["User"] = relationship(foreign_keys=[from_user_id])  # noqa: F821
    to_user: Mapped["User"] = relationship(foreign_keys=[to_user_id])  # noqa: F821

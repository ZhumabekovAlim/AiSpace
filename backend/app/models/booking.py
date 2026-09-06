from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Booking(Base):
    """Бронь комнаты на интервал [start_time, end_time).

    Ключевое требование задания — брони одной комнаты не пересекаются.
    Гарантию даёт НЕ проверка в коде (в ней есть гонка между двумя запросами),
    а ограничение на уровне PostgreSQL:

        EXCLUDE USING gist (
            room_id WITH =,
            tstzrange(start_time, end_time) WITH &&
        )

    БД физически не даст вставить пересекающийся интервал для той же комнаты,
    даже при одновременных запросах. Само ограничение добавляется миграцией
    Alembic (требует расширения btree_gist). См. alembic/versions.
    """

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))

    # Храним оба конца интервала как timestamptz (в UTC).
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    room: Mapped["Room"] = relationship(back_populates="bookings")  # noqa: F821
    user: Mapped["User"] = relationship(back_populates="bookings")  # noqa: F821

    __table_args__ = (
        # Дублирующая, «дешёвая» проверка корректности интервала.
        CheckConstraint("end_time > start_time", name="ck_booking_time_order"),
    )

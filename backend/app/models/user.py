import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """Две роли: обычный сотрудник и админ.

    Обычный — бронирует и отменяет только свои брони.
    Админ — плюс управляет комнатами и может отменять любые брони.
    """

    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.user
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Телефон — общий идентификатор для веба и Telegram (привязка по номеру).
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    # Один аккаунт на веб и Telegram: сюда пишется chat id после привязки.
    telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, unique=True, nullable=True
    )
    # Одноразовый код привязки, генерируется в вебе (второй способ линковки).
    telegram_link_code: Mapped[str | None] = mapped_column(
        String(12), nullable=True
    )
    telegram_link_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    bookings: Mapped[list["Booking"]] = relationship(  # noqa: F821
        back_populates="user"
    )

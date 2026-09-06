from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    # Телефон — общий идентификатор для веба и Telegram (привязка по номеру).
    phone: str | None = Field(default=None, max_length=32)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Что пользователь может поменять в своём профиле."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=32)


class UserRead(BaseModel):
    """Ответ наружу: без hashed_password.

    email — обычная строка (не EmailStr): формат проверяем на ВХОДЕ (UserCreate),
    а ответ не должен падать на уже сохранённых данных, напр. на служебных
    доменах вроде .local, которые email-validator считает зарезервированными.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime


class UserProfile(UserRead):
    """Профиль текущего юзера: плюс флаг привязки Telegram."""

    telegram_linked: bool = False


class UserAdminRead(UserRead):
    """Расширенная карточка для админки: с числом броней пользователя."""

    bookings_count: int = 0


class UserAdminUpdate(BaseModel):
    """Что админ может менять у пользователя."""

    role: UserRole | None = None
    is_active: bool | None = None

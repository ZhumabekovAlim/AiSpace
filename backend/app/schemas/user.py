from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


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
    role: UserRole
    is_active: bool
    created_at: datetime


class UserAdminRead(UserRead):
    """Расширенная карточка для админки: с числом броней пользователя."""

    bookings_count: int = 0


class UserAdminUpdate(BaseModel):
    """Что админ может менять у пользователя."""

    role: UserRole | None = None
    is_active: bool | None = None

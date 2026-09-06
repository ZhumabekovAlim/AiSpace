"""Привязка Telegram к аккаунту двумя способами: код из веба и номер телефона."""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()


class LinkError(Exception):
    pass


def normalize_phone(phone: str) -> str:
    """Только цифры — чтобы +7(701)... и 7701... матчились одинаково."""
    return "".join(ch for ch in phone if ch.isdigit())


async def generate_link_code(db: AsyncSession, user: User) -> str:
    """Генерирует одноразовый код привязки (веб-способ)."""
    code = secrets.token_hex(3).upper()  # 6 hex-символов, например 'A1B2C3'
    user.telegram_link_code = code
    user.telegram_link_expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.telegram_link_code_ttl_minutes
    )
    await db.commit()
    return code


async def link_by_code(db: AsyncSession, telegram_id: int, code: str) -> User:
    user = await db.scalar(
        select(User).where(User.telegram_link_code == code.strip().upper())
    )
    if user is None:
        raise LinkError("Неверный код")
    if (
        user.telegram_link_expires is None
        or user.telegram_link_expires < datetime.now(timezone.utc)
    ):
        raise LinkError("Код истёк, сгенерируйте новый в веб-версии")

    await _attach(db, user, telegram_id)
    user.telegram_link_code = None
    user.telegram_link_expires = None
    await db.commit()
    return user


async def link_by_phone(db: AsyncSession, telegram_id: int, phone: str) -> User:
    target = normalize_phone(phone)
    # Матчим по нормализованному номеру (в БД телефоны хранятся как введены).
    users = await db.scalars(select(User).where(User.phone.isnot(None)))
    match = next((u for u in users if normalize_phone(u.phone or "") == target), None)
    if match is None:
        raise LinkError(
            "Аккаунт с таким номером не найден. Укажите телефон в веб-версии "
            "или привяжите кодом."
        )
    await _attach(db, match, telegram_id)
    await db.commit()
    return match


async def get_by_telegram(db: AsyncSession, telegram_id: int) -> User | None:
    return await db.scalar(select(User).where(User.telegram_id == telegram_id))


async def _attach(db: AsyncSession, user: User, telegram_id: int) -> None:
    """Привязывает telegram_id к юзеру, снимая привязку с других (id уникален)."""
    existing = await db.scalar(
        select(User).where(User.telegram_id == telegram_id, User.id != user.id)
    )
    if existing is not None:
        existing.telegram_id = None
    user.telegram_id = telegram_id

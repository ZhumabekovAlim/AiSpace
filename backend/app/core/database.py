"""Подключение к БД: асинхронный движок SQLAlchemy и фабрика сессий.

Используем async-стек (asyncpg), т.к. FastAPI асинхронный — так под нагрузкой
воркер не блокируется на I/O к базе.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # проверяем живость соединения перед выдачей из пула
)

SessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей. От него наследуется Alembic-метаданные."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-зависимость: одна сессия на запрос, гарантированно закрывается."""
    async with SessionFactory() as session:
        yield session

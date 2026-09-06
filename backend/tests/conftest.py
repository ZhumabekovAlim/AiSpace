"""Тестовое окружение.

Тесты гоняются против РЕАЛЬНОГО PostgreSQL (тот же сервер, отдельная БД
`<db>_test`), потому что ключевые проверки — EXCLUDE-constraint на пересечение
броней — работают только в настоящей БД. Схема накатывается миграциями Alembic
(не metadata.create_all), чтобы тестировать ровно то, что уедет в прод.

Запуск:  docker compose run --rm backend pytest
"""
import asyncio
import os
import subprocess
from urllib.parse import urlparse

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User, UserRole

settings = get_settings()
_parsed = urlparse(settings.database_url)  # postgresql+asyncpg://user:pass@host:port/db
_netloc = _parsed.netloc
_db_name = _parsed.path.lstrip("/")
TEST_DB = f"{_db_name}_test"

TEST_URL = f"postgresql+asyncpg://{_netloc}/{TEST_DB}"
_MAINT_DSN = f"postgresql://{_netloc}/postgres"  # для CREATE DATABASE


async def _recreate_test_db() -> None:
    conn = await asyncpg.connect(_MAINT_DSN)
    try:
        await conn.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = $1 AND pid <> pg_backend_pid()",
            TEST_DB,
        )
        await conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB}"')
        await conn.execute(f'CREATE DATABASE "{TEST_DB}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def _prepare_database() -> None:
    """Один раз за прогон: пересоздаём тестовую БД и накатываем миграции."""
    asyncio.run(_recreate_test_db())
    env = {**os.environ, "DATABASE_URL": TEST_URL}
    subprocess.run(["alembic", "upgrade", "head"], env=env, check=True)


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_URL)
    # Чистим данные перед каждым тестом — полная изоляция.
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE booking_transfers, bookings, rooms, users "
                "RESTART IDENTITY CASCADE"
            )
        )
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(engine, session_factory):
    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------- Хелперы авторизации ----------


async def _login(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    resp = await client.post(
        "/auth/login", data={"username": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def user_headers(client) -> dict[str, str]:
    await client.post(
        "/auth/register",
        json={"email": "user@test.com", "full_name": "Test User", "password": "secret123"},
    )
    return await _login(client, "user@test.com", "secret123")


@pytest_asyncio.fixture
async def admin_headers(client, session_factory) -> dict[str, str]:
    # register создаёт только обычных юзеров — админа заводим напрямую.
    async with session_factory() as s:
        s.add(
            User(
                email="admin@test.com",
                full_name="Admin",
                hashed_password=hash_password("adminpass"),
                role=UserRole.admin,
            )
        )
        await s.commit()
    return await _login(client, "admin@test.com", "adminpass")


@pytest_asyncio.fixture
async def room(client, admin_headers) -> dict:
    """Готовая комната для тестов броней."""
    resp = await client.post(
        "/rooms",
        headers=admin_headers,
        json={"name": "Room A", "capacity": 6},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()

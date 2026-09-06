"""Телефон, профиль и привязка Telegram (код + номер)."""
from sqlalchemy import select

from app.models.user import User
from app.services import link_service


async def test_register_with_phone_and_profile(client):
    await client.post(
        "/auth/register",
        json={
            "email": "p@test.com",
            "full_name": "Phoney",
            "password": "secret123",
            "phone": "+7 700 000 11 22",
        },
    )
    login = await client.post(
        "/auth/login", data={"username": "p@test.com", "password": "secret123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = await client.get("/auth/me", headers=headers)
    assert me.json()["phone"] == "+7 700 000 11 22"
    assert me.json()["telegram_linked"] is False


async def test_update_phone(client, user_headers):
    resp = await client.patch(
        "/auth/me", headers=user_headers, json={"phone": "+7 701 555 44 33"}
    )
    assert resp.status_code == 200
    assert resp.json()["phone"] == "+7 701 555 44 33"


async def test_generate_telegram_code(client, user_headers):
    resp = await client.post("/auth/me/telegram-code", headers=user_headers)
    assert resp.status_code == 200
    assert len(resp.json()["code"]) == 6


async def test_link_by_code(client, user_headers, session_factory):
    resp = await client.post("/auth/me/telegram-code", headers=user_headers)
    code = resp.json()["code"]
    async with session_factory() as db:
        user = await link_service.link_by_code(db, 555111, code)
        assert user.telegram_id == 555111
        # Повторно тот же код уже не работает (одноразовый).
        try:
            await link_service.link_by_code(db, 999, code)
            assert False, "expected LinkError"
        except link_service.LinkError:
            pass


async def test_link_by_phone(client, session_factory):
    await client.post(
        "/auth/register",
        json={
            "email": "ph@test.com",
            "full_name": "Ph",
            "password": "secret123",
            "phone": "+7 (777) 123-45-67",
        },
    )
    async with session_factory() as db:
        # Разный формат того же номера должен сматчиться (нормализация по цифрам).
        user = await link_service.link_by_phone(db, 42, "7 777 1234567")
        assert user.telegram_id == 42
        linked = await db.scalar(select(User).where(User.telegram_id == 42))
        assert linked.email == "ph@test.com"


async def test_link_by_unknown_phone_fails(client, session_factory):
    async with session_factory() as db:
        try:
            await link_service.link_by_phone(db, 7, "0000000")
            assert False, "expected LinkError"
        except link_service.LinkError:
            pass

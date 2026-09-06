"""Идемпотентный сид: комнаты офиса и стартовый админ.

Запускается из entrypoint после миграций. Повторный запуск ничего не ломает:
сущности создаются только если их ещё нет.
"""
import asyncio
import os

from sqlalchemy import select

from app.core.database import SessionFactory
from app.core.security import hash_password
from app.models.room import Room
from app.models.user import User, UserRole

DEFAULT_ROOMS = [
    {"name": "Большая переговорная", "capacity": 12,
     "description": "Проектор, ВКС"},
    {"name": "Малая переговорная", "capacity": 4,
     "description": "Для быстрых обсуждений"},
    {"name": "Переговорная у окна", "capacity": 6, "description": None},
]


async def seed() -> None:
    async with SessionFactory() as db:
        # --- Комнаты ---
        existing = set(await db.scalars(select(Room.name)))
        created_rooms = 0
        for data in DEFAULT_ROOMS:
            if data["name"] not in existing:
                db.add(Room(**data))
                created_rooms += 1

        # --- Стартовый админ (по желанию, из окружения) ---
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        created_admin = False
        if admin_email and admin_password:
            found = await db.scalar(
                select(User).where(User.email == admin_email)
            )
            if found is None:
                db.add(
                    User(
                        email=admin_email,
                        full_name="Administrator",
                        hashed_password=hash_password(admin_password),
                        role=UserRole.admin,
                    )
                )
                created_admin = True

        await db.commit()
        print(
            f"[seed] rooms created: {created_rooms}, "
            f"admin created: {created_admin}"
        )


if __name__ == "__main__":
    asyncio.run(seed())

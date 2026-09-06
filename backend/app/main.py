"""Точка входа FastAPI.

Здесь только сборка приложения: подключение роутеров, CORS, метаданные.
Бизнес-логики тут нет — она в services/, доступ к данным — в моделях/запросах.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для теста; в проде — конкретные origin фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


from app.api.routes import auth, bookings, nl, rooms  # noqa: E402

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(nl.router)

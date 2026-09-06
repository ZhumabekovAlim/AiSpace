"""Разбор фразы на естественном языке в черновик брони через DeepSeek.

Сознательно НЕ создаём бронь здесь: модель может ошибиться или сервис —
отказать. Возвращаем распознанные поля, а пользователь подтверждает их формой.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.room import Room
from app.schemas.nl import NLBookingDraft

settings = get_settings()


class NLServiceError(Exception):
    """Внешний сервис недоступен/вернул мусор — наверх уйдёт 503."""


_SYSTEM_PROMPT = """\
Ты — помощник бронирования переговорных комнат. По фразе пользователя определи
параметры брони и верни СТРОГО JSON-объект без пояснений со следующими полями:

- room_id: number | null  — id комнаты из списка ниже, если однозначно понятна
- room_name: string | null — как пользователь назвал комнату
- title: string | null — тема встречи
- start_time: string | null — ISO 8601 с таймзоной, напр. "2026-09-07T14:00:00+05:00"
- end_time: string | null — ISO 8601 с таймзоной; вычисли из длительности
- missing: string[] — чего не хватает: любые из "room", "start_time", "end_time", "title"
- clarification: string | null — короткий уточняющий вопрос на русском, если чего-то не хватает

Правила:
- Считай относительные даты ("завтра", "в пятницу") от текущего времени.
- Длительность ("на час", "полтора часа") прибавляй к start_time -> end_time.
- Если время окончания не задано и длительность неизвестна — оставь end_time null и добавь "end_time" в missing.
- Не выдумывай комнату: если не уверен, room_id=null и добавь "room" в missing.
"""


def _build_user_prompt(text: str, rooms: list[Room], now: datetime) -> str:
    room_lines = "\n".join(f"  id={r.id}, name={r.name!r}" for r in rooms)
    return (
        f"Текущее время: {now.isoformat()}\n"
        f"Часовой пояс офиса: {settings.office_timezone}\n"
        f"Доступные комнаты:\n{room_lines}\n\n"
        f"Фраза пользователя: {text!r}"
    )


async def parse_booking(db: AsyncSession, text: str) -> NLBookingDraft:
    if not settings.deepseek_api_key:
        raise NLServiceError("DeepSeek API-ключ не сконфигурирован")

    rooms = list(await db.scalars(select(Room).where(Room.is_active)))
    now = datetime.now(ZoneInfo(settings.office_timezone))

    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(text, rooms, now)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }

    try:
        async with httpx.AsyncClient(
            timeout=settings.deepseek_timeout_seconds
        ) as client:
            resp = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        raise NLServiceError(f"DeepSeek недоступен: {exc}") from exc

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise NLServiceError("DeepSeek вернул некорректный JSON") from exc

    draft = NLBookingDraft.model_validate(data)
    _reconcile_room(draft, rooms)
    return draft


def _reconcile_room(draft: NLBookingDraft, rooms: list[Room]) -> None:
    """Сверяем распознанную комнату с реальным списком (не доверяем id вслепую)."""
    valid_ids = {r.id for r in rooms}
    if draft.room_id in valid_ids:
        return
    # id не совпал — пробуем сопоставить по имени.
    if draft.room_name:
        needle = draft.room_name.strip().lower()
        for room in rooms:
            if needle in room.name.lower() or room.name.lower() in needle:
                draft.room_id = room.id
                return
    draft.room_id = None
    if "room" not in draft.missing:
        draft.missing.append("room")

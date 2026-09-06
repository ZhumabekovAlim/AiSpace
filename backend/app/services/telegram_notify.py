"""Отправка сообщений в Telegram через Bot API (пуши).

Общий модуль: используется и бэкендом (события передачи брони), и ботом.
Если токен не сконфигурирован — тихо ничего не делает (не роняем основной поток).
"""
import logging

import httpx

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_API = "https://api.telegram.org"


async def send_message(
    chat_id: int,
    text: str,
    *,
    reply_markup: dict | None = None,
) -> bool:
    """Отправляет текст пользователю. reply_markup — inline-клавиатура (опционально).

    Возвращает True при успехе. Ошибки логируются, но не пробрасываются:
    пуш — вторичен, он не должен ломать бронирование/передачу.
    """
    if not settings.telegram_bot_token:
        logger.info("telegram token not set, skip push to %s", chat_id)
        return False

    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    url = f"{_API}/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        return True
    except httpx.HTTPError as exc:
        logger.warning("telegram push failed: %s", exc)
        return False


def inline_keyboard(buttons: list[list[tuple[str, str]]]) -> dict:
    """Хелпер: [[(текст, callback_data)]] -> формат Telegram inline keyboard."""
    return {
        "inline_keyboard": [
            [{"text": text, "callback_data": data} for text, data in row]
            for row in buttons
        ]
    }

"""Распознавание речи (STT) из голосовых сообщений.

Провайдер-агностик: любой OpenAI-совместимый эндпоинт /audio/transcriptions
(по умолчанию Groq Whisper — бесплатный тариф, хорошо с русским). Если ключ
не задан — фича считается выключенной.
"""
import httpx

from app.core.config import get_settings

settings = get_settings()


class STTError(Exception):
    """STT недоступен или не сконфигурирован."""


def is_configured() -> bool:
    return bool(settings.stt_api_key)


async def transcribe(audio: bytes, filename: str = "voice.ogg") -> str:
    """Возвращает распознанный текст. Бросает STTError при проблемах."""
    if not is_configured():
        raise STTError("STT не сконфигурирован (нет STT_API_KEY)")

    url = f"{settings.stt_base_url}/audio/transcriptions"
    try:
        async with httpx.AsyncClient(timeout=settings.stt_timeout_seconds) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.stt_api_key}"},
                files={"file": (filename, audio, "audio/ogg")},
                data={"model": settings.stt_model, "language": "ru"},
            )
            resp.raise_for_status()
            text = resp.json().get("text", "").strip()
    except httpx.HTTPError as exc:
        raise STTError(f"Ошибка распознавания: {exc}") from exc

    if not text:
        raise STTError("Не удалось распознать речь")
    return text

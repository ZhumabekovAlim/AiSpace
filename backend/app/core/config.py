"""Конфигурация приложения.

Все настройки читаются из переменных окружения (файл .env).
Единая точка правды: нигде в коде не должно быть хардкода секретов/адресов.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Приложение ---
    app_name: str = "AiSpace"
    debug: bool = False

    # --- База данных (PostgreSQL) ---
    # Пример: postgresql+asyncpg://user:pass@db:5432/aispace
    database_url: str = Field(..., alias="DATABASE_URL")

    # --- Аутентификация (JWT) ---
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 день

    # --- Внешний сервис: DeepSeek ---
    deepseek_api_key: str = Field("", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: float = 20.0

    # Часовой пояс офиса — нужен, чтобы LLM корректно понимала "завтра в 14:00".
    office_timezone: str = "Asia/Almaty"

    # --- Telegram-бот ---
    telegram_bot_token: str = Field("", alias="TELEGRAM_BOT_TOKEN")
    # Срок жизни одноразового кода привязки (второй способ линковки).
    telegram_link_code_ttl_minutes: int = 15

    # --- STT (распознавание речи из голосовых) ---
    # Провайдер-агностик: любой OpenAI-совместимый /audio/transcriptions.
    # По умолчанию Groq Whisper (бесплатный тариф, хорош с русским).
    stt_base_url: str = "https://api.groq.com/openai/v1"
    stt_api_key: str = Field("", alias="STT_API_KEY")
    stt_model: str = "whisper-large-v3"
    stt_timeout_seconds: float = 60.0


@lru_cache
def get_settings() -> Settings:
    """Кэшируем, чтобы .env читался один раз за жизнь процесса."""
    return Settings()

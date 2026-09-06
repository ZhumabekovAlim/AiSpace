"""Точка входа Telegram-бота: python -m app.bot (режим polling).

Polling выбран намеренно: не нужен публичный webhook/HTTPS — бот поднимается
на чистой машине одной командой вместе с остальным стеком.
"""
import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.bot import handlers
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger("aispace.bot")

settings = get_settings()


def main() -> None:
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не задан — бот не запускается.")
        return

    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_cmd))
    app.add_handler(CommandHandler("link", handlers.link_cmd))
    app.add_handler(CommandHandler("mybookings", handlers.mybookings))
    app.add_handler(MessageHandler(filters.CONTACT, handlers.contact_handler))
    app.add_handler(MessageHandler(filters.VOICE, handlers.voice_handler))
    app.add_handler(CallbackQueryHandler(handlers.on_callback))

    logger.info("Bot started (polling).")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()

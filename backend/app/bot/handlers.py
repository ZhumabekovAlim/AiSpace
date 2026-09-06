"""Логика Telegram-бота. Бот переиспользует сервисы бэкенда и ту же БД."""
import logging
from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from app.core.database import SessionFactory
from app.services import (
    booking_service,
    link_service,
    nl_service,
    stt_service,
    transfer_service,
)
from app.services.booking_service import BookingConflict, RoomNotFound
from app.services.link_service import LinkError
from app.services.transfer_service import (
    TransferError,
    TransferForbidden,
    TransferNotFound,
)
from app.time_utils import fmt_range

logger = logging.getLogger(__name__)

WELCOME = (
    "👋 Привет! Это бот бронирования переговорных AiSpace.\n\n"
    "Сначала привяжите аккаунт одним из способов:\n"
    "• в веб-версии нажмите «Привязать Telegram» и пришлите сюда <code>/link КОД</code>;\n"
    "• или поделитесь номером телефона кнопкой ниже (должен совпадать с профилем).\n\n"
    "После привязки: пришлите <b>голосовое</b> — забронирую по вашей фразе, "
    "или команды /mybookings и /help."
)

HELP = (
    "Команды:\n"
    "/link КОД — привязать аккаунт кодом из веба\n"
    "/mybookings — мои предстоящие брони\n"
    "🎤 голосовое — бронь по фразе (ИИ)\n"
    "Кнопки под запросами передачи — подтвердить/отклонить."
)


def _contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
    )


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(WELCOME, reply_markup=_contact_keyboard())


async def help_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP)


async def link_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Формат: /link КОД (код из веб-версии)")
        return
    async with SessionFactory() as db:
        try:
            user = await link_service.link_by_code(
                db, update.effective_user.id, context.args[0]
            )
        except LinkError as exc:
            await update.message.reply_text(f"❌ {exc}")
            return
    await update.message.reply_text(f"✅ Аккаунт привязан: {user.full_name}")


async def contact_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    phone = update.message.contact.phone_number
    async with SessionFactory() as db:
        try:
            user = await link_service.link_by_phone(
                db, update.effective_user.id, phone
            )
        except LinkError as exc:
            await update.message.reply_text(f"❌ {exc}")
            return
    await update.message.reply_text(f"✅ Аккаунт привязан: {user.full_name}")


async def _require_user(db, update: Update):
    user = await link_service.get_by_telegram(db, update.effective_user.id)
    if user is None:
        await update.message.reply_text(
            "Сначала привяжите аккаунт: /link КОД или кнопка «Поделиться номером»."
        )
    return user


async def mybookings(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    async with SessionFactory() as db:
        user = await _require_user(db, update)
        if user is None:
            return
        now = datetime.now().astimezone()
        items = await booking_service.list_bookings(db, user_id=user.id)
        upcoming = sorted(
            (b for b in items if b.end_time >= now), key=lambda b: b.start_time
        )
    if not upcoming:
        await update.message.reply_text("У вас нет предстоящих броней.")
        return
    lines = [f"• {fmt_range(b.start_time, b.end_time)} — {b.title}" for b in upcoming]
    await update.message.reply_text("Ваши брони:\n" + "\n".join(lines))


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with SessionFactory() as db:
        user = await _require_user(db, update)
        if user is None:
            return
        if not stt_service.is_configured():
            await update.message.reply_text(
                "🎤 Распознавание речи не настроено (нет STT_API_KEY)."
            )
            return

        await update.message.chat.send_action("typing")
        tg_file = await update.message.voice.get_file()
        audio = bytes(await tg_file.download_as_bytearray())
        try:
            text = await stt_service.transcribe(audio)
        except stt_service.STTError as exc:
            await update.message.reply_text(f"🎤 {exc}")
            return
        await update.message.reply_text(f"🎤 Распознал: «{text}»")

        try:
            draft = await nl_service.parse_booking(db, text)
        except nl_service.NLServiceError:
            await update.message.reply_text(
                "Сервис разбора недоступен, попробуйте позже или забронируйте в вебе."
            )
            return

    if not (draft.room_id and draft.start_time and draft.end_time):
        note = draft.clarification or "не хватает данных"
        missing = f" (не хватает: {', '.join(draft.missing)})" if draft.missing else ""
        await update.message.reply_text(f"Не смог собрать бронь: {note}{missing}")
        return

    context.user_data["draft"] = {
        "room_id": draft.room_id,
        "title": draft.title or "Без темы",
        "start": draft.start_time.isoformat(),
        "end": draft.end_time.isoformat(),
    }
    summary = (
        f"Проверьте бронь:\n"
        f"🏢 {draft.room_name or ('комната #' + str(draft.room_id))}\n"
        f"🕒 {fmt_range(draft.start_time, draft.end_time)}\n"
        f"📝 {draft.title or 'Без темы'}"
    )
    markup = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Забронировать", callback_data="book:confirm"),
            InlineKeyboardButton("❌ Отмена", callback_data="book:cancel"),
        ]]
    )
    await update.message.reply_text(summary, reply_markup=markup)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "book:cancel":
        context.user_data.pop("draft", None)
        await query.edit_message_text("Отменено.")
        return

    if data == "book:confirm":
        await _confirm_booking(update, context)
        return

    if data.startswith("transfer:"):
        await _handle_transfer_action(update, context)
        return


async def _confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    draft = context.user_data.get("draft")
    if not draft:
        await query.edit_message_text("Черновик устарел, пришлите голосовое заново.")
        return
    async with SessionFactory() as db:
        user = await link_service.get_by_telegram(db, update.effective_user.id)
        if user is None:
            await query.edit_message_text("Аккаунт не привязан.")
            return
        try:
            booking = await booking_service.create_booking(
                db,
                user_id=user.id,
                room_id=draft["room_id"],
                title=draft["title"],
                start_time=datetime.fromisoformat(draft["start"]),
                end_time=datetime.fromisoformat(draft["end"]),
            )
        except RoomNotFound:
            await query.edit_message_text("Комната не найдена.")
            return
        except BookingConflict:
            await query.edit_message_text(
                "❌ Комната занята на это время. Выберите другой слот."
            )
            return
    context.user_data.pop("draft", None)
    await query.edit_message_text(
        f"✅ Забронировано: {fmt_range(booking.start_time, booking.end_time)} — "
        f"{booking.title}"
    )


async def _handle_transfer_action(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    _, action, raw_id = query.data.split(":")
    transfer_id = int(raw_id)
    async with SessionFactory() as db:
        actor = await link_service.get_by_telegram(db, update.effective_user.id)
        if actor is None:
            await query.edit_message_text("Аккаунт не привязан.")
            return
        fn = (
            transfer_service.accept_transfer
            if action == "accept"
            else transfer_service.reject_transfer
        )
        try:
            transfer = await fn(db, transfer_id=transfer_id, actor_id=actor.id)
        except (TransferNotFound, TransferForbidden, TransferError) as exc:
            await query.edit_message_text(f"⚠️ {exc}")
            return
        except BookingConflict as exc:
            await query.edit_message_text(f"❌ {exc}")
            return
        to_user = transfer.to_user
        title = transfer.booking.title
        room = transfer.booking.room.name

    if action == "accept":
        await query.edit_message_text(f"✅ Бронь «{title}» передана {to_user.full_name}.")
        if to_user.telegram_id:
            await context.bot.send_message(
                to_user.telegram_id,
                f"✅ Бронь «{title}» ({room}) передана вам.",
            )
    else:
        await query.edit_message_text(f"❌ Запрос на «{title}» отклонён.")
        if to_user.telegram_id:
            await context.bot.send_message(
                to_user.telegram_id, f"❌ Запрос на бронь «{title}» отклонён."
            )

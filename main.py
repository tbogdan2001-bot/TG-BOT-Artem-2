# main.py
# Клубная воронка (club3-сценарий), портированная из tertiary_bot_standalone
# и привязанная к каналу этого бота.
#
# Поток:
#   /start                      -> просьба подписаться на канал и дождаться подтверждения
#   заявка на вступление        -> (опц.) одобрение + старт воронки в личке
#   фото + кнопка "Я не робот"  -> Шаг 2 ("Как заработать в 2026")
#   Шаг 3                       -> "ГОЛОС КЛУБА" (менеджер) + "СМОТРЕТЬ ОТЗЫВЫ"
#   "СМОТРЕТЬ ОТЗЫВЫ"           -> альбом с отзывами

import asyncio
import logging
import os
import sys
from contextlib import suppress

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import (
    Message,
    CallbackQuery,
    ChatJoinRequest,
    FSInputFile,
    InputMediaPhoto,
    ReplyKeyboardRemove,
)

import config
import database
import keyboards
from postback import send_keitaro_postback

# -------------------------------------------------------------------
# Логирование
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(config.BASE_DIR, "bot.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Проверка токена
# -------------------------------------------------------------------
if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    logger.critical("BOT_TOKEN не задан. Укажите его в .env перед запуском.")
    print("\n" + "=" * 70)
    print("❌ ТОКЕН БОТА (BOT_TOKEN) НЕ ЗАДАН.")
    print("Скопируйте .env.example в .env и впишите BOT_TOKEN.")
    print("=" * 70)
    sys.exit("Critical Error: BOT_TOKEN is missing.")

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# -------------------------------------------------------------------
# Медиа-хелперы
# -------------------------------------------------------------------
def _media_exists(path: str) -> bool:
    return bool(path and os.path.exists(path))


async def _send_photo_or_text(chat_id: int, image_path: str, caption: str, reply_markup=None):
    """Отправляет фото с подписью, либо просто текст, если фото нет."""
    if _media_exists(image_path):
        return await bot.send_photo(
            chat_id, FSInputFile(image_path), caption=caption,
            reply_markup=reply_markup, parse_mode="HTML",
        )
    return await bot.send_message(chat_id, caption, reply_markup=reply_markup, parse_mode="HTML")


# -------------------------------------------------------------------
# Проверка подписки на канал
# -------------------------------------------------------------------
async def check_subscription(user_id: int) -> bool:
    if not config.CHANNEL_ID:
        return False
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as exc:
        logger.error("Не удалось проверить подписку %s: %s", user_id, exc)
        return False


# -------------------------------------------------------------------
# Шаги клубной воронки
# -------------------------------------------------------------------
async def start_club_flow(chat_id: int, user_id: int) -> None:
    """Шаг 1 воронки: стартовое фото + кнопка «Я не робот»."""
    await _send_photo_or_text(
        chat_id, config.START_IMAGE, config.START_MESSAGE, keyboards.get_not_robot_keyboard()
    )
    await database.set_scenario_step(user_id, "club3_waiting_not_robot")


async def send_step2(chat_id: int, user_id: int) -> None:
    """Шаг 2: «Как заработать в 2026», затем сразу Шаг 3."""
    parts = [p for p in (config.CLUB_STEP2_TITLE, config.CLUB_STEP2_MESSAGE) if p]
    await bot.send_message(
        chat_id, "\n\n".join(parts), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML"
    )
    await database.set_scenario_step(user_id, "club3_step2_sent")
    await send_step3(chat_id, user_id)


async def send_step3(chat_id: int, user_id: int) -> None:
    """Шаг 3: «ГОЛОС КЛУБА» + «СМОТРЕТЬ ОТЗЫВЫ»."""
    await bot.send_message(
        chat_id, config.CLUB_STEP3_MESSAGE,
        reply_markup=keyboards.get_step3_keyboard(), parse_mode="HTML",
    )
    await database.set_scenario_step(user_id, "club3_step3_sent")


async def send_reviews(chat_id: int) -> None:
    """Отправляет альбом отзывов."""
    album = []
    for index, path in enumerate(config.REVIEWS_MEDIA):
        if not _media_exists(path):
            logger.warning("Файл отзыва не найден: %s", path)
            continue
        caption = config.REVIEWS_CAPTION if (index == 0 and config.REVIEWS_CAPTION) else None
        album.append(InputMediaPhoto(media=FSInputFile(path), caption=caption))
    if album:
        await bot.send_media_group(chat_id, album)
    elif config.REVIEWS_CAPTION:
        await bot.send_message(chat_id, config.REVIEWS_CAPTION)
    else:
        logger.warning("Отзывы запрошены, но ни одного файла нет.")


# -------------------------------------------------------------------
# Хендлеры
# -------------------------------------------------------------------
@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject = None) -> None:
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    subid = command.args if (command and command.args) else ""

    # Спец-диплинк: сразу к шагу 2 (как в эталоне club3_not_robot).
    if subid == "club3_not_robot":
        await database.add_or_update_user(user_id, username, subid="")
        await database.set_club_flow_allowed(user_id, True)
        logger.info("User %s entered via club3_not_robot deep link", user_id)
        await send_step2(message.chat.id, user_id)
        return

    await database.add_or_update_user(user_id, username, subid=subid)
    logger.info("User %s (@%s) started. subid=%r", user_id, username, subid)

    user = await database.get_user(user_id)
    already_allowed = bool(user and user.get("club_flow_allowed"))

    if config.CLUB_FLOW_REQUIRES_JOIN:
        # Режим 2: ждём вступления в канал — бот пишет первым после заявки.
        is_subscribed = await check_subscription(user_id)
        if already_allowed or is_subscribed:
            await database.set_club_flow_allowed(user_id, True)
            await start_club_flow(message.chat.id, user_id)
            return
        # Просим подписаться и дождаться подтверждения заявки.
        await _send_photo_or_text(
            message.chat.id, config.START_IMAGE, config.JOIN_WAIT_MESSAGE,
            keyboards.get_subscribe_keyboard(),
        )
        return

    # Режим 1: воронка стартует сразу, подписка предлагается в конце.
    await database.set_club_flow_allowed(user_id, True)
    await start_club_flow(message.chat.id, user_id)


@dp.chat_join_request()
async def on_chat_join_request(request: ChatJoinRequest) -> None:
    user_id = request.from_user.id
    username = request.from_user.username or "unknown"
    logger.info("Получена заявка на вступление от %s (@%s)", user_id, username)

    # Гарантируем наличие пользователя в БД.
    if await database.get_user(user_id) is None:
        await database.add_or_update_user(user_id, username, subid="")

    # Одобряем заявку (если включено).
    if config.AUTO_APPROVE_JOIN:
        with suppress(Exception):
            await bot.approve_chat_join_request(request.chat.id, user_id)

    await database.set_join_requested(user_id, True)
    await database.set_club_flow_allowed(user_id, True)
    await database.set_subscribed(user_id, True)

    # Keitaro PostBack по конверсии (если настроен).
    user = await database.get_user(user_id)
    user_subid = (user or {}).get("subid") or ""
    if user_subid and config.KEITARO_POSTBACK_URL:
        await send_keitaro_postback(user_subid, config.KEITARO_POSTBACK_URL)

    # Стартуем воронку в личке. Если пользователь не открывал чат с ботом —
    # дождёмся его /start (тогда воронка запустится оттуда).
    try:
        await start_club_flow(user_id, user_id)
    except TelegramForbiddenError:
        logger.info("Пользователь %s ещё не открыл чат с ботом — ждём /start", user_id)


@dp.message(F.text == config.NOT_ROBOT_BUTTON_TEXT)
async def on_not_robot(message: Message) -> None:
    """Нажатие reply-кнопки «Я не робот» -> Шаг 2."""
    user_id = message.from_user.id
    user = await database.get_user(user_id)
    if user is None:
        await database.add_or_update_user(user_id, message.from_user.username or "unknown")
    await database.set_club_flow_allowed(user_id, True)
    logger.info("User %s confirmed 'не робот'", user_id)
    await send_step2(message.chat.id, user_id)


@dp.callback_query(F.data == "club3:reviews")
async def on_reviews(callback: CallbackQuery) -> None:
    """Кнопка «СМОТРЕТЬ ОТЗЫВЫ» -> альбом отзывов."""
    await callback.answer()
    await send_reviews(callback.from_user.id)
    await database.set_scenario_step(callback.from_user.id, "club3_reviews_clicked")


@dp.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if message.from_user.id != config.ADMIN_ID:
        return
    stats = await database.get_stats()
    by_step = "\n".join(f"  • {k}: {v}" for k, v in stats["by_step"].items()) or "  (нет данных)"
    text = (
        "📊 <b>Статистика клубной воронки</b>\n\n"
        f"👥 Всего пользователей: {stats['total']}\n"
        f"📨 Подали заявку на вступление: {stats['joined']}\n"
        f"🤖 Прошли «Я не робот»: {stats['not_robot']}\n"
        f"⭐ Посмотрели отзывы: {stats['reviews']}\n\n"
        "🚦 <b>По шагам сценария:</b>\n"
        f"{by_step}"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message()
async def catch_all(message: Message) -> None:
    """Прочие сообщения игнорируем (кроме обработанных выше)."""
    if message.text and message.text.startswith("/"):
        return
    logger.info("Входящее сообщение от %s: %r", message.from_user.id, message.text)


# -------------------------------------------------------------------
# Жизненный цикл
# -------------------------------------------------------------------
async def on_startup() -> None:
    await database.init_db()
    if config.CHANNEL_ID:
        try:
            chat = await bot.get_chat(config.CHANNEL_ID)
            if chat.title:
                config.CHANNEL_NAME = chat.title
                logger.info("Название канала успешно обновлено из Telegram API: %s", config.CHANNEL_NAME)
        except Exception as e:
            logger.warning("Не удалось получить название канала из Telegram API: %s", e)
    logger.info("Бот клубной воронки запущен. Канал: %s (%s)", config.CHANNEL_ID or "(не задан)", config.CHANNEL_NAME)


async def on_shutdown() -> None:
    await database.close_db()


async def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "chat_join_request", "my_chat_member"],
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")

# config.py
# CHANGELOG ПРАВОК СЕНЬОР-РАЗРАБОТЧИКА:
# 1. Выполнено переименование persona id: "alexander" -> "artem" во всем файле (PERSONAS, CHANNELS, MANAGER_ACCOUNTS, DEFAULT_PERSONA_ID и хелперах).
# 2. Полностью удалена персона "elena" из словаря PERSONAS, остался только Артём.
# 3. Значение CLOSER_USERNAME исправлено на "nizaev_art".
# 4. Все заглушечные ссылки заменены на TODO-плейсхолдеры с пометкой `# ← ЗАПОЛНИТЬ`.
# 5. Описание и имя персоны Артёма в PERSONAS["artem"] обновлено в соответствии со специализацией (A-CLUB, трейдер, арбитраж, стейкинг).
# 6. Обновлен текст приветствия WELCOME_TEXT с перечислением крипто-тематик (торговые боты, арбитраж, стейкинг) и крипто-тематических вопросов.
# 7. Вопросы и варианты ответов квиза полностью адаптированы под криптовалюты и трейдинг.
# 8. Логика get_personalized_bonus() полностью переписана под сопоставление направления интереса (q2) с одним из 4-х новых крипто-бонусов Артёма.
# 9. Тексты CONTENT_PLAN и PRESSURE_PLAN избавлены от имени "Дмитрий" и переведены на обезличенные кейсы ("один из участников клуба A-CLUB").
# 10. В MANAGER_ACCOUNTS удален выбор elena/alexander: теперь все менеджеры получают persona_id = "artem".

import os
import sys
from dotenv import load_dotenv

# Resolve absolute directory where bot is running (handles PyInstaller compilation)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def check_and_interactive_config():
    env_path = os.path.join(BASE_DIR, ".env")
    
    config_values = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        config_values[k.strip()] = v.strip()
        except Exception:
            pass
            
    placeholders = {
        "BOT_TOKEN": ["YOUR_BOT_TOKEN_HERE", "", "BOT_TOKEN_HERE"]
    }
    
    needs_setup = not os.path.exists(env_path)
    if not needs_setup:
        val = config_values.get("BOT_TOKEN", "")
        if val in placeholders["BOT_TOKEN"] or not val:
            needs_setup = True
            
    if not needs_setup:
        # Load from resolved path and return
        load_dotenv(env_path, override=True)
        return

    # Wizard starts!
    print("\n=========================================================")
    print("🚀 НАСТРОЙКА TELEGRAM-БОТА // INTERACTIVE SETUP WIZARD 🚀")
    print("=========================================================")
    print("Обнаружен первый запуск или незаполненный конфигурационный файл.")
    print("Пожалуйста, заполните необходимые данные для работы бота.\n")

    def prompt_validated_input(prompt_text, validation_func, error_msg, required=True):
        while True:
            print(prompt_text, end="", flush=True)
            try:
                val = sys.stdin.readline().strip()
            except Exception:
                val = input().strip()
                
            if not val:
                if not required:
                    return ""
                print("❌ Значение не может быть пустым. Пожалуйста, попробуйте снова.")
                continue
                
            if validation_func(val):
                return val
            print(f"❌ {error_msg}")

    # БЛОК 1 — ОСНОВНЫЕ ДАННЫЕ БОТА
    print("--- [ БЛОК 1: Основные данные бота ] ---")
    bot_token = prompt_validated_input(
        "🔑 Введите ТОКЕН БОТА (BOT_TOKEN) от @BotFather: ",
        lambda v: ":" in v and len(v) > 5,
        "Токен бота должен содержать двоеточие (формат xxxxx:yyyyy) и быть не пустым."
    )
    admin_id = prompt_validated_input(
        "👤 Введите числовой Telegram ID администратора (ADMIN_ID): ",
        lambda v: v.isdigit(),
        "ID администратора должен состоять только из цифр."
    )
    print("✅ Блок 1 сохранён. Продолжаем...\n")

    # БЛОК 2 — КАНАЛЫ
    print("--- [ БЛОК 2: Подключение каналов ] ---")
    channels = []
    while True:
        ch_idx = len(channels) + 1
        print(f"\nНастройка канала #{ch_idx}:")
        
        ch_id = prompt_validated_input(
            f"📢 Введите ID канала #{ch_idx} (должен начинаться с -100): ",
            lambda v: v.startswith("-100") and v[4:].isdigit(),
            "ID канала должен начинаться с '-100' и далее содержать только цифры."
        )
        ch_link = prompt_validated_input(
            f"🔗 Введите invite-ссылку для канала #{ch_idx} (например, https://t.me/+XXXXXXXX): ",
            lambda v: v.startswith("https://t.me/"),
            "Ссылка должна начинаться с 'https://t.me/'"
        )
        ch_name = prompt_validated_input(
            f"📝 Введите название канала #{ch_idx}: ",
            lambda v: len(v) > 0,
            "Название не может быть пустым."
        )
        channels.append({
            "id": ch_id,
            "link": ch_link,
            "name": ch_name,
            "persona": "artem"
        })
        
        print(f"✅ Канал #{ch_idx} добавлен.")
        
        # Ask to add more
        while True:
            print("Добавить ещё один канал? (y/n): ", end="", flush=True)
            try:
                ans = sys.stdin.readline().strip().lower()
            except Exception:
                ans = input().strip().lower()
            if ans in ["y", "yes", "n", "no"]:
                break
            print("Пожалуйста, введите 'y' или 'n'.")
            
        if ans in ["n", "no"]:
            break
            
    print("\n✅ Блок 2 сохранён. Продолжаем...\n")

    # БЛОК 3 — KEITARO POSTBACK
    print("--- [ БЛОК 3: Интеграция Keitaro ] ---")
    keitaro_url = prompt_validated_input(
        "🔗 Введите KEITARO_POSTBACK_URL (нажмите Enter, чтобы пропустить): ",
        lambda v: v.startswith("http://") or v.startswith("https://"),
        "URL должен начинаться с http:// или https://",
        required=False
    )
    print("✅ Блок 3 сохранён. Продолжаем...\n")

    # БЛОК 4 — МЕНЕДЖЕРЫ / USERBOT АККАУНТЫ (Telethon)
    print("--- [ БЛОК 4: Менеджеры и Telethon API ] ---")
    api_id = prompt_validated_input(
        "🆔 Введите API ID с my.telegram.org (TELEGRAM_API_ID): ",
        lambda v: v.isdigit(),
        "API ID должен состоять только из цифр."
    )
    api_hash = prompt_validated_input(
        "🔐 Введите API Hash с my.telegram.org (TELEGRAM_API_HASH): ",
        lambda v: len(v) > 5,
        "API Hash не должен быть пустым."
    )
    
    managers = []
    while True:
        mgr_idx = len(managers) + 1
        print(f"\nНастройка менеджера #{mgr_idx}:")
        phone = prompt_validated_input(
            f"📱 Введите номер телефона менеджера #{mgr_idx} (в формате +380991234567): ",
            lambda v: v.startswith("+") and len(v) > 7 and v[1:].isdigit(),
            "Номер телефона должен начинаться с '+' и содержать только цифры."
        )
        managers.append(phone)
        print(f"✅ Менеджер #{mgr_idx} добавлен.")
        
        while True:
            print("Добавить ещё одного менеджера? (y/n): ", end="", flush=True)
            try:
                ans = sys.stdin.readline().strip().lower()
            except Exception:
                ans = input().strip().lower()
            if ans in ["y", "yes", "n", "no"]:
                break
            print("Пожалуйста, введите 'y' или 'n'.")
            
        if ans in ["n", "no"]:
            break
            
    print("\n✅ Блок 4 сохранён. Продолжаем...\n")

    # БЛОК 5 — AI КОНТЕНТ (Gemini)
    print("--- [ БЛОК 5: AI Контент и автопостинг ] ---")
    gemini_key = prompt_validated_input(
        "🤖 Введите Google Gemini API Key (GEMINI_API_KEY) (нажмите Enter, чтобы пропустить): ",
        lambda v: len(v) > 5,
        "API-ключ должен быть длиннее 5 символов.",
        required=False
    )
    
    def validate_posting_schedule(val):
        import re
        parts = val.split(",")
        for p in parts:
            p = p.strip()
            if not re.match(r"^\d{2}:\d{2}$", p):
                return False
        return True

    posting_schedule = prompt_validated_input(
        "⏰ Введите времена автопостинга в UTC через запятую (например, 09:00,17:00): ",
        validate_posting_schedule,
        "Неверный формат времени. Введите время в формате HH:MM через запятую."
    )
    print("✅ Блок 5 сохранён. Продолжаем...\n")

    # Write to .env
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# Telegram Bot Funnel Configuration\n")
            f.write("# Generated automatically via Setup Wizard\n\n")
            f.write(f"BOT_TOKEN={bot_token}\n")
            f.write(f"ADMIN_ID={admin_id}\n\n")
            
            # Channels
            # First channel added = TARGET_CHANNEL (invite link)
            f.write(f"TARGET_CHANNEL={channels[0]['link']}\n")
            
            # If 1 channel, write standard values for single channel fallback too
            if len(channels) == 1:
                f.write(f"CHANNEL_ID={channels[0]['id']}\n")
                f.write(f"CHANNEL_LINK={channels[0]['link']}\n")
                f.write(f"CHANNEL_NAME={channels[0]['name']}\n\n")
            else:
                for i, ch in enumerate(channels, 1):
                    f.write(f"CHANNEL_{i}_ID={ch['id']}\n")
                    f.write(f"CHANNEL_{i}_LINK={ch['link']}\n")
                    f.write(f"CHANNEL_{i}_NAME={ch['name']}\n")
                f.write("\n")
                
            # Keitaro
            f.write(f"KEITARO_POSTBACK_URL={keitaro_url}\n\n")
            
            # Managers / Userbots
            f.write(f"TELEGRAM_API_ID={api_id}\n")
            f.write(f"TELEGRAM_API_HASH={api_hash}\n")
            for i, phone in enumerate(managers, 1):
                f.write(f"MANAGER_{i}_PHONE={phone}\n")
            f.write("\n")
            
            # AI
            f.write(f"GEMINI_API_KEY={gemini_key}\n")
            f.write(f"POSTING_SCHEDULE={posting_schedule}\n\n")
            
        print("[УСПЕХ] Файл .env успешно создан!")
        
        # Резервное копирование в корень: если мы работаем в dist/ внутри папки разработчика,
        # сохраняем копию .env в родительской папке, чтобы настройки не стерлись при удалении dist
        try:
            import shutil
            parent_dir = os.path.dirname(BASE_DIR)
            if getattr(sys, 'frozen', False):
                # Проверяем, является ли родительская папка корнем исходников
                if os.path.exists(os.path.join(parent_dir, "build_bot.py")) or os.path.exists(os.path.join(parent_dir, "main.py")):
                    shutil.copy(env_path, os.path.join(parent_dir, ".env"))
                    print("[УСПЕХ] Резервная копия конфигурации сохранена в корне проекта (..\\.env)")
        except Exception as e:
            logger.debug(f"Failed to backup env file to parent folder: {e}")
    except Exception as e:
        print(f"❌ Ошибка при записи файла .env: {e}")

    # Summary
    last4 = bot_token[-4:] if len(bot_token) >= 4 else bot_token
    postback_status = "настроен" if keitaro_url else "не настроен"
    gemini_status = "настроен" if gemini_key else "не настроен"
    
    print("\n=========================================================")
    print("✅ НАСТРОЙКА ЗАВЕРШЕНА! Конфигурация бота:")
    print(f"- Бот токен: ***{last4}")
    print(f"- Каналов настроено: {len(channels)}")
    print(f"- Менеджеров настроено: {len(managers)}")
    print(f"- Keitaro PostBack: {postback_status}")
    print(f"- AI Контент (Gemini): {gemini_status}")
    print(f"- Расписание постинга: {posting_schedule.replace(',', ', ')} UTC")
    print("=========================================================\n")

    # Load from resolved path
    load_dotenv(env_path, override=True)

# Run interactive config check
check_and_interactive_config()

# 1. Telegram Connection Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")          # Default channel backup
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/+0npyyzG-yAoxYmMx")
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Артём Низаев | Криптовалюта, Аналитика, Доход")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "https://t.me/+0npyyzG-yAoxYmMx")
admin_id_raw = os.getenv("ADMIN_ID", "0")
ADMIN_ID = int(admin_id_raw) if admin_id_raw.isdigit() else 0

# Closer CRM Forwarding Destination Chat ID
CLOSER_NOTIFY_CHAT_ID = os.getenv("CLOSER_NOTIFY_CHAT_ID", "")
if CLOSER_NOTIFY_CHAT_ID.startswith("-") or CLOSER_NOTIFY_CHAT_ID.isdigit():
    CLOSER_NOTIFY_CHAT_ID = int(CLOSER_NOTIFY_CHAT_ID)

# CHANGED: Private Club link configuration - changed default placeholder to TODO
PRIVATE_CLUB_LINK = os.getenv("PRIVATE_CLUB_LINK", "TODO: вставить ссылку на приватный клуб")  # ← ЗАПОЛНИТЬ

# Keitaro PostBack URL configuration loaded from environment
KEITARO_POSTBACK_URL = os.getenv("KEITARO_POSTBACK_URL", "")

# Redis Connection URL
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Closer Telegram Username (for Day 30 retention link) - CHANGED to nizaev_art
CLOSER_USERNAME = os.getenv("CLOSER_USERNAME", "nizaev_art")


# CHANGED: Multi-Account Persona Support Configuration Profiles expanded to 5 images
# 1. Persona ID changed to "artem", "elena" removed.
# 2. Placeholders replaced by TODOs with comments.
# 3. Description and niche updated.
PERSONAS = {
    "artem": {
        "id": "artem",
        "name": "Артём",
        "description": "основатель закрытого клуба A-CLUB и практикующий трейдер",
        "niche": "криптовалюта, трейдинг, арбитраж и стейкинг",
        "images": {
            "image_1": os.getenv("ARTEM_IMAGE_1", "https://images.unsplash.com/photo-1621761191319-c6fb62004040?w=1080"),
            "image_2": os.getenv("ARTEM_IMAGE_2", "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=1080"),
            "image_3": os.getenv("ARTEM_IMAGE_3", "https://images.unsplash.com/photo-1642790106117-e829e14a795f?w=1080"),  # Quiz mid-point chart visual
            "image_4": os.getenv("ARTEM_IMAGE_4", "https://images.unsplash.com/photo-1513151233558-d860c5398176?w=1080"),  # Congrats
            "image_5": os.getenv("ARTEM_IMAGE_5", "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=1080"),  # Dark style final CTA card
        },
        "bonus_options": [
            {"label": "🎁 Гайд по Трейдингу", "value": "bonus_trading"},
            {"label": "🎁 Секретный DeFi Гайд", "value": "bonus_defi"},
            {"label": "🎁 Чек-лист по Арбитражу", "value": "bonus_arbitrage"},
            {"label": "🎁 Руководство по Торговым Ботам", "value": "bonus_bots"},
        ],
        "bonus_contents": {
            "bonus_trading": (
                "🎉 **Ваш Гайд по Трейдингу успешно разблокирован!**\n\n"
                "В этом руководстве вы найдете:\n"
                "1️⃣ Пошаговый разбор технического анализа для новичков\n"
                "2️⃣ Правила входа в сделки и риск-менеджмент\n"
                "3️⃣ Топ-3 индикатора для успешной торговли\n\n"
                "🔗 [Читать гайд в Notion](TODO: вставить ссылку на DeFi гайд)\n\n"  # ← ЗАПОЛНИТЬ
                "Обязательно изучи его! Скоро я пришлю тебе первый секретный совет."
            ),
            "bonus_defi": (
                "🎉 **Ваш DeFi Гайд успешно разблокирован!**\n\n"
                "В этом руководстве мы разложили по полочкам:\n"
                "1️⃣ Что такое фарминг и стейкинг простыми словами\n"
                "2️⃣ Пошаговый алгоритм покупки первой монеты\n"
                "3️⃣ Топ-3 кошелька для безопасного хранения активов\n\n"
                "🔗 [Читать гайд в Notion](TODO: вставить ссылку на DeFi гайд)\n\n"  # ← ЗАПОЛНИТЬ
                "Обязательно изучи его! Скоро я пришлю тебе первый секретный совет."
            ),
            "bonus_arbitrage": (
                "🎉 **Ваш Чек-лист по Арбитражу готов!**\n\n"
                "Начни зарабатывать на разнице курсов:\n"
                "1️⃣ Что такое межбиржевой и внутрибиржевой арбитраж\n"
                "2️⃣ Как находить связки и избегать блокировок карт\n"
                "3️⃣ Памятка по безопасности при P2P-сделках\n\n"
                "🔗 [Скачать Чек-лист в PDF](TODO: вставить ссылку на чек-лист PDF)\n\n"  # ← ЗАПОЛНИТЬ
                "Сохрани себе этот файл! Через час я пришлю тебе важную информацию."
            ),
            "bonus_bots": (
                "🎉 **Ваш Гайд по Торговым Ботам успешно разблокирован!**\n\n"
                "Автоматизируй свою торговлю:\n"
                "1️⃣ Как работают сеточные и DCA боты\n"
                "2️⃣ Настройка первого торгового бота шаг за шагом\n"
                "3️⃣ Стратегии минимизации рисков при высокой волатильности\n\n"
                "🔗 [Скачать Руководство PDF](TODO: вставить ссылку на чек-лист PDF)\n\n"  # ← ЗАПОЛНИТЬ
                "Сохрани себе этот файл! Через час я пришлю тебе важную информацию."
            )
        }
    }
}

# Multi-Channel / Multi-Group Referral Link Assignments (Dynamically parsed for backward compatibility)
CHANNELS = []
channel_idx = 1
while True:
    ch_id = os.getenv(f"CHANNEL_{channel_idx}_ID")
    if not ch_id:
        break
    CHANNELS.append({
        "id": f"channel_{channel_idx}",
        "link": os.getenv(f"CHANNEL_{channel_idx}_LINK", ""),
        "name": os.getenv(f"CHANNEL_{channel_idx}_NAME", f"Channel {channel_idx}"),
        "persona_id": os.getenv(f"CHANNEL_{channel_idx}_PERSONA", "artem"),
        "channel_id": ch_id
    })
    channel_idx += 1

if not CHANNELS:
    # Fallback to single format
    single_id = os.getenv("CHANNEL_ID")
    single_link = os.getenv("CHANNEL_LINK")
    single_name = os.getenv("CHANNEL_NAME")
    if single_id or single_link:
        CHANNELS.append({
            "id": "crypto_channel",
            "link": single_link or "https://t.me/+0npyyzG-yAoxYmMx",
            "name": single_name or "Артём Низаев | Криптовалюта, Аналитика, Доход",
            "persona_id": "artem",
            "channel_id": single_id or "-1003964301634"
        })

# Default channels if completely empty
if not CHANNELS:
    CHANNELS = [
        {
            "id": "crypto_channel",
            "link": "https://t.me/+0npyyzG-yAoxYmMx",
            "name": "Артём Низаев | Криптовалюта, Аналитика, Доход",
            "persona_id": "artem",
            "channel_id": "-1003964301634"
        }
    ]

DEFAULT_PERSONA_ID = "artem"

def get_persona_for_user(user: dict) -> dict:
    """Dynamically resolves the assigned persona config for a user based on their source channel"""
    source_channel_id = user.get("source_channel")
    persona_id = DEFAULT_PERSONA_ID
    
    if source_channel_id:
        for ch in CHANNELS:
            if ch["id"] == source_channel_id:
                persona_id = ch["persona_id"]
                break
                
    return PERSONAS.get(persona_id, PERSONAS[DEFAULT_PERSONA_ID])

def get_channel_id_for_user(user: dict) -> str:
    """Dynamically resolves target verification channel ID based on source channel"""
    source_channel_id = user.get("source_channel")
    if source_channel_id:
        for ch in CHANNELS:
            if ch["id"] == source_channel_id:
                return ch.get("channel_id", CHANNEL_ID)
    return CHANNEL_ID

# CHANGED: Added quiz answer combination personalized bonus resolver
# Elena branch removed, Artem logic maps direction of interest to corresponding bonus.
def get_personalized_bonus(persona_id: str, q1: str, q2: str, q3: str) -> str:
    """Dynamically resolves the personalized bonus content based on quiz responses."""
    if q2 == "trading":
        return "bonus_trading"
    elif q2 == "staking":
        return "bonus_defi"
    elif q2 == "arbitrage":
        return "bonus_arbitrage"
    elif q2 == "bots":
        return "bonus_bots"
    return "bonus_trading"

# Delays in minutes
# FOLLOW_UP_DELAYS[0] is the subscription nudge check (Step 2b) (e.g. 30 mins)
# FOLLOW_UP_DELAYS[1:5] are the main content plan stages (e.g. 1h, 24h, 48h, 72h)
# FOLLOW_UP_DELAYS[5:8] are the long-term retention stages (e.g. Day 7, Day 14, Day 30)
# FOLLOW_UP_DELAYS[8:10] are the new Day 4 and Day 5 pressure funnel stages (5760 and 7200 minutes)
# Append new delays to keep all existing indices fully compatible.
FOLLOW_UP_DELAYS = [30, 60, 1440, 2880, 4320, 10080, 20160, 43200, 5760, 7200]

# 4. Core Funnel Texts (Allows full translation/modification of messages)
# Updated Welcome text with specific specializations.
WELCOME_TEXT = (
    "👋 Приветствую! Меня зовут **{persona_name}**.\n\n"
    "Я — {persona_description}.\n\n"
    "Добро пожаловать в мой интерактивный бот-помощник! Моя цель — помочь тебе освоить **{niche}**, включая торговые боты, арбитраж и стейкинг, и выйти на стабильный доход без лишнего риска.\n\n"
    "Перед тем, как выдать тебе персональный бонус, давай пройдём короткий опрос из 3 вопросов 👇\n\n"
    "**Вопрос 1: Какой у тебя уровень опыта в трейдинге и криптовалюте?**"
)

SUBSCRIBE_CALL_TEXT = (
    "🔥 **Опрос завершен! Подходящий для тебя бонус подобран!**\n\n"
    "Чтобы получить доступ к закрытым материалам и забрать гарантированные подарки, "
    "тебе необходимо подписаться на мой официальный канал: **{channel_name}**.\n\n"
    "Подпишись по кнопке ниже и нажми «Я подписался» 👇"
)

NUDGE_TEXT = (
    "⌛ **Количество бонусов ограничено!**\n\n"
    "Мы заметили, что ты еще не подписался на наш канал. Подпишись прямо сейчас и мгновенно забери свой приветственный бонус 🎁"
)

ALREADY_SUBSCRIBED_NUDGE = "✅ Вы уже подписаны! Забирайте свои бонусы ниже."

STEP_4_CONGRATS_TEXT = (
    "🎉 **Поздравляю! Подписка успешно подтверждена!**\n\n"
    "Вы успешно прошли опрос и получили полный доступ к воронке полезных материалов.\n\n"
    "На основе ваших ответов я подготовил индивидуальный результат:"
)

# CHANGED: Added closing dark-themed post template
DARK_CTA_CAPTION = (
    "🔥 **ДОБРО ПОЖАЛОВАТЬ В ЗАКРЫТЫЙ КЛУБ // {persona_name}**\n\n"
    "Вы успешно прошли опрос, получили свой персональный бонус и подтвердили подписку!\n\n"
    "Теперь перед вами открывается уникальная возможность — войти в наше приватное сообщество по **{niche}**.\n\n"
    "**Что вас ждет внутри закрытого клуба:**\n"
    "1️⃣ Ежедневная инсайдерская аналитика рынка\n"
    "2️⃣ Совместные сделки и разбор инвест-идей\n"
    "3️⃣ Прямой доступ к сильному окружению и единомышленникам\n\n"
    "👇 Нажмите кнопку ниже прямо сейчас, чтобы занять свое место в клубе совершенно бесплатно!"
)

# Extended Warm-up Sequence Content Plan Supporting 8 Message Types
# Success case changed to "one of A-CLUB members"
CONTENT_PLAN = [
    {
        "type": "market_review",
        "delay_index": 1,  # FOLLOW_UP_DELAYS[1] = 60 minutes
        "text": (
            "📊 **{persona_name} // ОБЗОР РЫНКА ({niche})**\n\n"
            "👋 Привет! Надеюсь, вы уже начали изучать приветственный бонус!\n\n"
            "Давайте разберем, что происходит в сфере {niche} прямо сейчас. "
            "Крупный капитал активно заходит в перспективные активы, пока розничные инвесторы паникуют. "
            "В следующем сообщении я поделюсь реальным кейсом, как сделать на этом прибыль!"
        ),
        "image": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1080"
    },
    {
        "type": "success_case",
        "delay_index": 2,  # FOLLOW_UP_DELAYS[2] = 1440 minutes (24 hours)
        "text": (
            "📈 **КЕЙС УСПЕХА: +180% чистой прибыли**\n\n"
            "Хочу показать вам путь одного из участников нашего закрытого клуба A-CLUB.\n\n"
            "Этот участник пришел с нулевым опытом в {niche}. За месяц работы по моей системе "
            "он окупил вложения и сформировал стабильный пассивный доход. "
            "Это еще раз доказывает: системный подход побеждает хаос!"
        ),
        "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1080"
    },
    {
        "type": "failure_case",
        "delay_index": 3,  # FOLLOW_UP_DELAYS[3] = 2880 minutes (48 hours)
        "text": (
            "🚫 **РАЗБОР ОШИБКИ: Слив $1,500 на эмоциях**\n\n"
            "Сегодня поговорим о психологии инвестиций.\n\n"
            "Большинство новичков теряют свои депозиты в {niche} из-за синдрома FOMO "
            "(страха упущенной выгоды). Они покупают активы на пике и продают на низах. "
            "Запомните золотое правило: никогда не рискуйте суммой более 2% от депозита на одну сделку!"
        ),
        "image": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=1080"
    },
    {
        "type": "audience_qa",
        "delay_index": 4,  # FOLLOW_UP_DELAYS[4] = 4320 minutes (72 hours)
        "text": (
            "❓ **ОТВЕТЫ НА ВОПРОСЫ ПОДПИСЧИКОВ**\n\n"
            "Меня часто спрашивают: «С какого капитала лучше начать инвестировать в {niche}?»\n\n"
            "Мой ответ — начните с небольшой комфортной суммы (от $100), чтобы протестировать механику. "
            "Если хотите получить разбор вашей личной ситуации лично от меня ({persona_name}), забронируйте встречу ниже! 👇"
        ),
        "image": "https://images.unsplash.com/photo-1521737711867-e3b904737c88?w=1080",
        "keyboard": [
            [{"text": "🗓 Забронировать бесплатную консультацию", "url": "TODO: вставить ссылку на бронирование"}]  # ← ЗАПОЛНИТЬ
        ]
    }
]

# Retention Sequence Configurations for Long-Term Engagement
RETENTION_PLAN = [
    {
        "stage": 1,
        "type": "expert_tip",
        "delay_index": 5,  # FOLLOW_UP_DELAYS[5] = 10080 minutes (Day 7)
        "text": (
            "👋 Привет! Это {persona_name}. Давно не общались!\n\n"
            "В сфере {niche} вышли важные обновления. Я подготовил короткий совет: "
            "сейчас лучшее время для переоценки своего портфеля и фиксации прибыли по перегретым позициям. "
            "Подробности читайте в основном канале!"
        )
    },
    {
        "stage": 2,
        "type": "free_content",
        "delay_index": 6,  # FOLLOW_UP_DELAYS[6] = 20160 minutes (Day 14)
        "text": (
            "🎁 **СВЕЖИЙ МАТЕРИАЛ ДЛЯ ВАС!**\n\n"
            "Я записал новый подробный видео-гайд о том, как диверсифицировать доходы в {niche} "
            "и получать стабильный пассивный доход в долларах.\n\n"
            "🔗 [Смотреть видео-гайд бесплатно](TODO: вставить ссылку на видео-гайд)"  # ← ЗАПОЛНИТЬ
        )
    },
    {
        "stage": 3,
        "type": "promo_offer",
        "delay_index": 7,  # FOLLOW_UP_DELAYS[7] = 43200 minutes (Day 30)
        "text": (
            "🔥 **ПОСЛЕДНИЙ ШАНС ДЛЯ ВАС**\n\n"
            "Это {persona_name}. Я закрываю набор на индивидуальное наставничество по {niche}.\n\n"
            "Осталось последнее свободное место со скидкой 50%. Если вы хотите начать зарабатывать под моим руководством — нажимайте кнопку ниже прямо сейчас! 👇"
        ),
        "keyboard": [
            [{"text": "📥 Занять место", "url": CHANNEL_LINK}]
        ]
    }
]

# ==============================================================================
# NEW: AI CONTENT & AUTOPOSTING & MULTI-ACCOUNT MANAGER SYSTEM CONFIGURATION
# ==============================================================================

# AI Content Generation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Auto-posting schedule (UTC times - Parsed from comma-separated string)
POSTING_SCHEDULE_RAW = os.getenv("POSTING_SCHEDULE", "09:00,17:00")
POSTING_SCHEDULE = [t.strip() for t in POSTING_SCHEDULE_RAW.split(",") if t.strip()]

# Manager accounts (Telethon userbots)
api_id_raw = os.getenv("TELEGRAM_API_ID", "0")
TELEGRAM_API_ID = int(api_id_raw) if api_id_raw.isdigit() else 0
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")

# Manager accounts dynamically loaded
# 10. Every manager receives persona_id = "artem"
MANAGER_ACCOUNTS = []
manager_idx = 1
while True:
    mgr_phone = os.getenv(f"MANAGER_{manager_idx}_PHONE")
    if not mgr_phone:
        break
    
    MANAGER_ACCOUNTS.append({
        "session": f"manager_{manager_idx}",
        "persona_id": "artem",
        "groups": [],
        "phone": mgr_phone
    })
    manager_idx += 1

if not MANAGER_ACCOUNTS:
    single_phone = os.getenv("MANAGER_1_PHONE")
    if single_phone:
        MANAGER_ACCOUNTS.append({
            "session": "manager_1",
            "persona_id": "artem",
            "groups": [],
            "phone": single_phone
        })
    else:
        MANAGER_ACCOUNTS.append({
            "session": "manager_1",
            "persona_id": "artem",
            "groups": [],
            "phone": "+380000000000"
        })

# MANAGER_GROUPS configuration list for Feature 3 manager rotation
MANAGER_GROUPS = [
    {"group_id": "-1003964301634", "name": "Crypto Discussion 💬"},
    {"group_id": "-1003333333333", "name": "Estate Talk 🏢"},
    {"group_id": "-1004444444444", "name": "Arbitrage Club 📈"}
]

# Pressure Sequence (Дожим) for cold/inactive leads
# Social proof text changed to "one of A-CLUB members"
PRESSURE_PLAN = [
    {
        "stage": 1,
        "delay_index": 2,  # FOLLOW_UP_DELAYS[2] = 1440 minutes (Day 1)
        "type": "hook",
        "text": (
            "🎯 **{persona_name} // КОЕ-ЧТО ИНТЕРЕСНОЕ ДЛЯ ВАС**\n\n"
            "Привет! Я заметил, что вы интересовались темой **{niche}**, но так и не решились сделать первый шаг. "
            "Почему большинство людей так и остаются на месте? Из-за страха неизвестности.\n\n"
            "Я подготовил для вас небольшую инсайдерскую информацию, которая развеет все сомнения. Интересно? 😉"
        ),
        "image": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1080"
    },
    {
        "stage": 2,
        "delay_index": 3,  # FOLLOW_UP_DELAYS[3] = 2880 minutes (Day 2)
        "type": "social_proof",
        "text": (
            "📈 **РЕЗУЛЬТАТЫ НАШИХ УЧАСТНИКОВ**\n\n"
            "Посмотрите на результаты одного из участников нашего закрытого клуба A-CLUB в сфере **{niche}**!\n\n"
            "Он тоже начинал с нуля, сомневался и откладывал на потом. Но применив мою пошаговую систему, "
            "он заработал первые деньги уже через неделю! Никакой магии — чистая математика и алгоритмы."
        ),
        "image": "https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=1080"
    },
    {
        "stage": 3,
        "delay_index": 4,  # FOLLOW_UP_DELAYS[4] = 4320 minutes (Day 3)
        "type": "urgency",
        "text": (
            "⏳ **ВРЕМЯ УХОДИТ!**\n\n"
            "Бронь на ваше специальное предложение по {niche} сгорает.\n\n"
            "Количество мест в закрытой группе ограничено, и я физически не смогу "
            "держать место для вас дольше. Не упустите свой шанс начать зарабатывать на лучших условиях!"
        ),
        "image": "https://images.unsplash.com/photo-1508962914676-134849a727f0?w=1080"
    },
    {
        "stage": 4,
        "delay_index": 8,  # FOLLOW_UP_DELAYS[8] = 5760 minutes (Day 4)
        "type": "direct_offer",
        "text": (
            "🔥 **СПЕЦИАЛЬНОЕ ПРЕДЛОЖЕНИЕ ДЛЯ ВАС**\n\n"
            "Хватит сомневаться и откладывать жизнь на завтра! "
            "Вот ваша персональная ссылка на вступление в наше приватное сообщество по **{niche}**.\n\n"
            "Нажимайте на кнопку ниже прямо сейчас, забирайте свою скидку и занимайте место! 👇"
        ),
        "image": "https://images.unsplash.com/photo-1553729459-beb747028b4e?w=1080",
        "keyboard": [
            [{"text": "📥 Вступить по спец. условиям", "url": CHANNEL_LINK}]
        ]
    },
    {
        "stage": 5,
        "delay_index": 9,  # FOLLOW_UP_DELAYS[9] = 7200 minutes (Day 5)
        "type": "breakup",
        "text": (
            "💔 **ФИНАЛЬНОЕ УВЕДОМЛЕНИЕ // {persona_name}**\n\n"
            "Похоже, сфера {niche} сейчас вас не интересует. Это абсолютно нормально, у каждого свои приоритеты.\n\n"
            "Я удаляю вашу бронь. Это мое последнее сообщение вам. "
            "Если вы всё же решите изменить свою жизнь — вы знаете, где меня найти. Удачи!"
        ),
        "image": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1080"
    }
]

# Communication scripts
FIRST_MESSAGE_SCRIPT = (
    "Привет! Рад видеть тебя в нашей группе. 👋\n\n"
    "Меня зовут {persona_name}. Я вижу, что ты интересуешься сферой {niche}.\n"
    "Специально для новых участников я подготовил полезный подарок! Хочешь получить?"
)

FOLLOWUP_SCRIPTS = [
    # Day 1 Followup (24 hours)
    (
        "👋 Привет! Вчера писал тебе насчет подарка по {niche}. Заметил, что ты не ответил.\n\n"
        "Специально для тебя я выложил бесплатный гайд, который поможет тебе сэкономить кучу времени. Скинуть ссылку?"
    ),
    # Day 3 Followup (72 hours)
    (
        "🔥 Привет! Всё ещё актуальна тема заработка на {niche}?\n\n"
        "Мы сейчас запускаем новый закрытый поток участников, и осталось буквально 2 места. Если интересно получить подробности, просто напиши мне «ИНТЕРЕСНО» в ответ."
    ),
    # Day 5 Followup (120 hours)
    (
        "Привет! Последний раз пишу тебе по поводу {niche}.\n\n"
        "Если ты действительно хочешь выйти на стабильный доход и не терять время зря — это твой финальный шанс. "
        "Посмотри наш официальный канал: {channel_link}. Если надумаешь — пиши, я всегда на связи. Удачи!"
    )
]

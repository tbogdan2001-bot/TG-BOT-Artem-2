# config.py
# Конфигурация бота клубной воронки (club3-сценарий).
# Логика портирована из tertiary_bot_standalone и привязана к каналу этого бота.
#
# Сценарий:
#   /start  ->  "Подпишись на канал и дождись подтверждения" (+ кнопка на канал)
#   заявка на вступление (chat_join_request)  ->  старт клубной воронки в личке
#   фото + кнопка "Я не робот"  ->  Шаг 2 ("Как заработать в 2026")
#   Шаг 3: "ГОЛОС КЛУБА" (ссылка на менеджера) + "СМОТРЕТЬ ОТЗЫВЫ" (выдаёт отзывы)
#
# При первом запуске (нет .env или не заполнен BOT_TOKEN) в терминале
# автоматически открывается мастер настройки.

import os
import sys

try:
    from dotenv import load_dotenv
except Exception:  # python-dotenv может отсутствовать — деградируем мягко
    def load_dotenv(*args, **kwargs):
        return False


# Абсолютный путь к каталогу бота (корректно работает и в скомпилированном .exe)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# -------------------------------------------------------------------
# Мастер настройки в терминале (Interactive Setup Wizard)
# -------------------------------------------------------------------
def check_and_interactive_config() -> None:
    """Если .env отсутствует или не заполнен BOT_TOKEN — запускает мастер.
    В неинтерактивной среде (Docker, отсутствие TTY) мастер пропускается."""
    env_path = os.path.join(BASE_DIR, ".env")

    existing: dict[str, str] = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        existing[k.strip()] = v.strip()
        except Exception:
            pass

    token = existing.get("BOT_TOKEN", "") or os.getenv("BOT_TOKEN", "")
    needs_setup = token in ("", "YOUR_BOT_TOKEN_HERE", "BOT_TOKEN_HERE")

    if not needs_setup:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
        return

    # Без TTY (Docker/сервис) — не блокируем запуск, просто выходим.
    if not (sys.stdin and sys.stdin.isatty()):
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
        return

    print("\n=========================================================")
    print("🚀 НАСТРОЙКА TELEGRAM-БОТА // INTERACTIVE SETUP WIZARD 🚀")
    print("=========================================================")
    print("Первый запуск или незаполненный конфиг. Заполните данные бота.\n")

    def ask(prompt_text, validate, error_msg, required=True, default=None):
        hint = f" [{default}]" if default not in (None, "") else ""
        while True:
            print(f"{prompt_text}{hint}: ", end="", flush=True)
            try:
                val = sys.stdin.readline().strip()
            except Exception:
                val = input().strip()
            if not val:
                if default not in (None, ""):
                    return default
                if not required:
                    return ""
                print("❌ Значение не может быть пустым. Попробуйте снова.")
                continue
            if validate(val):
                return val
            print(f"❌ {error_msg}")

    def ask_bool(prompt_text, default=True):
        d = "y" if default else "n"
        while True:
            print(f"{prompt_text} (y/n) [{d}]: ", end="", flush=True)
            try:
                ans = sys.stdin.readline().strip().lower()
            except Exception:
                ans = input().strip().lower()
            if ans == "":
                return default
            if ans in ("y", "yes", "д", "да"):
                return True
            if ans in ("n", "no", "н", "нет"):
                return False
            print("Введите 'y' или 'n'.")

    # БЛОК 1 — основные данные
    print("--- [ БЛОК 1: Основные данные бота ] ---")
    bot_token = ask(
        "🔑 ТОКЕН БОТА (BOT_TOKEN) от @BotFather",
        lambda v: ":" in v and len(v) > 5,
        "Токен должен быть формата xxxxx:yyyyy.",
    )
    admin_id = ask(
        "👤 Telegram ID администратора (ADMIN_ID, цифры)",
        lambda v: v.isdigit(),
        "ID должен состоять только из цифр.",
    )
    print("✅ Блок 1 сохранён.\n")

    # БЛОК 2 — канал
    print("--- [ БЛОК 2: Канал ] ---")
    print("Бот должен быть АДМИНОМ канала, а инвайт-ссылка — типа «заявка на вступление».")
    channel_id = ask(
        "📢 ID канала (начинается с -100)",
        lambda v: v.startswith("-100") and v[1:].isdigit(),
        "ID канала должен начинаться с '-100' и содержать только цифры.",
    )
    channel_link = ask(
        "🔗 Инвайт-ссылка канала (https://t.me/...)",
        lambda v: v.startswith("https://t.me/"),
        "Ссылка должна начинаться с 'https://t.me/'.",
    )
    channel_name = ask(
        "📝 Название канала",
        lambda v: len(v) > 0,
        "Название не может быть пустым.",
    )
    print("✅ Блок 2 сохранён.\n")

    # БЛОК 3 — менеджер ("ГОЛОС КЛУБА")
    print("--- [ БЛОК 3: Менеджер («ГОЛОС КЛУБА») ] ---")
    manager_username = ask(
        "💬 Username менеджера без @ (кнопка «ГОЛОС КЛУБА»)",
        lambda v: len(v) > 0 and not v.startswith("@"),
        "Введите username без символа @.",
        default="nizaev_art",
    )
    print("✅ Блок 3 сохранён.\n")

    # БЛОК 4 — режим работы воронки
    print("--- [ БЛОК 4: Режим работы бота ] ---")
    print("  Вариант 1 — воронка стартует сразу по /start,")
    print("              подписка на канал предлагается в конце.")
    print("  Вариант 2 — бот ждёт вступления в канал и пишет первым")
    print("              сразу после заявки (как в tertiary_bot_standalone).")
    bot_mode = ask(
        "🎛  Выберите режим работы (1 или 2)",
        lambda v: v in ("1", "2"),
        "Введите 1 или 2.",
        default="1",
    )
    requires_join = (bot_mode == "2")
    # Автоодобрение заявок имеет смысл только в режиме 2.
    if requires_join:
        auto_approve = ask_bool("Автоматически одобрять заявки на вступление?", default=True)
    else:
        auto_approve = True
    print("✅ Блок 4 сохранён.\n")

    # БЛОК 5 — Keitaro (необязательно)
    print("--- [ БЛОК 5: Keitaro PostBack (необязательно) ] ---")
    keitaro_url = ask(
        "🔗 KEITARO_POSTBACK_URL (Enter — пропустить)",
        lambda v: v.startswith("http://") or v.startswith("https://"),
        "URL должен начинаться с http:// или https://.",
        required=False,
    )
    print("✅ Блок 5 сохранён.\n")

    # Запись .env
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# Конфигурация бота клубной воронки (club3)\n")
            f.write("# Создано мастером настройки\n\n")
            f.write(f"BOT_TOKEN={bot_token}\n")
            f.write(f"ADMIN_ID={admin_id}\n\n")
            f.write(f"CHANNEL_ID={channel_id}\n")
            f.write(f"CHANNEL_LINK={channel_link}\n")
            f.write(f"CHANNEL_NAME={channel_name}\n\n")
            f.write(f"CLOSER_USERNAME={manager_username}\n\n")
            f.write(f"BOT_MODE={bot_mode}\n")
            f.write(f"CLUB_FLOW_REQUIRES_JOIN={'true' if requires_join else 'false'}\n")
            f.write(f"AUTO_APPROVE_JOIN={'true' if auto_approve else 'false'}\n\n")
            f.write(f"KEITARO_POSTBACK_URL={keitaro_url}\n\n")
            f.write("# Тексты и медиа можно настроить здесь (см. .env.example) или в config.py\n")
        print("[УСПЕХ] Файл .env создан!")
    except Exception as e:
        print(f"❌ Ошибка записи .env: {e}")

    last4 = bot_token[-4:] if len(bot_token) >= 4 else bot_token
    mode_desc = "1 — воронка сразу, подписка в конце" if bot_mode == "1" \
        else "2 — бот пишет первым после вступления"
    print("\n=========================================================")
    print("✅ НАСТРОЙКА ЗАВЕРШЕНА:")
    print(f"- Токен бота: ***{last4}")
    print(f"- Канал: {channel_name} ({channel_id})")
    print(f"- Менеджер: @{manager_username}")
    print(f"- Режим работы: {mode_desc}")
    if requires_join:
        print(f"- Автоодобрение заявок: {'да' if auto_approve else 'нет'}")
    print(f"- Keitaro PostBack: {'настроен' if keitaro_url else 'не настроен'}")
    print("=========================================================\n")

    load_dotenv(env_path, override=True)


# Запускаем проверку/мастер ДО чтения переменных окружения ниже
check_and_interactive_config()


# -------------------------------------------------------------------
# Поиск медиа (работает и внутри .exe, и рядом с ним)
# -------------------------------------------------------------------
def _resource_roots() -> list[str]:
    roots = [BASE_DIR]
    meipass = getattr(sys, "_MEIPASS", None)  # каталог распаковки PyInstaller
    if meipass:
        roots.insert(0, meipass)
    return roots


def _media(path: str) -> str:
    if not path:
        return ""
    if os.path.isabs(path):
        return path
    for root in _resource_roots():
        candidate = os.path.join(root, path)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(BASE_DIR, path)


def _norm(value: str) -> str:
    """Превращает экранированные \\n из .env в реальные переносы строк."""
    return (value or "").replace("\\n", "\n")


def _as_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "true" if default else "false")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# -------------------------------------------------------------------
# 1. Подключение к Telegram
# -------------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/+0npyyzG-yAoxYmMx")
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Артём Низаев | Криптовалюта, Аналитика, Доход")

admin_id_raw = os.getenv("ADMIN_ID", "0")
ADMIN_ID = int(admin_id_raw) if admin_id_raw.isdigit() else 0


# -------------------------------------------------------------------
# 2. Поведение клубной воронки
# -------------------------------------------------------------------
# Режим работы:
#   "1" — воронка стартует сразу по /start, подписка предлагается в конце.
#   "2" — бот ждёт вступления в канал и пишет первым после заявки (standalone).
BOT_MODE = os.getenv("BOT_MODE", "1").strip()

# Требование вступления по умолчанию определяется режимом, но может быть
# переопределено явной переменной CLUB_FLOW_REQUIRES_JOIN в .env.
CLUB_FLOW_REQUIRES_JOIN = _as_bool("CLUB_FLOW_REQUIRES_JOIN", BOT_MODE == "2")
AUTO_APPROVE_JOIN = _as_bool("AUTO_APPROVE_JOIN", True)


# -------------------------------------------------------------------
# 3. Ссылка на менеджера ("ГОЛОС КЛУБА" / "Написать менеджеру")
# -------------------------------------------------------------------
CLOSER_USERNAME = os.getenv("CLOSER_USERNAME", "nizaev_art")
CLUB_MANAGER_URL = os.getenv("CLUB_MANAGER_URL", CHANNEL_LINK)


# -------------------------------------------------------------------
# 4. Тексты воронки (можно переопределить через .env, поддерживается \n)
# -------------------------------------------------------------------
JOIN_WAIT_MESSAGE = _norm(os.getenv(
    "JOIN_WAIT_MESSAGE",
    "Подпишись на канал по кнопке ниже и дождись подтверждения заявки — "
    "после этого я пришлю тебе доступ к закрытому клубу. 👇",
))

START_MESSAGE = _norm(os.getenv(
    "START_MESSAGE",
    "Добро пожаловать! 🚀\n\n"
    "Прежде чем открыть доступ к материалам клуба, подтверди, что ты не робот.",
))

CLUB_STEP2_TITLE = _norm(os.getenv("CLUB_STEP2_TITLE", "<b>Как заработать в 2026?</b>"))
CLUB_STEP2_MESSAGE = _norm(os.getenv(
    "CLUB_STEP2_MESSAGE",
    "Рынок криптовалют входит в новый цикл, и сейчас лучшее время, чтобы войти "
    "в него с проверенной командой.\n\n"
    "В закрытом клубе мы каждый день разбираем сделки, делимся аналитикой и "
    "помогаем участникам выходить на стабильный доход.",
))

CLUB_STEP3_MESSAGE = _norm(os.getenv(
    "CLUB_STEP3_MESSAGE",
    "Хочешь получить персональную консультацию и забрать место в клубе?\n\n"
    "Жми «Артём Низаев», чтобы связаться напрямую, или посмотри отзывы участников 👇",
))

NOT_ROBOT_BUTTON_TEXT = os.getenv("NOT_ROBOT_BUTTON_TEXT", "Я не робот")
VOICE_BUTTON_TEXT = os.getenv("VOICE_BUTTON_TEXT", "Артём Низаев")
REVIEWS_BUTTON_TEXT = os.getenv("REVIEWS_BUTTON_TEXT", "СМОТРЕТЬ ОТЗЫВЫ")
SUBSCRIBE_BUTTON_TEXT = os.getenv("SUBSCRIBE_BUTTON_TEXT", "Подписаться на канал")


# -------------------------------------------------------------------
# 5. Медиа
# -------------------------------------------------------------------
START_IMAGE = _media(os.getenv("START_IMAGE", "media/photo1.jpg"))

_reviews_raw = os.getenv(
    "REVIEWS_MEDIA",
    "media/otzivi1.png,media/otzivi2.png,media/otzivi3.png,media/otzivi4.jpg,media/otzivi5.png",
)
REVIEWS_MEDIA = [_media(p.strip()) for p in _reviews_raw.split(",") if p.strip()]

REVIEWS_CAPTION = _norm(os.getenv("REVIEWS_CAPTION", "Отзывы участников клуба 👇"))


# -------------------------------------------------------------------
# 6. Keitaro PostBack (необязательно)
# -------------------------------------------------------------------
KEITARO_POSTBACK_URL = os.getenv("KEITARO_POSTBACK_URL", "")

# build_bot.py
# Сборка бота клубной воронки в один .exe (PyInstaller).
# Обходит ограничения cmd.exe на длину/парсинг командной строки.
#
# Что делает:
#   1) Устанавливает зависимости + PyInstaller
#   2) Компилирует main.py в один .exe (медиа из папки media/ упаковываются внутрь)
#   3) Кладёт рядом с .exe папку media/ и файл .env (как запасной вариант)
#   4) Чистит временные файлы
#
# Запуск:  python build_bot.py   (или двойной клик по build_bot.bat на Windows)

import os
import sys
import shutil
import subprocess


def safe_input(prompt=""):
    if sys.stdin and sys.stdin.isatty():
        return input(prompt)
    print(prompt)
    return ""


def main():
    # Переходим в каталог самого скрипта (на случай запуска из другой папки,
    # например из C:\Windows при запуске .bat от администратора).
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("===================================================")
    print("   СБОРКА TELEGRAM-БОТА В .EXE (club3-воронка)")
    print("===================================================")

    os.environ["PYO3_USE_ABI3_FORWARD_COMPATIBILITY"] = "1"

    # [1/4] Зависимости
    print("\n[1/4] Установка зависимостей и PyInstaller...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "pyinstaller"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка установки зависимостей: {e}")
        safe_input("\nНажмите ENTER для выхода...")
        sys.exit(1)

    # [2/4] Компиляция
    print("\n[2/4] Компиляция в один .exe...")
    # Разделитель для --add-data: ';' на Windows, ':' на остальных ОС.
    sep = ";" if os.name == "nt" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name=club_bot",
        # Упаковываем папку media (стартовое фото + отзывы) внутрь .exe
        f"--add-data=media{sep}media",
        "--hidden-import=aiogram",
        "--hidden-import=aiogram.filters",
        "--hidden-import=aiogram.types",
        "--hidden-import=aiosqlite",
        "--hidden-import=aiohttp",
        "--hidden-import=dotenv",
        "main.py",
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка компиляции PyInstaller: {e}")
        safe_input("\nНажмите ENTER для выхода...")
        sys.exit(1)

    # [3/4] Кладём рядом с .exe медиа и .env (как запасной вариант)
    print("\n[3/4] Копирование медиа и конфигурации рядом с .exe...")
    dist_dir = "dist"
    os.makedirs(dist_dir, exist_ok=True)

    # 3a. Папка media рядом с .exe (на случай, если внутренняя распаковка недоступна)
    if os.path.isdir("media"):
        dst_media = os.path.join(dist_dir, "media")
        try:
            if os.path.isdir(dst_media):
                shutil.rmtree(dst_media, ignore_errors=True)
            shutil.copytree("media", dst_media)
            print("[УСПЕХ] Папка media скопирована в dist.")
        except Exception as e:
            print(f"[ВНИМАНИЕ] Не удалось скопировать media: {e}")

    # 3b. .env: сохраняем существующий, иначе кладём шаблон
    root_env = ".env"
    dist_env = os.path.join(dist_dir, ".env")
    if not os.path.exists(root_env) and os.path.exists(dist_env):
        try:
            with open(dist_env, "r", encoding="utf-8") as f:
                content = f.read()
            if "YOUR_BOT_TOKEN_HERE" not in content and "BOT_TOKEN=" in content:
                shutil.copy(dist_env, root_env)
                print("[УСПЕХ] Заполненный dist/.env сохранён в корень.")
        except Exception:
            pass

    if os.path.exists(root_env):
        try:
            shutil.copy(root_env, dist_env)
            print("[УСПЕХ] .env скопирован в dist.")
        except Exception as e:
            print(f"❌ Ошибка копирования .env в dist: {e}")
    elif os.path.exists(dist_env):
        print("[ИНФО] dist/.env уже существует — пропускаю шаблон.")
    elif os.path.exists(".env.example"):
        try:
            shutil.copy(".env.example", dist_env)
            print("[УСПЕХ] Шаблон .env.example скопирован как dist/.env.")
        except Exception as e:
            print(f"❌ Ошибка копирования .env.example: {e}")

    # [4/4] Очистка
    print("\n[4/4] Очистка временных файлов...")
    shutil.rmtree("build", ignore_errors=True)
    for spec in ("club_bot.spec", "main.spec"):
        if os.path.exists(spec):
            try:
                os.remove(spec)
            except Exception:
                pass
    print("[УСПЕХ] Готово.")

    print("\n===================================================")
    print("   СБОРКА ЗАВЕРШЕНА!")
    print('   1. Откройте папку "dist"')
    print('   2. Запустите "club_bot.exe" (.exe сам спросит данные при первом запуске)')
    print("===================================================")
    safe_input("\nНажмите ENTER для выхода...")


if __name__ == "__main__":
    main()

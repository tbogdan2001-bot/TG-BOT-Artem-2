# build_bot.py
# Python-based compiler script that bypasses command line length and character parsing limits of Windows cmd.exe.
# Installs dependencies, runs PyInstaller, copies configuration files, and cleans up.
#
# NOTE ON STARTUP BEHAVIOR:
# The compiled bot (telegram_funnel_bot.exe) boots via main.py. On startup,
# all active Telethon userbots (configured manager accounts in accounts.py)
# will automatically check if they are members of the target channel (TARGET_CHANNEL in config.py / .env)
# and automatically join it using the invite link (joinInviteLink / ImportChatInviteRequest) if not already a member.

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
    print("===================================================")
    print("   СТАРТ СБОРКИ TELEGRAM-БОТА В .EXE ФАЙЛ (Python-Сборщик)")
    print("===================================================")
    
    # 1. Bypassing Rust build version check for Python 3.14 Compatibility
    os.environ["PYO3_USE_ABI3_FORWARD_COMPATIBILITY"] = "1"
    
    # 2. Install dependencies
    print("\n[1/4] Установка PyInstaller и зависимостей...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "pyinstaller"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при установке зависимостей: {e}")
        safe_input("\nНажмите клавишу ENTER для выхода...")
        sys.exit(1)
        
    # 3. Compile with PyInstaller
    print("\n[2/4] Компиляция проекта в один .exe файл...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--console",
        "--name=telegram_funnel_bot",
        "--hidden-import=aiogram",
        "--hidden-import=aiogram.dispatcher",
        "--hidden-import=aiogram.filters",
        "--hidden-import=aiogram.fsm.storage.memory",
        "--hidden-import=aiogram.types",
        "--hidden-import=aiosqlite",
        "--hidden-import=apscheduler",
        "--hidden-import=apscheduler.schedulers.asyncio",
        "--hidden-import=apscheduler.triggers.cron",
        "--hidden-import=apscheduler.triggers.interval",
        "--hidden-import=apscheduler.triggers.date",
        "--hidden-import=telethon",
        "--hidden-import=telethon.crypto",
        "--hidden-import=telethon.extensions",
        "--hidden-import=google.generativeai",
        "--hidden-import=google.protobuf",
        "--hidden-import=google.protobuf.descriptor",
        "--hidden-import=google.protobuf.message",
        "--hidden-import=google.protobuf.pyext._message",
        "--hidden-import=redis",
        "--hidden-import=redis.asyncio",
        "--hidden-import=aiogram.fsm.storage.redis",
        "main.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при компиляции PyInstaller: {e}")
        safe_input("\nНажмите клавишу ENTER для выхода...")
        sys.exit(1)
        
    # 4. Copy configuration files and session files
    print("\n[3/4] Копирование конфигурационных и сессионных файлов...")
    dist_dir = "dist"
    os.makedirs(dist_dir, exist_ok=True)
    dist_env = os.path.join(dist_dir, ".env")
    root_env = ".env"
    
    # 4a. Если в корне нет .env, но в dist/.env есть заполненный файл, спасаем его и копируем в корень
    if not os.path.exists(root_env) and os.path.exists(dist_env):
        is_placeholder = True
        try:
            with open(dist_env, "r", encoding="utf-8") as f:
                content = f.read()
                if "YOUR_BOT_TOKEN_HERE" not in content and "BOT_TOKEN=" in content:
                    is_placeholder = False
        except Exception:
            pass
            
        if not is_placeholder:
            try:
                shutil.copy(dist_env, root_env)
                print("[УСПЕХ] Обнаружен заполненный файл dist\\.env! Он скопирован в корень проекта для сохранения настроек.")
            except Exception as e:
                print(f"[ВНИМАНИЕ] Не удалось скопировать dist\\.env в корень: {e}")
                
    # 4b. Синхронизируем .env
    if os.path.exists(root_env):
        try:
            shutil.copy(root_env, dist_env)
            print("[УСПЕХ] Файл .env успешно скопирован в папку dist!")
        except Exception as e:
            print(f"❌ Ошибка при копировании .env в dist: {e}")
    elif os.path.exists(dist_env):
        print("[ИНФО] Файл .env уже существует в папке dist. Пропуск копирования шаблона во избежание перезаписи настроек.")
    elif os.path.exists(".env.example"):
        try:
            shutil.copy(".env.example", dist_env)
            print("[УСПЕХ] Шаблон .env.example скопирован как dist\\.env!")
        except Exception as e:
            print(f"❌ Ошибка при копировании .env.example: {e}")
    else:
        print("[ВНИМАНИЕ] Конфигурационные файлы не найдены!")
        
    # 4c. Копируем сессии (.session файлы) из корня в dist
    import glob
    session_files = glob.glob("*.session")
    for f_path in session_files:
        try:
            shutil.copy(f_path, os.path.join(dist_dir, f_path))
            print(f"[УСПЕХ] Файл сессии {f_path} успешно скопирован в папку dist!")
        except Exception as e:
            print(f"❌ Ошибка при копировании файла сессии {f_path}: {e}")
        
    # 5. Clean up temporary files
    print("\n[4/4] Очистка временных файлов сборщика...")
    if os.path.exists("build"):
        shutil.rmtree("build", ignore_errors=True)
    if os.path.exists("telegram_funnel_bot.spec"):
        try:
            os.remove("telegram_funnel_bot.spec")
        except Exception:
            pass
    print("[УСПЕХ] Временные папки очищены.")
    
    print("\n===================================================")
    print("   СБОРКА УСПЕШНО ЗАВЕРШЕНА!")
    print("\n   1. Откройте появившуюся папку \"dist\"")
    print("   2. Запустите \"telegram_funnel_bot.exe\"")
    print("===================================================")
    safe_input("\nНажмите клавишу ENTER для выхода...")


if __name__ == "__main__":
    main()

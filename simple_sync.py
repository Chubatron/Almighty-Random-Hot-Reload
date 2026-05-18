import os
import time
import subprocess
import json
import sys
import shutil

PACKAGE = "org.almighty.almightyrandom"
APP_DIR = f"/data/data/{PACKAGE}/files/app"
FILES_DIR = f"/data/data/{PACKAGE}/files"
ADB = "adb.exe"

STATE_FILE = "sync_state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def get_files_to_watch():
    files_to_watch = []

    if os.path.exists("main.py"):
        files_to_watch.append("main.py")

    if os.path.exists("settings.json"):
        files_to_watch.append("settings.json")

    if os.path.exists("sound_manager.py"):
        files_to_watch.append("sound_manager.py")

    if os.path.exists("screens"):
        for f in os.listdir("screens"):
            if f.endswith(".py") and f != "__init__.py":
                files_to_watch.append(f"screens/{f}")

    if os.path.exists("components"):
        for f in os.listdir("components"):
            if f.endswith(".py") and f != "__init__.py":
                files_to_watch.append(f"components/{f}")

    if os.path.exists("locales"):
        for f in os.listdir("locales"):
            if f.endswith(".json"):
                files_to_watch.append(f"locales/{f}")

    return files_to_watch


def get_all_assets_files():
    assets_files = []
    assets_dir = "assets"

    if os.path.exists(assets_dir):
        for root, dirs, files in os.walk(assets_dir):
            for file in files:
                if file.startswith('.'):
                    continue
                rel_path = os.path.join(root, file)
                assets_files.append(rel_path)

    return assets_files


def print_file_list():
    files = get_files_to_watch()
    assets_files = get_all_assets_files()

    print("\n" + "=" * 60)
    print("📁 СПИСОК ОТСЛЕЖИВАЕМЫХ ФАЙЛОВ И ПАПОК")
    print("=" * 60)

    main_files = [f for f in files if f == "main.py"]
    settings_files = [f for f in files if f == "settings.json"]
    sound_manager_files = [f for f in files if f == "sound_manager.py"]
    screens_files = [f for f in files if f.startswith("screens/")]
    components_files = [f for f in files if f.startswith("components/")]
    locales_files = [f for f in files if f.startswith("locales/")]

    if main_files:
        print("\n📄 Главный файл:")
        for f in main_files:
            print(f"   • {f}")

    if settings_files:
        print("\n⚙️ Файл настроек:")
        for f in settings_files:
            print(f"   • {f}")

    if sound_manager_files:
        print("\n🔊 Файл управления звуком:")
        for f in sound_manager_files:
            print(f"   • {f}")

    if screens_files:
        print(f"\n📁 Папка screens/ ({len(screens_files)} файлов):")
        for f in sorted(screens_files):
            print(f"   • {f}")

    if components_files:
        print(f"\n📁 Папка components/ ({len(components_files)} файлов):")
        for f in sorted(components_files):
            print(f"   • {f}")

    if locales_files:
        print(f"\n📁 Папка locales/ ({len(locales_files)} файлов):")
        for f in sorted(locales_files):
            print(f"   • {f}")

    if assets_files:
        print(f"\n📁 Папка assets/ ({len(assets_files)} файлов):")
        for f in sorted(assets_files)[:10]:
            print(f"   • {f}")
        if len(assets_files) > 10:
            print(f"   ... и еще {len(assets_files) - 10} файлов")

    print("\n" + "=" * 60)
    print(f"📊 ВСЕГО ФАЙЛОВ: {len(files) + len(assets_files)}")
    print(f"   • Код и настройки: {len(files)}")
    print(f"   • Ресурсы (assets): {len(assets_files)}")
    print("=" * 60 + "\n")


def delete_sync_files_on_phone():
    """Удаляет на телефоне только те файлы, которые будут синхронизироваться"""
    print("\n" + "=" * 50)
    print("🗑️ УДАЛЕНИЕ ФАЙЛОВ НА ТЕЛЕФОНЕ (только синхронизируемые)")
    print("=" * 50)

    files_to_sync = get_files_to_watch()
    assets_files = get_all_assets_files()

    # Удаляем main.py
    if "main.py" in files_to_sync:
        print("Удаление main.py...")
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/main.py"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/main.pyc"', shell=True)
        print("   ✅ main.py удален")

    # Удаляем settings.json
    if "settings.json" in files_to_sync:
        print("Удаление settings.json...")
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {FILES_DIR}/settings.json"', shell=True)
        print("   ✅ settings.json удален")

    # Удаляем sound_manager.py
    if "sound_manager.py" in files_to_sync:
        print("Удаление sound_manager.py...")
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/sound_manager.py"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/sound_manager.pyc"', shell=True)
        print("   ✅ sound_manager.py удален")

    # Удаляем файлы из screens
    screens_files = [f for f in files_to_sync if f.startswith("screens/")]
    if screens_files:
        print(f"\nУдаление файлов из screens/ ({len(screens_files)} файлов):")
        for filepath in screens_files:
            filename = os.path.basename(filepath)
            subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/screens/{filename}"', shell=True)
            subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/screens/{filename[:-3]}.*"', shell=True)
            print(f"   ✅ {filename}")

    # Удаляем файлы из components
    components_files = [f for f in files_to_sync if f.startswith("components/")]
    if components_files:
        print(f"\nУдаление файлов из components/ ({len(components_files)} файлов):")
        for filepath in components_files:
            filename = os.path.basename(filepath)
            subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/components/{filename}"', shell=True)
            subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/components/{filename[:-3]}.*"', shell=True)
            print(f"   ✅ {filename}")

    # Удаляем файлы из locales
    locales_files = [f for f in files_to_sync if f.startswith("locales/")]
    if locales_files:
        print(f"\nУдаление файлов из locales/ ({len(locales_files)} файлов):")
        for filepath in locales_files:
            filename = os.path.basename(filepath)
            subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/locales/{filename}"', shell=True)
            print(f"   ✅ {filename}")

    # Удаляем ВСЮ папку assets (целиком)
    if assets_files:
        print(f"\nУдаление папки assets/ ({len(assets_files)} файлов)...")
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -rf {APP_DIR}/assets"', shell=True)
        print("   ✅ Папка assets удалена целиком")

    print("=" * 50 + "\n")


def full_sync():
    """Полная перезапись (удаляем синхронизируемые файлы, потом копируем заново)"""
    print("\n" + "=" * 50)
    print("📦 ПОЛНАЯ СИНХРОНИЗАЦИЯ (УДАЛЕНИЕ + ЗАПИСЬ)")
    print("=" * 50)

    # 1. Удаляем только синхронизируемые файлы на телефоне
    delete_sync_files_on_phone()

    files_to_sync = get_files_to_watch()
    assets_files = get_all_assets_files()

    total_files = len(files_to_sync) + len(assets_files)
    success_count = 0
    error_count = 0

    print("\n📤 КОПИРОВАНИЕ ФАЙЛОВ НА ТЕЛЕФОН")
    print("-" * 50)

    # 2. Копируем main.py
    if os.path.exists("main.py"):
        print("\n📄 Копирование main.py...")
        subprocess.run(f"{ADB} push main.py /data/local/tmp/", shell=True)
        result = subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/main.py {APP_DIR}/"', shell=True)
        if result.returncode == 0:
            success_count += 1
            print("   ✅ main.py")
        else:
            error_count += 1
            print("   ❌ main.py")

    # 3. Копируем settings.json
    if os.path.exists("settings.json"):
        print("\n⚙️ Копирование settings.json...")
        with open("settings.json", 'r') as f:
            print(f"   📄 Содержимое: {f.read().strip()}")
        subprocess.run(f"{ADB} push settings.json /data/local/tmp/", shell=True)
        result = subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/settings.json {FILES_DIR}/"',
                                shell=True)
        if result.returncode == 0:
            success_count += 1
            print("   ✅ settings.json")
        else:
            error_count += 1
            print("   ❌ settings.json")

    # 4. Копируем sound_manager.py
    if os.path.exists("sound_manager.py"):
        print("\n🔊 Копирование sound_manager.py...")
        subprocess.run(f"{ADB} push sound_manager.py /data/local/tmp/", shell=True)
        result = subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/sound_manager.py {APP_DIR}/"',
                                shell=True)
        if result.returncode == 0:
            success_count += 1
            print("   ✅ sound_manager.py")
        else:
            error_count += 1
            print("   ❌ sound_manager.py")

    # 5. Копируем screens файлы
    screens_files = [f for f in files_to_sync if f.startswith("screens/")]
    if screens_files:
        print(f"\n📁 Копирование screens/ ({len(screens_files)} файлов)...")
        for filepath in screens_files:
            filename = os.path.basename(filepath)
            subprocess.run(f"{ADB} push {filepath} /data/local/tmp/", shell=True, capture_output=True)
            subprocess.run(f'{ADB} shell "run-as {PACKAGE} mkdir -p {APP_DIR}/screens"', shell=True)
            result = subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/screens/"',
                                    shell=True)
            if result.returncode == 0:
                success_count += 1
                print(f"   ✅ {filename}")
            else:
                error_count += 1
                print(f"   ❌ {filename}")

    # 6. Копируем components файлы
    components_files = [f for f in files_to_sync if f.startswith("components/")]
    if components_files:
        print(f"\n📁 Копирование components/ ({len(components_files)} файлов)...")
        for filepath in components_files:
            filename = os.path.basename(filepath)
            subprocess.run(f"{ADB} push {filepath} /data/local/tmp/", shell=True, capture_output=True)
            subprocess.run(f'{ADB} shell "run-as {PACKAGE} mkdir -p {APP_DIR}/components"', shell=True)
            result = subprocess.run(
                f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/components/"', shell=True)
            if result.returncode == 0:
                success_count += 1
                print(f"   ✅ {filename}")
            else:
                error_count += 1
                print(f"   ❌ {filename}")

    # 7. Копируем locales файлы
    locales_files = [f for f in files_to_sync if f.startswith("locales/")]
    if locales_files:
        print(f"\n📁 Копирование locales/ ({len(locales_files)} файлов)...")
        for filepath in locales_files:
            filename = os.path.basename(filepath)
            subprocess.run(f"{ADB} push {filepath} /data/local/tmp/", shell=True, capture_output=True)
            subprocess.run(f'{ADB} shell "run-as {PACKAGE} mkdir -p {APP_DIR}/locales"', shell=True)
            result = subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/locales/"',
                                    shell=True)
            if result.returncode == 0:
                success_count += 1
                print(f"   ✅ {filename}")
            else:
                error_count += 1
                print(f"   ❌ {filename}")

    # 8. Копируем assets (вся папка целиком)
    if assets_files:
        print(f"\n📁 Копирование assets/ ({len(assets_files)} файлов)...")

        # Создаем временную папку
        temp_assets = "temp_assets_for_sync"
        if os.path.exists(temp_assets):
            shutil.rmtree(temp_assets)
        shutil.copytree("assets", temp_assets)

        # Копируем всю папку на телефон
        subprocess.run(f"{ADB} push {temp_assets} /data/local/tmp/", shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} mkdir -p {APP_DIR}/assets"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp -r /data/local/tmp/{temp_assets}/* {APP_DIR}/assets/"',
                       shell=True)

        # Удаляем временную папку
        shutil.rmtree(temp_assets)

        success_count += len(assets_files)
        print(f"   ✅ Скопировано {len(assets_files)} файлов")

    print("-" * 50)
    print(f"\n📊 ОТЧЕТ О ПОЛНОЙ СИНХРОНИЗАЦИИ:")
    print(f"   ✅ Успешно: {success_count}")
    print(f"   ❌ Ошибок: {error_count}")
    print(f"   📁 Всего: {total_files}")

    # 9. Перезапускаем приложение
    print("\n🔄 Перезапуск приложения...")
    subprocess.run(f"{ADB} shell am force-stop {PACKAGE}", shell=True)
    time.sleep(0.5)
    subprocess.run(f"{ADB} shell am start -n {PACKAGE}/org.kivy.android.PythonActivity", shell=True)
    print("✅ Приложение перезапущено")

    # 10. Сохраняем состояние
    state = {}
    for filepath in files_to_sync:
        if os.path.exists(filepath):
            state[filepath] = os.path.getmtime(filepath)
    save_state(state)
    print("📁 Состояние синхронизации обновлено")


def sync_file(filepath):
    """Синхронизация отдельного файла (для режима слежения)"""
    filename = os.path.basename(filepath)
    print(f"🔄 Синхронизация: {filepath}")

    if filepath == "settings.json":
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   📄 Содержимое исходного файла: {content.strip()}")
        except Exception as e:
            print(f"   ⚠️ Ошибка чтения: {e}")

    subprocess.run(f"{ADB} push {filepath} /data/local/tmp/", shell=True)

    if filepath.startswith("screens/"):
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/screens/{filename}"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/screens/"', shell=True)

    elif filepath.startswith("components/"):
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/components/{filename}"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/components/"',
                       shell=True)

    elif filepath.startswith("locales/"):
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/locales/{filename}"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/locales/"', shell=True)

    elif filepath == "main.py":
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/{filename}"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/"', shell=True)

    elif filepath == "sound_manager.py":
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/{filename}"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/"', shell=True)

    elif filepath == "settings.json":
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {FILES_DIR}/{filename}"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {FILES_DIR}/"', shell=True)

        result = subprocess.run(f'{ADB} shell "run-as {PACKAGE} cat {FILES_DIR}/{filename}"',
                                shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   📄 На телефоне после копирования: {result.stdout.strip()}")

    subprocess.run(f"{ADB} shell am force-stop {PACKAGE}", shell=True)
    time.sleep(0.5)
    subprocess.run(f"{ADB} shell am start -n {PACKAGE}/org.kivy.android.PythonActivity", shell=True)

    print(f"✅ Готово: {filename}")


def watch_mode():
    """Режим слежения за изменениями файлов"""
    print("\n" + "=" * 50)
    print("👀 РЕЖИМ СЛЕЖЕНИЯ ЗА ИЗМЕНЕНИЯМИ")
    print("=" * 50)
    print("При сохранении файла (Ctrl+S) синхронизация произойдёт.")
    print("Нажмите Ctrl+C для выхода в главное меню.")
    print("=" * 50)

    files_to_watch = get_files_to_watch()

    print(f"📋 Отслеживается {len(files_to_watch)} файлов")
    print_file_list()

    state = load_state()

    for file in files_to_watch:
        if file not in state:
            if os.path.exists(file):
                state[file] = os.path.getmtime(file)
            else:
                state[file] = 0

    save_state(state)

    try:
        while True:
            changed = False
            for file in files_to_watch:
                if os.path.exists(file):
                    mtime = os.path.getmtime(file)
                    if mtime != state.get(file, 0):
                        state[file] = mtime
                        changed = True
                        print(f"\n📝 Изменён: {file}")
                        sync_file(file)
                        save_state(state)

            if not changed:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Выход из режима слежения...")
        save_state(state)
        return


def show_menu():
    """Показывает меню выбора режима"""
    print("\n" + "=" * 50)
    print("🔄 СИНХРОНИЗАЦИЯ С ТЕЛЕФОНОМ")
    print("=" * 50)

    files = get_files_to_watch()
    assets_files = get_all_assets_files()

    print(f"\n📁 Отслеживаемые файлы и папки:")
    print(f"   • main.py")
    print(f"   • settings.json")
    print(f"   • sound_manager.py")
    print(f"   • screens/ (*.py)")
    print(f"   • components/ (*.py)")
    print(f"   • locales/ (*.json)")
    print(f"   • assets/ (все файлы, УДАЛЯЕТСЯ ЦЕЛИКОМ)")
    print(f"\n   📊 Всего файлов: {len(files) + len(assets_files)}")

    print("\n" + "-" * 50)
    print("\nВыберите режим работы:")
    print("  1. Обычный режим (слежение за изменениями)")
    print("  2. ПОЛНАЯ ПЕРЕЗАПИСЬ (удаляет синхронизируемые файлы на телефоне и копирует заново)")
    print("  3. Показать полный список файлов")
    print("  4. Выход")
    print("-" * 50)

    while True:
        try:
            choice = input("Ваш выбор (1, 2, 3 или 4): ").strip()
            if choice == "1":
                return "watch"
            elif choice == "2":
                return "full"
            elif choice == "3":
                return "list"
            elif choice == "4":
                return "exit"
            else:
                print("❌ Неверный ввод. Пожалуйста, введите 1, 2, 3 или 4.")
        except KeyboardInterrupt:
            return "exit"


def main():
    """Главная функция"""
    while True:
        choice = show_menu()

        if choice == "watch":
            watch_mode()
        elif choice == "full":
            full_sync()
            input("\nНажмите Enter для возврата в меню...")
        elif choice == "list":
            print_file_list()
            input("\nНажмите Enter для возврата в меню...")
        elif choice == "exit":
            print("\n👋 Завершение работы скрипта...")
            sys.exit(0)


if __name__ == "__main__":
    main()
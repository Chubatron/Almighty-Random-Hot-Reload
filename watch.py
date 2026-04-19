import os
import time
import subprocess
import hashlib

PACKAGE = "org.almighty.almightyrandom"
APP_DIR = f"/data/data/{PACKAGE}/files/app"
ADB = "adb.exe"

def get_file_hash(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def sync_file(local_path, remote_path):
    print(f"  📄 {local_path}")
    subprocess.run(f"{ADB} push {local_path} /data/local/tmp/", shell=True, capture_output=True)
    subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{os.path.basename(local_path)} {APP_DIR}/{remote_path}"', shell=True, capture_output=True)

def sync_folder(local_folder, remote_folder):
    """Копирует только .py файлы (кроме __init__.py)"""
    print(f"  📁 {local_folder}/")
    
    for root, dirs, files in os.walk(local_folder):
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        
        for file in files:
            # Копируем только .py файлы, исключая __init__.py
            if file.endswith('.py') and file != '__init__.py':
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, local_folder)
                remote_path = os.path.join(remote_folder, rel_path).replace('\\', '/')
                
                print(f"    📄 {rel_path}")
                subprocess.run(f"{ADB} push {local_path} /data/local/tmp/", shell=True, capture_output=True)
                subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{file} {APP_DIR}/{remote_path}"', shell=True, capture_output=True)

def restart_app():
    print("  🔄 Перезапуск приложения...")
    subprocess.run(f"{ADB} shell am force-stop {PACKAGE}", shell=True)
    time.sleep(1)
    subprocess.run(f"{ADB} shell am start -n {PACKAGE}/org.kivy.android.PythonActivity", shell=True)

def sync_all():
    print("\n🔄 Синхронизация с телефоном...")
    
    # Очищаем кеш
    subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -rf {APP_DIR}/__pycache__"', shell=True, capture_output=True)
    subprocess.run(f'{ADB} shell "run-as {PACKAGE} find {APP_DIR} -name "*.pyc" -delete"', shell=True, capture_output=True)
    
    # Синхронизируем файлы
    if os.path.exists("screens"):
        sync_folder("screens", "screens")
    if os.path.exists("components"):
        sync_folder("components", "components")
    if os.path.exists("locales"):
        for f in os.listdir("locales"):
            if f.endswith(".json"):
                sync_file(f"locales/{f}", "locales/")
    
    # Очищаем кеш ещё раз
    subprocess.run(f'{ADB} shell "run-as {PACKAGE} find {APP_DIR} -name "*.pyc" -delete"', shell=True, capture_output=True)
    subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -rf {APP_DIR}/__pycache__"', shell=True, capture_output=True)
    
    restart_app()
    print("✅ Готово!")

print("=" * 50)
print("👀 Синхронизация (без __pycache__ и __init__.py)")
print("=" * 50)
print("Отслеживаются:")
print("  - screens/*.py (кроме __init__.py)")
print("  - components/*.py (кроме __init__.py)")
print("  - locales/*.json")
print("")
print("При сохранении файла (Ctrl+S) синхронизация произойдёт автоматически.")
print("Нажмите Ctrl+C для выхода.")
print("=" * 50)

# Список файлов для отслеживания
files_to_watch = []

if os.path.exists("screens"):
    for f in os.listdir("screens"):
        if f.endswith('.py') and f != '__init__.py':
            files_to_watch.append(f"screens/{f}")

if os.path.exists("components"):
    for f in os.listdir("components"):
        if f.endswith('.py') and f != '__init__.py':
            files_to_watch.append(f"components/{f}")

if os.path.exists("locales"):
    for f in os.listdir("locales"):
        if f.endswith(".json"):
            files_to_watch.append(f"locales/{f}")

print(f"\nОтслеживается {len(files_to_watch)} файлов:")
for f in files_to_watch[:15]:
    print(f"  - {f}")
if len(files_to_watch) > 15:
    print(f"  ... и ещё {len(files_to_watch) - 15} файлов")
print("")

file_hashes = {}
for file in files_to_watch:
    if os.path.exists(file):
        file_hashes[file] = get_file_hash(file)

try:
    while True:
        changed = False
        for file in files_to_watch:
            if os.path.exists(file):
                current_hash = get_file_hash(file)
                if file_hashes.get(file) != current_hash:
                    file_hashes[file] = current_hash
                    changed = True
                    print(f"\n📝 Изменён: {file}")
        
        if changed:
            sync_all()
        
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n👋 Завершение работы...")
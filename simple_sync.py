import os
import time
import subprocess
import json

PACKAGE = "org.almighty.almightyrandom"
APP_DIR = f"/data/data/{PACKAGE}/files/app"
ADB = "adb.exe"

# Файл для сохранения состояния
STATE_FILE = "sync_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def sync_file(filepath):
    filename = os.path.basename(filepath)
    print(f"🔄 Синхронизация: {filepath}")
    
    subprocess.run(f"{ADB} push {filepath} /data/local/tmp/", shell=True)
    
    if filepath.startswith("screens/"):
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/screens/"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/screens/{filename[:-3]}.*"', shell=True)
    elif filepath.startswith("components/"):
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/components/"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/components/{filename[:-3]}.*"', shell=True)
    elif filepath.startswith("locales/"):
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/locales/"', shell=True)
    elif filepath == "main.py":
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} cp /data/local/tmp/{filename} {APP_DIR}/"', shell=True)
        subprocess.run(f'{ADB} shell "run-as {PACKAGE} rm -f {APP_DIR}/{filename[:-3]}.*"', shell=True)
    
    subprocess.run(f"{ADB} shell am force-stop {PACKAGE}", shell=True)
    time.sleep(0.5)
    subprocess.run(f"{ADB} shell am start -n {PACKAGE}/org.kivy.android.PythonActivity", shell=True)
    
    print(f"✅ Готово: {filename}")

print("=" * 50)
print("👀 Синхронизация (с сохранением состояния)")
print("=" * 50)
print("При сохранении файла (Ctrl+S) синхронизация произойдёт.")
print("Нажмите Ctrl+C для выхода.")
print("=" * 50)

# Загружаем сохранённое состояние
state = load_state()
print(f"Загружено {len(state)} файлов из истории")

# Собираем все файлы для отслеживания
files_to_watch = []

# ✅ ДОБАВЛЯЕМ main.py
if os.path.exists("main.py"):
    files_to_watch.append("main.py")

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

print(f"Отслеживается {len(files_to_watch)} файлов")
print("Список отслеживаемых файлов:")
for f in files_to_watch:
    print(f"  - {f}")

# Инициализируем состояние для новых файлов
for file in files_to_watch:
    if file not in state:
        state[file] = 0

# Сохраняем начальное состояние
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
                    save_state(state)  # Сохраняем после каждого изменения
        
        if not changed:
            time.sleep(1)
except KeyboardInterrupt:
    print("\n\n👋 Завершение работы...")
    save_state(state)
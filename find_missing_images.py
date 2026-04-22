import os
import sys

# Фикс путей
if 'ANDROID_ARGUMENT' in os.environ:
    android_dir = '/data/data/org.almighty.almightyrandom/files/app'
    if os.path.exists(android_dir):
        os.chdir(android_dir)

print("=" * 60)
print("ДИАГНОСТИКА ИЗОБРАЖЕНИЙ")
print("=" * 60)

# Проверяем все возможные пути для изображений
image_paths = [
    # Корневые изображения
    'assets/icon.png',
    
    # Кнопки
    'assets/images/buttons/white_exit_button.png',
    'assets/images/buttons/Exit_button.png',
    'assets/images/buttons/Blue_roulette_button.png',
    'assets/images/buttons/Green_random_button.png',
    'assets/images/buttons/Red_rus_roulette_button.png',
    'assets/images/buttons/Dice_button.png',
    'assets/images/buttons/rsp_button.png',
    'assets/images/buttons/Share_button.png',
    'assets/images/buttons/White_lang_button.png',
    'assets/images/buttons/White_rate_button.png',
    'assets/images/buttons/White_share_button.png',
    'assets/images/buttons/white_sound_off_button.png',
    'assets/images/buttons/White_sound_on_button.png',
    'assets/images/buttons/Orange_back_to_menu_button.png',
    'assets/images/buttons/load_button.png',
    'assets/images/buttons/spin_button_green.png',
    'assets/images/buttons/spin_button_red.png',
    'assets/images/buttons/rotate_button.png',
    'assets/images/buttons/rotate_red_button.png',
    'assets/images/buttons/Mute_blue_button.png',
    'assets/images/buttons/Unmute_orange_button.png',
    
    # Фоны
    'assets/backgrounds/coin_bg.png',
    'assets/backgrounds/indigo_bg.png',
    'assets/backgrounds/roulette_bg.jpg',
    'assets/backgrounds/rsp_bg.jpg',
    'assets/backgrounds/football_bg.jpg',
    'assets/backgrounds/rus_roulette_bg_1024x1024.jpg',
    
    # Мячи
    'assets/balls/basketball.png',
    'assets/balls/bowling_ball.png',
    'assets/balls/dice.png',
    'assets/balls/football.png',
    'assets/balls/Roulette_ball.png',
    
    # Монеты
    'assets/images/coin/orel.png',
    'assets/images/coin/reshka.png',
    
    # RSP
    'assets/images/rsp/rock.png',
    'assets/images/rsp/paper.png',
    'assets/images/rsp/scissors.png',
    'assets/images/rsp/lizard.png',
    'assets/images/rsp/spock.png',
    
    # Русская рулетка
    'assets/images/guns/revolver.png',
    'assets/images/guns/Drum_1024x1024.png',
]

print("\n📋 ПРОВЕРКА ФАЙЛОВ:")
print("-" * 60)

working = []
missing = []

for path in image_paths:
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {path}")
    if exists:
        working.append(path)
    else:
        missing.append(path)

print("\n" + "=" * 60)
print(f"✅ РАБОТАЮТ: {len(working)} файлов")
print(f"❌ ОТСУТСТВУЮТ: {len(missing)} файлов")
print("=" * 60)

if missing:
    print("\n❌ ОТСУТСТВУЮЩИЕ ФАЙЛЫ:")
    for m in missing:
        print(f"  - {m}")

print("\n💡 СОВЕТЫ:")
print("1. Убедитесь, что файлы существуют в папке assets на компьютере")
print("2. Проверьте правильность написания путей в вашем коде")
print("3. В Kivy используйте относительные пути от корня приложения")

# Проверяем содержимое папок
print("\n📁 СОДЕРЖИМОЕ ПАПОК:")
for folder in ['assets/images/buttons', 'assets/backgrounds', 'assets/balls']:
    if os.path.exists(folder):
        files = os.listdir(folder)
        print(f"\n{folder}: {len(files)} файлов")
        for f in files[:5]:
            print(f"  - {f}")

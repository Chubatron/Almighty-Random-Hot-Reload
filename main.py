import os
import sys
import json
import requests
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

# --- ЗАПРОС РАЗРЕШЕНИЙ ДЛЯ ANDROID ---
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission

        request_permissions([
            Permission.INTERNET,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.VIBRATE  # ← ДОБАВЛЕНО РАЗРЕШЕНИЕ ДЛЯ ВИБРАЦИИ
        ])
    except ImportError:
        print("⚠️ Не удалось импортировать android.permissions")
# ------------------------------------

# --- ПРАВИЛЬНАЯ РАБОЧАЯ ДИРЕКТОРИЯ ДЛЯ ANDROID ---
if platform == 'android':
    # ПРАВИЛЬНАЯ папка приложения (где лежат assets, screens, components)
    app_dir = "/data/data/org.almighty.almightyrandom/files/app"

    # Проверяем и устанавливаем рабочую директорию
    if os.path.exists(app_dir):
        os.chdir(app_dir)
        print(f"[DEBUG] Working directory set to: {os.getcwd()}")
    else:
        print(f"[ERROR] App directory not found: {app_dir}")

    # Проверяем наличие assets
    if os.path.exists('assets'):
        print(f"[DEBUG] Assets folder found!")
        print(f"[DEBUG] Fonts exist: {os.path.exists('assets/fonts/JockeyOne-Regular.ttf')}")
        print(f"[DEBUG] Backgrounds exist: {os.path.exists('assets/backgrounds/indigo_bg.png')}")
    else:
        print(f"[ERROR] Assets folder not found in {os.getcwd()}")
        print(f"[DEBUG] Directory contents: {os.listdir('.')}")

    # Папка для синхронизации (оставляем для других целей)
    sync_path = "/data/data/org.almighty.almightyrandom/files/sync"
    if not os.path.exists(sync_path):
        os.makedirs(sync_path)

    # Добавляем в путь поиска модулей (НЕ меняем рабочую директорию)
    if sync_path not in sys.path:
        sys.path.insert(0, sync_path)
# -----------------------------------------

# Импорты ваших модулей
from language_manager import LanguageManager
from sound_manager import SoundManager

# Импорты экранов с обработкой ошибок
try:
    from screens.menu_screen import MainMenuScreen
    from screens.coin_screen import CoinScreen
    from screens.dice_screen import DiceScreen
    from screens.roulette_screen import RouletteScreen
    from screens.rus_roulette_screen import RusRouletteScreen
    from screens.quiz_screen import QuizScreen
    from screens.random_screen import RandomScreen
    from screens.random_number import RandomNumberScreen
    from screens.magic_ball_screen import MagicBallScreen
    from screens.intermediate_roulette import IntermediateRoulette
    from screens.intermediate_random import IntermediateRandom
    from screens.rsp_screen import RSPScreen
except ImportError as e:
    print(f"Ошибка импорта экранов: {e}")
    # Создаем заглушки для критических случаев
    MainMenuScreen = None
    CoinScreen = None
    DiceScreen = None
    RouletteScreen = None
    RusRouletteScreen = None
    QuizScreen = None
    RandomScreen = None
    RandomNumberScreen = None
    MagicBallScreen = None
    IntermediateRoulette = None
    IntermediateRandom = None
    RSPScreen = None


def get_settings_path():
    """Возвращает правильный путь для settings.json в зависимости от платформы"""
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            files_dir = context.getFilesDir().getAbsolutePath()
            settings_path = os.path.join(files_dir, 'settings.json')
            print(f"🔍 [get_settings_path] Android путь: {settings_path}")
            return settings_path
        except Exception as e:
            print(f"⚠️ Ошибка получения пути на Android: {e}")
            return 'settings.json'
    else:
        return 'settings.json'


def load_mute_state():
    """Загружает состояние звука из файла"""
    settings_path = get_settings_path()

    # Проверяем также в текущей директории для отладки
    if os.path.exists('settings.json'):
        pass

    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                is_muted = settings.get('is_muted', False)
                print(f"📁 Загружено состояние звука при запуске: muted={is_muted}")
                return is_muted
        except Exception as e:
            print(f"⚠️ Ошибка загрузки настроек: {e}")
            return False
    else:
        print(f"⚠️ Файл настроек не найден по пути: {settings_path}")
        # Пытаемся создать файл
        try:
            default_settings = {"is_muted": False}
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=4)
            print(f"✅ Создан файл настроек: {settings_path}")
        except Exception as e:
            print(f"❌ Ошибка создания файла: {e}")
        return False


def save_mute_state(is_muted):
    """Сохраняет состояние звука в файл (используется другими модулями)"""
    settings_path = get_settings_path()
    settings = {}

    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except:
            pass

    settings['is_muted'] = is_muted

    try:
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        print(f"💾 Сохранено состояние звука: muted={is_muted} в {settings_path}")
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения: {e}")
        return False


class ScreenParams:
    """Класс для хранения параметров экрана и коэффициентов масштабирования"""

    def __init__(self):
        from kivy.core.window import Window
        from kivy.utils import platform

        # Получаем РЕАЛЬНЫЙ размер экрана в пикселях
        if platform == 'android':
            # На Android используем физические пиксели
            self.width, self.height = Window.system_size
        else:
            # На компьютере тоже используем system_size, если он есть
            if hasattr(Window, 'system_size') and Window.system_size[0] > 0:
                self.width, self.height = Window.system_size
            else:
                # Fallback для старых версий Kivy
                self.width, self.height = Window.width, Window.height

        self.aspect_ratio = self.width / self.height
        self.is_phone = platform == 'android'
        self.is_tablet = self.width > 600 if self.is_phone else False

        # Эталонные размеры (для масштабирования других элементов)
        self.base_width = 400
        self.base_height = 700

        # Коэффициенты масштабирования относительно эталонных размеров
        self.scale_x = self.width / self.base_width
        self.scale_y = self.height / self.base_height
        self.scale = min(self.scale_x, self.scale_y)

        print(f"[DEBUG] Screen params: {self.width}x{self.height}, scale={self.scale:.2f}")
        print(f"[DEBUG] Device: {'Phone' if self.is_phone else 'Computer'}")

    def get_size(self, width, height):
        """Возвращает размеры, масштабированные относительно экрана"""
        return (width * self.scale, height * self.scale)

    def get_x(self, x):
        """Возвращает координату X, масштабированную относительно экрана"""
        return x * self.scale_x

    def get_y(self, y):
        """Возвращает координату Y, масштабированную относительно экрана"""
        return y * self.scale_y

    def get_font_size(self, size):
        """Возвращает размер шрифта, масштабированный относительно экрана"""
        return size * self.scale


class UpdateManager:
    """Класс для обновления APK через Wi-Fi"""

    def __init__(self, app):
        self.app = app
        # ЗАМЕНИТЕ НА IP ВАШЕГО КОМПЬЮТЕРА
        self.server_url = "http://192.168.0.50:8000"
        self.current_version = "1.0.0"

    def check_for_updates(self, show_notification=True):
        """Проверка наличия новой версии APK на сервере"""

        def check():
            try:
                version_url = f"{self.server_url}/version.json"
                response = requests.get(version_url, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    server_version = data.get("version")
                    apk_url = data.get("url")

                    if server_version and server_version != self.current_version:
                        Clock.schedule_once(
                            lambda dt: self.show_update_dialog(server_version, apk_url)
                        )
                    elif show_notification:
                        Clock.schedule_once(
                            lambda dt: self.show_message("Нет обновлений", "У вас последняя версия")
                        )
                else:
                    print("Сервер обновлений не отвечает")

            except Exception as e:
                print(f"Ошибка проверки обновлений: {e}")

        thread = threading.Thread(target=check)
        thread.daemon = True
        thread.start()

    def show_update_dialog(self, new_version, apk_url):
        """Диалог предложения обновления"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=f"Доступна новая версия {new_version}\n\nХотите обновить?"))

        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        update_btn = Button(text="Обновить")
        later_btn = Button(text="Позже")

        btn_layout.add_widget(update_btn)
        btn_layout.add_widget(later_btn)
        content.add_widget(btn_layout)

        popup = Popup(title="Обновление", content=content, size_hint=(0.8, 0.4))

        def update(instance):
            popup.dismiss()
            self.download_and_install(apk_url)

        def later(instance):
            popup.dismiss()

        update_btn.bind(on_press=update)
        later_btn.bind(on_press=later)

        popup.open()

    def download_and_install(self, apk_url):
        """Скачивание и установка нового APK"""
        from kivy.uix.progressbar import ProgressBar

        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        pb = ProgressBar(max=100)
        label = Label(text="Скачивание обновления...")
        content.add_widget(label)
        content.add_widget(pb)

        popup = Popup(title="Обновление", content=content, size_hint=(0.8, 0.4))

        def download():
            try:
                response = requests.get(apk_url, stream=True)
                apk_path = f"/sdcard/Download/almightyrandom_new.apk"

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(apk_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                Clock.schedule_once(
                                    lambda dt, p=progress: setattr(pb, 'value', p)
                                )

                Clock.schedule_once(
                    lambda dt: self.install_apk(apk_path, popup)
                )

            except Exception as e:
                Clock.schedule_once(
                    lambda dt: self.show_message("Ошибка", f"Не удалось скачать:\n{str(e)}")
                )
                popup.dismiss()

        popup.open()
        threading.Thread(target=download).start()

    def install_apk(self, apk_path, popup):
        """Запуск установщика APK"""
        popup.dismiss()

        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                File = autoclass('java.io.File')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(
                    Uri.fromFile(File(apk_path)),
                    "application/vnd.android.package-archive"
                )
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                PythonActivity.mActivity.startActivity(intent)
                self.show_message("Готово", "Запуск установщика...")

            except Exception as e:
                self.show_message("Ошибка", f"Не удалось запустить установку:\n{str(e)}")
        else:
            self.show_message("Установка", "На ПК установка не поддерживается")

    def show_message(self, title, message):
        """Простое сообщение"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message))

        btn = Button(text="OK", size_hint_y=0.3)
        content.add_widget(btn)

        popup = Popup(title=title, content=content, size_hint=(0.7, 0.3))
        btn.bind(on_press=popup.dismiss)
        popup.open()


class SportsGameApp(App):
    def build(self):
        print("🚀 [App] Запуск приложения")

        # Настройка окна
        if platform == 'android':
            Window.fullscreen = 'auto'
        else:
            Window.size = (400, 700)

        Window.clearcolor = (0.1, 0.1, 0.1, 1)

        # --- СОЗДАЁМ ОБЪЕКТ С ПАРАМЕТРАМИ ЭКРАНА ---
        self.screen_params = ScreenParams()

        # Инициализация менеджеров
        print("🔧 [App] Инициализация менеджеров")
        self.lang = LanguageManager()
        self.sound_mgr = SoundManager()
        self.update_mgr = UpdateManager(self)

        # Загружаем сохраненное состояние звука
        if load_mute_state():
            self.sound_mgr.mute()
            print(f"🔇 [App] Применено сохраненное состояние: звук ВЫКЛЮЧЕН")
        else:
            print(f"🔊 [App] Применено сохраненное состояние: звук ВКЛЮЧЕН")

        # Звук (используем правильные пути)
        try:
            sound_path = "assets/sounds/background.wav"
            if os.path.exists(sound_path):
                self.sound_mgr.initialize(sound_path)
                print(f"✅ [App] Звук загружен из: {sound_path}")
            else:
                print(f"❌ [App] Файл звука не найден: {sound_path}")
        except Exception as e:
            print(f"❌ [App] Ошибка инициализации звука: {e}")

        # ========== НОВЫЙ КОД: ХРАНИМ КЛАССЫ ЭКРАНОВ ==========
        self.screen_classes = {
            'menu': MainMenuScreen,
            'magic_ball': MagicBallScreen,
            'coin': CoinScreen,
            'dice': DiceScreen,
            'roulette': RouletteScreen,
            'rus_roulette': RusRouletteScreen,
            'random': RandomScreen,
            'quiz': QuizScreen,
            'random_number': RandomNumberScreen,
            'rsp': RSPScreen,
            'intermediate_roulette': IntermediateRoulette,
            'intermediate_random': IntermediateRandom
        }

        # Создаем ScreenManager с анимацией
        self.sm = ScreenManager(transition=FadeTransition(duration=0.4))

        # Создаем ТОЛЬКО меню при старте (остальные будем создавать при переходе)
        if MainMenuScreen is not None:
            menu = MainMenuScreen(name='menu', screen_params=self.screen_params)
            self.sm.add_widget(menu)
            print("✅ [App] Создано меню")
        else:
            print("❌ [App] Ошибка: MainMenuScreen не загружен")

        # =====================================================

        # Запуск музыки
        def start_music(dt):
            if not self.sound_mgr.is_muted():
                self.sound_mgr.play()
            else:
                print("🔇 [App] Фоновая музыка не запущена - звук выключен")

        Clock.schedule_once(start_music, 0.5)

        # Проверка обновлений через 5 секунд после запуска
        Clock.schedule_once(lambda dt: self.update_mgr.check_for_updates(False), 5)

        print("✅ [App] Приложение запущено")
        return self.sm

    def switch_to_screen(self, screen_name, **kwargs):
        """
        Переключает на экран, удаляя старый и создавая новый.
        Это гарантирует, что FadeTransition будет работать при КАЖДОМ входе.
        """
        print(f"🔄 [App] Переключение на {screen_name}")

        # Проверяем, есть ли уже такой экран
        if self.sm.has_screen(screen_name):
            old_screen = self.sm.get_screen(screen_name)
            self.sm.remove_widget(old_screen)
            print(f"   Удален старый экран {screen_name}")

        # Создаем новый экран
        screen_class = self.screen_classes.get(screen_name)
        if screen_class is None:
            print(f"❌ Ошибка: экран {screen_name} не найден в screen_classes")
            return

        try:
            new_screen = screen_class(name=screen_name, screen_params=self.screen_params, **kwargs)
            self.sm.add_widget(new_screen)
            print(f"   Создан новый экран {screen_name}")
        except Exception as e:
            print(f"❌ Ошибка создания экрана {screen_name}: {e}")
            return

        # Переключаемся
        self.sm.current = screen_name
        print(f"✅ Переключено на {screen_name}")

    def go_to_menu(self):
        """Возврат в меню с пересозданием"""
        self.switch_to_screen('menu')

    def on_pause(self):
        print("📱 [App] on_pause - приложение свернуто")
        if hasattr(self, 'sound_mgr'):
            print("🔊 [App] Пауза звука при сворачивании")
            self.sound_mgr.pause()
        return True

    def on_resume(self):
        print("📱 [App] on_resume - приложение восстановлено")
        if hasattr(self, 'sound_mgr'):
            # Проверяем, не выключен ли звук
            if not self.sound_mgr.is_muted():
                print("🔊 [App] Возобновление звука при восстановлении")
                self.sound_mgr.play()
            else:
                print("🔇 [App] Звук выключен, не восстанавливаем при восстановлении")
        if hasattr(self, 'update_mgr'):
            Clock.schedule_once(lambda dt: self.update_mgr.check_for_updates(False), 2)

    def _(self, key):
        return self.lang._(key)


# Глобальная функция для удобного переключения экранов из любого места
def switch_screen(screen_name, **kwargs):
    """Глобальная функция для переключения экранов"""
    app = App.get_running_app()
    if hasattr(app, 'switch_to_screen'):
        app.switch_to_screen(screen_name, **kwargs)
    else:
        # Fallback на старый метод
        app.sm.current = screen_name


if __name__ == '__main__':
    print("🎮 Запуск SportsGameApp...")
    SportsGameApp().run()
    print("👋 Приложение завершено")
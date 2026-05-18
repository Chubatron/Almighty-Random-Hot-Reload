from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from components.control_button import ControlButton
from sound_manager import SoundManager
from multilanguage_widgets import MLTextMixin
from kivy.clock import Clock
from kivy.utils import platform
import json
import os


def get_settings_path():
    """Возвращает правильный путь для settings.json в зависимости от платформы"""
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            files_dir = context.getFilesDir().getAbsolutePath()
            return os.path.join(files_dir, 'settings.json')
        except Exception as e:
            return 'settings.json'
    else:
        return 'settings.json'


def save_mute_state(is_muted):
    """Сохраняет состояние звука в файл"""
    settings_path = get_settings_path()
    settings = {}

    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except:
            pass

    settings['is_muted'] = is_muted

    if 'language' not in settings:
        settings['language'] = {'code': 'ru'}

    try:
        settings_dir = os.path.dirname(settings_path)
        if settings_dir:
            os.makedirs(settings_dir, exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        pass


def load_mute_state():
    """Загружает состояние звука из файла"""
    settings_path = get_settings_path()

    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get('is_muted', False)
        except Exception as e:
            return False
    else:
        try:
            default_settings = {"is_muted": False, "language": {"code": "ru"}}
            settings_dir = os.path.dirname(settings_path)
            if settings_dir:
                os.makedirs(settings_dir, exist_ok=True)
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=4)
        except Exception as e:
            pass
        return False


class ControlPanel(FloatLayout):
    """Панель служебных кнопок внизу экрана"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 0.15)
        self.pos_hint = {'x': 0, 'y': 0}

        self.buttons = []
        self.buttons_data = None

        Clock.schedule_once(lambda dt: self.create_buttons(), 0.1)

    def create_buttons(self, *args):
        sound_mgr = SoundManager()
        is_sound_on = not (sound_mgr.is_muted() or sound_mgr.get_volume() == 0)

        self.buttons_data = [
            {
                'text_key': 'sound_on' if is_sound_on else 'sound_off',
                'text': 'SOUND ON' if is_sound_on else 'SOUND OFF',
                'callback': self.toggle_sound,
                'icon_path': 'assets/images/buttons/White_sound_on_button.png' if is_sound_on else 'assets/images/buttons/white_sound_off_button.png',
                'background_color': (0.2, 0.8, 0.2, 1) if is_sound_on else (0.5, 0.5, 0.5, 1)
            },
            {
                'text_key': 'language',
                'text': 'LANGUAGE',
                'callback': self.open_language,
                'icon_path': 'assets/images/buttons/White_lang_button.png',
                'background_color': (0.3, 0.5, 0.8, 1)
            },
            {
                'text_key': 'share',
                'text': 'SHARE',
                'callback': self.share_game,
                'icon_path': 'assets/images/buttons/White_share_button.png',
                'background_color': (0.1, 0.6, 0.9, 1)
            },
            {
                'text_key': 'rate',
                'text': 'RATE',
                'callback': self.rate_game,
                'icon_path': 'assets/images/buttons/White_rate_button.png',
                'background_color': (1, 0.8, 0.1, 1)
            },
            {
                'text_key': 'exit',
                'text': 'EXIT',
                'callback': self.exit_game,
                'icon_path': 'assets/images/buttons/white_exit_button.png',
                'background_color': (0.8, 0.1, 0.1, 1)
            },
        ]

        self.clear_widgets()
        self.buttons.clear()
        self.create_buttons_uniform()

    def create_buttons_uniform(self):
        num_buttons = len(self.buttons_data)
        available_width = 0.9
        spacing = 0.01
        total_spacing = spacing * (num_buttons - 1)
        button_width = (available_width - total_spacing) / num_buttons
        start_x = 0.05

        for i, btn_data in enumerate(self.buttons_data):
            x_pos = start_x + i * (button_width + spacing)

            btn = LanguageControlButton(
                text_key=btn_data.get('text_key', ''),
                fallback_text=btn_data['text'],
                icon_path=btn_data['icon_path'],
                background_color=btn_data['background_color'],
                size_hint=(button_width, 0.8),
                pos_hint={'x': x_pos, 'y': 0.1},
                callback=btn_data['callback']
            )
            self.add_widget(btn)
            self.buttons.append(btn)

    def on_size(self, *args):
        if self.buttons_data:
            Clock.schedule_once(lambda dt: self.reposition_buttons(), 0)

    def reposition_buttons(self):
        if not self.buttons:
            return

        num_buttons = len(self.buttons)
        available_width = 0.9
        spacing = 0.01
        total_spacing = spacing * (num_buttons - 1)
        button_width = (available_width - total_spacing) / num_buttons
        start_x = 0.05

        for i, btn in enumerate(self.buttons):
            x_pos = start_x + i * (button_width + spacing)
            btn.size_hint = (button_width, 0.8)
            btn.pos_hint = {'x': x_pos, 'y': 0.1}

    def toggle_sound(self, instance):
        """Переключение звука и вибрации"""
        sound_mgr = SoundManager()

        if sound_mgr.is_muted():
            # Включаем звук и вибрацию
            sound_mgr.unmute()
            save_mute_state(False)
            self.update_sound_button(instance, True)
            print("🔊 [ControlPanel] Звук и вибрация ВКЛЮЧЕНЫ")
        else:
            # Выключаем звук и вибрацию
            sound_mgr.mute()
            save_mute_state(True)
            self.update_sound_button(instance, False)
            print("🔇 [ControlPanel] Звук и вибрация ВЫКЛЮЧЕНЫ")

    def update_sound_button(self, instance, sound_on):
        """Обновляет внешний вид кнопки звука"""
        if sound_on:
            instance.text_key = 'sound_on'
            instance.fallback_text = 'SOUND ON'
            instance.background_color = (0.2, 0.8, 0.2, 1)
            instance.update_icon('assets/images/buttons/White_sound_on_button.png')
        else:
            instance.text_key = 'sound_off'
            instance.fallback_text = 'SOUND OFF'
            instance.background_color = (0.5, 0.5, 0.5, 1)
            instance.update_icon('assets/images/buttons/white_sound_off_button.png')

        instance.update_text()

    def open_language(self, instance):
        app = App.get_running_app()
        if 'language' not in app.sm.screen_names:
            from screens.language_screen import LanguageScreen
            app.sm.add_widget(LanguageScreen(name='language'))
        app.sm.current = 'language'

    def share_game(self, instance):
        pass

    def rate_game(self, instance):
        pass

    def exit_game(self, instance):
        App.get_running_app().stop()


class LanguageControlButton(ControlButton, MLTextMixin):
    """Кнопка управления с поддержкой языков"""

    def __init__(self, text_key='', fallback_text='', **kwargs):
        self.fallback_text = fallback_text

        if text_key:
            kwargs['text_key'] = text_key

        super().__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.update_text(), 0)

    def update_text(self, *args):
        app = App.get_running_app()
        if self.text_key and app and hasattr(app, '_'):
            new_text = app._(self.text_key)
            if self.text != new_text:
                self.text = new_text
        else:
            self.text = self.fallback_text
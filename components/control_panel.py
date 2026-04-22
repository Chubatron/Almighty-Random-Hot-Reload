from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from components.control_button import ControlButton
from sound_manager import SoundManager
from multilanguage_widgets import MLTextMixin
from kivy.clock import Clock


class ControlPanel(FloatLayout):
    """Панель служебных кнопок внизу экрана"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 0.15)
        self.pos_hint = {'x': 0, 'y': 0}

        self.buttons = []
        self.buttons_data = None  # Сохраняем данные кнопок для обновления

        # Создаем кнопки с небольшой задержкой, чтобы приложение полностью инициализировалось
        Clock.schedule_once(lambda dt: self.create_buttons(), 0.1)

    def create_buttons(self, *args):
        """Создает кнопки на панели управления"""
        print("🎮 Создаем кнопки панели управления")

        # Проверяем начальное состояние звука
        sound_mgr = SoundManager()
        is_sound_on = not (sound_mgr.is_muted() or sound_mgr.get_volume() == 0)

        self.buttons_data = [
            {
                'text_key': 'sound_on' if is_sound_on else 'sound_off',
                'text': 'SOUND ON' if is_sound_on else 'SOUND OFF',
                'callback': self.toggle_sound,
                'icon_path': 'assets/images/buttons/White_sound_on_button.png' if is_sound_on else 'assets/images/buttons/White_sound_off_button.png',
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
                'icon_path': 'assets/images/buttons/White_exit_button.png',
                'background_color': (0.8, 0.1, 0.1, 1)
            },
        ]

        # Очищаем предыдущие кнопки если есть
        self.clear_widgets()
        self.buttons.clear()

        # Создаем кнопки с равномерным распределением
        self.create_buttons_uniform()

    def create_buttons_uniform(self):
        """Создает кнопки равномерно распределенными по ширине"""
        num_buttons = len(self.buttons_data)

        # Рассчитываем ширину каждой кнопки и отступы
        # Используем 90% ширины для кнопок, 10% для отступов по краям
        available_width = 0.9  # 90% ширины для всех кнопок
        spacing = 0.01  # Отступ между кнопками (1%)
        total_spacing = spacing * (num_buttons - 1)  # Общая ширина отступов
        button_width = (available_width - total_spacing) / num_buttons

        # Начальная позиция (5% от левого края)
        start_x = 0.05

        # Создаем кнопки
        for i, btn_data in enumerate(self.buttons_data):
            x_pos = start_x + i * (button_width + spacing)

            btn = LanguageControlButton(
                text_key=btn_data.get('text_key', ''),
                fallback_text=btn_data['text'],
                icon_path=btn_data['icon_path'],
                background_color=btn_data['background_color'],
                size_hint=(button_width, 0.8),  # 80% высоты панели
                pos_hint={'x': x_pos, 'y': 0.1},  # 10% от нижнего края
                callback=btn_data['callback']
            )
            self.add_widget(btn)
            self.buttons.append(btn)

    def on_size(self, *args):
        """При изменении размера панели пересоздаем кнопки для точного позиционирования"""
        if self.buttons_data:
            Clock.schedule_once(lambda dt: self.reposition_buttons(), 0)

    def reposition_buttons(self):
        """Перепозиционирует кнопки при изменении размера"""
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

    def create_single_button(self, index, btn_data):
        """Создает одну кнопку (устаревший метод, оставлен для совместимости)"""
        num_buttons = 5
        available_width = 0.9
        spacing = 0.01
        total_spacing = spacing * (num_buttons - 1)
        button_width = (available_width - total_spacing) / num_buttons
        start_x = 0.05

        x_pos = start_x + index * (button_width + spacing)

        btn = LanguageControlButton(
            text_key=btn_data.get('text_key', ''),
            fallback_text=btn_data['text'],
            icon_path=btn_data['icon_path'],
            background_color=btn_data['background_color'],
            size_hint=(button_width, 0.8),
            pos_hint={'x': x_pos, 'y': 0.1},
            callback=btn_data['callback']
        )
        return btn

    def toggle_sound(self, instance):
        sound_mgr = SoundManager()
        if sound_mgr.is_muted() or sound_mgr.get_volume() == 0:
            sound_mgr.unmute()
            self.update_sound_button(instance, True)
        else:
            sound_mgr.mute()
            self.update_sound_button(instance, False)

    def update_sound_button(self, instance, sound_on):
        if sound_on:
            instance.text_key = 'sound_on'
            instance.fallback_text = 'SOUND ON'
            instance.background_color = (0.2, 0.8, 0.2, 1)
            instance.update_icon('assets/images/buttons/White_sound_on_button.png')
        else:
            instance.text_key = 'sound_off'
            instance.fallback_text = 'SOUND OFF'
            instance.background_color = (0.5, 0.5, 0.5, 1)
            instance.update_icon('assets/images/buttons/White_sound_off_button.png')

        instance.update_text()

    def open_language(self, instance):
        app = App.get_running_app()
        if 'language' not in app.sm.screen_names:
            from screens.language_screen import LanguageScreen
            app.sm.add_widget(LanguageScreen(name='language'))
        app.sm.current = 'language'

    def share_game(self, instance):
        print("Share")

    def rate_game(self, instance):
        print("Rate")

    def exit_game(self, instance):
        App.get_running_app().stop()


class LanguageControlButton(ControlButton, MLTextMixin):
    """Кнопка управления с поддержкой языков"""

    def __init__(self, text_key='', fallback_text='', **kwargs):
        self.fallback_text = fallback_text

        if text_key:
            kwargs['text_key'] = text_key
            print(f"🔘 Создана кнопка с ключом: {text_key}")

        super().__init__(**kwargs)

        # Устанавливаем начальный текст
        Clock.schedule_once(lambda dt: self.update_text(), 0)

    def update_text(self, *args):
        """Обновляет текст при смене языка"""
        app = App.get_running_app()
        if self.text_key and app and hasattr(app, '_'):
            new_text = app._(self.text_key)
            if self.text != new_text:
                print(f"🔄 Кнопка '{self.text_key}': '{self.text}' -> '{new_text}'")
                self.text = new_text
        else:
            self.text = self.fallback_text
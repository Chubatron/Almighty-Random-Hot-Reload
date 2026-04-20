# screens/intermediate_roulette.py
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from animated_background import AnimatedBackground
from components.icon_button import IconButton
from screens.intermediate_base_screen import IntermediateScreen
import os


class IntermediateRoulette(IntermediateScreen):
    """Промежуточный экран для выбора типа рулетки"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Передаём screen_params через kwargs

        # Анимированный фон
        self.background = AnimatedBackground()
        self.layout.add_widget(self.background)

        # Статический фон
        bg = Image(
            source='assets/backgrounds/indigo_bg.png',
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1),
            fit_mode='fill',
            opacity=0.7
        )
        self.layout.add_widget(bg)

        # Заголовок
        title = Label(
            text='SELECT ROULETTE TYPE',
            font_name='assets/fonts/JockeyOne-Regular.ttf',
            font_size='32sp',
            bold=True,
            color=(1, 1, 1, 1),
            outline_color=(0, 0, 0, 1),
            outline_width=2,
            size_hint=(None, None),
            size=(500, 50),
            pos_hint={'center_x': 0.5, 'top': 0.95}
        )
        self.layout.add_widget(title)

        # Создаем кнопки выбора рулетки
        self.create_buttons()

        # НЕ создаём отдельную кнопку назад - она создаётся в родительском классе
        # НЕ загружаем звук - он уже загружен в родительском классе

    def create_buttons(self):
        """Создает кнопки выбора типа рулетки"""
        sports = [
            ('Classic Roulette', 'assets/images/buttons/Blue_roulette_button.png', 'roulette', self.change_to_game),
            ('Russian Roulette', 'assets/images/buttons/Red_rus_roulette_button.png', 'rus_roulette', self.change_to_game),
        ]

        button_width, button_height = 0.3, 0.2
        start_x = 0.35
        start_y = 0.6
        vertical_spacing = 0.05

        for i, (text, icon_path, screen_name, callback) in enumerate(sports):
            y_pos = start_y - i * (button_height + vertical_spacing)

            btn = IconButton(
                text=text,
                icon_path=icon_path,
                sport=screen_name,
                size_hint=(button_width, button_height),
                pos_hint={'x': start_x, 'y': y_pos},
                callback=callback
            )
            self.layout.add_widget(btn)

    def change_to_game(self, instance):
        """Переход к игровому экрану"""
        print(f"🎲 Переход на {instance.sport}")
        if hasattr(self.manager.get_screen(instance.sport), 'start_game'):
            self.manager.get_screen(instance.sport).start_game()
        self.manager.current = instance.sport

    # Метод go_to_menu удалён - используется родительский
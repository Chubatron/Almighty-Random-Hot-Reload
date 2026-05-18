from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
import os


class IconButton(ButtonBehavior, FloatLayout):
    """Кнопка с иконкой и текстом"""

    def __init__(self, text, icon_path, sport, callback, sound_manager=None, **kwargs):
        super().__init__(**kwargs)

        self.sport = sport
        self.callback = callback
        self.sound_manager = sound_manager
        self.click_sound = None

        # Загружаем звук нажатия
        self._load_click_sound()

        # Устанавливаем фон кнопки
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.2, 0.2, 0.2, 0.0)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10, ])

        # Обновляем фон при изменении размера/позиции
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Иконка
        self.icon = Image(
            source=icon_path if icon_path else '',
            size_hint=(0.85, 0.85),
            pos_hint={'center_x': 0.5, 'center_y': 0.65},
            allow_stretch=True
        )

        # Текст
        self.label = Label(
            text=text,
            font_size='12sp',
            color=(1, 1, 1, 1),
            size_hint=(1, 0.3),
            pos_hint={'center_x': 0.5, 'y': 0}
        )

        self.add_widget(self.icon)
        self.add_widget(self.label)

    def _load_click_sound(self):
        """Загружает звук нажатия кнопки"""
        sound_path = 'assets/sounds/Schpun.ogg'
        if os.path.exists(sound_path):
            self.click_sound = SoundLoader.load(sound_path)
            if self.click_sound:
                self.click_sound.volume = 0.6

    def _play_click_sound(self):
        """Воспроизводит звук нажатия кнопки (только если звук не выключен)"""
        # Проверяем, не выключен ли звук глобально
        if self.sound_manager and self.sound_manager.is_muted():
            print(f"🔇 [IconButton] Звук нажатия пропущен - звук выключен")
            return

        if self.click_sound:
            try:
                if self.click_sound.state == 'play':
                    self.click_sound.stop()
                self.click_sound.play()
                print(f"🔊 [IconButton] Воспроизведение звука нажатия")
            except Exception as e:
                pass

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press(self):
        """Анимация и звук при нажатии"""
        # Воспроизводим звук
        self._play_click_sound()

        # Анимация нажатия
        self.canvas.before.clear()
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.3, 0.3, 0.3, 0.1)  # Более темный цвет
            RoundedRectangle(size=self.size, pos=self.pos, radius=[10, ])

    def on_release(self):
        """Возвращаем обычный цвет и вызываем callback"""
        self.canvas.before.clear()
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.2, 0.2, 0.2, 0.0)
            RoundedRectangle(size=self.size, pos=self.pos, radius=[10, ])

        # Вызываем callback после отпускания
        if self.callback:
            self.callback(self)
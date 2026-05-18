from kivy.uix.button import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.core.audio import SoundLoader
from kivy.properties import StringProperty, ListProperty, NumericProperty
from sound_manager import SoundManager
import os


class ControlButton(ButtonBehavior, FloatLayout):
    """Кнопка для панели управления"""
    text = StringProperty('')
    icon_path = StringProperty('')
    background_color = ListProperty([1, 1, 1, 1])
    icon_scale = NumericProperty(0.7)  # Относительный размер иконки (0-1)
    icon_size = ListProperty([0, 0])  # Абсолютный размер иконки [ширина, высота]

    def __init__(self, callback=None, icon_scale=None, icon_size=None, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.click_sound = None
        self.load_click_sound()

        # Устанавливаем размер иконки если передан
        if icon_scale is not None:
            self.icon_scale = icon_scale
        if icon_size is not None:
            self.icon_size = icon_size

        # Иконка
        if self.icon_path:
            self.icon = Image(
                source=self.icon_path,
                size_hint=(None, None),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                allow_stretch=True,
                keep_ratio=True
            )
            self.add_widget(self.icon)
            self.setup_icon()

    def load_click_sound(self):
        """Загружает звук нажатия кнопки"""
        sound_path = 'assets/sounds/Schpun.ogg'
        if os.path.exists(sound_path):
            self.click_sound = SoundLoader.load(sound_path)
            if self.click_sound:
                self.click_sound.volume = 0.6

    def play_click_sound(self):
        """Воспроизводит звук нажатия кнопки"""
        if self.click_sound and not SoundManager().is_muted():
            try:
                if self.click_sound.state == 'play':
                    self.click_sound.stop()
                self.click_sound.play()
            except:
                pass

    def on_press(self):
        """При нажатии на кнопку воспроизводим звук"""
        self.play_click_sound()
        if self.callback:
            self.callback(self)

    def setup_icon(self):
        """Настройка иконки кнопки с учетом размера"""
        if self.icon_path and hasattr(self, 'icon'):
            # Очищаем предыдущую иконку
            if self.icon in self.children:
                self.remove_widget(self.icon)

            # Определяем размер иконки
            if self.icon_size and self.icon_size[0] > 0 and self.icon_size[1] > 0:
                # Используем абсолютный размер
                icon_size = self.icon_size
            else:
                # Используем относительный размер
                icon_size = (self.height * self.icon_scale, self.height * self.icon_scale)

            # Создаем новую иконку
            self.icon = Image(
                source=self.icon_path,
                size_hint=(None, None),
                size=icon_size,
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                allow_stretch=True,
                keep_ratio=True
            )
            self.add_widget(self.icon)

    def update_icon(self, new_icon_path, icon_size=None):
        """Обновляет иконку кнопки"""
        self.icon_path = new_icon_path
        if icon_size:
            self.icon_size = icon_size
        self.setup_icon()

    def on_size(self, instance, value):
        """Обновляем размер иконки при изменении размера кнопки"""
        if hasattr(self, 'icon'):
            self.setup_icon()
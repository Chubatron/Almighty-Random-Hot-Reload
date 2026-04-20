from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.core.window import Window
from sound_manager import SoundManager
import os


class IntermediateScreen(Screen):
    """Базовый класс для промежуточных экранов (меню выбора)"""

    def __init__(self, **kwargs):
        # Извлекаем screen_params
        self.screen_params = kwargs.pop('screen_params', None)
        super().__init__(**kwargs)

        self.layout = FloatLayout()
        self.sound_manager = SoundManager()

        # Кнопка назад (будет создана позже, после получения размеров экрана)
        self.back_button = None
        self.back_sound = None

        # Загружаем звук для кнопки
        self.load_back_sound()

        self.add_widget(self.layout)

    def load_back_sound(self):
        """Загружает звук для кнопки назад"""
        sound_path = 'assets/sounds/Schpun.ogg'
        if os.path.exists(sound_path):
            self.back_sound = SoundLoader.load(sound_path)
            if self.back_sound:
                self.back_sound.volume = 0.8
                print(f"✅ Loaded back button sound: {sound_path}")
        else:
            print(f"⚠️ Back button sound file not found: {sound_path}")

    def play_back_sound(self):
        """Воспроизводит звук при нажатии на кнопку назад"""
        if hasattr(self, 'back_sound') and self.back_sound:
            try:
                self.back_sound.play()
                print("🔊 Playing back button sound")
            except:
                pass

    def on_enter(self):
        """При входе на промежуточный экран - возвращаем громкость и создаём кнопку"""
        self.sound_manager.fade_to(1.0, duration=0.5)
        # Создаём кнопку после получения размеров экрана
        Clock.schedule_once(lambda dt: self.create_back_button(), 0.05)

    def on_leave(self):
        """При выходе с промежуточного экрана"""
        pass

    def create_back_button(self):
        """Создает единую кнопку возврата в меню для всех промежуточных экранов"""
        # Удаляем старую кнопку если есть
        if self.back_button and self.back_button in self.layout.children:
            self.layout.remove_widget(self.back_button)

        class ImageButton(ButtonBehavior, Image):
            pass

        # Получаем реальные размеры экрана
        if platform == 'android':
            real_width = Window.system_size[0]
            real_height = Window.system_size[1]
            print(f"[DEBUG] IntermediateScreen Android real size: {real_width}x{real_height}")
        else:
            if self.screen_params and self.screen_params.width > 0:
                real_width = self.screen_params.width
                real_height = self.screen_params.height
            else:
                real_width = Window.width
                real_height = Window.height
            print(f"[DEBUG] IntermediateScreen Computer size: {real_width}x{real_height}")

        # Размер кнопки = 10% от реальной ширины экрана
        btn_size = real_width * 0.1
        # Позиция: левый нижний угол с отступом 5% (как в игровых экранах)
        btn_x = real_width * 0.1   # ← измените этот коэффициент для сдвига по горизонтали
        btn_y = real_height * 0.05  # ← измените этот коэффициент для сдвига по вертикали

        print(f"[DEBUG] IntermediateScreen back button: size={btn_size}, pos=({btn_x}, {btn_y})")

        back_btn = ImageButton(
            source='assets/images/buttons/Orange_back_to_menu_button.png',
            size_hint=(None, None),
            size=(btn_size, btn_size),
            pos=(btn_x, btn_y),
            allow_stretch=True
        )

        def on_press(instance):
            Animation(opacity=0.7, duration=0.1).start(instance)

        def on_release(instance):
            Animation(opacity=1.0, duration=0.1).start(instance)
            self.play_back_sound()
            Clock.schedule_once(lambda dt: self.go_to_menu(), 0.1)

        back_btn.bind(on_press=on_press)
        back_btn.bind(on_release=on_release)

        self.back_button = back_btn
        self.layout.add_widget(back_btn)
        print(f"[DEBUG] IntermediateScreen button added at pos={back_btn.pos}, size={back_btn.size}")

    def go_to_menu(self, instance=None):
        """Возврат в главное меню"""
        self.manager.current = 'menu'

    def go_to_game(self, game_name):
        """Переход к игре - будет убавлять громкость при входе в игру"""
        self.manager.current = game_name
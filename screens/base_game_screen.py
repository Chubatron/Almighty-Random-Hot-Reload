from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image as KivyImage
from kivy.graphics import Rotate, PushMatrix, PopMatrix
from sound_manager import SoundManager
import os


class BaseGameScreen(Screen):
    """Базовый класс ТОЛЬКО с музыкой и кнопкой назад"""

    background_image = StringProperty('')
    sound_file = StringProperty('')

    # Флаг для определения, является ли экран игровым (нужно для регулировки громкости)
    is_game_screen = True

    def __init__(self, **kwargs):
        # Извлекаем screen_params перед вызовом super()
        self.screen_params = kwargs.pop('screen_params', None)
        super().__init__(**kwargs)

        self.layout = FloatLayout()

        # Музыка/звук
        self.sound = None

        # Звук для кнопки назад
        self.back_sound = None

        # Фон
        self.bg_image = None

        # Кнопка назад
        self.back_button = None

        # Ссылка на глобальный SoundManager
        self.sound_manager = SoundManager()

        self.add_widget(self.layout)
        self.bind(size=self._on_size_change)

        # Загружаем звук для кнопки назад
        self.load_back_sound()

    def load_back_sound(self):
        """Загружает звук для кнопки назад"""
        from kivy.core.audio import SoundLoader

        sound_path = 'assets/sounds/Schpun.ogg'

        if os.path.exists(sound_path):
            self.back_sound = SoundLoader.load(sound_path)
            if self.back_sound:
                self.back_sound.volume = 0.8
                print(f"✅ Loaded back button sound: {sound_path}")
            else:
                print(f"⚠️ Failed to load back button sound: {sound_path}")
        else:
            print(f"⚠️ Back button sound file not found: {sound_path}")

    def play_back_sound(self):
        """Воспроизводит звук при нажатии на кнопку назад"""
        if self.back_sound:
            try:
                self.back_sound.play()
                print("🔊 Playing back button sound")
            except:
                pass

    def _on_size_change(self, instance, value):
        """Обновление позиций при изменении размера"""
        # Обновляем позицию кнопки при изменении размера экрана
        if self.back_button:
            Clock.schedule_once(lambda dt: self._update_button_position(), 0.05)

    def _update_button_position(self):
        """Обновляет позицию кнопки при изменении размера экрана"""
        if self.back_button:
            # Получаем реальную ширину экрана
            from kivy.utils import platform
            from kivy.core.window import Window

            if platform == 'android':
                real_width = Window.system_size[0]
                real_height = Window.system_size[1]
            else:
                if self.screen_params:
                    real_width = self.screen_params.width
                    real_height = self.screen_params.height
                else:
                    real_width = Window.width
                    real_height = Window.height

            btn_size = real_width * 0.1  # 10% от реальной ширины
            btn_x = real_width * 0.1   # 5% от левого края
            btn_y = real_height * 0.05  # 5% от нижнего края

            self.back_button.size = (btn_size, btn_size)
            self.back_button.pos = (btn_x, btn_y)

    def on_enter(self):
        """При входе на экран"""
        self.setup_background()
        self.setup_sound()
        # Небольшая задержка перед созданием кнопки
        Clock.schedule_once(lambda dt: self.create_back_button(), 0.05)

        if self.is_game_screen:
            self.sound_manager.fade_to(0.05, duration=1.0)

    def on_leave(self):
        """При выходе с экрана"""
        self.stop_sound()

        if self.is_game_screen:
            self.sound_manager.fade_to(1.0, duration=1.0)

    def go_to_menu(self):
        """Возврат в меню (БЕЗ ЗВУКА - звук уже в кнопке)"""
        self.stop_sound()
        self.sound_manager.fade_to(1.0, duration=0.5)
        self.manager.current = 'menu'

    def setup_background(self):
        """Настраивает фон"""
        if self.bg_image:
            self.layout.remove_widget(self.bg_image)

        from kivy.uix.image import Image
        self.bg_image = Image(
            source=self.background_image,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1)
        )
        self.layout.add_widget(self.bg_image)

    def setup_sound(self):
        """Настройка музыки/звуков"""
        if self.sound_file:
            from kivy.core.audio import SoundLoader
            self.sound = SoundLoader.load(self.sound_file)
            if self.sound:
                self.sound.loop = True
                self.sound.volume = 0.5
                self.sound.play()

    def stop_sound(self):
        """Остановка музыки"""
        if self.sound:
            self.sound.stop()
            self.sound = None

    def create_back_button(self):
        """Создает единую кнопку возврата в меню для всех экранов"""
        # Удаляем старую кнопку если есть
        if self.back_button and self.back_button in self.layout.children:
            self.layout.remove_widget(self.back_button)

        self._create_unified_back_button()

    def _create_unified_back_button(self):
        """Создает единую кнопку возврата в меню для всех экранов"""

        class ImageButton(ButtonBehavior, KivyImage):
            pass

        # Получаем реальные размеры экрана
        from kivy.utils import platform
        from kivy.core.window import Window

        if platform == 'android':
            # На телефоне используем реальные пиксели
            real_width = Window.system_size[0]
            real_height = Window.system_size[1]
            print(f"[DEBUG] Android real size: {real_width}x{real_height}")
        else:
            # На компьютере используем screen_params или Window.size
            if self.screen_params and self.screen_params.width > 0:
                real_width = self.screen_params.width
                real_height = self.screen_params.height
            else:
                real_width = Window.width
                real_height = Window.height
            print(f"[DEBUG] Computer size: {real_width}x{real_height}")

        # Размер кнопки = 10% от реальной ширины экрана
        btn_size = real_width * 0.1
        # Позиция: левый нижний угол с отступом 5%
        btn_x = real_width * 0.1   # ← измените этот коэффициент для сдвига по горизонтали
        btn_y = real_height * 0.05  # ← измените этот коэффициент для сдвига по вертикали

        print(f"[DEBUG] Back button: size={btn_size}, pos=({btn_x}, {btn_y})")

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
            # ЗВУК ТОЛЬКО ЗДЕСЬ
            self.play_back_sound()
            Clock.schedule_once(lambda dt: self.go_to_menu(), 0.1)

        back_btn.bind(on_press=on_press)
        back_btn.bind(on_release=on_release)

        self.back_button = back_btn
        self.layout.add_widget(back_btn)
        print(f"[DEBUG] Button added at pos={back_btn.pos}, size={back_btn.size}")

    def on_touch_down(self, touch):
        """Обработка касаний на всех экранах"""
        # Проверяем нажатие на кнопку назад
        if hasattr(self, 'back_button') and self.back_button:
            if self.back_button.collide_point(touch.x, touch.y):
                print("[DEBUG] Back button pressed")
                # Эмулируем нажатие на кнопку
                self.back_button.on_touch_down(touch)
                return True

        # Если кнопка не нажата, передаём обработку дальше
        return super().on_touch_down(touch)

    def start_game(self):
        """Метод для запуска игры (может быть переопределен в дочерних классах)"""
        pass
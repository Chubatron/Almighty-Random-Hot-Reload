from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.core.audio import SoundLoader
from sound_manager import SoundManager
import os


class ToggleButtonWithLabel(ButtonBehavior, FloatLayout):
    """Кнопка с изображением как фоном и текстом по центру"""

    def __init__(self, **kwargs):
        self._button_size = kwargs.pop('size', (250, 60))
        super().__init__(**kwargs)

        self.size_hint = (None, None)
        self.size = self._button_size

        self.bg_image = KivyImage(
            source='',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            allow_stretch=True,
            keep_ratio=False,
        )

        self.label = Label(
            text='',
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            halign='center',
            valign='middle'
        )
        self.label.bind(size=self.label.setter('text_size'))

        self.add_widget(self.bg_image)
        self.add_widget(self.label)

        # Загружаем звук для кнопки
        self.click_sound = None
        self.load_click_sound()

        Clock.schedule_once(lambda dt: self.update_font_size(), 0)

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

    def update_font_size(self):
        if hasattr(self, 'label') and self.label:
            font_size = self.height * 0.42
            self.label.font_size = font_size

    def on_size(self, *args):
        if hasattr(self, 'label') and self.label:
            self.update_font_size()

    @property
    def icon(self):
        return self.bg_image

    @icon.setter
    def icon(self, value):
        self.bg_image.source = value


class BaseGameScreen(Screen):
    """Базовый класс с музыкой и кнопкой назад (без собственного затемнения - использует FadeTransition)"""

    # КОЭФФИЦИЕНТЫ ДЛЯ КНОПКИ SWITCH
    SWITCH_BUTTON_WIDTH_COEFF = 0.55
    SWITCH_BUTTON_HEIGHT_COEFF = 0.08
    SWITCH_BUTTON_POS_Y_COEFF = 0.9

    background_image = StringProperty('')
    sound_file = StringProperty('')
    is_game_screen = True

    def __init__(self, **kwargs):
        self.screen_params = kwargs.pop('screen_params', None)
        super().__init__(**kwargs)

        self.layout = FloatLayout()
        self.layout.size_hint = (1, 1)

        self.sound = None
        self.back_sound = None
        self.bg_image = None
        self.back_button = None
        self.type_switch_button = None

        self.sound_manager = SoundManager()

        self.add_widget(self.layout)
        self.bind(size=self._on_size_change)

        self.load_back_sound()

    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С ПАРАМЕТРАМИ ЭКРАНА ====================

    def get_screen_width(self):
        from kivy.utils import platform
        from kivy.core.window import Window

        if platform == 'android':
            return Window.system_size[0]
        else:
            if self.screen_params and self.screen_params.width > 0:
                return self.screen_params.width
            return Window.width

    def get_screen_height(self):
        from kivy.utils import platform
        from kivy.core.window import Window

        if platform == 'android':
            return Window.system_size[1]
        else:
            if self.screen_params and self.screen_params.height > 0:
                return self.screen_params.height
            return Window.height

    def get_min_dimension(self):
        return min(self.get_screen_width(), self.get_screen_height())

    def get_relative_size(self, percent=1.0, use_min=True):
        base = self.get_min_dimension() if use_min else self.get_screen_width()
        return int(base * percent)

    def get_relative_size_tuple(self, percent_width=1.0, percent_height=1.0):
        return (int(self.get_screen_width() * percent_width),
                int(self.get_screen_height() * percent_height))

    def get_center(self):
        return (self.get_screen_width() / 2, self.get_screen_height() / 2)

    def get_screen_params_dict(self):
        width = self.get_screen_width()
        height = self.get_screen_height()
        return {
            'width': width,
            'height': height,
            'min_dimension': min(width, height),
            'center_x': width / 2,
            'center_y': height / 2
        }

    # ==================== МЕТОДЫ ДЛЯ КНОПКИ SWITCH ====================

    def create_switch_button(self, text="SWITCH", icon_path='assets/images/buttons/Roulette_switch_button.png',
                             callback=None, size=None, pos_hint=None):
        screen_width = self.get_screen_width()
        screen_height = self.get_screen_height()

        if size is None:
            button_width = screen_width * self.SWITCH_BUTTON_WIDTH_COEFF
            button_height = screen_height * self.SWITCH_BUTTON_HEIGHT_COEFF
            size = (button_width, button_height)

        if pos_hint is None:
            pos_hint = {'center_x': 0.5, 'center_y': self.SWITCH_BUTTON_POS_Y_COEFF}

        self.type_switch_button = ToggleButtonWithLabel(
            size_hint=(None, None),
            size=size,
            pos_hint=pos_hint
        )

        self.type_switch_button.label.text = text
        self.type_switch_button.icon.source = icon_path

        if callback:
            self.type_switch_button.bind(on_press=callback)
        self.layout.add_widget(self.type_switch_button)

        return self.type_switch_button

    def set_switch_button_state(self, enabled):
        if self.type_switch_button:
            self.type_switch_button.disabled = not enabled
            self.type_switch_button.opacity = 1.0 if enabled else 0.5

    def remove_switch_button(self):
        if self.type_switch_button and self.type_switch_button in self.layout.children:
            self.layout.remove_widget(self.type_switch_button)
            self.type_switch_button = None

    def update_switch_button_size(self):
        if self.type_switch_button:
            screen_width = self.get_screen_width()
            screen_height = self.get_screen_height()

            button_width = screen_width * self.SWITCH_BUTTON_WIDTH_COEFF
            button_height = screen_height * self.SWITCH_BUTTON_HEIGHT_COEFF
            self.type_switch_button.size = (button_width, button_height)

    # ==================== ОСТАЛЬНЫЕ МЕТОДЫ ====================

    def load_back_sound(self):
        sound_path = 'assets/sounds/Schpun.ogg'
        if os.path.exists(sound_path):
            self.back_sound = SoundLoader.load(sound_path)
            if self.back_sound:
                self.back_sound.volume = 0.8

    def play_back_sound(self):
        if self.back_sound and not self.sound_manager.is_muted():
            try:
                self.back_sound.play()
            except:
                pass

    def _on_size_change(self, instance, value):
        if self.back_button:
            Clock.schedule_once(lambda dt: self._update_button_position(), 0.05)
        if self.type_switch_button:
            Clock.schedule_once(lambda dt: self.update_switch_button_size(), 0.05)

    def _update_button_position(self):
        if self.back_button:
            real_width = self.get_screen_width()
            real_height = self.get_screen_height()
            btn_size = real_width * 0.1
            btn_x = real_width * 0.05
            btn_y = real_height * 0.05
            self.back_button.size = (btn_size, btn_size)
            self.back_button.pos = (btn_x, btn_y)

    def on_enter(self):
        """Вызывается при входе на экран (FadeTransition из main.py обеспечивает затемнение)"""
        # Настройка фона и звука
        self.setup_background()
        self.setup_sound()
        Clock.schedule_once(lambda dt: self.create_back_button(), 0.05)

        if self.is_game_screen:
            if not self.sound_manager.is_muted():
                self.sound_manager.fade_to(0.05, duration=1.0)

    def on_leave(self):
        """Вызывается при выходе с экрана"""
        self.stop_sound()
        if self.is_game_screen and not self.sound_manager.is_muted():
            self.sound_manager.fade_to(1.0, duration=1.0)

    def go_to_menu(self):
        """Возврат в меню через switch_screen (пересоздание экрана)"""
        self.stop_sound()
        if not self.sound_manager.is_muted():
            self.sound_manager.fade_to(1.0, duration=0.5)

        # Используем глобальную функцию из main.py для пересоздания экрана
        from main import switch_screen
        switch_screen('menu')

    def setup_background(self):
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
        if self.sound_file:
            self.sound = SoundLoader.load(self.sound_file)
            if self.sound:
                self.sound.loop = True
                self.sound.volume = 0.5 if not self.sound_manager.is_muted() else 0.0
                self.sound.play()

    def stop_sound(self):
        if self.sound:
            self.sound.stop()
            self.sound = None

    def create_back_button(self):
        if self.back_button and self.back_button in self.layout.children:
            self.layout.remove_widget(self.back_button)
        self._create_unified_back_button()

    def _create_unified_back_button(self):
        class ImageButton(ButtonBehavior, KivyImage):
            pass

        real_width = self.get_screen_width()
        real_height = self.get_screen_height()
        btn_size = real_width * 0.1
        btn_x = real_width * 0.05
        btn_y = real_height * 0.05

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

    def on_touch_down(self, touch):
        if hasattr(self, 'back_button') and self.back_button:
            if self.back_button.collide_point(touch.x, touch.y):
                self.back_button.on_touch_down(touch)
                return True
        return super().on_touch_down(touch)

    def start_game(self):
        pass

    # ==================== МЕТОДЫ ВИБРАЦИИ ====================

    def vibrate(self, duration=0.05):
        """
        Вибрация на игровом экране
        duration - длительность в секундах (по умолчанию 0.05 = 50 мс)
        """
        if hasattr(self, 'sound_manager') and self.sound_manager:
            self.sound_manager.vibrate(duration)

    def vibrate_custom(self, duration_ms):
        """
        Вибрация с произвольной длительностью в миллисекундах

        Args:
            duration_ms: длительность вибрации в миллисекундах (например, 100, 250, 500)

        Примеры:
            self.vibrate_custom(100)   # вибрация 100 мс
            self.vibrate_custom(250)   # вибрация 250 мс
            self.vibrate_custom(500)   # вибрация 500 мс
        """
        # Конвертируем миллисекунды в секунды
        duration_sec = duration_ms / 1000.0
        self.vibrate(duration_sec)

    def vibrate_short(self):
        """Короткая вибрация (30 мс)"""
        self.vibrate(0.03)

    def vibrate_medium(self):
        """Средняя вибрация (60 мс)"""
        self.vibrate(0.06)

    def vibrate_long(self):
        """Длинная вибрация (120 мс)"""
        self.vibrate(0.12)

    def vibrate_success(self):
        """Вибрация при успешном действии (двойная короткая)"""
        if hasattr(self, 'sound_manager') and self.sound_manager:
            self.sound_manager.vibrate_success()

    def vibrate_error(self):
        """Вибрация при ошибке (длинная)"""
        self.vibrate_long()

    def vibrate_selection(self):
        """Вибрация при выборе элемента"""
        self.vibrate_short()
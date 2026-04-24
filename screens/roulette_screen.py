import os
import math
import random
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Ellipse, Line
from screens.base_game_screen import BaseGameScreen
from kivy.properties import NumericProperty
from kivy.graphics import Rotate, PushMatrix, PopMatrix
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform


class AdaptiveBackground(Image):
    """
    Адаптивный фон, который сохраняет пропорции и не растягивается.
    """

    def __init__(self, source='', **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.allow_stretch = True
        self.keep_ratio = True
        self.size_hint = (None, None)

        Window.bind(on_resize=self._on_window_resize)
        self.bind(texture=self._on_texture_loaded)

        Clock.schedule_once(lambda dt: self._update_display(), 0.1)

    def _on_texture_loaded(self, instance, value):
        Clock.schedule_once(lambda dt: self._update_display(), 0.1)

    def _on_window_resize(self, window, width, height):
        Clock.schedule_once(lambda dt: self._update_display(), 0.05)

    def _update_display(self, *args):
        if not self.texture:
            return

        if Window.width <= 0 or Window.height <= 0:
            return

        tex_w = self.texture.width
        tex_h = self.texture.height

        if tex_w == 0 or tex_h == 0:
            return

        screen_w = Window.width
        screen_h = Window.height

        scale_w = screen_w / tex_w
        scale_h = screen_h / tex_h
        scale = max(scale_w, scale_h)

        self.width = tex_w * scale
        self.height = tex_h * scale

        self.x = (screen_w - self.width) / 2
        self.y = (screen_h - self.height) / 2


class RotatingImage(Image):
    """Image с поддержкой вращения вокруг центра"""
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._rotate = None
        self._setup_graphics()
        self.bind(
            pos=self._update_origin,
            size=self._update_origin,
            angle=self._update_angle
        )

    def _setup_graphics(self):
        with self.canvas.before:
            PushMatrix()
            self._rotate = Rotate(angle=self.angle, origin=self.center)
        with self.canvas.after:
            PopMatrix()

    def _update_angle(self, instance, value):
        if self._rotate:
            self._rotate.angle = value

    def _update_origin(self, *args):
        if self._rotate:
            center_x = self.x + self.width / 2
            center_y = self.y + self.height / 2
            self._rotate.origin = (center_x, center_y)


class ToggleButtonWithLabel(ButtonBehavior, FloatLayout):
    """Кнопка с изображением как фоном и текстом по центру"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (150, 50)

        self.bg_image = Image(
            source='',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            allow_stretch=True,
            keep_ratio=False
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

    @property
    def icon(self):
        return self.bg_image

    @icon.setter
    def icon(self, value):
        self.bg_image.source = value


class ImageButton(ButtonBehavior, Image):
    pass


class DebugHighlight(Widget):
    """Виджет для отладки - подсвечивает область нажатия"""

    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        self.color = color
        self.bind(pos=self._update, size=self._update)
        Clock.schedule_once(lambda dt: self._update(), 0.1)

    def _update(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
            Color(*self.color[:3], 0.2)
            Rectangle(pos=self.pos, size=self.size)


class RouletteScreen(BaseGameScreen):
    """Экран рулетки - только колесо и запуск"""

    # Флаг отладки - установите False чтобы отключить подсветку
    DEBUG_MODE = True

    def __init__(self, game_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'roulette'
        self.sound_file = 'assets/sounds/roulette_music.mp3'

        self.adaptive_bg = None
        self.roulette_type = 'european'

        self.wheel = None
        self.wheel_container = None
        self.is_spinning = False
        self.current_rotation = 0
        self.ball_launched = False

        self.spin_button = None

        self.wheel_spin_sound = None
        self.ball_roll_sound = None

        self.spin_timer = None
        self.ball_timer = None

        self.debug_wheel_area = None
        self.debug_click_area = None
        self.debug_button_area = None
        self.debug_wheel_image_area = None

        # Плотность экрана
        self.screen_density = 1.0

        self.roulette_data = {
            'european': {
                'button_image': 'assets/images/buttons/Roulette_switch_button.png',
                'name': 'EUROPEAN ROULETTE',
                'button_text': 'SWITCH',
                'button_color': (0.2, 0.4, 0.8, 1),
                'numbers': [
                    '0', '32', '15', '19', '4', '21', '2', '25', '17', '34',
                    '6', '27', '13', '36', '11', '30', '8', '23', '10', '5',
                    '24', '16', '33', '1', '20', '14', '31', '9', '22', '18',
                    '29', '7', '28', '12', '35', '3', '26'
                ],
                'colors': {
                    '0': (0, 0.5, 0, 1),
                    '32': (0.8, 0, 0, 1), '15': (0, 0, 0, 1), '19': (0.8, 0, 0, 1),
                    '4': (0, 0, 0, 1), '21': (0.8, 0, 0, 1), '2': (0, 0, 0, 1),
                    '25': (0.8, 0, 0, 1), '17': (0, 0, 0, 1), '34': (0.8, 0, 0, 1),
                    '6': (0, 0, 0, 1), '27': (0.8, 0, 0, 1), '13': (0, 0, 0, 1),
                    '36': (0.8, 0, 0, 1), '11': (0, 0, 0, 1), '30': (0.8, 0, 0, 1),
                    '8': (0, 0, 0, 1), '23': (0.8, 0, 0, 1), '10': (0, 0, 0, 1),
                    '5': (0.8, 0, 0, 1), '24': (0, 0, 0, 1), '16': (0.8, 0, 0, 1),
                    '33': (0, 0, 0, 1), '1': (0.8, 0, 0, 1), '20': (0, 0, 0, 1),
                    '14': (0.8, 0, 0, 1), '31': (0, 0, 0, 1), '9': (0.8, 0, 0, 1),
                    '22': (0, 0, 0, 1), '18': (0.8, 0, 0, 1), '29': (0, 0, 0, 1),
                    '7': (0.8, 0, 0, 1), '28': (0, 0, 0, 1), '12': (0.8, 0, 0, 1),
                    '35': (0, 0, 0, 1), '3': (0.8, 0, 0, 1), '26': (0, 0, 0, 1)
                }
            },
            'american': {
                'button_image': 'assets/images/buttons/Roulette_switch_button.png',
                'name': 'AMERICAN ROULETTE',
                'button_text': 'SWITCH',
                'button_color': (0.8, 0.2, 0.2, 1),
                'numbers': [
                    '0', '28', '9', '26', '30', '11', '7', '20', '32', '17',
                    '5', '22', '34', '15', '3', '24', '36', '13', '1', '00',
                    '27', '10', '25', '29', '12', '8', '19', '31', '18', '6',
                    '21', '33', '16', '4', '23', '35', '14', '2'
                ],
                'colors': {
                    '0': (0, 0.5, 0, 1),
                    '00': (0, 0.5, 0, 1),
                    '28': (0, 0, 0, 1), '9': (0.8, 0, 0, 1), '26': (0, 0, 0, 1),
                    '30': (0, 0, 0, 1), '11': (0.8, 0, 0, 1), '7': (0.8, 0, 0, 1),
                    '20': (0, 0, 0, 1), '32': (0.8, 0, 0, 1), '17': (0.8, 0, 0, 1),
                    '5': (0, 0, 0, 1), '22': (0.8, 0, 0, 1), '34': (0, 0, 0, 1),
                    '15': (0.8, 0, 0, 1), '3': (0, 0, 0, 1), '24': (0.8, 0, 0, 1),
                    '36': (0, 0, 0, 1), '13': (0.8, 0, 0, 1), '1': (0.8, 0, 0, 1),
                    '27': (0.8, 0, 0, 1), '10': (0, 0, 0, 1), '25': (0.8, 0, 0, 1),
                    '29': (0, 0, 0, 1), '12': (0, 0, 0, 1), '8': (0, 0, 0, 1),
                    '19': (0.8, 0, 0, 1), '31': (0, 0, 0, 1), '18': (0.8, 0, 0, 1),
                    '6': (0, 0, 0, 1), '21': (0.8, 0, 0, 1), '33': (0, 0, 0, 1),
                    '16': (0.8, 0, 0, 1), '4': (0, 0, 0, 1), '23': (0.8, 0, 0, 1),
                    '35': (0, 0, 0, 1), '14': (0.8, 0, 0, 1), '2': (0, 0, 0, 1)
                }
            }
        }

        self.type_switch_button = ToggleButtonWithLabel(
            size_hint=(1, 1),
            size=(250, 60),
            pos_hint={'center_x': 0.5, 'center_y': 0.9}
        )

        self.bind(size=self.on_size)

    def on_size(self, *args):
        Clock.schedule_once(lambda dt: self._force_update_wheel_size(), 0.1)

    def get_device_density(self):
        """Получает плотность пикселей устройства"""
        if platform == 'android':
            try:
                from jnius import autoclass
                DisplayMetrics = autoclass('android.util.DisplayMetrics')
                metrics = DisplayMetrics()
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                display = activity.getWindowManager().getDefaultDisplay()
                display.getRealMetrics(metrics)

                density = metrics.density
                print(f"\n📱 Плотность экрана (density): {density}")
                return density
            except Exception as e:
                print(f"Ошибка получения плотности: {e}")
                return 1.0
        else:
            return 1.0

    def _get_real_screen_size(self):
        """Получает реальный размер экрана в логических пикселях Kivy"""
        if platform == 'android':
            width, height = Window.width, Window.height
            self.screen_density = self.get_device_density()
            return width, height
        else:
            width, height = Window.width, Window.height
            return width, height

    def _force_update_wheel_size(self):
        """Принудительно обновляет размер контейнера и колеса"""
        if self.wheel_container:
            screen_width, screen_height = self._get_real_screen_size()

            # Для телефона используем больший процент
            if platform == 'android':
                container_size = min(screen_width, screen_height) * 0.95
                print(f"📱 Телефон: размер контейнера {container_size:.1f} (95% от {min(screen_width, screen_height)})")
            else:
                container_size = min(screen_width, screen_height) * 0.85
                print(
                    f"💻 Компьютер: размер контейнера {container_size:.1f} (85% от {min(screen_width, screen_height)})")

            container_x = (screen_width - container_size) / 2
            container_y = (screen_height - container_size) / 2

            self.wheel_container.size = (container_size, container_size)
            self.wheel_container.pos = (container_x, container_y)

            if self.wheel:
                self.wheel.canvas.ask_update()

    def get_screen_size(self):
        return self._get_real_screen_size()

    def on_enter(self):
        if not self.adaptive_bg:
            self.adaptive_bg = AdaptiveBackground(
                source='assets/backgrounds/roulette_bg.jpg'
            )
            self.layout.add_widget(self.adaptive_bg, index=0)

        if hasattr(self, 'bg_image') and self.bg_image:
            if self.bg_image in self.layout.children:
                self.layout.remove_widget(self.bg_image)
            self.bg_image = None

        super().on_enter()
        self.show_wheel_view()

    def _log_wheel_ratio(self, *args):
        """Выводит подробную информацию о соотношении размеров колеса и виджета"""
        if not self.wheel or not self.wheel_container:
            return

        print("\n" + "=" * 60)
        print("📊 СООТНОШЕНИЕ РАЗМЕРОВ КОЛЕСА И ВИДЖЕТА")
        print("=" * 60)

        container_w = self.wheel_container.width
        container_h = self.wheel_container.height
        wheel_w = self.wheel.width
        wheel_h = self.wheel.height

        print(f"📦 КОНТЕЙНЕР: {container_w:.1f} x {container_h:.1f}")
        print(f"🔄 КОЛЕСО: {wheel_w:.1f} x {wheel_h:.1f}")

        ratio_w = wheel_w / container_w if container_w > 0 else 0
        ratio_h = wheel_h / container_h if container_h > 0 else 0

        print(f"📐 СООТНОШЕНИЕ: {ratio_w:.3f} x {ratio_h:.3f}")

        if abs(ratio_w - 1.0) > 0.01:
            print(f"   ⚠️ ПРОБЛЕМА! Колесо должно занимать 100% контейнера!")
        else:
            print(f"   ✅ Колесо корректно занимает 100% контейнера")

        print(f"🖥 РАЗМЕР ЭКРАНА: {Window.width}x{Window.height}")
        print("=" * 60 + "\n")

    def show_wheel_view(self):
        print("\n" + "=" * 60)
        print("🎡 СОЗДАНИЕ КОЛЕСА РУЛЕТКИ")
        print("=" * 60)

        print(f"Тип рулетки: {self.roulette_data[self.roulette_type]['name']}")

        screen_width, screen_height = self._get_real_screen_size()

        self.is_spinning = False
        self.ball_launched = False

        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None
        if self.ball_timer:
            self.ball_timer.cancel()
            self.ball_timer = None

        self.clear_layout()

        data = self.roulette_data[self.roulette_type]
        self.type_switch_button.icon.source = data['button_image']
        self.type_switch_button.label.text = data['button_text']

        self.type_switch_button.bind(on_press=self.toggle_roulette_type)
        self.layout.add_widget(self.type_switch_button)

        title_label = Label(
            text=self.roulette_data[self.roulette_type]['name'],
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(400, 40),
            pos_hint={'center_x': 0.5, 'top': 1}
        )
        self.layout.add_widget(title_label)

        # ========== НАСТРОЙКИ КОЛЕСА ==========
        # Для телефона используем больший процент
        if platform == 'android':
            container_size = min(screen_width, screen_height) * 0.95
            print(f"📱 Телефон: размер контейнера {container_size:.1f} (95% от {min(screen_width, screen_height)})")
        else:
            container_size = min(screen_width, screen_height) * 0.85
            print(f"💻 Компьютер: размер контейнера {container_size:.1f} (85% от {min(screen_width, screen_height)})")

        container_x = (screen_width - container_size) / 2
        container_y = (screen_height - container_size) / 2

        print(
            f"📦 КОНТЕЙНЕР: размер {container_size:.1f}x{container_size:.1f}, позиция ({container_x:.1f}, {container_y:.1f})")

        self.wheel_container = FloatLayout(
            size_hint=(None, None),
            size=(container_size, container_size),
            pos=(container_x, container_y)
        )

        if self.roulette_type == 'american':
            wheel_source = 'assets/images/Roulette_wheel_00.png'
        else:
            wheel_source = 'assets/images/Roulette_wheel_0.png'

        print(f"🖼 Загрузка изображения: {wheel_source}")

        self.wheel = RotatingImage(
            source=wheel_source,
            size_hint=(1.0, 1.0),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        self.wheel_container.add_widget(self.wheel)
        self.layout.add_widget(self.wheel_container)

        Clock.schedule_once(lambda dt: self._force_update_wheel_size(), 0.1)
        Clock.schedule_once(lambda dt: self._log_wheel_ratio(), 0.3)

        # ========== ПОДСВЕТКА ОБЛАСТЕЙ ДЛЯ ОТЛАДКИ ==========
        if self.DEBUG_MODE:
            self.debug_wheel_image_area = DebugHighlight(
                color=(1, 0, 0, 0.8),
                size_hint=(1.0, 1.0),
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            self.wheel_container.add_widget(self.debug_wheel_image_area)

            self.debug_wheel_area = DebugHighlight(
                color=(0, 0, 1, 0.5),
                size_hint=(1.0, 1.0),
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            self.wheel_container.add_widget(self.debug_wheel_area)

            self.debug_click_area = DebugHighlight(
                color=(1, 1, 0, 0.5),
                size_hint=(1.0, 1.0),
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            self.wheel_container.add_widget(self.debug_click_area)

        # ========== НАСТРОЙКИ КНОПКИ ШАРИКА ==========
        if platform == 'android':
            button_size = min(screen_width, screen_height) * 0.15
            print(f"📱 Телефон: кнопка {button_size:.1f} (15% от {min(screen_width, screen_height)})")
        else:
            button_size = min(screen_width, screen_height) * 0.12
            print(f"💻 Компьютер: кнопка {button_size:.1f} (12% от {min(screen_width, screen_height)})")

        self.spin_button = ImageButton(
            source='assets/images/buttons/Roulette_ball.png',
            size_hint=(None, None),
            size=(button_size, button_size),
            pos_hint={'center_x': 0.5, 'y': 0.05},
            color=(1, 1, 1, 1)
        )
        self.spin_button.bind(on_press=self.spin_wheel)
        self.layout.add_widget(self.spin_button)

        if self.DEBUG_MODE:
            self.debug_button_area = DebugHighlight(
                color=(0, 1, 0, 0.5),
                size_hint=(None, None),
                size=(button_size, button_size),
                pos_hint={'center_x': 0.5, 'y': 0.05}
            )
            self.layout.add_widget(self.debug_button_area)

        print(f"\n📊 ИТОГОВЫЕ РАЗМЕРЫ:")
        print(f"   Platform: {platform}")
        print(f"   Screen: {screen_width}x{screen_height}")
        print(f"   Container: {container_size:.1f}x{container_size:.1f}")
        print(f"   Button: {button_size:.1f}x{button_size:.1f}")
        print("=" * 60 + "\n")

    def play_wheel_spin_sound(self):
        try:
            if not self.wheel_spin_sound:
                self.wheel_spin_sound = SoundLoader.load('assets/sounds/Roulette/roulette_drum_revolution.ogg')
                if not self.wheel_spin_sound:
                    print("Не удалось загрузить звук вращения колеса")
                    return
            if self.wheel_spin_sound:
                if self.wheel_spin_sound.state == 'play':
                    self.wheel_spin_sound.stop()
                self.wheel_spin_sound.loop = False
                self.wheel_spin_sound.play()
        except Exception as e:
            print(f"Ошибка при воспроизведении звука вращения колеса: {e}")

    def play_ball_roll_sound(self):
        try:
            if not self.ball_roll_sound:
                self.ball_roll_sound = SoundLoader.load('assets/sounds/Roulette/ball_throw_american.ogg')
                if not self.ball_roll_sound:
                    print("Не удалось загрузить звук качения шарика")
                    return 0
            if self.ball_roll_sound:
                if self.ball_roll_sound.state == 'play':
                    self.ball_roll_sound.stop()
                self.ball_roll_sound.loop = False
                self.ball_roll_sound.play()
                sound_length = self.ball_roll_sound.length
                return sound_length if sound_length else 15.0
        except Exception as e:
            print(f"Ошибка при воспроизведении звука качения шарика: {e}")
            return 15.0

    def toggle_roulette_type(self, instance=None):
        print("Method toggle_roulette_type() called.")
        if self.is_spinning:
            print("Колесо вращается, переключение типа запрещено")
            return
        new_type = 'american' if self.roulette_type == 'european' else 'european'
        self.roulette_type = new_type
        data = self.roulette_data[self.roulette_type]
        if hasattr(self, 'type_switch_button') and self.type_switch_button:
            self.type_switch_button.icon.source = data['button_image']
            self.type_switch_button.label.text = data['button_text']
        self.show_wheel_view()

    def switch_roulette_type(self, roulette_type):
        if self.roulette_type != roulette_type:
            self.roulette_type = roulette_type
            if hasattr(self, 'type_switch_button') and self.type_switch_button:
                data = self.roulette_data[self.roulette_type]
                self.type_switch_button.icon.source = data['button_image']
                self.type_switch_button.label.text = data['button_text']
            self.show_wheel_view()

    def return_to_menu(self, instance=None):
        self.manager.current = 'menu'

    def set_switch_button_state(self, enabled):
        if hasattr(self, 'type_switch_button') and self.type_switch_button:
            self.type_switch_button.disabled = not enabled
            self.type_switch_button.opacity = 1.0 if enabled else 0.5

    def spin_wheel(self, instance=None):
        if self.is_spinning or not self.wheel:
            return
        print(f"🎰 Запускаю вращение колеса {self.roulette_type} рулетки...")
        self.set_switch_button_state(False)
        self.ball_launched = False
        self.stop_all_sounds()
        self.play_wheel_spin_sound()
        self.is_spinning = True
        current_angle = self.wheel.angle % 360
        self.wheel.angle = current_angle
        full_rotations = random.randint(8, 12)
        additional_angle = random.randint(0, 360)
        target_angle = current_angle + 360 * full_rotations + additional_angle
        print(f"Начальный угол: {current_angle}°, целевой: {target_angle}°")
        anim = Animation(angle=target_angle, duration=16.0, t='out_quad')
        anim.bind(on_complete=self._on_wheel_spin_complete)
        anim.start(self.wheel)
        self.current_animation = anim
        self.spin_timer = Clock.schedule_once(self._force_stop_wheel, 18.0)

    def launch_ball(self, instance=None):
        if not self.is_spinning or self.ball_launched:
            if not self.is_spinning:
                self.spin_wheel()
            if self.ball_launched:
                return
        print("🎯 Запускаю шарик в рулетку...")
        if self.spin_button:
            anim_hide = Animation(opacity=0, duration=0.3, t='out_cubic')
            anim_hide.bind(on_complete=lambda *args: setattr(self.spin_button, 'disabled', True))
            anim_hide.start(self.spin_button)
        sound_duration = self.play_ball_roll_sound()
        self.ball_launched = True
        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None
        result_delay = sound_duration + 0.5
        self.ball_timer = Clock.schedule_once(self._show_ball_result, result_delay)
        print(f"⏱ Результат будет показан через {result_delay} секунд")

    def _on_wheel_spin_complete(self, animation, widget):
        print("🛑 Колесо остановилось самостоятельно, шарик не запускался")
        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None
        if not self.ball_launched:
            self.stop_all_sounds()
        self.set_switch_button_state(True)
        self.is_spinning = False

    def _force_stop_wheel(self, dt):
        print("⏰ Таймер: принудительная остановка колеса")
        if self.is_spinning:
            if hasattr(self, 'current_animation') and self.current_animation:
                self.current_animation.stop(self.wheel)
            if not self.ball_launched:
                self.stop_all_sounds()
            self.set_switch_button_state(True)
            self.is_spinning = False
        self.spin_timer = None

    def _show_ball_result(self, dt):
        print("🎯 Шарик остановился, показываю результат")
        if self.ball_roll_sound:
            self.ball_roll_sound.stop()
        if self.wheel_spin_sound:
            self.wheel_spin_sound.stop()
            self.wheel_spin_sound.loop = False
        if hasattr(self, 'current_animation') and self.current_animation:
            self.current_animation.stop(self.wheel)
        self.is_spinning = False
        self.ball_launched = False
        self.ball_timer = None
        self.set_switch_button_state(True)
        winning_sector = self._get_winning_sector()
        self._show_result(winning_sector)

    def _get_winning_sector(self):
        data = self.roulette_data[self.roulette_type]
        winning_number = random.choice(data['numbers'])
        if winning_number in ['0', '00']:
            color_name = 'GREEN'
        elif data['colors'][winning_number] == (0.8, 0, 0, 1):
            color_name = 'RED'
        else:
            color_name = 'BLACK'
        return f'{winning_number} {color_name}'

    def _show_result(self, result):
        main_layout = FloatLayout()
        main_layout.scale = 0.8
        main_layout.opacity = 0
        try:
            popup_bg = Image(
                source='assets/images/Out_image.png',
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(1, 1),
                pos_hint={'x': 0, 'y': 0}
            )
            main_layout.add_widget(popup_bg)
        except Exception as e:
            print(f"Не удалось загрузить фоновое изображение: {e}")
            with main_layout.canvas.before:
                Color(0.1, 0.1, 0.2, 0.95)
                Rectangle(size=main_layout.size, pos=main_layout.pos)
            main_layout.bind(size=self._update_rect, pos=self._update_rect)
        parts = result.split()
        number = parts[0]
        color = parts[1] if len(parts) > 1 else ''
        number_color = (0, 0.5, 0, 1) if color == 'GREEN' else (0.8, 0, 0, 1) if color == 'RED' else (0, 0, 0, 1)
        number_label = Label(
            text=number,
            font_size='96sp',
            bold=True,
            color=number_color,
            size_hint=(None, None),
            size=(200, 200),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        main_layout.add_widget(number_label)

        def dismiss_popup_with_animation(instance):
            anim_scale = Animation(scale=0.8, opacity=0, duration=0.3, t='out_cubic')
            anim_scale.start(main_layout)
            anim_text = Animation(opacity=0, duration=0.3, t='out_cubic')
            anim_text.start(number_label)
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.result_popup.dismiss(), 0.35)
            Clock.schedule_once(lambda dt: self._show_spin_button(), 0.4)

        close_button = Button(text='', size_hint=(1, 1), background_color=(0, 0, 0, 0), background_normal='')
        close_button.bind(on_press=dismiss_popup_with_animation)
        main_layout.add_widget(close_button)

        self.result_popup = Popup(
            title='',
            content=main_layout,
            size_hint=(0.7, 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            separator_height=0,
            background='',
            background_color=(0, 0, 0, 0),
            auto_dismiss=False,
            opacity=0
        )

        def animate_popup_open():
            self.result_popup.opacity = 1
            anim_bg = Animation(scale=1, opacity=1, duration=0.4, t='out_back')
            anim_bg.start(main_layout)
            from kivy.clock import Clock
            number_label.opacity = 0
            number_label.scale = 1.2
            anim_text_scale = Animation(scale=1, duration=0.4, t='out_back')
            anim_text_opacity = Animation(opacity=1, duration=0.4, t='out_cubic')
            Clock.schedule_once(lambda dt: (anim_text_scale.start(number_label), anim_text_opacity.start(number_label)),
                                0.15)

        self.result_popup.open()
        animate_popup_open()

    def _show_spin_button(self):
        if self.spin_button:
            self.spin_button.disabled = False
            anim_show = Animation(opacity=1, duration=0.5, t='out_cubic')
            anim_show.start(self.spin_button)

    @staticmethod
    def _update_rect(instance, value):
        if hasattr(instance, 'canvas'):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.1, 0.1, 0.2, 0.95)
                Rectangle(pos=instance.pos, size=instance.size)

    def clear_layout(self):
        for child in self.layout.children[:]:
            if child not in [self.adaptive_bg, self.back_button]:
                self.layout.remove_widget(child)

    def create_simple_wheel(self, container):
        from kivy.graphics import Color, Ellipse, Line, Rotate

        class SimpleWheel(Widget):
            angle = NumericProperty(0)

            def __init__(self, roulette_type='european', **kwargs):
                super().__init__(**kwargs)
                self.roulette_type = roulette_type
                self.size_hint = (1.0, 1.0)
                self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                with self.canvas.before:
                    PushMatrix()
                    self.rotate_instruction = Rotate(angle=self.angle, origin=self.center)
                with self.canvas.after:
                    PopMatrix()
                self.bind(pos=self.update_origin, size=self.update_origin, angle=self.update_angle)
                self.draw_wheel()

            def update_origin(self, *args):
                self.rotate_instruction.origin = (self.center_x, self.center_y)

            def update_angle(self, *args):
                self.rotate_instruction.angle = self.angle

            def draw_wheel(self):
                self.canvas.clear()
                center_x, center_y = self.width / 2, self.height / 2
                with self.canvas:
                    Color(0.7, 0.1, 0.1, 1)
                    Ellipse(pos=(0, 0), size=self.size)
                    Color(0.1, 0.1, 0.1, 1)
                    inner_size = self.size[0] - 100, self.size[1] - 100
                    inner_pos = 50, 50
                    Ellipse(pos=inner_pos, size=inner_size)
                    Color(1, 1, 1, 1)
                    radius = min(self.size) / 2 - 50
                    sectors = 38 if self.roulette_type == 'american' else 37
                    for i in range(sectors):
                        angle = i * (360 / sectors)
                        rad = angle * 3.14159 / 180
                        x1 = center_x + radius * 0.9 * math.cos(rad)
                        y1 = center_y + radius * 0.9 * math.sin(rad)
                        x2 = center_x + radius * 0.7 * math.cos(rad)
                        y2 = center_y + radius * 0.7 * math.sin(rad)
                        Line(points=[x1, y1, x2, y2], width=2)
                    Color(0, 0.5, 0, 1)
                    indicator_size = 20, 20
                    indicator_pos = center_x - 10, center_y - 10
                    Ellipse(pos=indicator_pos, size=indicator_size)

        self.wheel = SimpleWheel(self.roulette_type)
        container.add_widget(self.wheel)

    def on_touch_down(self, touch):
        if self.wheel and hasattr(self.wheel, 'collide_point') and self.wheel.collide_point(*touch.pos):
            if not self.is_spinning:
                self.spin_wheel()
            return True
        if self.spin_button and self.spin_button.collide_point(*touch.pos):
            if self.is_spinning and not self.ball_launched:
                self.launch_ball()
            elif not self.is_spinning:
                self.spin_wheel()
                Clock.schedule_once(lambda dt: self.launch_ball(), 0.5)
            return True
        return super().on_touch_down(touch)

    def on_leave(self):
        self.stop_all_sounds()
        Animation.cancel_all(self)
        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None
        if self.ball_timer:
            self.ball_timer.cancel()
            self.ball_timer = None
        self.is_spinning = False
        self.ball_launched = False
        self.set_switch_button_state(True)
        if self.wheel:
            self.wheel.angle = 0
        if self.spin_button:
            self.spin_button.opacity = 1
            self.spin_button.disabled = False
        super().on_leave()

    def stop_all_sounds(self):
        if self.wheel_spin_sound:
            self.wheel_spin_sound.stop()
            self.wheel_spin_sound.loop = False
        if self.ball_roll_sound:
            self.ball_roll_sound.stop()
            self.ball_roll_sound.loop = False
            #
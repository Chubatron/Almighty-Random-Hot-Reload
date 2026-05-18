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


class ImageButton(ButtonBehavior, Image):
    pass


class RouletteScreen(BaseGameScreen):
    DEBUG_MODE = False

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
        self.result_popup_closed = True
        self.wheel_only_mode = False

        self.spin_button = None

        self.wheel_spin_sound = None
        self.ball_roll_sound = None

        self.spin_timer = None
        self.ball_timer = None

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

        self.bind(size=self.on_size)

    def on_size(self, *args):
        Clock.schedule_once(lambda dt: self._force_update_wheel_size(), 0.1)

    def set_switch_button_state(self, enabled):
        super().set_switch_button_state(enabled)

    def set_spin_button_state(self, enabled, hide=False):
        if self.spin_button:
            self.spin_button.disabled = not enabled
            if hide:
                self.spin_button.opacity = 0 if not enabled else 1
            else:
                self.spin_button.opacity = 1 if enabled else 0.5

    def get_device_density(self):
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
                return density
            except Exception as e:
                return 1.0
        else:
            return 1.0

    def _get_real_screen_size(self):
        if platform == 'android':
            width, height = Window.width, Window.height
            self.screen_density = self.get_device_density()
            return width, height
        else:
            return Window.width, Window.height

    def _force_update_wheel_size(self):
        if self.wheel_container:
            screen_width, screen_height = self._get_real_screen_size()

            if platform == 'android':
                container_size = min(screen_width, screen_height) * 0.95
            else:
                container_size = min(screen_width, screen_height) * 0.85

            container_x = (screen_width - container_size) / 2
            container_y = (screen_height - container_size) / 2

            self.wheel_container.size = (container_size, container_size)
            self.wheel_container.pos = (container_x, container_y)

            if self.wheel:
                self.wheel.canvas.ask_update()

    def get_screen_size(self):
        return self._get_real_screen_size()

    def on_enter(self):
        self.result_popup_closed = True
        self.set_switch_button_state(True)
        self.set_spin_button_state(True)

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

    def show_wheel_view(self):
        screen_width, screen_height = self._get_real_screen_size()

        self.is_spinning = False
        self.ball_launched = False
        self.wheel_only_mode = False

        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None
        if self.ball_timer:
            self.ball_timer.cancel()
            self.ball_timer = None

        self.clear_layout()

        data = self.roulette_data[self.roulette_type]
        self.create_switch_button(
            text=data['button_text'],
            icon_path=data['button_image'],
            callback=self.toggle_roulette_type
        )

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

        if platform == 'android':
            container_size = min(screen_width, screen_height) * 0.95
        else:
            container_size = min(screen_width, screen_height) * 0.85

        container_x = (screen_width - container_size) / 2
        container_y = (screen_height - container_size) / 2

        self.wheel_container = FloatLayout(
            size_hint=(None, None),
            size=(container_size, container_size),
            pos=(container_x, container_y)
        )

        if self.roulette_type == 'american':
            wheel_source = 'assets/images/Roulette_wheel_00.png'
        else:
            wheel_source = 'assets/images/Roulette_wheel_0.png'

        self.wheel = RotatingImage(
            source=wheel_source,
            size_hint=(1.0, 1.0),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        self.wheel_container.add_widget(self.wheel)
        self.layout.add_widget(self.wheel_container)

        Clock.schedule_once(lambda dt: self._force_update_wheel_size(), 0.1)

        if platform == 'android':
            button_size = min(screen_width, screen_height) * 0.15
        else:
            button_size = min(screen_width, screen_height) * 0.12

        self.spin_button = ImageButton(
            source='assets/images/buttons/Roulette_ball.png',
            size_hint=(None, None),
            size=(button_size, button_size),
            pos_hint={'center_x': 0.5, 'y': 0.05},
            color=(1, 1, 1, 1)
        )
        self.spin_button.bind(on_press=self.launch_ball_only)
        self.layout.add_widget(self.spin_button)

    def play_wheel_spin_sound(self):
        if self.sound_manager.is_muted():
            return

        try:
            if not self.wheel_spin_sound:
                self.wheel_spin_sound = SoundLoader.load('assets/sounds/Roulette/roulette_drum_revolution.ogg')
                if not self.wheel_spin_sound:
                    return
            if self.wheel_spin_sound:
                if self.wheel_spin_sound.state == 'play':
                    self.wheel_spin_sound.stop()
                self.wheel_spin_sound.loop = False
                self.wheel_spin_sound.play()
        except Exception as e:
            pass

    def play_ball_roll_sound(self):
        if self.sound_manager.is_muted():
            return 15.0

        try:
            if not self.ball_roll_sound:
                self.ball_roll_sound = SoundLoader.load('assets/sounds/Roulette/ball_throw_american.ogg')
                if not self.ball_roll_sound:
                    return 15.0
            if self.ball_roll_sound:
                if self.ball_roll_sound.state == 'play':
                    self.ball_roll_sound.stop()
                self.ball_roll_sound.loop = False
                self.ball_roll_sound.play()
                sound_length = self.ball_roll_sound.length
                return sound_length if sound_length else 15.0
        except Exception as e:
            return 15.0

    def toggle_roulette_type(self, instance=None):
        if self.is_spinning or not self.result_popup_closed:
            return
        new_type = 'american' if self.roulette_type == 'european' else 'european'
        self.roulette_type = new_type
        data = self.roulette_data[self.roulette_type]
        if hasattr(self, 'type_switch_button') and self.type_switch_button:
            self.type_switch_button.icon.source = data['button_image']
            self.type_switch_button.label.text = data['button_text']
        self.show_wheel_view()

    def start_wheel_only(self, instance=None):
        if self.is_spinning or not self.wheel or not self.result_popup_closed:
            return

        # Вибрация при запуске колеса
        self.vibrate_medium()

        self.set_switch_button_state(False)
        self.result_popup_closed = False
        self.wheel_only_mode = True
        self.ball_launched = False

        self.spin_wheel()

    def launch_ball_only(self, instance=None):
        if not self.is_spinning or self.ball_launched:
            return

        # Вибрация при нажатии на кнопку шарика
        self.vibrate_medium()

        self.set_spin_button_state(False, hide=False)

        sound_duration = self.play_ball_roll_sound()
        self.ball_launched = True

        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None

        result_delay = sound_duration + 0.5
        self.ball_timer = Clock.schedule_once(self._show_result_popup, result_delay)

    def start_full_roulette(self, instance=None):
        if self.is_spinning or not self.wheel or not self.result_popup_closed:
            return

        # Вибрация при запуске полной рулетки
        self.vibrate_medium()

        self.set_switch_button_state(False)
        self.set_spin_button_state(False)
        self.result_popup_closed = False
        self.wheel_only_mode = False
        self.ball_launched = False

        self.spin_wheel()

    def spin_wheel(self, instance=None):
        if self.is_spinning or not self.wheel:
            return

        self.stop_all_sounds()
        self.play_wheel_spin_sound()
        self.is_spinning = True
        current_angle = self.wheel.angle % 360
        self.wheel.angle = current_angle
        full_rotations = random.randint(8, 12)
        additional_angle = random.randint(0, 360)
        target_angle = current_angle + 360 * full_rotations + additional_angle
        anim = Animation(angle=target_angle, duration=16.0, t='out_quad')
        anim.bind(on_complete=self._on_wheel_spin_complete)
        anim.start(self.wheel)
        self.current_animation = anim
        self.spin_timer = Clock.schedule_once(self._force_stop_wheel, 18.0)

        if not self.wheel_only_mode:
            Clock.schedule_once(lambda dt: self.launch_ball_only(), 2.0)

    def _on_wheel_spin_complete(self, animation, widget):
        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None

        if self.wheel_only_mode and not self.ball_launched:
            self._enable_buttons_after_wheel_only()

    def _force_stop_wheel(self, dt):
        if self.is_spinning:
            if hasattr(self, 'current_animation') and self.current_animation:
                self.current_animation.stop(self.wheel)

            if self.wheel_only_mode and not self.ball_launched:
                self._enable_buttons_after_wheel_only()

    def _enable_buttons_after_wheel_only(self):
        self.is_spinning = False
        self.result_popup_closed = True
        self.set_switch_button_state(True)
        self.set_spin_button_state(True)

    def _show_result_popup(self, dt):
        if self.ball_roll_sound:
            self.ball_roll_sound.stop()
        if self.wheel_spin_sound:
            self.wheel_spin_sound.stop()
            self.wheel_spin_sound.loop = False

        if hasattr(self, 'current_animation') and self.current_animation:
            self.current_animation.stop(self.wheel)

        self.is_spinning = False
        self.ball_launched = False

        winning_number = self.get_random_number()

        # Вибрация при выводе результата с задержкой 0.1 секунды
        Clock.schedule_once(lambda dt: self.vibrate_long(), 0.1)

        self._show_result(winning_number)

    def get_random_number(self):
        data = self.roulette_data[self.roulette_type]
        return random.choice(data['numbers'])

    def _show_result(self, number):
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
            with main_layout.canvas.before:
                Color(0.1, 0.1, 0.2, 0.95)
                Rectangle(size=main_layout.size, pos=main_layout.pos)
            main_layout.bind(size=self._update_rect, pos=self._update_rect)

        if number == '0' or number == '00':
            number_color = (0, 0.5, 0, 1)
        elif self.roulette_data[self.roulette_type]['colors'].get(number) == (0.8, 0, 0, 1):
            number_color = (0.8, 0, 0, 1)
        else:
            number_color = (0, 0, 0, 1)

        number_label = Label(
            text=str(number),
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
            Clock.schedule_once(lambda dt: self.result_popup.dismiss(), 0.35)
            Clock.schedule_once(lambda dt: self._enable_all_buttons(), 0.5)

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
            number_label.opacity = 0
            number_label.scale = 1.2
            anim_text_scale = Animation(scale=1, duration=0.4, t='out_back')
            anim_text_opacity = Animation(opacity=1, duration=0.4, t='out_cubic')
            Clock.schedule_once(lambda dt: (anim_text_scale.start(number_label), anim_text_opacity.start(number_label)),
                                0.15)

        self.result_popup.open()
        animate_popup_open()

    def _enable_all_buttons(self):
        self.result_popup_closed = True
        self.set_switch_button_state(True)
        self.set_spin_button_state(True)

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
        self.wheel_only_mode = False
        self.result_popup_closed = True
        self.set_switch_button_state(True)
        self.set_spin_button_state(True)
        if self.wheel:
            self.wheel.angle = 0

        self.remove_switch_button()

        super().on_leave()

    def stop_all_sounds(self):
        if self.wheel_spin_sound:
            self.wheel_spin_sound.stop()
            self.wheel_spin_sound.loop = False
        if self.ball_roll_sound:
            self.ball_roll_sound.stop()
            self.ball_roll_sound.loop = False

    def go_to_menu(self):
        """Возврат в меню"""
        print(f"🏠 [RouletteScreen] Возврат в меню")
        self.stop_all_sounds()
        super().go_to_menu()

    def on_touch_down(self, touch):
        # Проверяем нажатие на колесо (запуск только колеса)
        if self.wheel_container and self.wheel_container.collide_point(touch.x, touch.y):
            if not self.is_spinning and self.result_popup_closed:
                self.start_wheel_only()
                return True

        # Проверяем нажатие на кнопку запуска шарика
        if self.spin_button and self.spin_button.collide_point(touch.x, touch.y):
            if self.spin_button.disabled:
                return True

            # Вибрация при нажатии на кнопку шарика
            self.vibrate_medium()

            if self.is_spinning:
                self.launch_ball_only()
            else:
                self.start_full_roulette()
            return True

        # Кнопка назад обрабатывается в базовом классе (там есть звук)
        return super().on_touch_down(touch)
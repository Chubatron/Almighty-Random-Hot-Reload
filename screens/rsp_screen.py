# screens/rsp_screen.py
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.properties import NumericProperty, StringProperty
from kivy.clock import Clock
from kivy.graphics import Rotate, PushMatrix, PopMatrix
import random
import os
import math

from screens.base_game_screen import BaseGameScreen


class RotatingImage(Image):
    """Изображение с поддержкой вращения вокруг своего центра"""
    angle = NumericProperty(0)

    def __init__(self, name="", **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.allow_stretch = True
        self.keep_ratio = True

        self._rotate = None
        self._setup_graphics()

        self.bind(
            center=self._update_origin,
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
            self._rotate.origin = (self.center_x, self.center_y)


class RotatingImageWithShadow(FloatLayout):
    """Контейнер с двумя независимо вращающимися изображениями: тень и спиннер"""
    angle = NumericProperty(0)

    def __init__(self, name="", source=None, shadow_source=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.size_hint = (None, None)

        self.shadow_image = RotatingImage(
            name=f"{name}_shadow",
            source=shadow_source if shadow_source else source,
            allow_stretch=True,
            keep_ratio=True,
            opacity=0.35,
            color=(0, 0, 0, 1)
        )

        self.main_image = RotatingImage(
            name=f"{name}_main",
            source=source,
            allow_stretch=True,
            keep_ratio=True,
            opacity=1
        )

        self.add_widget(self.shadow_image)
        self.add_widget(self.main_image)

        self.shadow_offset_y = 0

        self.bind(
            pos=self._update_position,
            size=self._update_size,
            angle=self._update_angle
        )

    def set_shadow_offset(self, offset_y):
        self.shadow_offset_y = offset_y
        self._update_position()

    def _update_angle(self, instance, value):
        self.shadow_image.angle = value
        self.main_image.angle = value

    def _update_position(self, *args):
        self.main_image.center = (self.center_x, self.center_y)
        self.main_image.size = self.size
        self.shadow_image.center = (self.center_x, self.center_y - self.shadow_offset_y)
        self.shadow_image.size = self.size

    def _update_size(self, *args):
        self.main_image.size = self.size
        self.shadow_image.size = self.size
        self._update_position()


class SpinButton(ButtonBehavior, Image):
    """Кнопка SPIN с кастомными изображениями для разных состояний"""

    is_active = NumericProperty(1)

    def __init__(self, **kwargs):
        passed_size = kwargs.get('size', None)

        super().__init__(**kwargs)

        self.green_button_path = 'assets/images/buttons/spin_button_green.png'
        self.red_button_path = 'assets/images/buttons/spin_button_red.png'

        self.size_hint = (None, None)

        if passed_size:
            self.size = passed_size
        else:
            self.size = (80, 80)

        self.allow_stretch = True
        self.update_button_image()
        self.bind(is_active=self.update_button_image)

    def update_button_image(self, *args):
        if self.is_active:
            if os.path.exists(self.green_button_path):
                self.source = self.green_button_path
                self.color = (1, 1, 1, 1)
        else:
            if os.path.exists(self.red_button_path):
                self.source = self.red_button_path
                self.color = (1, 1, 1, 1)


class RSPScreen(BaseGameScreen):
    """
    Экран игры "Камень, ножницы, бумага"
    """

    player_score = NumericProperty(0)
    computer_score = NumericProperty(0)
    result_text = StringProperty("Нажмите SPIN!")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_image = 'assets/backgrounds/rsp_bg.jpg'

        self.game_type = 'classic'

        self.spin_button = None
        self.title_label = None

        self.spinner_image_3 = None
        self.spinner_image_5 = None
        self.current_spinner = None

        self.is_spinning = False
        self.center_x = 0
        self.center_y = 0
        self.radius = 0
        self.winner_image = None

        self.current_animation = None
        self.spin_timer = None
        self.vibration_check_timer = None
        self.last_vibration_angle = None
        self.start_angle = 0
        self.total_rotations = 0
        self.target_angle = 0

        self.spin_sound = None
        self.result_sounds = {}

        self.classic_angles = {
            0: 'scissors',
            120: 'paper',
            240: 'rock'
        }
        self.classic_ordered_angles = [0, 120, 240]

        self.extended_angles = {
            0: 'spock',
            72: 'scissors',
            144: 'lizard',
            216: 'rock',
            288: 'paper'
        }
        self.extended_ordered_angles = [0, 72, 144, 216, 288]

    def on_enter(self):
        super().on_enter()

        self.is_spinning = False
        self.winner_image = None

        self.clear_ui()
        self.show_ui()
        self.load_result_sounds()
        self.reset_spinner()

        self.layout.bind(size=self.update_layout, pos=self.update_layout)
        self.update_layout()

    def on_leave(self):
        self.stop_all_vibration()

        if self.current_spinner:
            Animation.cancel_all(self.current_spinner)
            self.current_spinner.angle = 0

        if self.spinner_image_3:
            Animation.cancel_all(self.spinner_image_3)
            self.spinner_image_3.angle = 0
            self.spinner_image_3.opacity = 0

        if self.spinner_image_5:
            Animation.cancel_all(self.spinner_image_5)
            self.spinner_image_5.angle = 0
            self.spinner_image_5.opacity = 0

        if self.current_animation:
            if self.current_spinner:
                self.current_animation.stop(self.current_spinner)
            self.current_animation = None

        self.stop_all_sounds()
        self.stop_spinner_animation()

        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None

        if hasattr(self, 'spin_button') and self.spin_button:
            self.spin_button.unbind(on_press=self.start_spin)

        if hasattr(self, 'layout'):
            self.layout.unbind(size=self.update_layout, pos=self.update_layout)

        self.spin_button = None
        self.title_label = None
        self.spinner_image_3 = None
        self.spinner_image_5 = None
        self.current_spinner = None
        self.winner_image = None
        self.current_animation = None

        self.remove_switch_button()

        super().on_leave()

    def stop_all_vibration(self):
        """Останавливает все таймеры вибрации"""
        if self.vibration_check_timer:
            self.vibration_check_timer.cancel()
            self.vibration_check_timer = None
        self.last_vibration_angle = None

    def stop_all_sounds(self):
        if self.spin_sound:
            try:
                if self.spin_sound.state == 'play':
                    self.spin_sound.stop()
            except:
                pass
            self.spin_sound = None

        for sound in self.result_sounds.values():
            try:
                if sound.state == 'play':
                    sound.stop()
            except:
                pass

    def stop_spinner_animation(self):
        Animation.cancel_all(self)
        self.is_spinning = False
        self.stop_all_vibration()

        if self.current_spinner:
            self.current_spinner.angle = 0

        if self.spin_button:
            self.spin_button.is_active = 1
            self.spin_button.disabled = False

    def set_switch_button_state(self, enabled):
        super().set_switch_button_state(enabled)

    def reset_spinner(self):
        self.stop_all_sounds()
        self.stop_spinner_animation()
        self.stop_all_vibration()

        if self.spinner_image_3:
            Animation.cancel_all(self.spinner_image_3)
            self.spinner_image_3.angle = 0
        if self.spinner_image_5:
            Animation.cancel_all(self.spinner_image_5)
            self.spinner_image_5.angle = 0

        if self.current_animation:
            self.current_animation = None

    def go_to_menu(self):
        """Возврат в меню"""
        print(f"🏠 [RSPScreen] Возврат в меню")
        self.stop_all_sounds()
        self.stop_spinner_animation()
        self.stop_all_vibration()
        super().go_to_menu()

    def apply_current_game_type(self):
        if self.title_label:
            self.title_label.text = 'CLASSIC RSP' if self.game_type == 'classic' else 'EXTENDED RSP'

        if self.spinner_image_3:
            Animation.cancel_all(self.spinner_image_3)
            self.spinner_image_3.angle = 0
            self.spinner_image_3.opacity = 0
        if self.spinner_image_5:
            Animation.cancel_all(self.spinner_image_5)
            self.spinner_image_5.angle = 0
            self.spinner_image_5.opacity = 0

        if self.game_type == 'classic':
            if self.spinner_image_3:
                self.spinner_image_3.opacity = 1
                self.current_spinner = self.spinner_image_3
        else:
            if self.spinner_image_5:
                self.spinner_image_5.opacity = 1
                self.current_spinner = self.spinner_image_5

        self.recreate_spin_button()

    def update_layout(self, *args):
        self.center_x = self.layout.width / 2
        self.center_y = self.layout.height / 2

        min_dimension = min(self.layout.width, self.layout.height)
        self.radius = min_dimension * 0.3

        spinner_size_3 = min_dimension * 1.1
        spinner_size_5 = min_dimension * 1.0
        shadow_offset_y = self.layout.height * 0.05

        if self.spinner_image_3:
            self.spinner_image_3.size = (spinner_size_3, spinner_size_3)
            self.spinner_image_3.center = (self.center_x, self.center_y)
            self.spinner_image_3.set_shadow_offset(shadow_offset_y)

        if self.spinner_image_5:
            self.spinner_image_5.size = (spinner_size_5, spinner_size_5)
            self.spinner_image_5.center = (self.center_x, self.center_y)
            self.spinner_image_5.set_shadow_offset(shadow_offset_y)

        if self.spin_button:
            self.spin_button.center = (self.center_x, self.center_y)

    def setup_background(self):
        if self.bg_image:
            self.layout.remove_widget(self.bg_image)

        from kivy.uix.image import Image
        self.bg_image = Image(
            source=self.background_image,
            allow_stretch=True,
            keep_ratio=False
        )
        self.layout.add_widget(self.bg_image)

    def show_ui(self):
        self.create_switch_button(
            text="SWITCH",
            icon_path='assets/images/buttons/Roulette_switch_button.png',
            callback=self.toggle_game_type
        )

        self.title_label = Label(
            text='',
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(400, 40),
            pos_hint={'center_x': 0.5, 'top': 1}
        )
        self.layout.add_widget(self.title_label)

        self.create_spinner_images()
        self.create_spin_button()

        self.update_layout()
        self.apply_current_game_type()

    def create_spin_button(self):
        screen_width = self.layout.width if self.layout else 400

        if self.game_type == 'classic' and self.spinner_image_3:
            spinner_size = self.spinner_image_3.width
        elif self.spinner_image_5:
            spinner_size = self.spinner_image_5.width
        else:
            spinner_size = 0

        koef = 1.15
        button_size = (spinner_size * koef, spinner_size * koef)

        self.spin_button = SpinButton(
            is_active=1,
            size=button_size
        )
        self.spin_button.bind(on_press=self.start_spin)
        self.layout.add_widget(self.spin_button)

    def recreate_spin_button(self):
        if self.spin_button:
            self.spin_button.unbind(on_press=self.start_spin)
            self.layout.remove_widget(self.spin_button)
            self.spin_button = None

        self.create_spin_button()
        if hasattr(self, 'center_x') and hasattr(self, 'center_y'):
            self.spin_button.center = (self.center_x, self.center_y)

    def create_spinner_images(self):
        if os.path.exists('assets/images/rsp/spinner_3.png'):
            self.spinner_image_3 = RotatingImageWithShadow(
                name="spinner_3",
                source='assets/images/rsp/spinner_3.png',
                shadow_source='assets/images/rsp/spinner_3.png',
                size_hint=(None, None),
                opacity=0,
                angle=0
            )
            self.layout.add_widget(self.spinner_image_3)

        if os.path.exists('assets/images/rsp/spinner_5.png'):
            self.spinner_image_5 = RotatingImageWithShadow(
                name="spinner_5",
                source='assets/images/rsp/spinner_5.png',
                shadow_source='assets/images/rsp/spinner_5.png',
                size_hint=(None, None),
                opacity=0,
                angle=0
            )
            self.layout.add_widget(self.spinner_image_5)

    def load_result_sounds(self):
        sound_files = {
            'rock': 'assets/sounds/rsp/stone.ogg',
            'paper': 'assets/sounds/rsp/paper.ogg',
            'scissors': 'assets/sounds/rsp/scissors.ogg',
            'lizard': 'assets/sounds/rsp/lizard.ogg',
            'spock': 'assets/sounds/rsp/Spock.ogg'
        }

        from kivy.core.audio import SoundLoader

        for key, path in sound_files.items():
            if os.path.exists(path):
                sound = SoundLoader.load(path)
                if sound:
                    sound.volume = 0.8
                    self.result_sounds[key] = sound

    def play_result_sound(self, result):
        if self.sound_manager.is_muted():
            return

        if result in self.result_sounds:
            sound = self.result_sounds[result]
            if self.spin_sound and self.spin_sound.state == 'play':
                self.spin_sound.stop()
                self.spin_sound = None
            sound.play()

    def start_spin(self, instance):
        if self.is_spinning or not self.current_spinner:
            return

        self.set_switch_button_state(False)
        self.play_spin_sound()

        # ДЛИННАЯ ВИБРАЦИЯ ПРИ ЗАПУСКЕ ВРАЩЕНИЯ
        self.vibrate_long()

        self.is_spinning = True
        self.result_text = "ВРАЩЕНИЕ..."

        self.spin_button.is_active = 0
        self.spin_button.disabled = True

        # Запоминаем начальный угол для синхронизации вибрации
        self.start_angle = self.current_spinner.angle % 360

        if self.game_type == 'classic':
            valid_angles = [0, 120, 240]
        else:
            valid_angles = [0, 72, 144, 216, 288]

        target_base_angle = random.choice(valid_angles)
        full_rotations = random.randint(16, 24)
        self.total_rotations = full_rotations

        # Рассчитываем целевой угол (уходим в минус для вращения по часовой)
        self.target_angle = target_base_angle - 360 * full_rotations

        anim = Animation(
            angle=self.target_angle,
            duration=14.0,
            t='out_quad'
        )
        anim.bind(on_complete=self._on_spin_complete)
        anim.start(self.current_spinner)

        self.current_animation = anim
        self.spin_timer = Clock.schedule_once(self._force_stop_spin, 16.0)

        # Запускаем синхронизированный таймер вибрации
        self.start_vibration_sync()

    def start_vibration_sync(self):
        """Запускает синхронизированный таймер вибрации для точного отслеживания углов"""
        self.last_vibration_angle = None

        if self.game_type == 'classic':
            self.vibration_angles = [0, 120, 240]
        else:
            self.vibration_angles = [0, 72, 144, 216, 288]

        def check_angle(dt):
            if not self.is_spinning or not self.current_spinner:
                return

            # Получаем текущий угол
            current_angle = self.current_spinner.angle % 360
            if current_angle < 0:
                current_angle += 360

            # Проверяем каждый целевой угол
            for target_angle in self.vibration_angles:
                # Проверяем, прошли ли мы через этот угол
                if self.last_vibration_angle is not None:
                    # Проверяем пересечение угла
                    angle_passed = False

                    # При вращении по часовой (угол уменьшается)
                    old_angle = self.last_vibration_angle
                    new_angle = current_angle

                    # Нормализуем углы для сравнения
                    if old_angle > new_angle:
                        # Нормальное вращение по часовой (угол уменьшается)
                        if target_angle <= old_angle and target_angle >= new_angle:
                            angle_passed = True
                    else:
                        # Переход через 0 градусов
                        if target_angle <= old_angle and target_angle >= 0:
                            angle_passed = True
                        elif target_angle >= new_angle and target_angle <= 360:
                            angle_passed = True

                    if angle_passed:
                        self.vibrate_short()

            self.last_vibration_angle = current_angle

        self.vibration_check_timer = Clock.schedule_interval(check_angle, 0.02)  # 50 раз в секунду

    def _on_spin_complete(self, animation, widget):
        if not hasattr(self, 'layout') or not self.layout:
            return

        self.stop_vibration_check()

        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None

        if not widget or widget not in self.layout.children:
            return

        normalized_angle = widget.angle % 360
        if normalized_angle < 0:
            normalized_angle += 360

        if self.game_type == 'classic':
            valid_angles = [0, 120, 240]
        else:
            valid_angles = [0, 72, 144, 216, 288]

        closest_angle = min(valid_angles, key=lambda x: min(abs(x - normalized_angle), abs(x + 360 - normalized_angle)))
        widget.angle = closest_angle

        self._finish_spin()

    def stop_vibration_check(self):
        """Останавливает проверку углов для вибрации"""
        if self.vibration_check_timer:
            self.vibration_check_timer.cancel()
            self.vibration_check_timer = None
        self.last_vibration_angle = None

    def _force_stop_spin(self, dt):
        if not hasattr(self, 'layout') or not self.layout:
            return

        self.stop_vibration_check()

        if self.is_spinning and self.current_animation:
            self.current_animation.stop(self.current_spinner)

            normalized_angle = self.current_spinner.angle % 360
            if normalized_angle < 0:
                normalized_angle += 360

            if self.game_type == 'classic':
                valid_angles = [0, 120, 240]
            else:
                valid_angles = [0, 72, 144, 216, 288]

            closest_angle = min(valid_angles,
                                key=lambda x: min(abs(x - normalized_angle), abs(x + 360 - normalized_angle)))
            self.current_spinner.angle = closest_angle

            self._finish_spin()

        self.spin_timer = None

    def _finish_spin(self):
        self.is_spinning = False
        self.set_switch_button_state(True)
        self.stop_vibration_check()

        if self.spin_button:
            self.spin_button.is_active = 1
            self.spin_button.disabled = False

        if not self.current_spinner:
            return

        current_angle = self.current_spinner.angle % 360

        if self.game_type == 'classic':
            result = self.classic_angles.get(current_angle, 'scissors')
        else:
            result = self.extended_angles.get(current_angle, 'spock')

        self.show_result(result)
        self.play_result_sound(result)

    def show_result(self, result):
        result_names = {
            'rock': '🪨 КАМЕНЬ',
            'paper': '📄 БУМАГА',
            'scissors': '✂️ НОЖНИЦЫ',
            'lizard': '🦎 ЯЩЕРИЦА',
            'spock': '🖖 СПОК'
        }
        self.result_text = f"ВЫПАЛО: {result_names.get(result, '')}"

    def toggle_game_type(self, instance=None):
        if self.is_spinning:
            return

        self.stop_vibration_check()
        Animation.cancel_all(self)
        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None

        if self.game_type == 'classic':
            self.game_type = 'extended'
            if self.title_label:
                self.title_label.text = 'EXTENDED RSP'
        else:
            self.game_type = 'classic'
            if self.title_label:
                self.title_label.text = 'CLASSIC RSP'

        self.apply_current_game_type()

    def clear_ui(self):
        if not hasattr(self, 'layout') or not self.layout:
            return

        back_button = self.back_button

        for child in self.layout.children[:]:
            if child != self.bg_image and child != back_button:
                self.layout.remove_widget(child)

        self.spin_button = None
        self.title_label = None
        self.spinner_image_3 = None
        self.spinner_image_5 = None
        self.current_spinner = None
        self.winner_image = None

    def play_spin_sound(self):
        if self.sound_manager.is_muted():
            return

        from kivy.core.audio import SoundLoader

        sound_path = 'assets/sounds/rsp/spinner_14.ogg'

        if os.path.exists(sound_path):
            self.spin_sound = SoundLoader.load(sound_path)
            if self.spin_sound:
                self.spin_sound.volume = 0.7
                self.spin_sound.play()
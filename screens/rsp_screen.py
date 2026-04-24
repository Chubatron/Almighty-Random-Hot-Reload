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
        """Настраиваем графические инструкции для вращения вокруг центра"""
        with self.canvas.before:
            PushMatrix()
            self._rotate = Rotate(angle=self.angle, origin=self.center)
        with self.canvas.after:
            PopMatrix()

    def _update_angle(self, instance, value):
        """Обновляет угол вращения"""
        if self._rotate:
            self._rotate.angle = value

    def _update_origin(self, *args):
        """Обновляет центр вращения"""
        if self._rotate:
            self._rotate.origin = (self.center_x, self.center_y)


class RotatingImageWithShadow(FloatLayout):
    """Контейнер с двумя независимо вращающимися изображениями: тень и спиннер"""
    angle = NumericProperty(0)

    def __init__(self, name="", source=None, shadow_source=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.size_hint = (None, None)

        # Создаем тень (нижний слой) - силуэт
        self.shadow_image = RotatingImage(
            name=f"{name}_shadow",
            source=shadow_source if shadow_source else source,
            allow_stretch=True,
            keep_ratio=True,
            opacity=0.35,
            color=(0, 0, 0, 1)  # Черный цвет для силуэта
        )

        # Создаем основное изображение (верхний слой)
        self.main_image = RotatingImage(
            name=f"{name}_main",
            source=source,
            allow_stretch=True,
            keep_ratio=True,
            opacity=1
        )

        # Добавляем оба изображения в контейнер
        self.add_widget(self.shadow_image)
        self.add_widget(self.main_image)

        self.shadow_offset_y = 0

        self.bind(
            pos=self._update_position,
            size=self._update_size,
            angle=self._update_angle
        )

    def set_shadow_offset(self, offset_y):
        """Устанавливает смещение тени по Y (в пикселях)"""
        self.shadow_offset_y = offset_y
        self._update_position()

    def _update_angle(self, instance, value):
        """Обновляет угол вращения для обоих изображений"""
        self.shadow_image.angle = value
        self.main_image.angle = value

    def _update_position(self, *args):
        """Обновляет позицию изображений"""
        # Основное изображение - в центре контейнера
        self.main_image.center = (self.center_x, self.center_y)
        self.main_image.size = self.size

        # Тень - смещена вниз, ее центр вращения тоже смещен
        self.shadow_image.center = (self.center_x, self.center_y - self.shadow_offset_y)
        self.shadow_image.size = self.size

    def _update_size(self, *args):
        """Обновляет размер изображений"""
        self.main_image.size = self.size
        self.shadow_image.size = self.size
        self._update_position()


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
        """Обновляет изображение в зависимости от состояния is_active"""
        if self.is_active:
            if os.path.exists(self.green_button_path):
                self.source = self.green_button_path
                self.color = (1, 1, 1, 1)
            else:
                print(f"⚠️ Файл {self.green_button_path} не найден!")
                self.source = ''
                self.color = (0, 1, 0, 1)
        else:
            if os.path.exists(self.red_button_path):
                self.source = self.red_button_path
                self.color = (1, 1, 1, 1)
            else:
                print(f"⚠️ Файл {self.red_button_path} не найден!")
                self.source = ''
                self.color = (1, 0, 0, 1)


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

        self.type_switch_button = None
        self.spin_button = None
        self.title_label = None

        # Спиннеры
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

        self.spin_sound = None
        self.result_sounds = {}

        self.classic_angles = {
            0: 'scissors',
            120: 'paper',
            240: 'rock'
        }

        self.extended_angles = {
            0: 'spock',
            72: 'scissors',
            144: 'lizard',
            216: 'rock',
            288: 'paper'
        }

    def on_enter(self):
        """При входе на экран"""
        super().on_enter()

        self.is_spinning = False
        self.winner_image = None

        self.clear_ui()
        self.show_ui()
        self.load_result_sounds()
        self.reset_spinner()

        self.layout.bind(size=self.update_layout, pos=self.update_layout)
        Clock.schedule_once(lambda dt: self.update_layout(), 0.1)

    def on_leave(self):
        """При выходе с экрана"""
        self.stop_all_sounds()
        self.stop_spinner_animation()

        if self.spin_timer:
            self.spin_timer.cancel()
            self.spin_timer = None

        if hasattr(self, 'spin_button') and self.spin_button:
            self.spin_button.unbind(on_press=self.start_spin)

        if hasattr(self, 'type_switch_button') and self.type_switch_button:
            self.type_switch_button.unbind(on_press=self.toggle_game_type)

        if hasattr(self, 'layout'):
            self.layout.unbind(size=self.update_layout, pos=self.update_layout)

        self.spin_button = None
        self.title_label = None
        self.type_switch_button = None
        self.spinner_image_3 = None
        self.spinner_image_5 = None
        self.current_spinner = None
        self.winner_image = None

        super().on_leave()

    def stop_all_sounds(self):
        """Останавливает все звуки"""
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
        """Останавливает анимацию спиннера"""
        Animation.cancel_all(self)
        self.is_spinning = False

        if self.current_spinner:
            self.current_spinner.angle = 0

        if self.spin_button:
            self.spin_button.is_active = 1
            self.spin_button.disabled = False

    def set_switch_button_state(self, enabled):
        """Включить/выключить кнопку переключения"""
        if hasattr(self, 'type_switch_button') and self.type_switch_button:
            self.type_switch_button.disabled = not enabled
            self.type_switch_button.opacity = 1.0 if enabled else 0.5

    def reset_spinner(self):
        """Сбрасывает спиннер"""
        self.stop_all_sounds()
        self.stop_spinner_animation()

        if self.spinner_image_3:
            self.spinner_image_3.angle = 0
        if self.spinner_image_5:
            self.spinner_image_5.angle = 0

        print("🔄 Spinner reset to start position")

    def go_to_menu(self):
        """Возврат в меню"""
        self.stop_all_sounds()
        self.stop_spinner_animation()
        super().go_to_menu()

    def apply_current_game_type(self):
        """Применяет текущий тип игры"""
        if self.title_label:
            self.title_label.text = 'CLASSIC RSP' if self.game_type == 'classic' else 'EXTENDED RSP'

        if self.spinner_image_3:
            self.spinner_image_3.opacity = 0
            self.spinner_image_3.angle = 0
        if self.spinner_image_5:
            self.spinner_image_5.opacity = 0
            self.spinner_image_5.angle = 0

        if self.game_type == 'classic':
            if self.spinner_image_3:
                self.spinner_image_3.opacity = 1
                self.current_spinner = self.spinner_image_3
            print("Classic mode: showing spinner_3")
        else:
            if self.spinner_image_5:
                self.spinner_image_5.opacity = 1
                self.current_spinner = self.spinner_image_5
            print("Extended mode: showing spinner_5")

        self.recreate_spin_button()
        print(f"Applied game type: {self.game_type}")

    def update_layout(self, *args):
        """Обновляет параметры layout"""
        self.center_x = self.layout.width / 2
        self.center_y = self.layout.height / 2

        min_dimension = min(self.layout.width, self.layout.height)
        self.radius = min_dimension * 0.3

        spinner_size_3 = min_dimension * 1.1
        spinner_size_5 = min_dimension * 1.0

        # Вычисляем смещение тени: 5% от высоты экрана
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
        """Настраивает фон"""
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
        """Показать интерфейс с кнопкой переключения"""
        self.type_switch_button = ToggleButtonWithLabel(
            size_hint=(None, None),
            size=(150, 50),
            pos_hint={'center_x': 0.5, 'top': 0.95}
        )
        self.type_switch_button.icon.source = 'assets/images/buttons/Roulette_switch_button.png'
        self.type_switch_button.label.text = 'SWITCH'
        self.type_switch_button.bind(on_press=self.toggle_game_type)
        self.layout.add_widget(self.type_switch_button)

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
        """Создаёт кнопку SPIN с размером в зависимости от режима"""
        # Получаем ширину экрана
        screen_width = self.layout.width if self.layout else 400

        # Получаем размер виджета спиннера
        if self.game_type == 'classic' and self.spinner_image_3:
            spinner_size = self.spinner_image_3.width
        elif self.spinner_image_5:
            spinner_size = self.spinner_image_5.width
        else:
            spinner_size = 0
        print(f"Widget spiner size: {spinner_size}")

        # Размер кнопки = размер спиннера * коэффициент 1.15
        koef = 1.15
        button_size = (spinner_size * koef, spinner_size * koef)

        print(
            f"Создание кнопки SPIN: screen_width={screen_width}, spinner_size={spinner_size}, button_size={button_size}")

        self.spin_button = SpinButton(
            is_active=1,
            size=button_size
        )
        self.spin_button.bind(on_press=self.start_spin)
        self.layout.add_widget(self.spin_button)

    def recreate_spin_button(self):
        """Пересоздаёт кнопку SPIN с новым размером"""
        if self.spin_button:
            self.spin_button.unbind(on_press=self.start_spin)
            self.layout.remove_widget(self.spin_button)
            self.spin_button = None

        self.create_spin_button()
        if hasattr(self, 'center_x') and hasattr(self, 'center_y'):
            self.spin_button.center = (self.center_x, self.center_y)

    def create_spinner_images(self):
        """Создает изображения спиннеров с тенью (силуэтом)"""
        # Для классического режима (3 луча)
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
            print("Created spinner_3 image with shadow")

        # Для расширенного режима (5 лучей)
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
            print("Created spinner_5 image with shadow")

    def load_result_sounds(self):
        """Загружает звуки результатов"""
        sound_files = {
            'rock': 'assets/sounds/rsp/stone.ogg',
            'paper': 'assets/sounds/rsp/paper.ogg',
            'scissors': 'assets/sounds/rsp/scissors.ogg',
            'lizard': 'assets/sounds/rsp/lizard.ogg',
            'spock': 'assets/sounds/rsp/spock.ogg'
        }

        from kivy.core.audio import SoundLoader

        for key, path in sound_files.items():
            if os.path.exists(path):
                sound = SoundLoader.load(path)
                if sound:
                    sound.volume = 0.8
                    self.result_sounds[key] = sound
                    print(f"✅ Loaded sound: {path}")
                else:
                    print(f"⚠️ Failed to load sound: {path}")
            else:
                print(f"⚠️ Sound file not found: {path}")

    def play_result_sound(self, result):
        """Воспроизводит звук результата"""
        if result in self.result_sounds:
            sound = self.result_sounds[result]
            if self.spin_sound and self.spin_sound.state == 'play':
                self.spin_sound.stop()
                self.spin_sound = None
            sound.play()
            print(f"🔊 Playing result sound: {result}")

    def start_spin(self, instance):
        """Запускает вращение"""
        if self.is_spinning or not self.current_spinner:
            return

        print("🎡 Spin button pressed - starting rotation")

        self.set_switch_button_state(False)
        self.play_spin_sound()

        self.is_spinning = True
        self.result_text = "ВРАЩЕНИЕ..."

        self.spin_button.is_active = 0
        self.spin_button.disabled = True

        current_angle = self.current_spinner.angle % 360
        self.current_spinner.angle = current_angle

        if self.game_type == 'classic':
            valid_angles = [0, 120, 240]
        else:
            valid_angles = [0, 72, 144, 216, 288]

        target_base_angle = random.choice(valid_angles)
        full_rotations = random.randint(16, 24)

        target_angle = target_base_angle - 360 * full_rotations

        if current_angle < target_base_angle:
            target_angle -= 360

        print(f"Начальный угол: {current_angle}°, финальный: {target_angle}°")

        anim = Animation(
            angle=target_angle,
            duration=14.0,
            t='out_quad'
        )

        anim.bind(on_complete=self._on_spin_complete)
        anim.start(self.current_spinner)

        self.current_animation = anim
        self.spin_timer = Clock.schedule_once(self._force_stop_spin, 16.0)

    def _on_spin_complete(self, animation, widget):
        """Завершение вращения"""
        print("🛑 Спиннер остановился")

        if not hasattr(self, 'layout') or not self.layout:
            return

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

    def _force_stop_spin(self, dt):
        """Принудительная остановка"""
        print("⏰ Таймер: принудительная остановка спиннера")

        if not hasattr(self, 'layout') or not self.layout:
            return

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
        """Завершение вращения"""
        self.is_spinning = False
        self.set_switch_button_state(True)

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

        print(f"Результат по углу: {result}")
        self.show_result(result)
        self.play_result_sound(result)

    def show_result(self, result):
        """Показывает результат"""
        result_names = {
            'rock': '🪨 КАМЕНЬ',
            'paper': '📄 БУМАГА',
            'scissors': '✂️ НОЖНИЦЫ',
            'lizard': '🦎 ЯЩЕРИЦА',
            'spock': '🖖 СПОК'
        }
        self.result_text = f"ВЫПАЛО: {result_names.get(result, '')}"
        print(f"Result: {self.result_text}")

    def toggle_game_type(self, instance=None):
        """Переключение типа игры"""
        if self.is_spinning:
            print("Нельзя переключить режим во время вращения!")
            return

        print(f"\n=== SWITCHING GAME TYPE FROM {self.game_type} ===")

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
        print(f"Game type switched to: {self.game_type}")

    def clear_ui(self):
        """Очищает интерфейс"""
        if not hasattr(self, 'layout') or not self.layout:
            return

        back_button = self.back_button

        for child in self.layout.children[:]:
            if child != self.bg_image and child != back_button:
                self.layout.remove_widget(child)

        self.spin_button = None
        self.title_label = None
        self.type_switch_button = None
        self.spinner_image_3 = None
        self.spinner_image_5 = None
        self.current_spinner = None
        self.winner_image = None

    def play_spin_sound(self):
        """Воспроизводит звук вращения"""
        from kivy.core.audio import SoundLoader

        sound_path = 'assets/sounds/rsp/spinner_14.ogg'

        if os.path.exists(sound_path):
            self.spin_sound = SoundLoader.load(sound_path)
            if self.spin_sound:
                self.spin_sound.volume = 0.7
                self.spin_sound.play()
                print(f"🎵 Playing spin sound: {sound_path}")
            else:
                print(f"⚠️ Failed to load spin sound : {sound_path}")
        else:
            print(f"⚠️ Spin sound file not found: {sound_path}")
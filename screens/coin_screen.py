from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import NumericProperty, BooleanProperty, ColorProperty, ListProperty, StringProperty, \
    ObjectProperty
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Ellipse, Rectangle, Line, PushMatrix, PopMatrix, Rotate, Translate, \
    Scale
import random
import os
import math
from functools import partial

from screens.base_game_screen import BaseGameScreen


class AdaptiveBackground(Image):
    """Адаптивный фон для CoinScreen - растягивается на весь экран"""

    def __init__(self, source='', **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.allow_stretch = True
        self.keep_ratio = False
        self.size_hint = (1, 1)
        self.pos_hint = {'x': 0, 'y': 0}


class DustParticle(Widget):
    """Частица пыли/искры с анимацией"""
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    opacity = NumericProperty(1.0)
    size_factor = NumericProperty(1.0)
    color = ColorProperty((1, 1, 0.5, 0.8))
    glow_intensity = NumericProperty(1.0)
    target_glow = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (random.uniform(2, 5), random.uniform(2, 5))
        self.velocity_x = random.uniform(-30, 30)
        self.velocity_y = random.uniform(-30, 30)
        self.opacity = random.uniform(0.3, 0.8)
        self.color = (
            random.uniform(0.8, 1.0),
            random.uniform(0.5, 0.8),
            random.uniform(0.2, 0.4),
            self.opacity
        )
        self.glow_intensity = 1.0
        self.target_glow = 1.0
        self.x = random.uniform(0, Window.width)
        self.y = random.uniform(0, Window.height)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*self.color[:3], self.color[3] * self.glow_intensity)
            Ellipse(pos=self.pos, size=self.size)
            if self.glow_intensity > 0.3:
                glow_size = (self.size[0] * 3, self.size[1] * 3)
                glow_pos = (self.x - self.size[0], self.y - self.size[1])
                Color(*self.color[:3], self.color[3] * self.glow_intensity * 0.3)
                Ellipse(pos=glow_pos, size=glow_size)

    def update(self, dt):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        if random.random() < 0.05:
            self.velocity_x += random.uniform(-10, 10)
            self.velocity_y += random.uniform(-10, 10)
        max_speed = 50
        self.velocity_x = max(-max_speed, min(max_speed, self.velocity_x))
        self.velocity_y = max(-max_speed, min(max_speed, self.velocity_y))
        if self.x < -self.width:
            self.x = Window.width
        elif self.x > Window.width:
            self.x = -self.width
        if self.y < -self.height:
            self.y = Window.height
        elif self.y > Window.height:
            self.y = -self.height
        if abs(self.glow_intensity - self.target_glow) > 0.01:
            self.glow_intensity += (self.target_glow - self.glow_intensity) * 0.1


class ParticleSystem(Widget):
    """Система частиц для создания эффекта пыли/искр"""
    particles = ListProperty([])
    is_active = BooleanProperty(False)
    glow_mode = BooleanProperty(False)
    base_glow = NumericProperty(0.5)
    active_glow = NumericProperty(1.2)

    def __init__(self, num_particles=20, **kwargs):
        super().__init__(**kwargs)
        self.num_particles = num_particles
        self.update_clock = None
        self.bind(pos=self._update_all, size=self._update_all)
        self.create_particles()
        self.start_perpetual_motion()

    def create_particles(self):
        self.particles = []
        for _ in range(self.num_particles):
            particle = DustParticle()
            self.particles.append(particle)
            self.add_widget(particle)

    def start_perpetual_motion(self):
        self.is_active = True
        if not self.update_clock:
            self.update_clock = Clock.schedule_interval(self.update_particles, 1 / 60)

    def set_glow_mode(self, active=True):
        self.glow_mode = active
        target_glow = self.active_glow if active else self.base_glow
        for particle in self.particles:
            particle.target_glow = target_glow

    def update_particles(self, dt):
        if not self.is_active:
            return
        for particle in self.particles:
            particle.update(dt)
        if self.glow_mode and random.random() < 0.02:
            for particle in self.particles:
                particle.glow_intensity = min(particle.target_glow * 1.3, 2.0)

    def _update_all(self, *args):
        for particle in self.particles:
            particle._update_rect()

    def cleanup(self):
        self.is_active = False
        if self.update_clock:
            self.update_clock.cancel()
            self.update_clock = None
        self.particles = []
        self.clear_widgets()


class FullScreenTouchArea(Widget):
    """Область на весь экран для возврата монеты"""
    is_enabled = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.pos_hint = {'x': 0, 'y': 0}

    def on_touch_down(self, touch):
        if self.is_enabled and self.collide_point(*touch.pos):
            return True
        return super().on_touch_down(touch)


class TouchArea(Widget):
    """Область для нажатия с визуальной подсветкой"""
    highlight_color = ColorProperty((0, 1, 0, 0.3))
    is_pressed = BooleanProperty(False)
    is_enabled = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.touch_pos = (0, 0)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def on_touch_down(self, touch):
        if self.is_enabled and self.collide_point(*touch.pos):
            self.is_pressed = True
            self.touch_pos = touch.pos
            self.show_touch_feedback()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.is_enabled and self.collide_point(*touch.pos):
            self.is_pressed = False
            self.hide_touch_feedback()
            return True
        return super().on_touch_up(touch)

    def show_touch_feedback(self):
        self.canvas.clear()
        with self.canvas:
            Color(*self.highlight_color)
            Ellipse(pos=(self.touch_pos[0] - 40, self.touch_pos[1] - 40), size=(80, 80))
            Color(0, 1, 0, 0.8)
            Ellipse(pos=(self.touch_pos[0] - 40, self.touch_pos[1] - 40), size=(80, 80), width=2)
        Clock.schedule_once(lambda dt: self.hide_touch_feedback(), 0.3)

    def hide_touch_feedback(self):
        self.canvas.clear()

    def _update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.5, 0.5, 0.5, 0.1)
            Rectangle(pos=self.pos, size=self.size)


class SpritesheetCoin(Image):
    """Монета из спрайт-листа 12x9 (108 кадров)"""
    current_frame = NumericProperty(0)
    is_animating = BooleanProperty(False)
    frames = ListProperty([])
    rotation_angle = NumericProperty(-90)
    coin_mirror = NumericProperty(1)
    animation_range = ListProperty([0, 11])
    ellipse_offset_x = NumericProperty(0)
    ellipse_offset_y = NumericProperty(0)
    extra_offset_x = NumericProperty(0)
    extra_offset_y = NumericProperty(0)
    shadow_offset_x = NumericProperty(0)
    shadow_offset_y = NumericProperty(0)
    shadow_scale_y = NumericProperty(1)
    shadow_alpha = NumericProperty(0.6)
    frame_step = NumericProperty(1)
    spiral_factor = NumericProperty(1.0)
    coin_opacity = NumericProperty(1.0)
    current_spritesheet = StringProperty('')
    _updating = BooleanProperty(False)
    debug_mode = BooleanProperty(False)

    def __init__(self, spritesheet_paths=None, frame_width=64, frame_height=64,
                 cols=12, rows=9, total_frames=108, start_frame=0,
                 shadow_offset_x=0, shadow_offset_y=0,
                 shadow_scale_y=1.0, shadow_alpha=0.6, coin_opacity=1.0, debug=False, **kwargs):
        super().__init__(**kwargs)
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.cols = cols
        self.rows = rows
        self.total_frames = total_frames
        self.start_frame = start_frame
        self.anim_clock = None
        self.current_fps = 60
        self.spritesheet_paths = spritesheet_paths or {}
        self.frame_step = 1
        self.spiral_factor = 1.0
        self.coin_opacity = coin_opacity
        self.debug_mode = debug
        self.shadow_offset_x = shadow_offset_x
        self.shadow_offset_y = shadow_offset_y
        self.shadow_scale_y = shadow_scale_y
        self.shadow_alpha = shadow_alpha
        self.bind(texture=self._update_rotation)
        self.bind(pos=self._update_rotation, size=self._update_rotation)
        self.bind(rotation_angle=self._update_rotation)
        self.bind(ellipse_offset_x=self._update_position,
                  ellipse_offset_y=self._update_position,
                  extra_offset_x=self._update_position,
                  extra_offset_y=self._update_position)
        self.bind(coin_mirror=self._update_rotation)
        self.bind(spiral_factor=self._update_position)
        self.bind(coin_opacity=self._update_rotation)
        self.bind(shadow_offset_x=self._update_rotation,
                  shadow_offset_y=self._update_rotation,
                  shadow_scale_y=self._update_rotation,
                  shadow_alpha=self._update_rotation)

    def load_spritesheet(self, spritesheet_path):
        if not os.path.exists(spritesheet_path):
            return False
        try:
            img = CoreImage(spritesheet_path)
            texture = img.texture
            if not texture:
                return False
            tex_width, tex_height = texture.size
            frame_w = min(self.frame_width, tex_width // self.cols)
            frame_h = min(self.frame_height, tex_height // self.rows)
            frames = []
            for i in range(self.total_frames):
                row = i // self.cols
                col = i % self.cols
                x = col * frame_w
                y = (self.rows - 1 - row) * frame_h
                try:
                    frame = texture.get_region(x, y, frame_w, frame_h)
                    frames.append(frame)
                except Exception as e:
                    pass
            self.frames = frames
            self.current_spritesheet = spritesheet_path
            if self.frames and 0 <= self.start_frame < len(self.frames):
                self.texture = self.frames[self.start_frame]
            return True
        except Exception as e:
            return False

    def set_animation_range(self, start_frame, end_frame):
        if not self.frames:
            return
        start_frame = max(0, min(start_frame, len(self.frames) - 1))
        end_frame = max(0, min(end_frame, len(self.frames) - 1))
        if start_frame > end_frame:
            start_frame, end_frame = end_frame, start_frame
        self.animation_range = [start_frame, end_frame]

    def _update_rotation(self, *args):
        if not self.texture:
            return
        if self.width <= 0 or self.height <= 0 or (self.x == 0 and self.y == 0):
            Clock.schedule_once(lambda dt: self._update_rotation(), 0.1)
            return
        if self._updating:
            return
        self._updating = True
        self.canvas.clear()
        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2
        with self.canvas:
            PushMatrix()
            Translate(center_x, center_y)
            Rotate(angle=self.rotation_angle, origin=(0, 0))
            Translate(self.shadow_offset_x, self.shadow_offset_y)
            Scale(1, -abs(self.shadow_scale_y), 1)
            Translate(-center_x, -center_y)
            Color(0, 0, 0, self.shadow_alpha)
            Rectangle(texture=self.texture, pos=self.pos, size=self.size)
            PopMatrix()
            PushMatrix()
            Translate(center_x, center_y)
            Scale(self.coin_mirror, 1, 1)
            Rotate(angle=self.rotation_angle, origin=(0, 0))
            Translate(-center_x, -center_y)
            Color(1.3, 1.3, 1.3, self.coin_opacity)
            Rectangle(texture=self.texture, pos=self.pos, size=self.size)
            PopMatrix()
        self._updating = False

    def _update_position(self, *args):
        base_center_x = 0.35
        base_center_y = 0.5
        current_offset_x = self.ellipse_offset_x * self.spiral_factor
        current_offset_y = self.ellipse_offset_y * self.spiral_factor
        self.pos_hint = {
            'center_x': base_center_x + current_offset_x + (self.extra_offset_x / Window.width),
            'center_y': base_center_y + current_offset_y + (self.extra_offset_y / Window.height)
        }
        Clock.schedule_once(lambda dt: self._update_rotation(), 0.05)

    def start_animation(self, fps=60, frame_step=1):
        if not self.frames or self.is_animating:
            return
        self.is_animating = True
        self.current_fps = fps
        self.frame_step = max(1, frame_step)
        self.current_frame = self.animation_range[0]
        self.frame_duration = 1.0 / fps
        if self.anim_clock:
            self.anim_clock.cancel()
        self.anim_clock = Clock.schedule_interval(self.next_frame, self.frame_duration)

    def next_frame(self, dt):
        if not self.is_animating or not self.frames:
            return
        next_frame = self.current_frame + self.frame_step
        if next_frame > self.animation_range[1]:
            range_size = self.animation_range[1] - self.animation_range[0] + 1
            next_frame = self.animation_range[0] + ((next_frame - self.animation_range[0]) % range_size)
        elif next_frame < self.animation_range[0]:
            range_size = self.animation_range[1] - self.animation_range[0] + 1
            next_frame = self.animation_range[1] - ((self.animation_range[1] - next_frame) % range_size)
        next_frame = max(self.animation_range[0], min(next_frame, self.animation_range[1]))
        self.current_frame = next_frame
        self.texture = self.frames[self.current_frame]
        self._update_rotation()

    def stop_animation(self):
        self.is_animating = False
        if self.anim_clock:
            self.anim_clock.cancel()
            self.anim_clock = None

    def set_result(self, result):
        if not self.frames:
            return
        self.stop_animation()
        frame_index = 107
        self.texture = self.frames[frame_index]
        self.canvas.clear()
        Clock.schedule_once(lambda dt: self._force_redraw(), 0.01)

    def _force_redraw(self):
        self._updating = False
        self._update_rotation()

    def reset_to_first_animation(self, start_frame=0):
        self.stop_animation()
        self.set_animation_range(0, min(11, len(self.frames) - 1))
        self.extra_offset_x = 0
        self.extra_offset_y = 0
        self.ellipse_offset_x = 0
        self.ellipse_offset_y = 0
        self.spiral_factor = 1.0
        self.coin_opacity = 1.0
        if 0 <= start_frame < len(self.frames):
            self.texture = self.frames[start_frame]
        Clock.schedule_once(lambda dt: self._update_rotation(), 0.02)

    def cleanup(self):
        self.stop_animation()
        self.frames = []
        self.texture = None
        self.canvas.clear()


class FinalSpritesheetCoin(Image):
    """Монета для финальной анимации из спрайт-листа 6x6 (36 кадров) с тенью"""
    current_frame = NumericProperty(0)
    is_animating = BooleanProperty(False)
    frames = ListProperty([])
    rotation_angle = NumericProperty(270)

    # Параметры тени
    shadow_offset_x = NumericProperty(0)
    shadow_offset_y = NumericProperty(0)
    shadow_scale_y = NumericProperty(1)
    shadow_alpha = NumericProperty(0.6)
    coin_opacity = NumericProperty(1.0)

    debug_mode = BooleanProperty(False)
    _updating = BooleanProperty(False)

    def __init__(self, spritesheet_path, frame_width=128, frame_height=128,
                 cols=6, rows=6, total_frames=36, start_frame=0,
                 shadow_offset_x=0, shadow_offset_y=0,
                 shadow_scale_y=1.0, shadow_alpha=0.6, coin_opacity=1.0, debug=False, **kwargs):
        super().__init__(**kwargs)
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.cols = cols
        self.rows = rows
        self.total_frames = total_frames
        self.start_frame = start_frame
        self.anim_clock = None
        self.current_fps = 60
        self.debug_mode = debug
        self.shadow_offset_x = shadow_offset_x
        self.shadow_offset_y = shadow_offset_y
        self.shadow_scale_y = shadow_scale_y
        self.shadow_alpha = shadow_alpha
        self.coin_opacity = coin_opacity

        self.load_spritesheet(spritesheet_path)

        self.bind(texture=self._update_display)
        self.bind(pos=self._update_display, size=self._update_display)
        self.bind(shadow_offset_x=self._update_display,
                  shadow_offset_y=self._update_display,
                  shadow_scale_y=self._update_display,
                  shadow_alpha=self._update_display,
                  coin_opacity=self._update_display)

    def load_spritesheet(self, spritesheet_path):
        if not os.path.exists(spritesheet_path):
            return False
        try:
            img = CoreImage(spritesheet_path)
            texture = img.texture
            if not texture:
                return False
            tex_width, tex_height = texture.size
            frame_w = min(self.frame_width, tex_width // self.cols)
            frame_h = min(self.frame_height, tex_height // self.rows)
            frames = []
            for i in range(self.total_frames):
                row = i // self.cols
                col = i % self.cols
                x = col * frame_w
                y = (self.rows - 1 - row) * frame_h
                try:
                    frame = texture.get_region(x, y, frame_w, frame_h)
                    frames.append(frame)
                except Exception as e:
                    pass
            self.frames = frames
            if self.frames and 0 <= self.start_frame < len(self.frames):
                self.texture = self.frames[self.start_frame]
            return True
        except Exception as e:
            return False

    def start_animation(self, fps=30, loop=False):
        if not self.frames or self.is_animating:
            return
        self.is_animating = True
        self.current_fps = fps
        self.current_frame = 0
        self.loop = loop
        self.frame_duration = 1.0 / fps
        if self.anim_clock:
            self.anim_clock.cancel()
        self.anim_clock = Clock.schedule_interval(self.next_frame, self.frame_duration)

    def next_frame(self, dt):
        if not self.is_animating or not self.frames:
            return
        next_frame = self.current_frame + 1
        if next_frame >= len(self.frames):
            if self.loop:
                next_frame = 0
            else:
                self.stop_animation()
                return
        self.current_frame = next_frame
        self.texture = self.frames[self.current_frame]
        self._update_display()

    def stop_animation(self):
        self.is_animating = False
        if self.anim_clock:
            self.anim_clock.cancel()
            self.anim_clock = None

    def _update_display(self, *args):
        """Обновляет отображение с поворотом на 270 градусов и тенью"""
        if not self.texture:
            return
        if self.width <= 0 or self.height <= 0:
            return
        if self._updating:
            return
        self._updating = True

        self.canvas.clear()

        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2

        with self.canvas:
            # ===== ТЕНЬ (смещена по оси X) =====
            PushMatrix()
            Translate(center_x, center_y)
            Rotate(angle=self.rotation_angle, origin=(0, 0))
            Translate(self.shadow_offset_x, self.shadow_offset_y)
            Scale(1, -abs(self.shadow_scale_y), 1)
            Translate(-center_x, -center_y)

            Color(0, 0, 0, self.shadow_alpha)
            Rectangle(texture=self.texture, pos=self.pos, size=self.size)
            PopMatrix()

            # ===== МОНЕТА =====
            PushMatrix()
            Translate(center_x, center_y)
            Rotate(angle=self.rotation_angle, origin=(0, 0))
            Translate(-center_x, -center_y)

            Color(1.3, 1.3, 1.3, self.coin_opacity)
            Rectangle(texture=self.texture, pos=self.pos, size=self.size)
            PopMatrix()

        self._updating = False

    def cleanup(self):
        self.stop_animation()
        self.frames = []
        self.texture = None
        self.canvas.clear()


class CoinScreen(BaseGameScreen):
    """Игровой экран с монетой из спрайт-листов 12x9 (108 кадров)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.adaptive_background = None

        self.spritesheet_path_1 = 'assets/sprites/coin_spritesheet_1.png'
        self.spritesheet_path_2 = 'assets/sprites/coin_spritesheet_2.png'
        self.final_spritesheet_orel = 'assets/sprites/orel_spritesheet.png'
        self.final_spritesheet_reshka = 'assets/sprites/reshka_spritesheet.png'
        self.orel_image = 'assets/sprites/orel.png'
        self.reshka_image = 'assets/sprites/reshka.png'

        self.coin = None
        self.final_coin = None
        self.touch_area = None
        self.fullscreen_touch_area = None
        self.info_label = None
        self.stats_label = None
        self.flip_sound = None
        self.crystal_sound = None
        self.particle_system = None
        self.return_animation_active = False
        self.is_animating = False

        self.current_side = 0
        self.total_flips = 0
        self.heads_count = 0
        self.tails_count = 0
        self.coin_start_frame = 0
        self.coin_start_side = 0

        self.coin_height = 55
        self.final_coin_size = 220
        self.initial_shadow_offset = -53.35
        self.current_shadow_offset = -53.35
        self.shadow_reduction_factor = 11

        self.ellipse_radius_x = 0.2
        self.ellipse_radius_y = 0.4
        self.start_offset_x = -0.2
        self.start_offset_y = 0

        self.final_offset_x_pixels = -18.15

        self.center_pos_x = 0.35
        self.center_pos_y = 0.5
        self.start_pos_x = self.center_pos_x - self.ellipse_radius_x
        self.start_pos_y = self.center_pos_y

        self.debug_mode = True

    def get_screen_size(self):
        """Получает актуальный размер экрана в пикселях"""
        from kivy.utils import platform

        if platform == 'android':
            width, height = Window.system_size
        else:
            if self.screen_params:
                width = self.screen_params.width
                height = self.screen_params.height
            else:
                width = Window.width
                height = Window.height

        return width, height

    def calculate_ellipse_params(self):
        """
        Рассчитывает параметры эллипса в относительных координатах
        Длинная ось (вертикальная) = 80% от высоты экрана
        Короткая ось (горизонтальная) = 40% от ширины экрана
        """
        screen_width, screen_height = self.get_screen_size()

        radius_y = 0.35
        radius_x = 0.2

        aspect_ratio = screen_width / screen_height

        if aspect_ratio > 1.5:
            radius_x = min(radius_x * 1.2, 0.35)
        elif aspect_ratio < 0.7:
            radius_y = min(radius_y * 1.2, 0.55)

        print(f"[DEBUG] Screen: {screen_width}x{screen_height}, aspect={aspect_ratio:.2f}")
        print(f"[DEBUG] Ellipse radius: x={radius_x:.3f}, y={radius_y:.3f}")

        return radius_x, radius_y

    def calculate_coin_size(self):
        """Рассчитывает размер монеты в зависимости от ширины экрана"""
        screen_width, screen_height = self.get_screen_size()
        base_width = 400
        base_coin_size = 55
        scale = screen_width / base_width
        coin_size = base_coin_size * scale
        coin_size = max(40, min(coin_size, 120))
        print(f"[DEBUG] Coin size: {coin_size:.1f}px")
        return coin_size

    def calculate_shadow_offset(self, coin_height):
        """Рассчитывает смещение тени в зависимости от размера монеты"""
        shadow_offset = -coin_height * 0.97 + coin_height * 0.13
        return shadow_offset

    def calculate_final_coin_size(self, coin_height):
        """Рассчитывает размер финальной монеты (в 4 раза больше)"""
        return coin_height * 4

    def calculate_final_offset(self, coin_height):
        """Рассчитывает смещение для финального этапа"""
        return -coin_height * 0.33

    def on_enter(self):
        """При входе на экран"""
        if not self.adaptive_background:
            self.adaptive_background = AdaptiveBackground(
                source='assets/backgrounds/coin_bg.png'
            )
            self.layout.add_widget(self.adaptive_background, index=0)

        super().on_enter()

        if hasattr(self, 'bg_image') and self.bg_image:
            if self.bg_image in self.layout.children:
                self.layout.remove_widget(self.bg_image)
            self.bg_image = None

        self.setup_game_ui()
        self.load_flip_sound()
        self.load_crystal_sound()
        Window.bind(on_resize=self.on_window_resize)

        if self.coin:
            self.coin.stop_animation()
            Animation.cancel_all(self.coin)

            if self.current_side == 0:
                self.coin.load_spritesheet(self.spritesheet_path_1)
            else:
                self.coin.load_spritesheet(self.spritesheet_path_2)

            if self.coin.frames and len(self.coin.frames) > 0:
                self.coin.texture = self.coin.frames[0]

            self.coin.pos_hint = {'center_x': self.start_pos_x, 'center_y': self.start_pos_y}
            self.coin.size = (self.coin_height, self.coin_height)
            self.coin.opacity = 1
            self.coin.shadow_offset_x = 0
            self.coin.shadow_offset_y = self.initial_shadow_offset
            self.coin.shadow_scale_y = 1.0
            self.coin.shadow_alpha = 0.5
            self.coin.ellipse_offset_x = -self.ellipse_radius_x
            self.coin.ellipse_offset_y = 0
            self.coin.spiral_factor = 1.0
            self.coin.extra_offset_x = 0
            self.coin._update_position()
            self.coin._update_rotation()

        if self.final_coin:
            self.final_coin.stop_animation()
            Animation.cancel_all(self.final_coin)
            self.final_coin.opacity = 0

        self.is_animating = False
        self.return_animation_active = False

        if self.fullscreen_touch_area:
            self.fullscreen_touch_area.is_enabled = False

        if self.touch_area:
            self.touch_area.is_enabled = True

        if self.particle_system:
            self.particle_system.set_glow_mode(False)

    def on_leave(self):
        super().on_leave()
        self.cleanup_all()
        Window.unbind(on_resize=self.on_window_resize)

    def cleanup_all(self):
        if self.coin:
            Animation.cancel_all(self.coin)
            self.coin.cleanup()
            if self.coin in self.layout.children:
                self.layout.remove_widget(self.coin)
            self.coin = None

        if self.final_coin:
            Animation.cancel_all(self.final_coin)
            self.final_coin.cleanup()
            if self.final_coin in self.layout.children:
                self.layout.remove_widget(self.final_coin)
            self.final_coin = None

        if self.particle_system:
            self.particle_system.cleanup()
            if self.particle_system in self.layout.children:
                self.layout.remove_widget(self.particle_system)
            self.particle_system = None

        if self.touch_area and self.touch_area in self.layout.children:
            self.layout.remove_widget(self.touch_area)
            self.touch_area = None

        if self.fullscreen_touch_area and self.fullscreen_touch_area in self.layout.children:
            self.layout.remove_widget(self.fullscreen_touch_area)
            self.fullscreen_touch_area = None

        if self.flip_sound:
            self.flip_sound.stop()
            self.flip_sound.unload()
            self.flip_sound = None

        if self.crystal_sound:
            self.crystal_sound.stop()
            self.crystal_sound.unload()
            self.crystal_sound = None

        self.is_animating = False
        self.return_animation_active = False

    def on_window_resize(self, instance, width, height):
        """При изменении размера окна пересчитываем параметры"""
        if self.coin:
            new_radius_x, new_radius_y = self.calculate_ellipse_params()

            if abs(self.ellipse_radius_x - new_radius_x) > 0.01:
                self.ellipse_radius_x = new_radius_x
                self.ellipse_radius_y = new_radius_y
                self.start_pos_x = self.center_pos_x - self.ellipse_radius_x

                if not self.coin.is_animating:
                    self.coin.ellipse_offset_x = -self.ellipse_radius_x
                    self.coin._update_position()

            new_coin_size = self.calculate_coin_size()

            if abs(self.coin.size[0] - new_coin_size) > 1:
                self.coin.size = (new_coin_size, new_coin_size)
                self.coin_height = new_coin_size
                self.final_coin_size = self.calculate_final_coin_size(new_coin_size)
                self.initial_shadow_offset = self.calculate_shadow_offset(new_coin_size)
                self.coin.shadow_offset_y = self.initial_shadow_offset
                self.final_offset_x_pixels = self.calculate_final_offset(new_coin_size)

                if self.touch_area:
                    touch_area_size = min(0.4, 0.4 * (width / 400))
                    self.touch_area.size_hint = (touch_area_size, touch_area_size)
                    self.touch_area.pos_hint = {'center_x': self.start_pos_x, 'center_y': self.start_pos_y}

                Clock.schedule_once(lambda dt: self.coin._update_rotation(), 0.1)

    def check_file(self, path):
        return os.path.exists(path)

    def load_flip_sound(self):
        sound_path = 'assets/sounds/coin/coin_13s.ogg'
        if os.path.exists(sound_path):
            self.flip_sound = SoundLoader.load(sound_path)
            if self.flip_sound:
                self.flip_sound.volume = 0.7

    def load_crystal_sound(self):
        sound_path = 'assets/sounds/coin/crystal.ogg'
        if os.path.exists(sound_path):
            self.crystal_sound = SoundLoader.load(sound_path)
            if self.crystal_sound:
                self.crystal_sound.volume = 1.0
                print("✅ Загружен звук crystal.ogg")
        else:
            print("⚠️ Файл crystal.ogg не найден")

    def play_flip_sound(self):
        if self.flip_sound:
            try:
                if self.flip_sound.state == 'play':
                    self.flip_sound.stop()
                self.flip_sound.play()
            except:
                pass

    def stop_flip_sound(self):
        if self.flip_sound and self.flip_sound.state == 'play':
            self.flip_sound.stop()

    def play_crystal_sound(self):
        if self.crystal_sound:
            try:
                if self.crystal_sound.state == 'play':
                    self.crystal_sound.stop()
                self.crystal_sound.play()
                print("🔊 Воспроизводится crystal.ogg")
            except Exception as e:
                print(f"⚠️ Ошибка воспроизведения crystal.ogg: {e}")

    def stop_crystal_sound(self):
        if self.crystal_sound and self.crystal_sound.state == 'play':
            self.crystal_sound.stop()

    def setup_game_ui(self):
        self.check_file(self.spritesheet_path_1)
        self.check_file(self.spritesheet_path_2)
        self.check_file(self.final_spritesheet_orel)
        self.check_file(self.final_spritesheet_reshka)
        self.check_file(self.orel_image)
        self.check_file(self.reshka_image)

        screen_width, screen_height = self.get_screen_size()

        self.ellipse_radius_x, self.ellipse_radius_y = self.calculate_ellipse_params()
        self.start_pos_x = self.center_pos_x - self.ellipse_radius_x

        self.coin_height = self.calculate_coin_size()
        self.final_coin_size = self.calculate_final_coin_size(self.coin_height)
        self.initial_shadow_offset = self.calculate_shadow_offset(self.coin_height)
        self.final_offset_x_pixels = self.calculate_final_offset(self.coin_height)

        self.current_side = random.randint(0, 1)

        if self.current_side == 0:
            self.coin_start_side = 0
            self.coin_start_frame = 0
            initial_spritesheet = self.spritesheet_path_1
        else:
            self.coin_start_side = 1
            self.coin_start_frame = 0
            initial_spritesheet = self.spritesheet_path_2

        if hasattr(self, 'menu_button') and self.menu_button:
            self.menu_button.pos_hint = {'x': 0.02, 'top': 0.98}
            self.menu_button.size_hint = (None, None)
            self.menu_button.size = (100, 50)

        spritesheet_paths = {
            'heads': self.spritesheet_path_1,
            'tails': self.spritesheet_path_2
        }

        self.coin = SpritesheetCoin(
            spritesheet_paths=spritesheet_paths,
            frame_width=128,
            frame_height=128,
            cols=12,
            rows=9,
            total_frames=108,
            start_frame=self.coin_start_frame,
            rotation_angle=-90,
            size_hint=(None, None),
            size=(self.coin_height, self.coin_height),
            pos_hint={'center_x': self.start_pos_x, 'center_y': self.start_pos_y},
            allow_stretch=True,
            shadow_offset_x=0,
            shadow_offset_y=self.initial_shadow_offset,
            shadow_scale_y=1.0,
            shadow_alpha=0.5,
            coin_opacity=1.0,
            debug=self.debug_mode
        )

        self.coin.load_spritesheet(initial_spritesheet)

        if self.coin.frames and len(self.coin.frames) > 0:
            self.coin.texture = self.coin.frames[0]

        self.coin.ellipse_offset_x = -self.ellipse_radius_x
        self.coin.ellipse_offset_y = 0
        self.coin.spiral_factor = 1.0

        self.layout.add_widget(self.coin)

        # СОЗДАЕМ ФИНАЛЬНУЮ МОНЕТУ С ПОДДЕРЖКОЙ ТЕНИ
        self.final_coin = FinalSpritesheetCoin(
            spritesheet_path=self.final_spritesheet_orel,
            frame_width=128,
            frame_height=128,
            cols=6,
            rows=6,
            total_frames=36,
            start_frame=0,
            size_hint=(None, None),
            size=(self.final_coin_size, self.final_coin_size),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            shadow_offset_x=0,
            shadow_offset_y=self.initial_shadow_offset,
            shadow_scale_y=1.0,
            shadow_alpha=0.5,
            coin_opacity=1.0,
            opacity=0,
            debug=self.debug_mode
        )
        self.layout.add_widget(self.final_coin)

        self.particle_system = ParticleSystem(num_particles=30)
        self.layout.add_widget(self.particle_system)

        self.fullscreen_touch_area = FullScreenTouchArea()
        self.fullscreen_touch_area.is_enabled = False
        self.layout.add_widget(self.fullscreen_touch_area)
        self.fullscreen_touch_area.bind(on_touch_down=self.on_fullscreen_touch)

        touch_area_size = min(0.4, 0.4 * (screen_width / 400))
        self.touch_area = TouchArea(
            size_hint=(touch_area_size, touch_area_size),
            pos_hint={'center_x': self.start_pos_x, 'center_y': self.start_pos_y},
        )
        self.layout.add_widget(self.touch_area)
        self.touch_area.bind(on_touch_down=self.on_area_touch)

    def on_fullscreen_touch(self, instance, touch):
        if instance.is_enabled and instance.collide_point(*touch.pos):
            self.return_coin_to_start()
            return True
        return False

    def create_spiral_animation(self, duration=8.0, rotations=3):
        anim = Animation(duration=0)
        steps = 60
        step_duration = duration / steps
        start_angle = math.pi
        end_angle = start_angle + (2 * math.pi * rotations)

        for i in range(1, steps + 1):
            t = i / steps
            current_angle = start_angle + (end_angle - start_angle) * t
            x_offset = self.ellipse_radius_x * math.cos(current_angle)
            y_offset = self.ellipse_radius_y * math.sin(current_angle)
            spiral_factor = 1.0 - t

            step_anim = Animation(
                ellipse_offset_x=x_offset,
                ellipse_offset_y=y_offset,
                spiral_factor=spiral_factor,
                duration=step_duration,
                t='linear'
            )
            anim += step_anim

        return anim

    def on_area_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if self.is_animating:
                return True
            if self.final_coin and self.final_coin.opacity == 1 and not self.final_coin.is_animating:
                self.return_coin_to_start()
                return True
            elif not self.coin.is_animating and not self.final_coin.is_animating:
                self.flip_coin()
                return True
        return False

    def set_animating_state(self, animating):
        self.is_animating = animating
        if self.touch_area:
            self.touch_area.is_enabled = not animating

    def flip_coin(self):
        if self.coin.is_animating:
            return

        self.set_animating_state(True)
        if self.fullscreen_touch_area:
            self.fullscreen_touch_area.is_enabled = False

        if self.final_coin:
            self.final_coin.stop_animation()
            self.final_coin.opacity = 0

        self.play_flip_sound()

        if self.particle_system:
            self.particle_system.set_glow_mode(True)

        result = random.randint(0, 1)

        if result == 0:
            spritesheet_to_use = self.spritesheet_path_1
            self.heads_count += 1
        else:
            spritesheet_to_use = self.spritesheet_path_2
            self.tails_count += 1

        self.total_flips += 1
        self.coin.load_spritesheet(spritesheet_to_use)
        self.coin.reset_to_first_animation(0)
        self.coin.shadow_offset_y = self.initial_shadow_offset
        self.current_shadow_offset = self.initial_shadow_offset
        self.coin.ellipse_offset_x = -self.ellipse_radius_x
        self.coin.ellipse_offset_y = 0
        self.coin.spiral_factor = 1.0
        self.coin.extra_offset_x = 0

        base_fps = 50
        base_frame_step = 1
        spiral_duration = 8.0
        center_rotation_duration = 2.0
        rotations = 3

        self.coin.set_animation_range(0, 11)
        self.coin.start_animation(fps=base_fps, frame_step=base_frame_step)

        spiral_anim = self.create_spiral_animation(spiral_duration, rotations)

        def on_spiral_complete(animation, coin):
            if self.coin is not None and not self.return_animation_active:
                self.start_center_rotation(result, base_fps, base_frame_step,
                                           center_rotation_duration)

        spiral_anim.bind(on_complete=on_spiral_complete)
        spiral_anim.start(self.coin)

    def start_center_rotation(self, result, fps, frame_step, duration):
        if self.coin is None:
            return
        self.coin.spiral_factor = 0
        self.coin.set_animation_range(0, 11)
        self.coin.start_animation(fps=fps, frame_step=frame_step)
        Clock.schedule_once(lambda dt: self.start_final_rotation_with_offset(result, fps, frame_step)
        if self.coin is not None and not self.return_animation_active else None, duration)

    def start_final_rotation_with_offset(self, result, fps, frame_step):
        if self.coin is None:
            return
        self.coin.stop_animation()
        self.coin.set_animation_range(12, 107)
        frames_to_play = 96
        frame_duration = 1.0 / fps
        total_duration = frames_to_play * frame_duration
        self.coin.current_frame = 12
        self.coin.texture = self.coin.frames[12]

        offset_anim = Animation(
            extra_offset_x=self.final_offset_x_pixels,
            duration=total_duration,
            t='linear'
        )

        target_shadow_offset = self.initial_shadow_offset * 0.1
        shadow_anim = Animation(
            shadow_offset_y=target_shadow_offset,
            duration=total_duration,
            t='linear'
        )

        self.coin.is_animating = True

        def update_frame(dt):
            if not self.coin.is_animating or self.coin is None:
                return False
            next_frame = self.coin.current_frame + 1
            if next_frame > 107:
                self.coin.is_animating = False
                self.finish_rotation(result)
                return False
            self.coin.current_frame = next_frame
            self.coin.texture = self.coin.frames[next_frame]
            self.coin._update_rotation()
            return True

        frame_interval = 1.0 / fps
        Clock.schedule_interval(update_frame, frame_interval)

        def on_anim_complete(animation, coin):
            pass

        offset_anim.bind(on_complete=on_anim_complete)
        offset_anim.start(self.coin)
        shadow_anim.start(self.coin)

        Clock.schedule_once(lambda dt: self.finish_rotation(result)
        if self.coin is not None and self.coin.is_animating else None, total_duration + 0.1)

    def finish_rotation(self, result):
        if self.coin is None:
            return
        if self.coin:
            self.coin.stop_animation()
            # НЕ ВОССТАНАВЛИВАЕМ ВИДИМОСТЬ МОНЕТЫ! Она будет скрыта в start_final_animation
            # self.coin.opacity = 1  <- УБИРАЕМ ЭТУ СТРОКУ
        Clock.schedule_once(lambda dt: self.start_final_animation(result)
        if self.coin is not None and not self.return_animation_active else None, 0.5)

    def start_final_animation(self, result):
        """Запускает финальную анимацию - монета увеличивается, тень смещается по оси X"""
        if self.final_coin is None:
            return

        # СРАЗУ СКРЫВАЕМ ОСНОВНУЮ МОНЕТУ
        if self.coin:
            self.coin.opacity = 0

        # Запускаем звук
        self.play_crystal_sound()

        # Выбираем нужный спрайт-лист
        if result == 0:
            final_spritesheet = self.final_spritesheet_orel
        else:
            final_spritesheet = self.final_spritesheet_reshka

        # Загружаем спрайт-лист
        self.final_coin.load_spritesheet(final_spritesheet)

        # Сбрасываем параметры финальной монеты
        self.final_coin.opacity = 1
        self.final_coin.size = (self.coin_height, self.coin_height)
        self.final_coin.pos_hint = {'center_x': self.center_pos_x, 'center_y': self.center_pos_y}

        # Устанавливаем параметры тени (смещение по оси X)
        self.final_coin.shadow_offset_x = 0
        self.final_coin.shadow_offset_y = self.initial_shadow_offset
        self.final_coin.shadow_scale_y = 1.0
        self.final_coin.shadow_alpha = 0.5
        self.final_coin.coin_opacity = 1.0

        # Принудительно обновляем позицию
        self.final_coin.pos = self.final_coin.pos
        self.final_coin.size = self.final_coin.size

        # Длительность анимации
        animation_duration = 1.5
        target_size = self.final_coin_size

        # Запускаем анимацию кадров
        frame_fps = 36 / animation_duration
        self.final_coin.start_animation(fps=frame_fps, loop=False)

        # Анимация монеты (без изменений)
        grow_anim = Animation(
            size=(target_size, target_size),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            duration=animation_duration,
            t='linear'
        )

        # АНИМАЦИЯ ТЕНИ: смещается по оси X (влево)
        shadow_move_anim = Animation(
            shadow_offset_y=-self.coin_height * 15,  # Смещаем тень влево по оси Y
            shadow_alpha=0.5,  # Тень становится прозрачнее
            duration=animation_duration,
            t='linear'
        )

        def on_grow_complete(animation, coin):
            if self.particle_system:
                self.particle_system.set_glow_mode(False)
            self.set_animating_state(False)
            if self.fullscreen_touch_area:
                self.fullscreen_touch_area.is_enabled = True

        grow_anim.bind(on_complete=on_grow_complete)
        grow_anim.start(self.final_coin)
        shadow_move_anim.start(self.final_coin)

        self.stop_flip_sound()
        self.current_side = result

    def return_coin_to_start(self):
        """Возвращает монету в исходное положение с анимацией тени"""
        self.set_animating_state(True)
        if self.fullscreen_touch_area:
            self.fullscreen_touch_area.is_enabled = False
        self.return_animation_active = True
        self.stop_crystal_sound()

        if self.final_coin:
            self.final_coin.stop_animation()
            self.final_coin.opacity = 0

        if self.coin:
            self.coin.opacity = 1
            if self.current_side == 0:
                self.coin.load_spritesheet(self.spritesheet_path_1)
            else:
                self.coin.load_spritesheet(self.spritesheet_path_2)

            if self.coin.frames and len(self.coin.frames) > 0:
                self.coin.texture = self.coin.frames[0]

            # Сначала устанавливаем тень ДАЛЕКО ЗА ПРЕДЕЛЫ ЭКРАНА (сверху)
            self.coin.shadow_offset_x = 0
            self.coin.shadow_offset_y = -Window.height
            self.coin.shadow_scale_y = 1.0
            self.coin.shadow_alpha = 0.5

            # Устанавливаем начальную позицию для анимации возврата - ИЗ ЦЕНТРА ЭКРАНА
            self.coin.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            self.coin.size = (self.final_coin_size, self.final_coin_size)

        # Анимация уменьшения монеты и возврата на стартовую позицию
        return_anim = Animation(
            size=(self.coin_height, self.coin_height),
            pos_hint={'center_x': self.start_pos_x, 'center_y': self.start_pos_y},
            duration=1.2,
            t='out_quad'
        )

        # Анимация тени: плавный возврат в нормальное положение
        shadow_return_anim = Animation(
            shadow_offset_y=self.initial_shadow_offset,
            shadow_offset_x=0,
            duration=1.2,
            t='out_quad'
        )

        def on_return_complete(animation, coin):
            self.return_animation_active = False
            self.set_animating_state(False)

        return_anim.bind(on_complete=on_return_complete)

        # Запускаем анимации
        return_anim.start(self.coin)
        shadow_return_anim.start(self.coin)

    def go_to_menu(self):
        self.cleanup_all()
        super().go_to_menu()
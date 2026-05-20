"""
Dice Screen - экран с кубиками из спрайт-листа
"""
import os
import random
import math
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate, Translate, Line, Ellipse
from PIL import Image as PILImage
from kivy.graphics.texture import Texture
from screens.base_game_screen import BaseGameScreen
from kivy.core.window import Window
from kivy.utils import platform
from kivy.core.audio import SoundLoader

# ===== НАСТРОЙКИ ОТЛАДКИ =====
DEBUG_MODE = False  # True - показывать зону и точку и зеленые рамки, False - скрыть
# =============================


class GlowEffect(Widget):
    """Виджет свечения под кубиком в виде эллипса с градиентной прозрачностью"""

    def __init__(self, size, pos, **kwargs):
        super().__init__(**kwargs)
        self.dice_size = size

        self.ellipse_width_factor = 1.6
        self.ellipse_height_factor = 0.7
        self.ellipse_offset_x_factor = 0.15

        self.rotation = 90
        self.update_ellipse_size()

        self.pos = (pos[0] + (size - self.glow_width) / 2 - self.offset_x,
                    pos[1] + (size - self.glow_height) / 2)
        self.opacity = 1
        self._draw_glow()

    def update_ellipse_size(self):
        self.glow_width = self.dice_size * self.ellipse_width_factor
        self.glow_height = self.dice_size * self.ellipse_height_factor
        self.offset_x = self.dice_size * self.ellipse_offset_x_factor
        self.size = (self.glow_width, self.glow_height)

    def _draw_glow(self):
        self.canvas.clear()
        with self.canvas:
            PushMatrix()
            Translate(self.pos[0] + self.glow_width / 2, self.pos[1] + self.glow_height / 2)
            Rotate(angle=self.rotation, origin=(0, 0))
            Translate(-(self.pos[0] + self.glow_width / 2), -(self.pos[1] + self.glow_height / 2))

            size_factors = [1.0, 0.92, 0.84, 0.76, 0.68, 0.60, 0.52, 0.44, 0.36, 0.28]
            opacity_factors = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]

            for i in range(10):
                size_factor = size_factors[i]
                opacity = opacity_factors[i] * self.opacity

                inner_width = self.glow_width * size_factor
                inner_height = self.glow_height * size_factor
                inner_pos = (self.pos[0] + (self.glow_width - inner_width) / 2,
                            self.pos[1] + (self.glow_height - inner_height) / 2)

                Color(0.5, 0.7, 1.0, opacity)
                Ellipse(pos=inner_pos, size=(inner_width, inner_height))

            PopMatrix()

    def update_position(self, pos, dice_size):
        self.dice_size = dice_size
        self.update_ellipse_size()
        self.pos = (pos[0] + (dice_size - self.glow_width) / 2 - self.offset_x,
                    pos[1] + (dice_size - self.glow_height) / 2)
        self._draw_glow()

    def fade_out(self, duration=0.3, callback=None):
        anim = Animation(opacity=0, duration=duration)
        anim.bind(on_complete=lambda *args: self._on_fade_complete(callback))
        anim.start(self)

    def _on_fade_complete(self, callback):
        if callback:
            callback()

    def on_opacity(self, instance, value):
        self._draw_glow()


class DropZone(Widget):
    """Зона для сброса стакана в левой части экрана в виде эллипса"""

    def __init__(self, screen_width, screen_height, **kwargs):
        super().__init__(**kwargs)

        self.zone_width = screen_width * 0.48
        self.zone_height = screen_height * 1.05
        self.zone_x = screen_width * 0.03
        self.zone_y = screen_height * 0.5 - self.zone_height / 2

        self.size = (self.zone_width, self.zone_height)
        self.pos = (self.zone_x, self.zone_y)

        if DEBUG_MODE:
            self.draw_zone()

    def draw_zone(self):
        """Рисует желтую подсветку зоны сброса"""
        self.canvas.clear()
        with self.canvas:
            Color(1, 0.8, 0, 0.35)
            Ellipse(pos=self.pos, size=self.size)
            Color(1, 0.6, 0, 1.0)
            Line(ellipse=(self.pos[0], self.pos[1], self.size[0], self.size[1]), width=4)
            Color(1, 1, 0, 0.2)
            inner_pos = (self.pos[0] + 10, self.pos[1] + 10)
            inner_size = (self.size[0] - 20, self.size[1] - 20)
            Ellipse(pos=inner_pos, size=inner_size)

    def update_zone_visibility(self):
        if DEBUG_MODE:
            self.draw_zone()
        else:
            self.canvas.clear()

    def check_point_in_zone(self, point_x, point_y):
        ellipse_center_x = self.pos[0] + self.size[0] / 2
        ellipse_center_y = self.pos[1] + self.size[1] / 2

        nx = (point_x - ellipse_center_x) / (self.size[0] / 2)
        ny = (point_y - ellipse_center_y) / (self.size[1] / 2)

        return (nx * nx + ny * ny) <= 1

    def check_collision(self, widget_pos, widget_size):
        widget_center_x = widget_pos[0] + widget_size[0] / 2
        widget_center_y = widget_pos[1] + widget_size[1] / 2
        return self.check_point_in_zone(widget_center_x, widget_center_y)

    def clamp_point_to_zone(self, point_x, point_y):
        ellipse_center_x = self.pos[0] + self.size[0] / 2
        ellipse_center_y = self.pos[1] + self.size[1] / 2

        dx = point_x - ellipse_center_x
        dy = point_y - ellipse_center_y

        nx = dx / (self.size[0] / 2)
        ny = dy / (self.size[1] / 2)

        if (nx * nx + ny * ny) <= 1:
            return (point_x, point_y)

        length = math.sqrt(nx * nx + ny * ny)
        nx /= length
        ny /= length

        clamped_x = ellipse_center_x + nx * (self.size[0] / 2)
        clamped_y = ellipse_center_y + ny * (self.size[1] / 2)

        return (clamped_x, clamped_y)


class PointMarker(Widget):
    """Виджет для отображения точки на экране"""

    def __init__(self, color=(1, 0, 0, 1), size=15, **kwargs):
        super().__init__(**kwargs)
        self.point_x = 0
        self.point_y = 0
        self.color = color
        self.point_size = size
        self.is_visible = False

    def draw_point(self):
        self.canvas.clear()
        if not self.is_visible:
            return
        with self.canvas:
            Color(self.color[0], self.color[1], self.color[2], 0.3)
            Ellipse(pos=(self.point_x - self.point_size, self.point_y - self.point_size),
                   size=(self.point_size * 2, self.point_size * 2))
            Color(self.color[0], self.color[1], self.color[2], self.color[3])
            Ellipse(pos=(self.point_x - self.point_size/2, self.point_y - self.point_size/2),
                   size=(self.point_size, self.point_size))
            Color(1, 1, 1, 0.8)
            Ellipse(pos=(self.point_x - self.point_size/4, self.point_y - self.point_size/4),
                   size=(self.point_size/2, self.point_size/2))

    def update_position(self, x, y, visible=True):
        self.point_x = x
        self.point_y = y
        self.is_visible = visible
        self.draw_point()


class DiceWidget(Widget):
    """Виджет кубика с поддержкой вращения через смену кадров"""

    sprite_sheet_path = StringProperty('')
    dice_size = NumericProperty(100)
    rows = NumericProperty(6)
    cols = NumericProperty(12)
    frame_index = NumericProperty(0)
    rotation_angle = NumericProperty(-90)
    debug_mode = BooleanProperty(False)

    _texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.initial_dice_size = kwargs.pop('dice_size', None)
        self.on_dice_click = kwargs.pop('on_dice_click', None)
        self.on_animation_complete = kwargs.pop('on_animation_complete', None)
        self.is_animating = False
        self.animation_frames = []
        self.glow = None
        self.original_size = None
        self.enlarged_size = None
        self.original_position = None
        self.original_center = None
        self.rotation_frames = []
        super().__init__(**kwargs)

        if self.sprite_sheet_path and os.path.exists(self.sprite_sheet_path):
            self._load_spritesheet(self.sprite_sheet_path)
        else:
            if self.initial_dice_size:
                self.dice_size = self.initial_dice_size
                self.size = (self.dice_size, self.dice_size)

        self.bind(
            frame_index=self._update_display,
            pos=self._update_display,
            size=self._update_display,
            dice_size=self._on_dice_size_changed,
            rotation_angle=self._update_display
        )

        if DEBUG_MODE:
            self.bind(pos=self._update_debug_border, size=self._update_debug_border)

        Clock.schedule_once(lambda dt: self._create_glow(), 0)

    def _on_dice_size_changed(self, instance, value):
        self.size = (value, value)
        self._update_display()

    def _create_glow(self):
        if self.parent and self.glow is None:
            self.glow = GlowEffect(self.dice_size, self.pos)
            self.parent.add_widget(self.glow, index=0)

    def _remove_glow(self):
        if self.glow and self.glow.parent:
            self.glow.parent.remove_widget(self.glow)
            self.glow = None

    def _update_glow_position(self):
        if self.glow:
            self.glow.update_position(self.pos, self.dice_size)

    def _load_spritesheet(self, path):
        try:
            img = PILImage.open(path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            self._texture = Texture.create(size=img.size, colorfmt='rgba')
            self._texture.blit_buffer(img.tobytes(), colorfmt='rgba', bufferfmt='ubyte')

            if self.initial_dice_size:
                self.dice_size = self.initial_dice_size
            else:
                if platform == 'android':
                    real_width = Window.system_size[0]
                    self.dice_size = real_width * 0.12
                else:
                    app = App.get_running_app()
                    screen_params = getattr(app, 'screen_params', None)
                    if screen_params:
                        self.dice_size = screen_params.width * 0.12
                    else:
                        self.dice_size = 80

            self.size = (self.dice_size, self.dice_size)
            self._update_display()

        except Exception as e:
            print(f"Error loading dice spritesheet: {e}")

    def _update_display(self, *args):
        if not self._texture or self.width == 0:
            return

        total_frames = self.rows * self.cols
        if total_frames == 0:
            return

        frame_idx = self.frame_index % total_frames
        row = frame_idx // self.cols
        col = frame_idx % self.cols

        tex_left = col / self.cols
        tex_right = (col + 1) / self.cols
        tex_top = row / self.rows
        tex_bottom = (row + 1) / self.rows

        tex_coords = (tex_left, tex_bottom,
                      tex_right, tex_bottom,
                      tex_right, tex_top,
                      tex_left, tex_top)

        self.canvas.clear()

        with self.canvas:
            PushMatrix()
            Translate(self.x + self.width / 2, self.y + self.height / 2)
            Rotate(angle=self.rotation_angle, origin=(0, 0))
            Translate(-(self.x + self.width / 2), -(self.y + self.height / 2))
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size, texture=self._texture, tex_coords=tex_coords)
            PopMatrix()

        self._update_glow_position()

        if DEBUG_MODE:
            self.canvas.after.clear()
            with self.canvas.after:
                Color(0, 1, 0, 0.8)
                Line(rectangle=(self.x, self.y, self.width, self.height), width=2)

    def _update_debug_border(self, *args):
        if not DEBUG_MODE:
            return
        self._update_display()

    def set_random_frame(self):
        total_frames = self.rows * self.cols
        self.frame_index = random.randint(0, total_frames - 1)

    def set_random_frame_same_row(self):
        total_frames = self.rows * self.cols
        current_row = (self.frame_index // self.cols) % self.rows
        new_col = random.randint(0, self.cols - 1)
        self.frame_index = current_row * self.cols + new_col

    def set_frame_direct(self, frame_index):
        self.frame_index = frame_index

    def enable_glow(self):
        if self.glow:
            self.glow.update_position(self.pos, self.dice_size)
            self.glow.opacity = 1

    def disable_glow(self):
        if self.glow:
            self.glow.opacity = 0

    def update_glow_position(self):
        if self.glow:
            self.glow.update_position(self.pos, self.dice_size)

    def _find_parent_with_method(self, method_name):
        parent = self.parent
        while parent:
            if hasattr(parent, method_name):
                return parent
            parent = parent.parent
        return None

    def generate_rotation_frames(self, start_frame, num_rotations=5):
        """Генерирует последовательность кадров для анимации вращения (num_rotations оборотов по 12 кадров)"""
        total_frames = self.rows * self.cols
        start_row = start_frame // self.cols
        start_col = start_frame % self.cols

        frames = []

        # Делаем num_rotations полных оборотов
        for rotation in range(num_rotations):
            # Каждый оборот - проход по всем колонкам текущего ряда
            for col_offset in range(1, self.cols + 1):
                new_col = (start_col + col_offset) % self.cols
                frames.append(start_row * self.cols + new_col)

        # Возвращаемся в исходный кадр
        frames.append(start_frame)

        return frames

    def animate_rotation(self, start_frame, num_rotations=5, duration=0.3, callback=None):
        """Анимирует вращение кубика с заданным количеством оборотов"""
        if self.is_animating:
            if callback:
                callback()
            return

        self.is_animating = True
        frames = self.generate_rotation_frames(start_frame, num_rotations)

        if not frames:
            self.is_animating = False
            if callback:
                callback()
            return

        frame_duration = duration / len(frames)
        self._animate_rotation_frames(0, frames, frame_duration, callback)

    def _animate_rotation_frames(self, idx, frames, frame_duration, callback):
        if idx >= len(frames):
            self.frame_index = frames[-1]
            self.is_animating = False
            if callback:
                callback()
            return

        self.frame_index = frames[idx]
        Clock.schedule_once(
            lambda dt: self._animate_rotation_frames(idx + 1, frames, frame_duration, callback),
            frame_duration
        )

    def animate_disappear_in_place(self, duration=0.5, callback=None):
        if self.is_animating:
            return

        self.is_animating = True

        parent = self._find_parent_with_method('play_dice_disappear_sound')
        if parent:
            parent.play_dice_disappear_sound()

        current_frame = self.frame_index
        frames = self.generate_rotation_frames(current_frame, num_rotations=5)
        self.animation_frames = frames

        anim_fade = Animation(opacity=0, duration=duration)

        if self.glow:
            self.glow.fade_out(duration)

        def on_fade_complete(*args):
            self._remove_glow()
            self.is_animating = False
            if callback:
                callback()

        anim_fade.bind(on_complete=on_fade_complete)
        anim_fade.start(self)

        frame_duration = duration / len(frames) if frames else duration
        self._animate_next_frame(0, frame_duration)

    def _animate_next_frame(self, idx, frame_duration):
        if idx >= len(self.animation_frames):
            return

        self.frame_index = self.animation_frames[idx]
        Clock.schedule_once(lambda dt: self._animate_next_frame(idx + 1, frame_duration), frame_duration)

    def animate_disappear_to_center(self, target_center, duration=0.5, callback=None):
        if self.is_animating:
            return

        self.is_animating = True

        parent = self._find_parent_with_method('play_dice_disappear_sound')
        if parent:
            parent.play_dice_disappear_sound()

        current_frame = self.frame_index
        frames = self.generate_rotation_frames(current_frame, num_rotations=5)
        self.animation_frames = frames

        anim_move = Animation(pos=target_center, duration=duration)
        anim_fade = Animation(opacity=0, duration=duration)

        if self.glow:
            glow_move = Animation(pos=target_center, duration=duration)
            self.glow.fade_out(duration)
            glow_move.start(self.glow)

        def on_fade_complete(*args):
            self._remove_glow()
            self.is_animating = False
            if callback:
                callback()

        anim_fade.bind(on_complete=on_fade_complete)
        anim_move.start(self)
        anim_fade.start(self)

        frame_duration = duration / len(frames) if frames else duration
        self._animate_next_frame(0, frame_duration)

    def animate_appearance_from_center(self, target_pos, start_pos, duration=0.6, callback=None):
        if self.is_animating:
            return

        self.is_animating = True
        self.opacity = 1

        self.pos = start_pos

        self._create_glow()
        if self.glow:
            self.glow.opacity = 1
            self.glow.update_position(start_pos, self.dice_size)

        start_row = random.randint(0, self.rows - 1)
        start_frame = start_row * self.cols

        # Генерируем 5 оборотов вращения
        frames = []
        for rotation in range(5):
            for col in range(1, self.cols + 1):
                frames.append(start_row * self.cols + (col % self.cols))

        # Финальный кадр - случайный
        final_col = random.randint(0, self.cols - 1)
        final_frame = start_row * self.cols + final_col
        frames.append(final_frame)

        self.animation_frames = frames

        anim_move = Animation(pos=target_pos, duration=duration)
        anim_move.start(self)

        if self.glow:
            glow_move = Animation(pos=target_pos, duration=duration)
            glow_move.start(self.glow)

        self._animate_appearance(0, duration / len(frames), callback)

    def _animate_appearance(self, idx, frame_duration, callback):
        if idx >= len(self.animation_frames):
            self.frame_index = self.animation_frames[-1]
            self.is_animating = False
            if callback:
                callback(self)
            return

        self.frame_index = self.animation_frames[idx]
        Clock.schedule_once(lambda dt: self._animate_appearance(idx + 1, frame_duration, callback), frame_duration)

    def on_touch_down(self, touch):
        # Проверяем, заблокированы ли кубики
        if self.parent and hasattr(self.parent, 'is_dice_blocked') and self.parent.is_dice_blocked:
            if DEBUG_MODE:
                print("🔒 [DiceWidget] Кубики заблокированы, клик игнорируется")
            return True

        if self.collide_point(*touch.pos) and not self.is_animating:
            print(f"🎲 [DiceWidget] КЛИК ПО КУБИКУ!")
            if self.on_dice_click:
                self.on_dice_click()
            return True
        return super().on_touch_down(touch)


class GlassWidget(Widget):
    """Виджет стакана со своим спрайт-листом (2 ряда × 12 колонок)"""

    sprite_sheet_path = StringProperty('')
    glass_size = NumericProperty(100)
    rows = NumericProperty(2)
    cols = NumericProperty(12)
    frame_index = NumericProperty(0)
    rotation_angle = NumericProperty(-90)
    is_raised = BooleanProperty(False)

    _texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.initial_glass_size = kwargs.pop('glass_size', None)
        self.on_glass_click = kwargs.pop('on_glass_click', None)
        self.on_glass_drag = kwargs.pop('on_glass_drag', None)
        self.on_glass_drag_end = kwargs.pop('on_glass_drag_end', None)
        self.is_animating = False
        self.drag_active = False
        self.has_moved_during_drag = False
        self.touch_start_pos = None
        self.touch_start_time = None
        super().__init__(**kwargs)

        if self.sprite_sheet_path and os.path.exists(self.sprite_sheet_path):
            self._load_spritesheet(self.sprite_sheet_path)
        else:
            if self.initial_glass_size:
                self.glass_size = self.initial_glass_size
                self.size = (self.glass_size, self.glass_size)

        self.bind(
            frame_index=self._update_display,
            pos=self._update_display,
            size=self._update_display,
            rotation_angle=self._update_display
        )

    def _load_spritesheet(self, path):
        try:
            img = PILImage.open(path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            self._texture = Texture.create(size=img.size, colorfmt='rgba')
            self._texture.blit_buffer(img.tobytes(), colorfmt='rgba', bufferfmt='ubyte')

            if self.initial_glass_size:
                self.glass_size = self.initial_glass_size
            else:
                if platform == 'android':
                    real_width = Window.system_size[0]
                    self.glass_size = real_width * 0.12
                else:
                    app = App.get_running_app()
                    screen_params = getattr(app, 'screen_params', None)
                    if screen_params:
                        self.glass_size = screen_params.width * 0.12
                    else:
                        self.glass_size = 80

            self.size = (self.glass_size, self.glass_size)
            self._update_display()

        except Exception as e:
            print(f"Error loading glass spritesheet: {e}")

    def _update_display(self, *args):
        if not self._texture or self.width == 0:
            return

        total_frames = self.rows * self.cols
        if total_frames == 0:
            return

        frame_idx = self.frame_index % total_frames
        row = frame_idx // self.cols
        col = frame_idx % self.cols

        tex_left = col / self.cols
        tex_right = (col + 1) / self.cols
        tex_top = row / self.rows
        tex_bottom = (row + 1) / self.rows

        tex_coords = (tex_left, tex_bottom,
                      tex_right, tex_bottom,
                      tex_right, tex_top,
                      tex_left, tex_top)

        self.canvas.clear()

        with self.canvas:
            PushMatrix()
            Translate(self.x + self.width / 2, self.y + self.height / 2)
            Rotate(angle=self.rotation_angle, origin=(0, 0))
            Translate(-(self.x + self.width / 2), -(self.y + self.height / 2))
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size, texture=self._texture, tex_coords=tex_coords)
            PopMatrix()

        if DEBUG_MODE:
            self.canvas.after.clear()
            with self.canvas.after:
                Color(0, 1, 0, 0.8)
                Line(rectangle=(self.x, self.y, self.width, self.height), width=2)

    def set_frame(self, frame_index):
        total_frames = self.rows * self.cols
        if 0 <= frame_index < total_frames:
            self.frame_index = frame_index
            if frame_index == 0:
                self.is_raised = False
            elif frame_index == total_frames - 1:
                self.is_raised = True

    def set_raised(self, raised):
        total_frames = self.rows * self.cols
        if raised:
            self.set_frame(total_frames - 1)
        else:
            self.set_frame(0)

    def animate_movement(self, start_pos, end_pos, duration, forward=True, callback=None):
        if self.is_animating:
            return

        self.is_animating = True
        total_frames = self.rows * self.cols
        self.pos = start_pos

        if forward:
            frames = list(range(total_frames))
        else:
            frames = list(range(total_frames - 1, -1, -1))

        frame_duration = duration / total_frames

        anim_move = Animation(pos=end_pos, duration=duration)
        anim_move.start(self)

        self._animate_frame_sequence(0, frames, frame_duration, callback)

    def _animate_frame_sequence(self, idx, frames, frame_duration, callback):
        if idx >= len(frames):
            self.frame_index = frames[-1] if frames else 0
            self.is_animating = False
            if callback:
                callback()
            return

        self.frame_index = frames[idx]
        Clock.schedule_once(
            lambda dt: self._animate_frame_sequence(idx + 1, frames, frame_duration, callback),
            frame_duration
        )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.is_animating:
            if self.parent and hasattr(self.parent, 'is_glass_blocked') and self.parent.is_glass_blocked:
                if DEBUG_MODE:
                    print("🔒 [WIDGET] Стакан заблокирован, клик игнорируется")
                return True

            self.drag_active = True
            self.has_moved_during_drag = False
            self.touch_start_pos = (touch.x, touch.y)
            self.touch_start_time = Clock.get_time()
            if DEBUG_MODE:
                print(f"🟢 [WIDGET] on_touch_down: начали перетаскивание, pos={self.touch_start_pos}")
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.drag_active:
            if self.parent and hasattr(self.parent, 'is_glass_blocked') and self.parent.is_glass_blocked:
                if DEBUG_MODE:
                    print("🔒 [WIDGET] Стакан заблокирован, движение игнорируется")
                return True

            if self.touch_start_pos:
                delta_x = touch.x - self.touch_start_pos[0]
                delta_y = touch.y - self.touch_start_pos[1]

                if abs(delta_x) > 5 or abs(delta_y) > 5:
                    self.has_moved_during_drag = True
                    if DEBUG_MODE:
                        print(f"🟡 [WIDGET] on_touch_move: delta=({delta_x:.1f}, {delta_y:.1f})")
                    if self.on_glass_drag:
                        self.on_glass_drag(delta_x, delta_y, touch)
                    self.touch_start_pos = (touch.x, touch.y)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if DEBUG_MODE:
            print(f"🟢 [WIDGET] on_touch_up: drag_active={self.drag_active}, has_moved={self.has_moved_during_drag}")
        if self.drag_active:
            if self.parent and hasattr(self.parent, 'is_glass_blocked') and self.parent.is_glass_blocked:
                if DEBUG_MODE:
                    print("🔒 [WIDGET] Стакан заблокирован, клик игнорируется")
                self.drag_active = False
                self.has_moved_during_drag = False
                self.touch_start_pos = None
                self.touch_start_time = None
                return True

            touch_duration = Clock.get_time() - self.touch_start_time

            if not self.has_moved_during_drag and touch_duration < 0.3 and self.on_glass_click:
                if DEBUG_MODE:
                    print(f"   👆 Это клик")
                self.on_glass_click()
            elif self.has_moved_during_drag and self.on_glass_drag_end:
                if DEBUG_MODE:
                    print(f"   ✋ Это окончание перетаскивания")
                self.on_glass_drag_end(touch)

            self.drag_active = False
            self.has_moved_during_drag = False
            self.touch_start_pos = None
            self.touch_start_time = None
            return True
        return super().on_touch_up(touch)


class ShadowWidget(Widget):
    """Виджет тени стакана со своим спрайт-листом (2 ряда × 12 колонок)"""

    scale_factor = NumericProperty(1.0)
    rotation_angle = NumericProperty(-90)
    offset_x = NumericProperty(0)
    offset_y = NumericProperty(0)
    opacity = NumericProperty(1.0)
    move_factor_x = NumericProperty(0.8)
    move_factor_y = NumericProperty(0.8)
    glass_size = NumericProperty(0)

    sprite_sheet_path = StringProperty('')
    shadow_size = NumericProperty(100)
    rows = NumericProperty(2)
    cols = NumericProperty(12)
    frame_index = NumericProperty(0)

    _texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.initial_shadow_size = kwargs.pop('shadow_size', None)
        self.is_animating = False
        super().__init__(**kwargs)

        if self.sprite_sheet_path and os.path.exists(self.sprite_sheet_path):
            self._load_spritesheet(self.sprite_sheet_path)
        else:
            if self.initial_shadow_size:
                self.shadow_size = self.initial_shadow_size
                self.size = (self.shadow_size, self.shadow_size)

        self.bind(
            frame_index=self._update_display,
            pos=self._update_display,
            size=self._update_display,
            scale_factor=self._update_display,
            rotation_angle=self._update_display,
            opacity=self._update_display
        )

    def _load_spritesheet(self, path):
        try:
            img = PILImage.open(path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            self._texture = Texture.create(size=img.size, colorfmt='rgba')
            self._texture.blit_buffer(img.tobytes(), colorfmt='rgba', bufferfmt='ubyte')

            if self.initial_shadow_size:
                self.shadow_size = self.initial_shadow_size
            else:
                if platform == 'android':
                    real_width = Window.system_size[0]
                    self.shadow_size = real_width * 0.12
                else:
                    app = App.get_running_app()
                    screen_params = getattr(app, 'screen_params', None)
                    if screen_params:
                        self.shadow_size = screen_params.width * 0.12
                    else:
                        self.shadow_size = 80

            scaled_size = self.shadow_size * self.scale_factor
            self.size = (scaled_size, scaled_size)
            self._update_display()

        except Exception as e:
            print(f"Error loading shadow spritesheet: {e}")

    def _update_display(self, *args):
        if not self._texture or self.width == 0:
            return

        total_frames = self.rows * self.cols
        if total_frames == 0:
            return

        frame_idx = self.frame_index % total_frames
        row = frame_idx // self.cols
        col = frame_idx % self.cols

        tex_left = col / self.cols
        tex_right = (col + 1) / self.cols
        tex_top = row / self.rows
        tex_bottom = (row + 1) / self.rows

        tex_coords = (tex_left, tex_bottom,
                     tex_right, tex_bottom,
                     tex_right, tex_top,
                     tex_left, tex_top)

        self.canvas.clear()

        with self.canvas:
            PushMatrix()
            Translate(self.x + self.width / 2, self.y + self.height / 2)
            Rotate(angle=self.rotation_angle, origin=(0, 0))
            Translate(-(self.x + self.width / 2), -(self.y + self.height / 2))
            Color(1, 1, 1, self.opacity)
            Rectangle(pos=self.pos, size=self.size, texture=self._texture, tex_coords=tex_coords)
            PopMatrix()

    def set_frame(self, frame_index):
        total_frames = self.rows * self.cols
        if 0 <= frame_index < total_frames:
            self.frame_index = frame_index

    def move_by_delta(self, delta_x, delta_y):
        self.pos = (self.pos[0] + delta_x, self.pos[1] + delta_y)

    def animate_movement_to_target(self, target_pos, duration, forward=True, callback=None):
        if self.is_animating:
            return

        self.is_animating = True
        total_frames = self.rows * self.cols

        if forward:
            frames = list(range(total_frames))
        else:
            frames = list(range(total_frames - 1, -1, -1))

        frame_duration = duration / total_frames

        anim_move = Animation(pos=target_pos, duration=duration)
        anim_move.start(self)

        self._animate_frame_sequence(0, frames, frame_duration, callback)

    def _animate_frame_sequence(self, idx, frames, frame_duration, callback):
        if idx >= len(frames):
            self.frame_index = frames[-1] if frames else 0
            self.is_animating = False
            if callback:
                callback()
            return

        self.frame_index = frames[idx]
        Clock.schedule_once(
            lambda dt: self._animate_frame_sequence(idx + 1, frames, frame_duration, callback),
            frame_duration
        )


class DiceScreen(BaseGameScreen):
    """Экран с кубиками на столе и стаканом рядом"""

    background_image = StringProperty('assets/backgrounds/dice_bg.png')
    sprite_sheet_path = StringProperty('assets/sprites/dice_spritesheet.png')
    glass_sprite_sheet_path = StringProperty('assets/sprites/spritesheet_glass12.png')
    shadow_sprite_sheet_path = StringProperty('assets/sprites/spritesheet_shadow.png')

    shadow_scale_factor = NumericProperty(2.6)
    shadow_rotation = NumericProperty(-90)
    shadow_offset_x_factor = NumericProperty(-1.25)
    shadow_offset_y_factor = NumericProperty(-0.35)
    shadow_opacity = NumericProperty(0.7)
    shadow_move_factor_x = NumericProperty(-1.0)
    shadow_move_factor_y = NumericProperty(0.0)

    ANIMATION_DURATION = 1.5  # Общая длительность анимации увеличения/уменьшения

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.disappear_duration = 0.5
        self.appear_duration = 0.6
        self.overlap_time = 0.2

        self.dice_size = 0
        self.large_dice_size = 0
        self.glass_size = 0
        self.shadow_size = 0

        self.START_POSITION_DICE_X = 0
        self.START_POSITION_DICE_Y = 0
        self.START_POSITION_GLASS_X = 0
        self.START_POSITION_GLASS_Y = 0
        self.SHADOW_POSITION_X = 0
        self.SHADOW_POSITION_Y = 0
        self.SHADOW_TARGET_POSITION_X = 0
        self.SHADOW_TARGET_POSITION_Y = 0

        self.dice_list = []
        self.glass = None
        self.shadow = None
        self.drop_zone = None
        self.point_a_marker = None
        self.current_mode = 1
        self.bg = None
        self.is_animating = False
        self.animation_counter = 0
        self.dice_hidden = False
        self.pending_hide_dice = False

        self.glass_start_pos = None
        self.glass_target_pos = None
        self.is_at_target = True

        self.last_dice_center = None

        self.last_touch_pos = None
        self.last_touch_time = None
        self.max_speed = 0

        self.sound_glass_lower = None
        self.sound_glass_raise = None
        self.sound_dice_roll = None
        self.sound_glass_drag = None
        self.sound_dice_appear = None
        self.sound_dice_disappear = None

        self.volume_fade_clock = None
        self.target_volume = 0.0

        self.is_dice_enlarged = False
        self.is_glass_blocked = False
        self.is_dice_blocked = False

    def get_screen_size(self):
        if platform == 'android':
            width, height = Window.system_size
        else:
            width = Window.width
            height = Window.height
        return width, height

    def _get_center_positions(self):
        screen_width, screen_height = self.get_screen_size()
        center_x = screen_width / 2
        pos1_y = screen_height * 0.33
        pos2_y = screen_height * 0.5
        pos3_y = screen_height * 0.66
        return {
            'pos1': (center_x, pos1_y),
            'pos2': (center_x, pos2_y),
            'pos3': (center_x, pos3_y)
        }

    def _get_dice_target_position(self, dice, mode='grow'):
        positions = self._get_center_positions()
        if mode == 'grow':
            if len(self.dice_list) == 1:
                target_x = positions['pos2'][0] - dice.width / 2
                target_y = positions['pos2'][1] - dice.height / 2
                return (target_x, target_y)
            else:
                index = self.dice_list.index(dice) if dice in self.dice_list else 0
                if index == 0:
                    target_x = positions['pos1'][0] - dice.width / 2
                    target_y = positions['pos1'][1] - dice.height / 2
                else:
                    target_x = positions['pos3'][0] - dice.width / 2
                    target_y = positions['pos3'][1] - dice.height / 2
                return (target_x, target_y)
        else:
            if hasattr(dice, 'original_position') and dice.original_position:
                return dice.original_position
            return (self.START_POSITION_DICE_X, dice.pos[1] if len(self.dice_list) > 1 else self.START_POSITION_DICE_Y)

    def _get_dice_original_positions(self):
        screen_width, screen_height = self.get_screen_size()
        positions = {}
        if len(self.dice_list) == 1:
            x = self.START_POSITION_DICE_X
            y = self.START_POSITION_DICE_Y
            positions[0] = (x, y)
        else:
            distance_between = self.dice_size * 0.3
            center_y = self.START_POSITION_DICE_Y + (self.large_dice_size // 2) - (self.dice_size // 2)
            y_top = center_y - distance_between
            y_bottom = center_y + distance_between
            positions[0] = (self.START_POSITION_DICE_X, y_top)
            positions[1] = (self.START_POSITION_DICE_X, y_bottom)
        return positions

    def _load_dice_sounds(self):
        try:
            if os.path.exists('assets/sounds/dice/glass_lower.mp3'):
                self.sound_glass_lower = SoundLoader.load('assets/sounds/dice/glass_lower.mp3')
                if self.sound_glass_lower:
                    print("✅ Загружен звук: glass_lower.mp3")

            if os.path.exists('assets/sounds/dice/glass_raise.mp3'):
                self.sound_glass_raise = SoundLoader.load('assets/sounds/dice/glass_raise.mp3')
                if self.sound_glass_raise:
                    print("✅ Загружен звук: glass_raise.mp3")

            if os.path.exists('assets/sounds/dice/dice_roll.mp3'):
                self.sound_dice_roll = SoundLoader.load('assets/sounds/dice/dice_roll.mp3')
                if self.sound_dice_roll:
                    print("✅ Загружен звук: dice_roll.mp3")

            if os.path.exists('assets/sounds/dice/glass_drag.mp3'):
                self.sound_glass_drag = SoundLoader.load('assets/sounds/dice/glass_drag.mp3')
                if self.sound_glass_drag:
                    self.sound_glass_drag.loop = True
                    self.sound_glass_drag.volume = 0.0
                    self.sound_glass_drag.play()
                    print("✅ Загружен звук: glass_drag.mp3 (зацикленный)")

            if os.path.exists('assets/sounds/dice/dice_appear.mp3'):
                self.sound_dice_appear = SoundLoader.load('assets/sounds/dice/dice_appear.mp3')
                if self.sound_dice_appear:
                    print("✅ Загружен звук: dice_appear.mp3")

            if os.path.exists('assets/sounds/dice/dice_disappear.mp3'):
                self.sound_dice_disappear = SoundLoader.load('assets/sounds/dice/dice_disappear.mp3')
                if self.sound_dice_disappear:
                    print("✅ Загружен звук: dice_disappear.mp3")

        except Exception as e:
            print(f"Ошибка загрузки звуков кубиков: {e}")

    def _fade_volume(self, target_volume, duration=0.2):
        if not self.sound_glass_drag:
            return

        self.target_volume = target_volume
        start_volume = self.sound_glass_drag.volume

        if self.volume_fade_clock:
            self.volume_fade_clock.cancel()
            self.volume_fade_clock = None

        def update_volume(step, steps):
            if step <= 0:
                self.sound_glass_drag.volume = target_volume
                self.volume_fade_clock = None
                return

            progress = step / steps
            self.sound_glass_drag.volume = start_volume + (target_volume - start_volume) * (1 - progress)

            self.volume_fade_clock = Clock.schedule_once(
                lambda dt: update_volume(step - 1, steps),
                duration / steps
            )

        steps = 20
        update_volume(steps, steps)

    def play_dice_roll_sound(self):
        if self.sound_dice_roll and not self.sound_manager.is_muted():
            self.sound_dice_roll.play()

    def play_dice_appear_sound(self):
        if self.sound_dice_appear and not self.sound_manager.is_muted():
            self.sound_dice_appear.play()

    def play_dice_disappear_sound(self):
        if self.sound_dice_disappear and not self.sound_manager.is_muted():
            self.sound_dice_disappear.play()

    def _block_glass(self):
        self.is_glass_blocked = True
        if DEBUG_MODE:
            print("🔒 [GLASS] Стакан заблокирован")

    def _unblock_glass(self):
        self.is_glass_blocked = False
        if DEBUG_MODE:
            print("🔓 [GLASS] Стакан разблокирован")

    def _block_dice(self):
        self.is_dice_blocked = True
        if DEBUG_MODE:
            print("🔒 [DICE] Кубики заблокированы")

    def _unblock_dice(self):
        self.is_dice_blocked = False
        if DEBUG_MODE:
            print("🔓 [DICE] Кубики разблокированы")

    def _animate_dice_grow_with_move(self, dice, target_size, target_position, on_complete_callback=None):
        if hasattr(dice, 'is_animating_scale') and dice.is_animating_scale:
            return
        dice.is_animating_scale = True

        # Блокируем стакан в начале анимации увеличения
        self._block_glass()

        if dice.original_center is None:
            original_center_x = dice.pos[0] + dice.width / 2
            original_center_y = dice.pos[1] + dice.height / 2
            dice.original_center = (original_center_x, original_center_y)
            if DEBUG_MODE:
                print(f"📐 [GROW] Сохранен исходный центр: ({original_center_x:.1f}, {original_center_y:.1f})")

        positions = self._get_center_positions()

        if len(self.dice_list) == 1:
            target_center_x = positions['pos2'][0]
            target_center_y = positions['pos2'][1]
        else:
            index = self.dice_list.index(dice) if dice in self.dice_list else 0
            if index == 0:
                target_center_x = positions['pos1'][0]
                target_center_y = positions['pos1'][1]
            else:
                target_center_x = positions['pos3'][0]
                target_center_y = positions['pos3'][1]

        corrected_target_x = target_center_x - target_size / 2
        corrected_target_y = target_center_y - target_size / 2
        target_position = (corrected_target_x, corrected_target_y)

        # Анимация свечения: гаснет в первые 0.3 секунды
        if dice.glow:
            anim_glow_fade = Animation(opacity=0, duration=0.3)
            anim_glow_fade.start(dice.glow)

        # Сохраняем текущий кадр для вращения
        current_frame = dice.frame_index

        # Запускаем анимацию вращения (5 оборотов)
        dice.animate_rotation(current_frame, num_rotations=5, duration=self.ANIMATION_DURATION)

        # Линейная анимация размера и позиции
        anim_grow = Animation(dice_size=target_size, duration=self.ANIMATION_DURATION, t='linear')
        anim_move = Animation(pos=target_position, duration=self.ANIMATION_DURATION, t='linear')

        def on_complete(*args):
            dice.is_animating_scale = False
            self.is_dice_enlarged = True
            dice.enlarged_size = target_size
            # Разблокируем кубики после завершения анимации увеличения
            self._unblock_dice()
            if on_complete_callback:
                on_complete_callback()

        anim_grow.bind(on_complete=on_complete)
        anim_grow.start(dice)
        anim_move.start(dice)

    def _animate_dice_shrink_with_move(self, dice, original_size, on_complete_callback=None):
        if hasattr(dice, 'is_animating_scale') and dice.is_animating_scale:
            return
        dice.is_animating_scale = True

        if dice.original_center is None:
            original_center_x = dice.pos[0] + dice.width / 2
            original_center_y = dice.pos[1] + dice.height / 2
        else:
            original_center_x, original_center_y = dice.original_center

        corrected_original_x = original_center_x - original_size / 2
        corrected_original_y = original_center_y - original_size / 2
        target_position = (corrected_original_x, corrected_original_y)

        # Сохраняем текущий кадр для вращения
        current_frame = dice.frame_index

        # Запускаем анимацию вращения (5 оборотов)
        dice.animate_rotation(current_frame, num_rotations=5, duration=self.ANIMATION_DURATION)

        # Анимация свечения: появляется в последние 0.3 секунды
        if dice.glow:
            dice.glow.opacity = 0
            Clock.schedule_once(lambda dt: self._appear_glow(dice.glow), self.ANIMATION_DURATION - 0.3)

        # Линейная анимация размера и позиции
        anim_shrink = Animation(dice_size=original_size, duration=self.ANIMATION_DURATION, t='linear')
        anim_move_back = Animation(pos=target_position, duration=self.ANIMATION_DURATION, t='linear')

        def on_complete(*args):
            dice.is_animating_scale = False
            dice.original_center = None
            if on_complete_callback:
                on_complete_callback()

        anim_shrink.bind(on_complete=on_complete)
        anim_shrink.start(dice)
        anim_move_back.start(dice)

    def _appear_glow(self, glow):
        """Плавное появление свечения"""
        if glow:
            anim = Animation(opacity=1, duration=0.1)
            anim.start(glow)

    def _animate_dice_appearance(self):
        """Анимация появления кубиков: перемещение и увеличение в 5 раз"""
        # Блокируем кубики
        self._block_dice()

        original_positions = self._get_dice_original_positions()

        completed_animations = [0]
        total_dice = len(self.dice_list)

        def check_all_complete():
            completed_animations[0] += 1
            if completed_animations[0] >= total_dice:
                # Кубики разблокируются в on_complete каждой анимации увеличения
                pass

        for i, dice in enumerate(self.dice_list):
            if not hasattr(dice, 'original_position') or dice.original_position is None:
                dice.original_position = original_positions.get(i, dice.pos)

            if not hasattr(dice, 'original_size') or dice.original_size is None:
                dice.original_size = dice.dice_size

            if dice.original_center is None:
                original_center_x = dice.pos[0] + dice.width / 2
                original_center_y = dice.pos[1] + dice.height / 2
                dice.original_center = (original_center_x, original_center_y)

            target_size = dice.original_size * 5
            target_position = self._get_dice_target_position(dice, 'grow')

            self._animate_dice_grow_with_move(dice, target_size, target_position, check_all_complete)

    def _shrink_all_dice(self, on_complete_callback=None):
        """Возвращает все кубики к исходному размеру и позициям"""
        if not self.is_dice_enlarged:
            if on_complete_callback:
                on_complete_callback()
            return

        # Блокируем кубики во время уменьшения
        self._block_dice()

        completed_animations = [0]
        total_dice = len(self.dice_list)

        def check_all_complete():
            completed_animations[0] += 1
            if completed_animations[0] >= total_dice:
                if DEBUG_MODE:
                    print("🔓 [SHRINK] Все кубики вернулись, разблокируем стакан и кубики")
                self.is_dice_enlarged = False
                # Разблокируем стакан в конце анимации уменьшения
                self._unblock_glass()
                self._unblock_dice()
                if on_complete_callback:
                    on_complete_callback()

        for dice in self.dice_list:
            original_size = getattr(dice, 'original_size', dice.dice_size)
            self._animate_dice_shrink_with_move(dice, original_size, check_all_complete)

    def _raise_glass(self, on_complete_callback=None):
        # Блокируем кубики при подъёме стакана
        self._block_dice()

        if self.sound_glass_raise and not self.sound_manager.is_muted():
            self.sound_glass_raise.play()

        shadow_target_pos = (self.SHADOW_TARGET_POSITION_X, self.SHADOW_TARGET_POSITION_Y)

        for dice in self.dice_list:
            if dice.glow:
                dice.glow.update_position(dice.pos, dice.dice_size)
            dice.enable_glow()

        def on_animation_complete(*args):
            self.is_at_target = False
            if self._on_glass_move_complete:
                self._on_glass_move_complete()
            if on_complete_callback:
                on_complete_callback()
            self._update_point_a_marker()
            # Разблокируем кубики после подъёма стакана
            self._unblock_dice()

        self.glass.animate_movement(
            start_pos=self.glass_start_pos,
            end_pos=self.glass_target_pos,
            duration=0.6,
            forward=True,
            callback=on_animation_complete
        )

        self.shadow.animate_movement_to_target(
            target_pos=shadow_target_pos,
            duration=0.6,
            forward=True
        )

    def _lower_glass(self):
        # Блокируем кубики при опускании стакана
        self._block_dice()

        self.max_speed = 0
        self.last_touch_pos = None
        self.last_touch_time = None

        self.shadow.pos = (self.SHADOW_TARGET_POSITION_X, self.SHADOW_TARGET_POSITION_Y)
        shadow_target_pos = (self.SHADOW_POSITION_X, self.SHADOW_POSITION_Y)

        def on_animation_complete(*args):
            self.is_at_target = True
            if self.sound_glass_lower and not self.sound_manager.is_muted():
                self.sound_glass_lower.play()
            if self._on_glass_move_complete:
                self._on_glass_move_complete()
            self._update_point_a_marker()
            # Разблокируем кубики после опускания стакана
            self._unblock_dice()

        self.glass.animate_movement(
            start_pos=self.glass_target_pos,
            end_pos=self.glass_start_pos,
            duration=0.6,
            forward=False,
            callback=on_animation_complete
        )

        self.shadow.animate_movement_to_target(
            target_pos=shadow_target_pos,
            duration=0.6,
            forward=False
        )

    def _lower_glass_to_center(self, target_center_x, target_center_y):
        # Блокируем кубики при опускании стакана в центр
        self._block_dice()

        self.max_speed = 0
        self.last_touch_pos = None
        self.last_touch_time = None

        old_start_x = self.glass_start_pos[0]
        old_start_y = self.glass_start_pos[1]
        old_target_x = self.glass_target_pos[0]
        old_target_y = self.glass_target_pos[1]
        old_shadow_x = self.SHADOW_POSITION_X
        old_shadow_y = self.SHADOW_POSITION_Y
        old_shadow_target_x = self.SHADOW_TARGET_POSITION_X
        old_shadow_target_y = self.SHADOW_TARGET_POSITION_Y

        new_start_x = target_center_x - self.glass_size / 6.5
        new_start_y = target_center_y - self.glass_size / 2

        offset_x = new_start_x - old_start_x
        offset_y = new_start_y - old_start_y

        self.shadow.pos = (old_shadow_target_x, old_shadow_target_y)
        shadow_target_pos = (old_shadow_x + offset_x, old_shadow_y + offset_y)

        Clock.schedule_once(lambda dt: self._disable_glow_for_all_dice(), 0.5)

        def on_animation_complete(*args):
            self.glass_start_pos = (new_start_x, new_start_y)
            self.glass_target_pos = (old_target_x + offset_x, old_target_y + offset_y)
            self.SHADOW_POSITION_X = old_shadow_x + offset_x
            self.SHADOW_POSITION_Y = old_shadow_y + offset_y
            self.SHADOW_TARGET_POSITION_X = old_shadow_target_x + offset_x
            self.SHADOW_TARGET_POSITION_Y = old_shadow_target_y + offset_y

            self.glass.pos = self.glass_start_pos
            self.shadow.move_by_delta(offset_x, offset_y)

            self.is_at_target = True

            if self.sound_glass_lower and not self.sound_manager.is_muted():
                self.sound_glass_lower.play()

            if self.pending_hide_dice:
                for dice in self.dice_list:
                    dice.opacity = 0
                    if dice.glow:
                        dice.glow.opacity = 0
                self.dice_hidden = True
                self.pending_hide_dice = False

            self._update_point_a_marker()

            # Разблокируем кубики после опускания стакана
            self._unblock_dice()

            if self._on_glass_move_complete:
                self._on_glass_move_complete()

        self.glass.animate_movement(
            start_pos=self.glass_target_pos,
            end_pos=(new_start_x, new_start_y),
            duration=0.6,
            forward=False,
            callback=on_animation_complete
        )

        self.shadow.animate_movement_to_target(
            target_pos=shadow_target_pos,
            duration=0.6,
            forward=False
        )

    def _on_dice_click(self):
        """Обработка клика по кубику в зависимости от состояния"""
        # Проверяем, заблокированы ли кубики
        if self.is_dice_blocked:
            if DEBUG_MODE:
                print("🔒 [DiceScreen] Кубики заблокированы, клик игнорируется")
            return

        print(f"🔴 [DiceScreen] _on_dice_click ВЫЗВАН, is_dice_enlarged={self.is_dice_enlarged}, current_mode={self.current_mode}")

        if self.is_animating:
            print("   но is_animating=True")
            return

        if self.is_dice_enlarged:
            # Режим 3 - кубики увеличены, возвращаем в предыдущий режим (1 или 2)
            print("   Режим 3 (увеличенные кубики) - возвращаем на место")
            self._shrink_all_dice()
        else:
            # Режим 1 или 2 - переключаем между ними
            print(f"   Режим {self.current_mode} - переключаем на {3 - self.current_mode}")
            self._start_switch_animation()

    def on_enter(self):
        super().on_enter()
        self._load_dice_sounds()

        screen_width, screen_height = self.get_screen_size()

        self.dice_size = screen_width * 0.1
        self.large_dice_size = self.dice_size * 1.26
        self.glass_size = screen_width * 0.20
        self.shadow_size = self.glass_size * 0.9

        self.START_POSITION_DICE_X = screen_width * 0.3
        self.START_POSITION_DICE_Y = screen_height * 0.5 - (self.large_dice_size // 2)

        self.START_POSITION_GLASS_X = screen_width * 0.27
        self.START_POSITION_GLASS_Y = screen_height * 0.35

        self.SHADOW_POSITION_X = self.START_POSITION_GLASS_X + (self.glass_size * self.shadow_offset_x_factor)
        self.SHADOW_POSITION_Y = self.START_POSITION_GLASS_Y + (self.glass_size * self.shadow_offset_y_factor)

        self.glass_start_pos = (self.START_POSITION_GLASS_X, self.START_POSITION_GLASS_Y)
        self.glass_target_pos = (self.START_POSITION_GLASS_X + self.glass_size, self.START_POSITION_GLASS_Y - self.glass_size)

        self.SHADOW_TARGET_POSITION_X = self.SHADOW_POSITION_X + (self.glass_size * self.shadow_move_factor_x)
        self.SHADOW_TARGET_POSITION_Y = self.SHADOW_POSITION_Y - (self.glass_size * self.shadow_move_factor_y)

        self._setup_ui()

        Clock.schedule_once(lambda dt: self._create_drop_zone(), 0.1)

    def _create_drop_zone(self):
        screen_width, screen_height = self.get_screen_size()
        self.drop_zone = DropZone(screen_width, screen_height)
        self.layout.add_widget(self.drop_zone)

    def _create_point_a_marker(self):
        if DEBUG_MODE:
            self.point_a_marker = PointMarker(color=(1, 0, 0, 1), size=10)
        else:
            self.point_a_marker = PointMarker(color=(1, 1, 1, 0.4), size=2)

        self.layout.add_widget(self.point_a_marker, index=0)
        self._update_point_a_marker()

    def _update_point_a_marker(self):
        if self.point_a_marker and self.drop_zone:
            point_a_x = self.glass_start_pos[0] + self.glass_size / 6.5
            point_a_y = self.glass_start_pos[1] + self.glass_size / 2

            if DEBUG_MODE:
                in_zone = self.drop_zone.check_point_in_zone(point_a_x, point_a_y)
                if in_zone:
                    self.point_a_marker.color = (0, 1, 0, 1)
                else:
                    self.point_a_marker.color = (1, 0, 0, 1)
            else:
                self.point_a_marker.color = (1, 1, 1, 0.4)

            self.point_a_marker.update_position(point_a_x, point_a_y, visible=True)
            return in_zone if DEBUG_MODE else True
        return True

    def on_leave(self):
        if self.volume_fade_clock:
            self.volume_fade_clock.cancel()
            self.volume_fade_clock = None
        if self.sound_glass_drag:
            try:
                self.sound_glass_drag.stop()
            except:
                pass
        self._clear_all_dice()
        if self.glass and self.glass.parent:
            self.layout.remove_widget(self.glass)
            self.glass = None
        if self.shadow and self.shadow.parent:
            self.layout.remove_widget(self.shadow)
            self.shadow = None
        if self.drop_zone and self.drop_zone.parent:
            self.layout.remove_widget(self.drop_zone)
            self.drop_zone = None
        if self.point_a_marker and self.point_a_marker.parent:
            self.layout.remove_widget(self.point_a_marker)
            self.point_a_marker = None
        if self.bg and self.bg.parent:
            self.layout.remove_widget(self.bg)
            self.bg = None
        super().on_leave()

    def _setup_ui(self):
        if os.path.exists(self.background_image):
            self.bg = Image(source=self.background_image, allow_stretch=True, keep_ratio=False, size_hint=(1, 1))
            self.layout.add_widget(self.bg, index=0)

        self._create_point_a_marker()
        self._create_shadow()
        self._create_dice_for_mode(1, animate=False)
        self._create_glass()

    def _create_shadow(self):
        offset_x_px = self.glass_size * self.shadow_offset_x_factor
        offset_y_px = self.glass_size * self.shadow_offset_y_factor

        self.shadow = ShadowWidget(
            sprite_sheet_path=self.shadow_sprite_sheet_path,
            shadow_size=self.shadow_size,
            rows=2,
            cols=12,
            frame_index=0,
            rotation_angle=self.shadow_rotation,
            scale_factor=self.shadow_scale_factor,
            offset_x=offset_x_px,
            offset_y=offset_y_px,
            opacity=self.shadow_opacity,
            move_factor_x=self.shadow_move_factor_x,
            move_factor_y=self.shadow_move_factor_y,
            glass_size=self.glass_size,
            size_hint=(None, None),
            size=(self.shadow_size * self.shadow_scale_factor, self.shadow_size * self.shadow_scale_factor),
            pos=(self.SHADOW_POSITION_X, self.SHADOW_POSITION_Y)
        )
        self.shadow.set_frame(0)
        self.layout.add_widget(self.shadow)

    def _create_glass(self):
        self.glass = GlassWidget(
            sprite_sheet_path=self.glass_sprite_sheet_path,
            glass_size=self.glass_size,
            rows=2,
            cols=12,
            frame_index=0,
            rotation_angle=-90,
            size_hint=(None, None),
            size=(self.glass_size, self.glass_size),
            pos=self.glass_start_pos,
            on_glass_click=self._on_glass_click,
            on_glass_drag=self._on_glass_drag,
            on_glass_drag_end=self._on_glass_drag_end
        )
        self.glass.set_frame(0)
        self.layout.add_widget(self.glass)
        self.is_at_target = True

    def _update_dice_position(self, delta_x, delta_y):
        if not self.dice_list:
            return
        for dice in self.dice_list:
            new_x = dice.pos[0] + delta_x
            new_y = dice.pos[1] + delta_y
            dice.pos = (new_x, new_y)
            if dice.glow:
                dice.glow.update_position(dice.pos, dice.dice_size)

    def _on_glass_drag(self, delta_x, delta_y, touch):
        # Блокировка стакана - если заблокирован, игнорируем перетаскивание
        if self.is_glass_blocked:
            if DEBUG_MODE:
                print("🔒 [GLASS] Стакан заблокирован, перетаскивание игнорируется")
            return

        if self.is_animating:
            return
        if delta_x == 0 and delta_y == 0:
            return

        if self.is_at_target:
            current_time = Clock.get_time()
            current_pos = (touch.x, touch.y)

            if self.last_touch_pos is None or self.last_touch_time is None:
                self.last_touch_pos = current_pos
                self.last_touch_time = current_time
                current_speed = 0
            else:
                dx = current_pos[0] - self.last_touch_pos[0]
                dy = current_pos[1] - self.last_touch_pos[1]
                distance = math.sqrt(dx * dx + dy * dy)
                dt = current_time - self.last_touch_time
                if dt > 0:
                    current_speed = distance / dt
                    if current_speed > self.max_speed:
                        self.max_speed = current_speed
                else:
                    current_speed = 0
                self.last_touch_pos = current_pos
                self.last_touch_time = current_time

            MIN_SPEED = 50
            MAX_SPEED = 800
            MIN_VOLUME = 0.0
            MAX_VOLUME = 0.5

            if current_speed > MIN_SPEED:
                target_volume = MIN_VOLUME + (current_speed - MIN_SPEED) / (MAX_SPEED - MIN_SPEED) * (MAX_VOLUME - MIN_VOLUME)
                target_volume = max(MIN_VOLUME, min(MAX_VOLUME, target_volume))
            else:
                target_volume = 0.0

            if self.sound_glass_drag and not self.sound_manager.is_muted():
                if abs(target_volume - self.sound_glass_drag.volume) > 0.1:
                    self._fade_volume(target_volume, 0.1)
                else:
                    self.sound_glass_drag.volume = target_volume
        else:
            if self.sound_glass_drag:
                self._fade_volume(0.0, 0.2)

        if self.dice_hidden:
            self._update_dice_position(delta_x, delta_y)

        new_glass_x = self.glass.pos[0] + delta_x
        new_glass_y = self.glass.pos[1] + delta_y

        self.glass_start_pos = (self.glass_start_pos[0] + delta_x, self.glass_start_pos[1] + delta_y)
        self.glass_target_pos = (self.glass_target_pos[0] + delta_x, self.glass_target_pos[1] + delta_y)
        self.SHADOW_POSITION_X += delta_x
        self.SHADOW_POSITION_Y += delta_y
        self.SHADOW_TARGET_POSITION_X += delta_x
        self.SHADOW_TARGET_POSITION_Y += delta_y

        self.glass.pos = (new_glass_x, new_glass_y)
        self.shadow.move_by_delta(delta_x, delta_y)

        self._update_point_a_marker()

    def _on_glass_drag_end(self, touch):
        if DEBUG_MODE:
            print("🔴 [DRAG_END] Вызван")
        if self.sound_glass_drag:
            self._fade_volume(0.0, 0.3)
        self.last_touch_pos = None
        self.last_touch_time = None

    def _on_glass_click(self):
        # Блокировка стакана - если заблокирован, игнорируем клик
        if self.is_glass_blocked:
            if DEBUG_MODE:
                print("🔒 [GLASS] Стакан заблокирован, клик игнорируется")
            return

        if self.is_animating:
            return

        if self.is_at_target:
            if self.dice_hidden:
                self.play_dice_roll_sound()

                SPEED_THRESHOLD = 300

                if self.max_speed > SPEED_THRESHOLD:
                    for dice in self.dice_list:
                        dice.set_random_frame()
                else:
                    for dice in self.dice_list:
                        dice.set_random_frame_same_row()

                self.max_speed = 0
                self.last_touch_pos = None
                self.last_touch_time = None

                for dice in self.dice_list:
                    dice.opacity = 1
                    if dice.glow:
                        dice.glow.opacity = 1
                self.dice_hidden = False
                self.pending_hide_dice = False

                for dice in self.dice_list:
                    dice.enable_glow()

                def after_glass_raise():
                    Clock.schedule_once(lambda dt: self._animate_dice_appearance(), 0.1)

                self._raise_glass(on_complete_callback=after_glass_raise)
            else:
                self._raise_glass()
        else:
            if self.is_dice_enlarged:
                self._shrink_all_dice()
                Clock.schedule_once(lambda dt: self._process_glass_lower(), 0.4)
            else:
                self._process_glass_lower()

    def _process_glass_lower(self):
        if self.dice_list and not self.dice_hidden:
            if len(self.dice_list) == 1:
                target_dice = self.dice_list[0]
                dice_center_x = target_dice.pos[0] + target_dice.width / 2
                dice_center_y = target_dice.pos[1] + target_dice.height / 2
            else:
                total_x = 0
                total_y = 0
                for dice in self.dice_list:
                    total_x += dice.pos[0] + dice.width / 2
                    total_y += dice.pos[1] + dice.height / 2
                dice_center_x = total_x / len(self.dice_list)
                dice_center_y = total_y / len(self.dice_list)

            current_point_a_x = self.glass_start_pos[0] + self.glass_size / 6.5
            current_point_a_y = self.glass_start_pos[1] + self.glass_size / 2

            distance_x = abs(current_point_a_x - dice_center_x)
            distance_y = abs(current_point_a_y - dice_center_y)

            if distance_x <= 50 and distance_y <= 50:
                self.pending_hide_dice = True
                self._lower_glass_to_center(dice_center_x, dice_center_y)
            else:
                self._lower_glass()
        else:
            self._lower_glass()

    def _disable_glow_for_all_dice(self):
        for dice in self.dice_list:
            dice.disable_glow()

    def _on_glass_move_complete(self):
        pass

    def _on_appearance_complete(self, dice):
        self.animation_counter += 1
        if self.animation_counter >= 2:
            self.is_animating = False
            self.animation_counter = 0

    def _get_dice_center(self):
        if not self.dice_list:
            if self.last_dice_center:
                return self.last_dice_center
            center_x = self.START_POSITION_DICE_X + self.large_dice_size // 2
            center_y = self.START_POSITION_DICE_Y + self.large_dice_size // 2
            return (center_x, center_y)

        if len(self.dice_list) == 1:
            dice = self.dice_list[0]
            center = (dice.pos[0] + dice.width / 2, dice.pos[1] + dice.height / 2)
            self.last_dice_center = center
            return center
        else:
            total_x = 0
            total_y = 0
            for dice in self.dice_list:
                total_x += dice.pos[0] + dice.width / 2
                total_y += dice.pos[1] + dice.height / 2
            center = (total_x / len(self.dice_list), total_y / len(self.dice_list))
            self.last_dice_center = center
            return center

    def _create_dice_for_mode(self, mode, animate=True):
        self._clear_all_dice()
        self.dice_hidden = False
        self.pending_hide_dice = False
        self.is_dice_enlarged = False

        if not animate:
            if mode == 1:
                dice = DiceWidget(
                    sprite_sheet_path=self.sprite_sheet_path,
                    dice_size=self.large_dice_size,
                    rows=6,
                    cols=12,
                    frame_index=0,
                    rotation_angle=-90,
                    size_hint=(None, None),
                    size=(self.large_dice_size, self.large_dice_size),
                    pos=(self.START_POSITION_DICE_X, self.START_POSITION_DICE_Y),
                    on_dice_click=self._on_dice_click
                )
                dice.set_random_frame()
                dice.original_position = dice.pos
                dice.original_size = dice.dice_size
                self.layout.add_widget(dice)
                self.dice_list.append(dice)

            elif mode == 2:
                distance_between = self.dice_size * 0.3
                center_y = self.START_POSITION_DICE_Y + (self.large_dice_size // 2) - (self.dice_size // 2)

                y_top = center_y - distance_between
                y_bottom = center_y + distance_between

                dice1 = DiceWidget(
                    sprite_sheet_path=self.sprite_sheet_path,
                    dice_size=self.dice_size,
                    rows=6,
                    cols=12,
                    frame_index=0,
                    rotation_angle=-90,
                    size_hint=(None, None),
                    size=(self.dice_size, self.dice_size),
                    pos=(self.START_POSITION_DICE_X, y_top),
                    on_dice_click=self._on_dice_click
                )
                dice1.original_position = dice1.pos
                dice1.original_size = dice1.dice_size

                dice2 = DiceWidget(
                    sprite_sheet_path=self.sprite_sheet_path,
                    dice_size=self.dice_size,
                    rows=6,
                    cols=12,
                    frame_index=0,
                    rotation_angle=-90,
                    size_hint=(None, None),
                    size=(self.dice_size, self.dice_size),
                    pos=(self.START_POSITION_DICE_X, y_bottom),
                    on_dice_click=self._on_dice_click
                )
                dice2.original_position = dice2.pos
                dice2.original_size = dice2.dice_size

                dice1.set_random_frame()
                dice2.set_random_frame()

                self.layout.add_widget(dice1)
                self.layout.add_widget(dice2)
                self.dice_list.append(dice1)
                self.dice_list.append(dice2)

                Clock.schedule_once(lambda dt: dice1._create_glow(), 0)
                Clock.schedule_once(lambda dt: dice2._create_glow(), 0)

            if self.glass and self.glass.parent:
                self.layout.remove_widget(self.glass)
                self.layout.add_widget(self.glass)
            return

        center = self._get_dice_center()

        if mode == 1:
            target_x = center[0] - self.large_dice_size / 2
            target_y = center[1] - self.large_dice_size / 2
            start_pos = (target_x, target_y)

            dice = DiceWidget(
                sprite_sheet_path=self.sprite_sheet_path,
                dice_size=self.large_dice_size,
                rows=6,
                cols=12,
                frame_index=0,
                rotation_angle=-90,
                size_hint=(None, None),
                size=(self.large_dice_size, self.large_dice_size),
                pos=start_pos,
                on_dice_click=self._on_dice_click
            )
            dice.set_random_frame()
            self.layout.add_widget(dice)
            self.dice_list.append(dice)

            dice.animate_appearance_from_center(
                (target_x, target_y),
                start_pos,
                self.appear_duration,
                None
            )

        elif mode == 2:
            distance_between = self.dice_size * 0.3

            y_top = center[1] - distance_between - self.dice_size / 2
            y_bottom = center[1] + distance_between - self.dice_size / 2
            dice_x = center[0] - self.dice_size / 2

            start_pos = (center[0] - self.dice_size / 2, center[1] - self.dice_size / 2)

            dice1 = DiceWidget(
                sprite_sheet_path=self.sprite_sheet_path,
                dice_size=self.dice_size,
                rows=6,
                cols=12,
                frame_index=0,
                rotation_angle=-90,
                size_hint=(None, None),
                size=(self.dice_size, self.dice_size),
                pos=start_pos,
                on_dice_click=self._on_dice_click
            )

            dice2 = DiceWidget(
                sprite_sheet_path=self.sprite_sheet_path,
                dice_size=self.dice_size,
                rows=6,
                cols=12,
                frame_index=0,
                rotation_angle=-90,
                size_hint=(None, None),
                size=(self.dice_size, self.dice_size),
                pos=start_pos,
                on_dice_click=self._on_dice_click
            )

            self.layout.add_widget(dice1)
            self.layout.add_widget(dice2)
            self.dice_list.append(dice1)
            self.dice_list.append(dice2)

            self.is_animating = True
            self.animation_counter = 0

            Clock.schedule_once(lambda dt: dice1._create_glow(), 0)
            Clock.schedule_once(lambda dt: dice2._create_glow(), 0)

            dice1.animate_appearance_from_center(
                (dice_x, y_top),
                start_pos,
                self.appear_duration,
                self._on_appearance_complete
            )
            dice2.animate_appearance_from_center(
                (dice_x, y_bottom),
                start_pos,
                self.appear_duration,
                self._on_appearance_complete
            )

        if self.glass and self.glass.parent:
            self.layout.remove_widget(self.glass)
            self.layout.add_widget(self.glass)

    def _start_switch_animation(self):
        print("🔴 [DiceScreen] _start_switch_animation ВЫЗВАН")
        if self.is_animating:
            print("   но is_animating=True")
            return

        if self.is_dice_enlarged:
            print("   Кубики увеличены - возвращаем на место вместо переключения")
            self._shrink_all_dice()
            return

        self.is_animating = True
        self._get_dice_center()

        if self.current_mode == 1:
            print("   переключаем 1→2")
            self._animate_one_to_two()
        else:
            print("   переключаем 2→1")
            self._animate_two_to_one()

    def _animate_one_to_two(self):
        print("🔴 [DiceScreen] _animate_one_to_two ВЫЗВАН")
        if not self.dice_list:
            self.is_animating = False
            return

        old_dice = self.dice_list[0]
        old_dice.animate_disappear_in_place(self.disappear_duration, None)

        appear_delay = self.disappear_duration - self.overlap_time
        Clock.schedule_once(lambda dt: self._create_small_dice(), appear_delay)

    def _create_small_dice(self):
        self._clear_all_dice()
        self.current_mode = 2
        self._create_dice_for_mode(2, animate=True)

    def _animate_two_to_one(self):
        if len(self.dice_list) < 2:
            self.is_animating = False
            return

        dice_top = self.dice_list[0]
        dice_bottom = self.dice_list[1]

        center = self._get_dice_center()
        center_pos = (center[0] - self.large_dice_size / 2, center[1] - self.large_dice_size / 2)

        def on_single_disappear():
            pass

        dice_top.animate_disappear_to_center(center_pos, self.disappear_duration, on_single_disappear)
        dice_bottom.animate_disappear_to_center(center_pos, self.disappear_duration, on_single_disappear)

        appear_delay = self.disappear_duration - self.overlap_time
        Clock.schedule_once(lambda dt: self._create_big_dice(), appear_delay)

    def _create_big_dice(self):
        self._clear_all_dice()
        self.current_mode = 1
        self._create_dice_for_mode(1, animate=True)
        self.is_animating = False

    def _clear_all_dice(self):
        for dice in self.dice_list:
            if dice.parent:
                self.layout.remove_widget(dice)
        self.dice_list.clear()

    def go_to_menu(self):
        if self.volume_fade_clock:
            self.volume_fade_clock.cancel()
            self.volume_fade_clock = None
        if self.sound_glass_drag:
            try:
                self.sound_glass_drag.stop()
            except:
                pass
        self._clear_all_dice()
        if self.glass and self.glass.parent:
            self.layout.remove_widget(self.glass)
            self.glass = None
        if self.shadow and self.shadow.parent:
            self.layout.remove_widget(self.shadow)
            self.shadow = None
        if self.drop_zone and self.drop_zone.parent:
            self.layout.remove_widget(self.drop_zone)
            self.drop_zone = None
        if self.point_a_marker and self.point_a_marker.parent:
            self.layout.remove_widget(self.point_a_marker)
            self.point_a_marker = None
        self.play_back_sound()
        self.sound_manager.fade_to(1.0, duration=0.5)
        from main import switch_screen
        switch_screen('menu')
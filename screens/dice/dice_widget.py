"""
Виджет кубика
"""
import os
import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate, Translate, Line
from PIL import Image as PILImage
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.utils import platform

from .glow_effect import GlowEffect

DEBUG_MODE = False


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
        """Генерирует последовательность кадров для анимации вращения"""
        total_frames = self.rows * self.cols
        start_row = start_frame // self.cols
        start_col = start_frame % self.cols

        frames = []

        for rotation in range(num_rotations):
            for col_offset in range(1, self.cols + 1):
                new_col = (start_col + col_offset) % self.cols
                frames.append(start_row * self.cols + new_col)

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

        frames = []
        for rotation in range(5):
            for col in range(1, self.cols + 1):
                frames.append(start_row * self.cols + (col % self.cols))

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
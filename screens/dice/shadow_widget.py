"""
Виджет тени стакана
"""
import os
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate, Translate
from PIL import Image as PILImage
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.utils import platform


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
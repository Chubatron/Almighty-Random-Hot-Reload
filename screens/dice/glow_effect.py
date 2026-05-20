"""
Эффект свечения под кубиком
"""
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate, Translate, Ellipse


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
"""
Зона для сброса стакана
"""
import math
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line

DEBUG_MODE = False


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